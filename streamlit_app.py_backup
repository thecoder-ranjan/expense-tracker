import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import os
import database
import auth
import ai_helper
import reports

# Set Streamlit Page Config
st.set_page_config(
    page_title="Antigravity Expense Tracker",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Glassmorphism & Sleek Cards)
st.markdown("""
<style>
    /* Main Layout Styling */
    .stApp {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        color: #F8FAFC;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit Main Menu & Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background-color: transparent !important;}
    
    /* Card Styles */
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        backdrop-filter: blur(8px);
        margin-bottom: 15px;
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        margin-top: 5px;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Form & Input adjustments */
    div[data-baseweb="select"] > div {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
    }
    
    /* Alert Banners */
    .custom-alert {
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 12px;
        font-weight: 500;
    }
    .custom-alert-danger {
        background-color: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.3);
        color: #FCA5A5;
    }
    .custom-alert-warning {
        background-color: rgba(245, 158, 11, 0.15);
        border: 1px solid rgba(245, 158, 11, 0.3);
        color: #FDE047;
    }
</style>
""", unsafe_allow_html=True)

# Define Core Categories
DEFAULT_CATEGORIES = ["Food", "Housing", "Utilities", "Transport", "Entertainment", "Healthcare", "Shopping", "Education", "Travel", "Others"]

# Initialize Session State
if 'user' not in st.session_state:
    st.session_state['user'] = None
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'gemini_key' not in st.session_state:
    st.session_state['gemini_key'] = ""

def logout():
    st.session_state['user'] = None
    st.session_state['chat_history'] = []
    st.rerun()

