import os
import pandas as pd
from google import genai
from datetime import datetime

def analyze_spending_habits_fallback(expenses, budgets, savings_goals):
    """Provides a rule-based smart analysis when Gemini API is unavailable."""
    if not expenses:
        return """### 📊 Spending Habits Analysis
No expense data found for analysis. Start adding expenses to receive insights!"""

    df = pd.DataFrame(expenses)
    total_spent = df['amount'].sum()
    num_expenses = len(df)
    
    # Calculate category totals
    cat_totals = df.groupby('category')['amount'].sum().to_dict()
    
    # Identify largest spending category
    largest_cat = max(cat_totals, key=cat_totals.get) if cat_totals else "None"
    largest_cat_amount = cat_totals.get(largest_cat, 0)
    largest_cat_pct = (largest_cat_amount / total_spent) * 100 if total_spent > 0 else 0

    analysis = []
    analysis.append("### 📊 Personal Financial Insights (Smart Heuristic Fallback)")
    analysis.append(f"Based on your **{num_expenses}** recorded transactions, you have spent a total of **${total_spent:,.2f}**.")
    analysis.append(f"\n- **Primary Driver**: Your largest spending category is **{largest_cat}** with **${largest_cat_amount:,.2f}** ({largest_cat_pct:.1f}% of total).")
    
    # Budget check
    over_budget_cats = []
    warning_cats = []
    
    # Map budgets for checking
    budget_map = {b['category']: b['limit_amount'] for b in budgets}
    
    for cat, spent in cat_totals.items():
        if cat in budget_map:
            limit = budget_map[cat]
            pct = (spent / limit) * 100
            if pct >= 100:
                over_budget_cats.append(f"**{cat}** (Spent: ${spent:,.2f} vs. Budget: ${limit:,.2f})")
            elif pct >= 80:
                warning_cats.append(f"**{cat}** (Spent: ${spent:,.2f} vs. Budget: ${limit:,.2f} - {pct:.1f}% used)")
                
    if over_budget_cats:
        analysis.append("\n#### 🚨 Budget Overruns")
        for item in over_budget_cats:
            analysis.append(f"- You have exceeded your budget in {item}.")
    
    if warning_cats:
        analysis.append("\n#### ⚠️ Budget Warnings")
        for item in warning_cats:
            analysis.append(f"- You are approaching your budget limit in {item}.")

    # Savings checks
    if savings_goals:
        analysis.append("\n#### 🎯 Savings Progress")
        for goal in savings_goals:
            target = goal['target_amount']
            curr = goal['current_amount']
            pct = (curr / target) * 100 if target > 0 else 0
            if pct >= 100:
                analysis.append(f"- 🎉 Congratulations! You've achieved your savings goal for **{goal['goal_name']}** (${curr:,.2f}/${target:,.2f}).")
            else:
                analysis.append(f"- Keep pushing! You are **{pct:.1f}%** of the way to your goal: **{goal['goal_name']}** (${curr:,.2f}/${target:,.2f}).")

    # Recommendations
    analysis.append("\n### 💡 Actionable Advice")
    if largest_cat_pct > 30:
        analysis.append(f"1. **Optimize {largest_cat}**: Since {largest_cat} accounts for {largest_cat_pct:.1f}% of your budget, lowering transactions here by even 10% would save you **${largest_cat_amount * 0.1:,.2f}**.")
    else:
        analysis.append("1. **Diversify Savings**: Your spending is relatively balanced across categories. Try setting strict sub-budgets to scrape extra savings.")
        
    if over_budget_cats:
        analysis.append("2. **Adjust Budgets**: For categories where you consistently exceed limits, consider adjusting the limit to reflect reality, or enforce stricter spending limits early in the month.")
    else:
        analysis.append("2. **Maintain Budget Discipline**: You haven't exceeded any budgets! Maintain this discipline and transfer any leftover funds straight into your savings goals.")
        
    analysis.append("3. **Automate Savings**: Allocate a portion of your income directly to your savings goals at the beginning of the month rather than saving what is left over at the end.")
    
    analysis.append("\n*Note: To unlock advanced, highly personalized AI recommendations, please add your Gemini API Key in the application sidebar.*")
    
    return "\n".join(analysis)

def get_gemini_client(api_key=None):
    """Initializes and returns a google.genai Client."""
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        return None
    try:
        client = genai.Client(api_key=key)
        return client
    except Exception:
        return None

