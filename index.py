import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from flask_session import Session
from datetime import datetime, date
import pandas as pd
import json
import plotly
import plotly.express as px
import database
import auth
import ai_helper
import reports
import markdown

app = Flask(__name__)
app.config["SECRET_KEY"] = os.urandom(24)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)

DEFAULT_CATEGORIES = ["Food", "Housing", "Utilities", "Transport", "Entertainment", "Healthcare", "Shopping", "Education", "Travel", "Others"]

def login_required(f):
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = auth.authenticate_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['chat_history'] = []
            flash(f"Welcome back, {user['username'].capitalize()}!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password.", "danger")
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    password_confirm = request.form.get('password_confirm', '')
    
    if not username:
        flash("Username cannot be empty.", "danger")
    elif len(password) < 6:
        flash("Password must be at least 6 characters.", "danger")
    elif password != password_confirm:
        flash("Passwords do not match.", "danger")
    else:
        success = auth.register_user(username, password)
        if success:
            flash("Account created successfully! You can now log in.", "success")
        else:
            flash("Username already exists. Please choose a different one.", "danger")
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/set_gemini_key', methods=['POST'])
def set_gemini_key():
    session['gemini_key'] = request.form.get('api_key', '')
    flash("Gemini API Key updated!", "success")
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    username = session['username']
    
    expenses = database.get_expenses(user_id)
    savings_goals = database.get_savings_goals(user_id)
    current_month_str = datetime.now().strftime("%Y-%m")
    budgets = database.get_budgets(user_id, current_month_str)
    
    df_exp = pd.DataFrame(expenses) if expenses else pd.DataFrame(columns=["id", "user_id", "amount", "category", "date", "description"])
    if not df_exp.empty:
        df_exp['amount'] = df_exp['amount'].astype(float)
        df_exp['date'] = pd.to_datetime(df_exp['date'])
        df_current_month = df_exp[df_exp['date'].dt.strftime("%Y-%m") == current_month_str]
    else:
        df_current_month = pd.DataFrame(columns=["id", "user_id", "amount", "category", "date", "description"])
        
    total_spent = df_current_month['amount'].sum() if not df_current_month.empty else 0.0
    month_budgets = {b['category']: b['limit_amount'] for b in budgets}
    total_budget = sum(month_budgets.values())
    
    total_savings_target = sum(g['target_amount'] for g in savings_goals)
    total_savings = sum(g['current_amount'] for g in savings_goals)
    tx_count = len(df_current_month)
    
    alerts = []
    cat_spending = {}
    if not df_current_month.empty and month_budgets:
        cat_spending = df_current_month.groupby('category')['amount'].sum().to_dict()
        for cat, spent in cat_spending.items():
            if cat in month_budgets:
                limit = month_budgets[cat]
                pct = (spent / limit) * 100
                if pct >= 100:
                    alerts.append({"cat": cat, "spent": spent, "limit": limit, "pct": pct, "type": "danger"})
                elif pct >= 80:
                    alerts.append({"cat": cat, "spent": spent, "limit": limit, "pct": pct, "type": "warning"})

    pie_json = "{}"
    line_json = "{}"
    
    if tx_count > 0:
        cat_group = df_current_month.groupby('category')['amount'].sum().reset_index()
        fig_pie = px.pie(cat_group, values='amount', names='category', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#F8FAFC', margin=dict(t=10, b=10, l=10, r=10), legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
        pie_json = json.dumps(fig_pie, cls=plotly.utils.PlotlyJSONEncoder)
        
        daily_spending = df_current_month.groupby('date')['amount'].sum().reset_index().sort_values('date')
        fig_line = px.line(daily_spending, x='date', y='amount', markers=True, line_shape='linear', labels={'date': 'Date', 'amount': 'Amount Spent ($)'})
        fig_line.update_traces(line_color='#60A5FA', marker=dict(size=8, color='#3B82F6'))
        fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#F8FAFC', xaxis=dict(showgrid=True, gridcolor='#334155'), yaxis=dict(showgrid=True, gridcolor='#334155'), margin=dict(t=20, b=20, l=20, r=20))
        line_json = json.dumps(fig_line, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('dashboard.html', username=username, total_spent=total_spent, total_budget=total_budget, 
                           total_savings=total_savings, total_savings_target=total_savings_target, tx_count=tx_count, 
                           alerts=alerts, month_budgets=month_budgets, cat_spending=cat_spending, pie_json=pie_json, line_json=line_json)

@app.route('/expenses')
@login_required
def expenses():
    user_id = session['user_id']
    expenses = database.get_expenses(user_id)
    db_categories = list(set([e['category'] for e in expenses])) if expenses else []
    categories = sorted(list(set(DEFAULT_CATEGORIES + db_categories)))
    
    filter_cat = request.args.get('filter_cat', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    f_cat = filter_cat if filter_cat else None
    f_start = start_date if start_date else None
    f_end = end_date if end_date else None
    
    filtered_expenses = database.get_expenses(user_id, category=f_cat, start_date=f_start, end_date=f_end)
    today_date = date.today().strftime("%Y-%m-%d")
    
    return render_template('expenses.html', categories=categories, expenses_list=filtered_expenses, 
                           today_date=today_date, filter_cat=filter_cat, start_date=start_date, end_date=end_date)

@app.route('/expenses/add', methods=['POST'])
@login_required
def add_expense():
    amount = float(request.form.get('amount'))
    cat_choice = request.form.get('category')
    custom_cat = request.form.get('custom_category', '').strip()
    expense_date = request.form.get('date')
    description = request.form.get('description', '').strip()
    
    final_cat = custom_cat if cat_choice == "custom" else cat_choice
    if cat_choice == "custom" and not final_cat:
        flash("Custom category name cannot be empty.", "danger")
    else:
        database.add_expense(session['user_id'], amount, final_cat.capitalize(), expense_date, description)
        flash(f"Expense of ${amount:.2f} in '{final_cat.capitalize()}' added!", "success")
    return redirect(url_for('expenses'))

@app.route('/expenses/delete/<int:exp_id>', methods=['POST'])
@login_required
def delete_exp(exp_id):
    if database.delete_expense(exp_id, session['user_id']):
        flash("Expense deleted successfully!", "success")
    return redirect(url_for('expenses'))

@app.route('/budgets')
@login_required
def budgets():
    user_id = session['user_id']
    expenses = database.get_expenses(user_id)
    db_categories = list(set([e['category'] for e in expenses])) if expenses else []
    categories = sorted(list(set(DEFAULT_CATEGORIES + db_categories)))
    
    current_month_str = datetime.now().strftime("%Y-%m")
    active_budgets = database.get_budgets(user_id, current_month_str)
    savings_goals = database.get_savings_goals(user_id)
    
    return render_template('budgets.html', categories=categories, active_budgets=active_budgets, 
                           current_month_str=current_month_str, savings_goals=savings_goals)

@app.route('/budgets/set', methods=['POST'])
@login_required
def set_budget():
    category = request.form.get('category')
    limit_amount = float(request.form.get('limit_amount'))
    month_year = request.form.get('month_year')
    database.set_budget(session['user_id'], category, limit_amount, month_year)
    flash(f"Budget for '{category}' set to ${limit_amount:.2f} for {month_year}!", "success")
    return redirect(url_for('budgets'))

@app.route('/budgets/delete', methods=['POST'])
@login_required
def delete_budget():
    category = request.form.get('category')
    month_year = request.form.get('month_year')
    database.delete_budget(session['user_id'], category, month_year)
    flash(f"Budget for '{category}' deleted!", "success")
    return redirect(url_for('budgets'))

@app.route('/savings/add', methods=['POST'])
@login_required
def create_savings_goal():
    goal_name = request.form.get('goal_name').strip()
    target_amount = float(request.form.get('target_amount'))
    current_amount = float(request.form.get('current_amount', 0))
    target_date = request.form.get('target_date')
    
    if not goal_name:
        flash("Goal name cannot be empty.", "danger")
    elif current_amount > target_amount:
        flash("Currently saved cannot be larger than target amount.", "danger")
    else:
        database.add_savings_goal(session['user_id'], goal_name, target_amount, current_amount, target_date)
        flash(f"Savings Goal '{goal_name}' created!", "success")
    return redirect(url_for('budgets'))

@app.route('/savings/update', methods=['POST'])
@login_required
def update_savings_goal():
    goal_id = request.form.get('goal_id')
    new_amount = float(request.form.get('new_amount'))
    database.update_savings_progress(session['user_id'], goal_id, new_amount)
    flash(f"Updated balance to ${new_amount:.2f}!", "success")
    return redirect(url_for('budgets'))

@app.route('/savings/delete/<int:goal_id>', methods=['POST'])
@login_required
def delete_savings_goal(goal_id):
    database.delete_savings_goal(session['user_id'], goal_id)
    flash("Goal deleted.", "success")
    return redirect(url_for('budgets'))

@app.route('/reports')
@login_required
def reports_page():
    user_id = session['user_id']
    selected_month = request.args.get('report_month', datetime.now().strftime("%Y-%m"))
    expenses = database.get_expenses(user_id)
    
    df_all = pd.DataFrame(expenses) if expenses else pd.DataFrame()
    if not df_all.empty:
        df_all['date_dt'] = pd.to_datetime(df_all['date'])
        df_month = df_all[df_all['date_dt'].dt.strftime("%Y-%m") == selected_month]
    else:
        df_month = pd.DataFrame()
        
    if df_month.empty:
        return render_template('reports.html', has_data=False, selected_month=selected_month)
        
    total_spent = df_month['amount'].sum()
    num_transactions = len(df_month)
    largest_expense = df_month['amount'].max()
    avg_spend = total_spent / num_transactions
    month_label = datetime.strptime(selected_month, "%Y-%m").strftime('%B %Y')
    
    return render_template('reports.html', has_data=True, selected_month=selected_month, month_label=month_label,
                           total_spent=total_spent, num_transactions=num_transactions, largest_expense=largest_expense, avg_spend=avg_spend)

@app.route('/export/csv', methods=['POST'])
@login_required
def export_csv():
    month_str = request.form.get('month_str')
    expenses = database.get_expenses(session['user_id'])
    df_all = pd.DataFrame(expenses)
    df_all['date_dt'] = pd.to_datetime(df_all['date'])
    df_month = df_all[df_all['date_dt'].dt.strftime("%Y-%m") == month_str]
    
    csv_data = reports.generate_csv(df_month.to_dict('records'))
    
    import io
    from flask import send_file
    return send_file(io.BytesIO(csv_data), mimetype='text/csv', as_attachment=True, download_name=f'expense_report_{month_str}.csv')

@app.route('/export/pdf', methods=['POST'])
@login_required
def export_pdf():
    month_str = request.form.get('month_str')
    user_id = session['user_id']
    expenses = database.get_expenses(user_id)
    
    df_all = pd.DataFrame(expenses)
    df_all['date_dt'] = pd.to_datetime(df_all['date'])
    df_month = df_all[df_all['date_dt'].dt.strftime("%Y-%m") == month_str]
    
    cat_breakdown = df_month.groupby('category')['amount'].sum().rename('Spent').reset_index().rename(columns={'category': 'Category'})
    month_budgets = database.get_budgets(user_id, month_str)
    budget_status = {b['category']: {'limit': b['limit_amount']} for b in month_budgets}
    
    pdf_data = reports.generate_pdf(session['username'], month_str, df_month.to_dict('records'), cat_breakdown, budget_status)
    
    import io
    from flask import send_file
    return send_file(io.BytesIO(pdf_data), mimetype='application/pdf', as_attachment=True, download_name=f'expense_report_{month_str}.pdf')

@app.route('/ai_advisor', methods=['GET'])
@login_required
def ai_advisor():
    chat_history = session.get('chat_history', [])
    analysis_html = session.get('analysis_html', '')
    return render_template('ai_advisor.html', chat_history=chat_history, analysis_html=analysis_html, analysis_result=bool(analysis_html))

@app.route('/ai_analyze', methods=['POST'])
@login_required
def ai_analyze():
    user_id = session['user_id']
    api_key = session.get('gemini_key')
    expenses = database.get_expenses(user_id)
    savings_goals = database.get_savings_goals(user_id)
    budgets = database.get_budgets(user_id, datetime.now().strftime("%Y-%m"))
    
    res = ai_helper.analyze_spending_habits(expenses, budgets, savings_goals, api_key)
    session['analysis_html'] = markdown.markdown(res)
    return redirect(url_for('ai_advisor'))

@app.route('/ask_ai', methods=['POST'])
@login_required
def ask_ai():
    question = request.json.get('question')
    user_id = session['user_id']
    api_key = session.get('gemini_key')
    expenses = database.get_expenses(user_id)
    savings_goals = database.get_savings_goals(user_id)
    budgets = database.get_budgets(user_id, datetime.now().strftime("%Y-%m"))
    
    history = session.get('chat_history', [])
    history.append({'role': 'user', 'content': question})
    
    res = ai_helper.ask_financial_assistant(question, history, expenses, budgets, savings_goals, api_key)
    
    # We must format as markdown. Here we do it via python markdown for simple things or let frontend handle it.
    # To keep simple, we can render it in backend.
    res_html = markdown.markdown(res)
    history.append({'role': 'assistant', 'content': res_html})
    session['chat_history'] = history
    session.modified = True
    
    return jsonify({'answer': res_html})

@app.route('/clear_chat', methods=['POST'])
@login_required
def clear_chat():
    session['chat_history'] = []
    return redirect(url_for('ai_advisor'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