def show_auth_page():
    """Displays user login/signup panel."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div style='text-align: center; margin-top: 50px;'><h1 style='color:#60A5FA; font-size:3rem; margin-bottom:5px;'>💸 Antigravity</h1><p style='color:#94A3B8; font-size:1.1rem; margin-bottom:30px;'>Your Smart Personal Expense & Savings Assistant</p></div>", unsafe_allow_html=True)
        
        tab_login, tab_signup = st.tabs(["🔐 Sign In", "📝 Create Account"])
        
        with tab_login:
            st.write("Welcome back! Please enter your details below.")
            login_user = st.text_input("Username", key="login_username").strip()
            login_pwd = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Log In", use_container_width=True):
                user = auth.authenticate_user(login_user, login_pwd)
                if user:
                    st.session_state['user'] = user
                    st.toast(f"Welcome back, {user['username'].capitalize()}!", icon="👋")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
                    
        with tab_signup:
            st.write("Register a new secure account.")
            signup_user = st.text_input("Username", key="signup_username").strip()
            signup_pwd = st.text_input("Password", type="password", key="signup_password")
            signup_pwd_confirm = st.text_input("Confirm Password", type="password", key="signup_password_confirm")
            
            if st.button("Sign Up", use_container_width=True):
                if not signup_user:
                    st.error("Username cannot be empty.")
                elif len(signup_pwd) < 6:
                    st.error("Password must be at least 6 characters.")
                elif signup_pwd != signup_pwd_confirm:
                    st.error("Passwords do not match.")
                else:
                    success = auth.register_user(signup_user, signup_pwd)
                    if success:
                        st.success("Account created successfully! You can now log in.")
                    else:
                        st.error("Username already exists. Please choose a different one.")

def render_dashboard(user_id, user_name, expenses, budgets, savings_goals):
    """Renders the main dashboard metrics and charts."""
    st.markdown(f"## 📊 Financial Overview for {user_name.capitalize()}")
    
    # Pre-process expenses data
    df_exp = pd.DataFrame(expenses) if expenses else pd.DataFrame(columns=["id", "user_id", "amount", "category", "date", "description"])
    if not df_exp.empty:
        df_exp['amount'] = df_exp['amount'].astype(float)
        df_exp['date'] = pd.to_datetime(df_exp['date'])
        
    current_month_str = datetime.now().strftime("%Y-%m")
    
    # Filter for current month's expenses
    if not df_exp.empty:
        df_current_month = df_exp[df_exp['date'].dt.strftime("%Y-%m") == current_month_str]
    else:
        df_current_month = pd.DataFrame(columns=["id", "user_id", "amount", "category", "date", "description"])
        
    total_spent_month = df_current_month['amount'].sum() if not df_current_month.empty else 0.0
    
    # Calculate budget summary for current month
    month_budgets = {b['category']: b['limit_amount'] for b in budgets}
    total_budget_limit = sum(month_budgets.values())
    
    # Budget alert checks
    alerts = []
    if not df_current_month.empty and month_budgets:
        cat_spending = df_current_month.groupby('category')['amount'].sum().to_dict()
        for cat, spent in cat_spending.items():
            if cat in month_budgets:
                limit = month_budgets[cat]
                pct = (spent / limit) * 100
                if pct >= 100:
                    alerts.append((cat, spent, limit, "danger"))
                elif pct >= 80:
                    alerts.append((cat, spent, limit, "warning"))

    # Render Budget Warnings Alert Section
    if alerts:
        st.markdown("### 🔔 Budget Notifications")
        for cat, spent, limit, alert_type in alerts:
            pct = (spent / limit) * 100
            if alert_type == "danger":
                st.markdown(f"""
                <div class="custom-alert custom-alert-danger">
                    🚨 <b>Over Budget:</b> You have exceeded your <b>{cat}</b> budget! Spent: <b>${spent:,.2f}</b> (Limit: ${limit:,.2f} | <b>{pct:.1f}%</b> used).
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="custom-alert custom-alert-warning">
                    ⚠️ <b>Budget Warning:</b> You have used 80%+ of your <b>{cat}</b> budget! Spent: <b>${spent:,.2f}</b> (Limit: ${limit:,.2f} | <b>{pct:.1f}%</b> used).
                </div>
                """, unsafe_allow_html=True)
        st.write("")

    # Summary KPI Cards
    col_spent, col_budget, col_savings, col_count = st.columns(4)
    
    with col_spent:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Spent This Month</div>
            <div class="metric-value" style="color: #EF4444;">${total_spent_month:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_budget:
        budget_color = "#3B82F6" if total_budget_limit > 0 else "#64748B"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Monthly Budget</div>
            <div class="metric-value" style="color: {budget_color};">${total_budget_limit:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_savings:
        # Calculate total savings targets and current savings accumulated
        total_savings_target = sum(g['target_amount'] for g in savings_goals)
        total_savings_current = sum(g['current_amount'] for g in savings_goals)
        savings_color = "#10B981" if total_savings_current > 0 else "#64748B"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Total Savings Progress</div>
            <div class="metric-value" style="color: {savings_color};">${total_savings_current:,.2f} / ${total_savings_target:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_count:
        tx_count = len(df_current_month)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Month Transactions</div>
            <div class="metric-value" style="color: #F59E0B;">{tx_count}</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # If no data, display a nice empty state illustration and guide
    if df_exp.empty:
        st.info("💡 **Welcome to your new Expense Tracker!** Tap the '💸 Expenses Manager' tab in the left sidebar to add your first expense.")
        return

    # Visualizations layout (2 Columns)
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("### 🍩 Spending by Category (This Month)")
        if not df_current_month.empty:
            cat_group = df_current_month.groupby('category')['amount'].sum().reset_index()
            fig = px.pie(
                cat_group, 
                values='amount', 
                names='category', 
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#F8FAFC',
                margin=dict(t=10, b=10, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No transactions recorded for the current month.")

    with col_chart2:
        st.markdown("### 📈 Daily Spending Trend")
        if not df_current_month.empty:
            # Group by Date and Sum
            daily_spending = df_current_month.groupby('date')['amount'].sum().reset_index()
            # Sort by date
            daily_spending = daily_spending.sort_values('date')
            
            fig = px.line(
                daily_spending,
                x='date',
                y='amount',
                markers=True,
                line_shape='linear',
                labels={'date': 'Date', 'amount': 'Amount Spent ($)'}
            )
            # Style chart to match dark mode theme
            fig.update_traces(line_color='#60A5FA', marker=dict(size=8, color='#3B82F6'))
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#F8FAFC',
                xaxis=dict(showgrid=True, gridcolor='#334155'),
                yaxis=dict(showgrid=True, gridcolor='#334155'),
                margin=dict(t=20, b=20, l=20, r=20)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No data available.")

    # Budget Utilization Progress Bars (Full Width)
    st.markdown("### 📊 Budget Progress tracker (Current Month)")
    if month_budgets:
        # Loop through each category budget and show progress bar
        cat_spending = df_current_month.groupby('category')['amount'].sum().to_dict() if not df_current_month.empty else {}
        
        for cat, limit in month_budgets.items():
            spent = cat_spending.get(cat, 0.0)
            pct = (spent / limit) if limit > 0 else 0
            pct_display = min(pct, 1.0)
            
            # Select colors based on usage
            if pct >= 1.0:
                bar_color = "red"
                status_text = f"🚨 Over Budget (${spent:,.2f} spent of ${limit:,.2f})"
            elif pct >= 0.8:
                bar_color = "orange"
                status_text = f"⚠️ Warning: {pct*100:.1f}% used (${spent:,.2f} spent of ${limit:,.2f})"
            else:
                bar_color = "green"
                status_text = f"✅ Healthy: {pct*100:.1f}% used (${spent:,.2f} spent of ${limit:,.2f})"
                
            st.write(f"**{cat}**")
            st.progress(pct_display, text=status_text)
    else:
        st.info("No budget limits set. Head to the '🎯 Budgets & Savings Goals' tab to configure category limits.")

def render_expense_manager(user_id, expenses):
    """Enables adding, viewing, filtering, and deleting expenses."""
    st.markdown("## 💸 Expense Manager")
    
    # Retrieve categories used in database, plus default ones
    db_categories = list(set([e['category'] for e in expenses])) if expenses else []
    categories = sorted(list(set(DEFAULT_CATEGORIES + db_categories)))
    
    # 2-Column layout: Left for Adding Expense, Right for Viewing/Filtering & Deleting
    col_add, col_list = st.columns([1, 2])
    
    with col_add:
        st.markdown("### ➕ Add Daily Expense")
        with st.form("add_expense_form", clear_on_submit=True):
            amount = st.number_input("Amount ($)", min_value=0.01, step=0.01, format="%.2f")
            
            # Select Category with custom option
            cat_choice = st.selectbox("Category", categories + ["➕ Add Custom Category"])
            custom_cat = ""
            if cat_choice == "➕ Add Custom Category":
                custom_cat = st.text_input("Enter Custom Category Name").strip()
                
            expense_date = st.date_input("Date", max_value=date.today())
            description = st.text_input("Description / Notes (Optional)").strip()
            
            submitted = st.form_submit_button("Save Expense")
            if submitted:
                # Resolve category
                final_cat = custom_cat if cat_choice == "➕ Add Custom Category" else cat_choice
                if cat_choice == "➕ Add Custom Category" and not final_cat:
                    st.error("Custom category name cannot be empty.")
                else:
                    expense_id = database.add_expense(
                        user_id=user_id,
                        amount=amount,
                        category=final_cat.capitalize(),
                        date=expense_date.strftime("%Y-%m-%d"),
                        description=description
                    )
                    if expense_id:
                        st.success(f"Expense of ${amount:.2f} in '{final_cat.capitalize()}' added!")
                        st.rerun()
                    else:
                        st.error("Failed to add expense. Try again.")

    with col_list:
        st.markdown("### 🔍 Expense History")
        
        # Filtering controls
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filter_cat = st.selectbox("Filter by Category", ["All"] + categories)
        with col_f2:
            # Let's default to last 30 days
            min_date = date.today() - pd.Timedelta(days=30)
            filter_dates = st.date_input("Filter by Date Range", [min_date, date.today()])
            
        # Perform filter query
        f_cat = None if filter_cat == "All" else filter_cat
        f_start = None
        f_end = None
        
        if isinstance(filter_dates, (list, tuple)) and len(filter_dates) == 2:
            f_start = filter_dates[0].strftime("%Y-%m-%d")
            f_end = filter_dates[1].strftime("%Y-%m-%d")
            
        filtered_expenses = database.get_expenses(user_id, category=f_cat, start_date=f_start, end_date=f_end)
        
        if filtered_expenses:
            df_filtered = pd.DataFrame(filtered_expenses)
            
            # Show interactive dataframe
            # Format clean column names
            df_display = df_filtered.rename(columns={
                'date': 'Date',
                'category': 'Category',
                'amount': 'Amount ($)',
                'description': 'Description'
            })[['Date', 'Category', 'Amount ($)', 'Description']]
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Delete Expense Section
            st.markdown("### 🗑️ Delete Expense")
            # Generate options for deletion dropdown
            delete_options = {
                e['id']: f"[{e['date']}] {e['category']} - ${e['amount']:.2f} ({e['description'][:15] if e['description'] else 'No Details'})"
                for e in filtered_expenses
            }
            
            col_d1, col_d2 = st.columns([3, 1])
            with col_d1:
                to_delete_id = st.selectbox("Select expense to delete", list(delete_options.keys()), format_func=lambda x: delete_options[x], label_visibility="collapsed")
            with col_d2:
                if st.button("Delete Selected", type="primary", use_container_width=True):
                    success = database.delete_expense(to_delete_id, user_id)
                    if success:
                        st.success("Expense deleted successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to delete expense.")
        else:
            st.info("No matching expenses found for the selected filters.")

def render_budgets_and_savings(user_id, expenses, budgets, savings_goals):
    """Enables setting budgets and tracking savings goals."""
    st.markdown("## 🎯 Budgets & Savings Goals")
    
    tab_budgets, tab_savings = st.tabs(["📊 Category Budgets", "💰 Savings Tracker"])
    
    # Extract unique categories
    db_categories = list(set([e['category'] for e in expenses])) if expenses else []
    categories = sorted(list(set(DEFAULT_CATEGORIES + db_categories)))
    
    with tab_budgets:
        col_b1, col_b2 = st.columns([1, 2])
        
        with col_b1:
            st.markdown("### ⚙️ Set/Update Category Budget")
            with st.form("set_budget_form", clear_on_submit=True):
                cat_budget = st.selectbox("Category", categories)
                budget_amount = st.number_input("Monthly Limit ($)", min_value=1.0, step=10.0, format="%.2f")
                budget_month = st.date_input("Target Month", value=date.today())
                
                submitted = st.form_submit_button("Save Budget")
                if submitted:
                    month_str = budget_month.strftime("%Y-%m")
                    database.set_budget(user_id, cat_budget, budget_amount, month_str)
                    st.success(f"Budget for '{cat_budget}' set to ${budget_amount:.2f} for {month_str}!")
                    st.rerun()
                    
        with col_b2:
            st.markdown("### 📋 Configured Budgets")
            current_month_str = datetime.now().strftime("%Y-%m")
            
            # Option to choose which month to view
            view_month = st.date_input("View Budgets for Month", value=date.today(), key="budget_view_month")
            view_month_str = view_month.strftime("%Y-%m")
            
            active_budgets = database.get_budgets(user_id, view_month_str)
            
            if active_budgets:
                df_b = pd.DataFrame(active_budgets)
                df_b_display = df_b.rename(columns={
                    'category': 'Category',
                    'limit_amount': 'Monthly Limit ($)',
                    'month_year': 'Month'
                })[['Category', 'Monthly Limit ($)', 'Month']]
                
                st.dataframe(df_b_display, use_container_width=True, hide_index=True)
                
                st.markdown("### 🗑️ Delete Budget")
                col_del_b1, col_del_b2 = st.columns([3, 1])
                with col_del_b1:
                    cat_to_del = st.selectbox("Select budget to remove", [b['category'] for b in active_budgets], label_visibility="collapsed")
                with col_del_b2:
                    if st.button("Delete Budget", type="primary", use_container_width=True):
                        database.delete_budget(user_id, cat_to_del, view_month_str)
                        st.success(f"Budget for '{cat_to_del}' deleted!")
                        st.rerun()
            else:
                st.info(f"No budgets configured for {view_month_str}.")
                
    with tab_savings:
        col_s1, col_s2 = st.columns([1, 2])
        
        with col_s1:
            st.markdown("### 🎯 Create Savings Goal")
            with st.form("create_savings_form", clear_on_submit=True):
                goal_name = st.text_input("Goal Name (e.g. Vacation, Emergency Fund)").strip()
                target_amount = st.number_input("Target Amount ($)", min_value=1.0, step=100.0)
                current_saved = st.number_input("Currently Saved ($)", min_value=0.0, step=50.0)
                target_date = st.date_input("Target Achieve Date", value=date.today() + pd.Timedelta(days=365))
                
                submitted = st.form_submit_button("Create Goal")
                if submitted:
                    if not goal_name:
                        st.error("Goal name cannot be empty.")
                    elif current_saved > target_amount:
                        st.error("Currently saved cannot be larger than target amount.")
                    else:
                        database.add_savings_goal(
                            user_id=user_id,
                            goal_name=goal_name,
                            target_amount=target_amount,
                            current_amount=current_saved,
                            target_date=target_date.strftime("%Y-%m-%d")
                        )
                        st.success(f"Savings Goal '{goal_name}' created!")
                        st.rerun()
                        
            # Update Progress section
            if savings_goals:
                st.write("---")
                st.markdown("### 🔄 Update Goal Balance")
                with st.form("update_savings_form"):
                    goal_choice = st.selectbox("Select Goal", savings_goals, format_func=lambda x: x['goal_name'])
                    new_amount = st.number_input("New Cumulative Saved Amount ($)", min_value=0.0, step=10.0, value=float(goal_choice['current_amount']))
                    
                    submitted = st.form_submit_button("Update Balance")
                    if submitted:
                        if new_amount > goal_choice['target_amount']:
                            st.warning("Updated amount exceeds target. High achievement!")
                        database.update_savings_progress(user_id, goal_choice['id'], new_amount)
                        st.success(f"Updated balance for '{goal_choice['goal_name']}' to ${new_amount:.2f}!")
                        st.rerun()
                        
        with col_s2:
            st.markdown("### 📈 Savings Goals Status")
            if savings_goals:
                for goal in savings_goals:
                    target = goal['target_amount']
                    curr = goal['current_amount']
                    pct = (curr / target) if target > 0 else 0
                    pct_display = min(pct, 1.0)
                    
                    # Highlight achieved goal
                    achievement_badge = "🏆 Achieved!" if pct >= 1.0 else f"Target: ${target:,.2f} | Saved: ${curr:,.2f}"
                    target_dt = datetime.strptime(goal['target_date'], "%Y-%m-%d").strftime("%b %d, %Y") if goal['target_date'] else "No target date"
                    
                    st.write(f"#### {goal['goal_name']}")
                    st.progress(pct_display, text=f"{pct*100:.1f}% ({achievement_badge})")
                    st.caption(f"📅 Target Date: {target_dt}")
                    
                    # Simple delete option for goal
                    if st.button(f"Delete Goal '{goal['goal_name']}'", key=f"del_g_{goal['id']}", type="secondary"):
                        database.delete_savings_goal(user_id, goal['id'])
                        st.success(f"Goal '{goal['goal_name']}' deleted.")
                        st.rerun()
                    st.write("---")
            else:
                st.info("No active savings goals configured. Add a goal on the left to start tracking!")

def render_reports_page(user_id, username, expenses, budgets):
    """Generates monthly summary stats and export utilities."""
    st.markdown("## 📑 Monthly Reports & Exports")
    st.write("Review, structure, and export your monthly spending data in CSV or print-ready PDF formats.")
    
    # Month selector
    report_month = st.date_input("Select Report Month", value=date.today())
    month_str = report_month.strftime("%Y-%m")
    
    # Filter expenses for selected month
    df_all = pd.DataFrame(expenses) if expenses else pd.DataFrame()
    if not df_all.empty:
        df_all['date_dt'] = pd.to_datetime(df_all['date'])
        df_month = df_all[df_all['date_dt'].dt.strftime("%Y-%m") == month_str]
    else:
        df_month = pd.DataFrame()
        
    if not df_month.empty:
        st.markdown(f"### Report Summary for {report_month.strftime('%B %Y')}")
        
        # Summary details
        total_spent = df_month['amount'].sum()
        num_transactions = len(df_month)
        largest = df_month['amount'].max()
        avg_spend = total_spent / num_transactions
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Spent", f"${total_spent:,.2f}")
        c2.metric("Transactions", num_transactions)
        c3.metric("Average Spent", f"${avg_spend:,.2f}")
        c4.metric("Largest Expense", f"${largest:,.2f}")
        
        st.write("")
        
        # Setup tables for PDF generation
        cat_breakdown = df_month.groupby('category')['amount'].sum().rename('Spent').reset_index().rename(columns={'category': 'Category'})
        month_budgets = database.get_budgets(user_id, month_str)
        budget_status = {b['category']: {'limit': b['limit_amount']} for b in month_budgets}
        
        # Export Actions
        col_csv, col_pdf = st.columns(2)
        
        with col_csv:
            csv_data = reports.generate_csv(df_month.to_dict('records'))
            st.download_button(
                label="📥 Export Report as CSV",
                data=csv_data,
                file_name=f"expense_report_{month_str}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
        with col_pdf:
            # Generate PDF data
            pdf_data = reports.generate_pdf(
                username=username,
                month_year=month_str,
                expenses=df_month.to_dict('records'),
                category_breakdown=cat_breakdown,
                budget_status=budget_status
            )
            st.download_button(
                label="📥 Export Report as PDF",
                data=pdf_data,
                file_name=f"expense_report_{month_str}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            
        st.write("---")
        st.markdown("### Expense Breakdown")
        df_month_display = df_month.rename(columns={
            'date': 'Date',
            'category': 'Category',
            'amount': 'Amount ($)',
            'description': 'Description'
        })[['Date', 'Category', 'Amount ($)', 'Description']].sort_values('Date', ascending=False)
        st.dataframe(df_month_display, use_container_width=True, hide_index=True)
    else:
        st.warning(f"No expense transactions recorded in {report_month.strftime('%B %Y')}. Export features disabled until data is present.")

def render_ai_advisor(user_id, expenses, budgets, savings_goals):
    """Integrates Gemini AI recommendations and interactive chatbot."""
    st.markdown("## 🤖 AI Financial Advisor")
    
    tab_analysis, tab_chat = st.tabs(["📊 Personal Finance Analysis", "💬 Chat Financial Assistant"])
    
    api_key = st.session_state['gemini_key']
    
    with tab_analysis:
        st.write("Generate a comprehensive spending analysis and receive actionable financial advice.")
        
        if st.button("🚀 Analyze Spending & Generate Tips", use_container_width=True):
            with st.spinner("Antigravity AI is analyzing your financial patterns..."):
                analysis_result = ai_helper.analyze_spending_habits(
                    expenses=expenses,
                    budgets=budgets,
                    savings_goals=savings_goals,
                    api_key=api_key
                )
                st.markdown(analysis_result)
                
    with tab_chat:
        st.write("Ask our AI assistant any questions regarding budgeting, saving strategies, or insights on your spending.")
        
        # Display existing chats
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
        # Ask question
        if user_prompt := st.chat_input("How can I lower my food spending?"):
            # Add to state and display immediately
            st.session_state.chat_history.append({"role": "user", "content": user_prompt})
            with st.chat_message("user"):
                st.markdown(user_prompt)
                
            # Query Gemini
            with st.spinner("AI is thinking..."):
                ai_response = ai_helper.ask_financial_assistant(
                    question=user_prompt,
                    chat_history=st.session_state.chat_history,
                    expenses=expenses,
                    budgets=budgets,
                    savings_goals=savings_goals,
                    api_key=api_key
                )
                
            # Add AI response to state
            st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
            with st.chat_message("assistant"):
                st.markdown(ai_response)
                
        if st.button("🧹 Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

def main():
    # If user is not authenticated, show login/signup screen
    if not st.session_state['user']:
        show_auth_page()
        return

    user = st.session_state['user']
    user_id = user['id']
    username = user['username']

    # Retrieve all user's historical records from DB
    expenses = database.get_expenses(user_id)
    savings_goals = database.get_savings_goals(user_id)
    
    current_month_str = datetime.now().strftime("%Y-%m")
    budgets = database.get_budgets(user_id, current_month_str)

    # Sidebar Navigation Layout
    st.sidebar.markdown(f"<div style='text-align: center; margin-bottom: 20px;'><h1 style='color:#60A5FA; font-size:2.2rem; margin-bottom:0;'>💸 Antigravity</h1><p style='color:#94A3B8; font-size:0.85rem;'>Logged in as: <b>{username.capitalize()}</b></p></div>", unsafe_allow_html=True)
    
    menu_options = [
        "📊 Dashboard Overview",
        "💸 Expenses Manager",
        "🎯 Budgets & Savings Goals",
        "📑 Reports & Exports",
        "🤖 AI Financial Advisor"
    ]
    choice = st.sidebar.radio("Navigation", menu_options)
    
    st.sidebar.write("---")
    
    # Gemini Configuration in Sidebar
    st.sidebar.markdown("### 🔑 Gemini Configuration")
    gemini_key_input = st.sidebar.text_input(
        "Enter Gemini API Key",
        type="password",
        value=st.session_state['gemini_key'],
        placeholder="AI features will use fallbacks if empty",
        help="Acquire an API Key from Google AI Studio. Your key is only stored locally in the session memory."
    )
    if gemini_key_input != st.session_state['gemini_key']:
        st.session_state['gemini_key'] = gemini_key_input
        st.toast("Gemini API Key updated!", icon="🔑")
        
    st.sidebar.write("")
    if st.sidebar.button("🔓 Log Out", use_container_width=True):
        logout()

    # Route content depending on selection
    if choice == "📊 Dashboard Overview":
        render_dashboard(user_id, username, expenses, budgets, savings_goals)
    elif choice == "💸 Expenses Manager":
        render_expense_manager(user_id, expenses)
    elif choice == "🎯 Budgets & Savings Goals":
        render_budgets_and_savings(user_id, expenses, budgets, savings_goals)
    elif choice == "📑 Reports & Exports":
        render_reports_page(user_id, username, expenses, budgets)
    elif choice == "🤖 AI Financial Advisor":
        render_ai_advisor(user_id, expenses, budgets, savings_goals)

if __name__ == "__main__":
    main()