def analyze_spending_habits(expenses, budgets, savings_goals, api_key=None):
    """Analyzes spending habits using Gemini AI, falling back to heuristics if unavailable."""
    client = get_gemini_client(api_key)
    if not client:
        return analyze_spending_habits_fallback(expenses, budgets, savings_goals)
    
    # Prepare structured financial text context for Gemini
    expenses_text = ""
    if expenses:
        df = pd.DataFrame(expenses)
        total_spent = df['amount'].sum()
        cat_breakdown = df.groupby('category')['amount'].sum().to_string()
        recent_expenses = df.head(10)[['date', 'category', 'amount', 'description']].to_string()
        expenses_text = f"""
Total Spent: ${total_spent:,.2f}
Number of Transactions: {len(expenses)}

Category Spending Breakdown:
{cat_breakdown}

Recent Transactions:
{recent_expenses}
"""
    else:
        expenses_text = "No expenses recorded yet."

    budgets_text = ""
    if budgets:
        budgets_df = pd.DataFrame(budgets)
        budgets_text = budgets_df[['category', 'limit_amount', 'month_year']].to_string()
    else:
        budgets_text = "No budget limits set yet."

    savings_text = ""
    if savings_goals:
        savings_df = pd.DataFrame(savings_goals)
        savings_text = savings_df[['goal_name', 'target_amount', 'current_amount', 'target_date']].to_string()
    else:
        savings_text = "No savings goals established yet."

    prompt = f"""
You are an expert personal financial advisor and spending habits analyst.
Analyze the user's financial profile and offer an engaging, highly detailed, and customized financial habits report.

Here is the user's current transaction and financial planning profile:

--- EXPENSE TRANSACTIONS & SUMMARY ---
{expenses_text}

--- CATEGORY BUDGETS ---
{budgets_text}

--- SAVINGS GOALS ---
{savings_text}

Please provide your analysis in the following markdown structure:
1. ### 📊 Spending Habits Analysis: A breakdown of key observations, identifying overspending patterns, high-frequency categories, and positive/negative trends.
2. ### 🚨 Budget & Savings Evaluation: Evaluate how well the user is staying within budget thresholds and their progress towards savings goals.
3. ### 💡 Actionable Advice: 3 to 5 highly specific, realistic tips tailored to their data showing where they can save money (with estimated savings calculations).

Make the tone encouraging, expert, clear, and actionable. Use bullet points and bold styling where appropriate.
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error communicating with Gemini: {str(e)}\n\n" + analyze_spending_habits_fallback(expenses, budgets, savings_goals)

def ask_financial_assistant(question, chat_history, expenses, budgets, savings_goals, api_key=None):
    """Answers financial questions in context of user's spending data using Gemini."""
    client = get_gemini_client(api_key)
    if not client:
        return "I need a Gemini API Key to run the interactive chat. Please enter your API Key in the sidebar."
    
    # Build financial context
    df_exp = pd.DataFrame(expenses) if expenses else None
    exp_summary = ""
    if df_exp is not None:
        total = df_exp['amount'].sum()
        cats = df_exp.groupby('category')['amount'].sum().to_dict()
        exp_summary = f"Total spending this month: ${total:.2f}. Categories: {cats}."
    else:
        exp_summary = "No expense data yet."

    budgets_summary = str([{b['category']: b['limit_amount']} for b in budgets]) if budgets else "No budgets configured."
    savings_summary = str([{s['goal_name']: f"{s['current_amount']}/{s['target_amount']}"} for s in savings_goals]) if savings_goals else "No savings goals configured."

    system_instruction = f"""
You are "Antigravity Finance", a friendly personal financial helper.
You help users manage budgets, analyze spending, track savings, and answer questions.
Keep answers concise, direct, and helpful. Use emojis to make it friendly.
Base your calculations and recommendations on the user's actual data when possible.

User's Financial Profile:
- {exp_summary}
- Budgets: {budgets_summary}
- Savings: {savings_summary}
"""
    
    # Formulate chat context
    # Build prompt combining history
    history_text = ""
    for msg in chat_history[-6:]: # Include last 6 messages
        role_label = "User" if msg['role'] == 'user' else "Assistant"
        history_text += f"{role_label}: {msg['content']}\n"
        
    full_prompt = f"{system_instruction}\n\nChat History:\n{history_text}User: {question}\nAssistant:"
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt
        )
        return response.text
    except Exception as e:
        return f"Sorry, I encountered an error answering that: {str(e)}"
