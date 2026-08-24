import sqlite3
import os

DB_NAME = "expenses.db"

def get_connection():
    """Returns a connection to the SQLite database."""
    # Place the database file in the same directory as this module
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def init_db():
    """Initializes the database schemas if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Create expenses table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        date TEXT NOT NULL,
        description TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # Create budgets table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        limit_amount REAL NOT NULL,
        month_year TEXT NOT NULL,
        UNIQUE(user_id, category, month_year),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    # Create savings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS savings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        goal_name TEXT NOT NULL,
        target_amount REAL NOT NULL,
        current_amount REAL DEFAULT 0.0,
        target_date TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()

# Users related database functions
def create_user(username, password_hash):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

# Expenses related database functions
def add_expense(user_id, amount, category, date, description):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (user_id, amount, category, date, description)
    )
    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()
    return expense_id

def get_expenses(user_id, category=None, start_date=None, end_date=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM expenses WHERE user_id = ?"
    params = [user_id]

    if category:
        query += " AND category = ?"
        params.append(category)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)

    query += " ORDER BY date DESC, id DESC"
    cursor.execute(query, params)
    expenses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return expenses

def delete_expense(expense_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

# Budgets related database functions
def set_budget(user_id, category, limit_amount, month_year):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO budgets (user_id, category, limit_amount, month_year)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(user_id, category, month_year) 
        DO UPDATE SET limit_amount = excluded.limit_amount
    """, (user_id, category, limit_amount, month_year))
    conn.commit()
    conn.close()

def get_budgets(user_id, month_year):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM budgets WHERE user_id = ? AND month_year = ?",
        (user_id, month_year)
    )
    budgets = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return budgets

def delete_budget(user_id, category, month_year):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM budgets WHERE user_id = ? AND category = ? AND month_year = ?",
        (user_id, category, month_year)
    )
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

# Savings goals related database functions
def add_savings_goal(user_id, goal_name, target_amount, current_amount, target_date):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO savings (user_id, goal_name, target_amount, current_amount, target_date)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, goal_name, target_amount, current_amount, target_date))
    conn.commit()
    goal_id = cursor.lastrowid
    conn.close()
    return goal_id

def get_savings_goals(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM savings WHERE user_id = ? ORDER BY id DESC", (user_id,))
    goals = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return goals

def update_savings_progress(user_id, goal_id, current_amount):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE savings 
        SET current_amount = ? 
        WHERE id = ? AND user_id = ?
    """, (current_amount, goal_id, user_id))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

def delete_savings_goal(user_id, goal_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM savings WHERE id = ? AND user_id = ?", (goal_id, user_id))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

# Initialize tables when this file is imported
init_db()
