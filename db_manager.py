import sqlite3
import logging

logger = logging.getLogger(__name__)

DB_NAME = 'my_expenses.db'

def connect_db(db_name=DB_NAME):
    try:
        conn = sqlite3.connect(db_name)
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database ချိတ်ဆက်ရာတွင် အမှား: {e}")
        return None

def close_db(conn):
    if conn:
        conn.close()

def create_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                amount INTEGER NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        logger.info("Table ဖန်တီးပြီးပါပြီ။ (သို့) ရှိနှင့်ပြီးသားဖြစ်ပါက စစ်ဆေးပြီးပါပြီ။")
    except sqlite3.Error as e:
        logger.error(f"Table ဖန်တီးရာတွင် အမှား: {e}")

def add_expense(conn, item, amount):
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO expenses (item, amount) VALUES (?, ?)", (item, amount))
        conn.commit()
        logger.info(f"'{item}' - {amount} ကို မှတ်တမ်းတင်ပြီးပါပြီ။")
        return True
    except sqlite3.Error as e:
        logger.error(f"အသုံးစရိတ်ထည့်သွင်းရာတွင် အမှား: {e}")
        return False

def get_all_expenses(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, item, amount, timestamp FROM expenses ORDER BY timestamp DESC")
        expenses = cursor.fetchall()
        return expenses
    except sqlite3.Error as e:
        logger.error(f"အသုံးစရိတ်များ ပြန်ယူရာတွင် အမှား: {e}")
        return []

def get_total_expenses(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(amount) FROM expenses")
        total = cursor.fetchone()[0]
        return total if total is not None else 0
    except sqlite3.Error as e:
        logger.error(f"စုစုပေါင်းတွက်ချက်ရာတွင် အမှား: {e}")
        return 0

# --- အသစ်ထပ်ထည့်မည့် Functions များ ---

def delete_expense_by_id(conn, expense_id):
    """ID ဖြင့် မှတ်တမ်းတစ်ခုကို ဖျက်သည်။"""
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
        if cursor.rowcount > 0:
            logger.info(f"Expense with ID {expense_id} deleted successfully.")
            return True
        else:
            logger.warning(f"No expense found with ID {expense_id}.")
            return False
    except sqlite3.Error as e:
        logger.error(f"ID {expense_id} ဖြင့် ဖျက်ရာတွင် အမှား: {e}")
        return False

def clear_all_expenses(conn):
    """Database မှ မှတ်တမ်းအားလုံးကို ဖျက်သည်။"""
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses")
        conn.commit()
        logger.info("All expenses cleared successfully.")
        return True
    except sqlite3.Error as e:
        logger.error(f"မှတ်တမ်းအားလုံးကို ဖျက်ရာတွင် အမှား: {e}")
        return False

# Test the database functions (optional, remove or comment out for production)
if __name__ == '__main__':
    conn = connect_db()
    if conn:
        create_table(conn)
        
        # Test adding expenses
        print("\n--- Adding Expenses ---")
        add_expense(conn, "မနက်စာ", 2500)
        add_expense(conn, "ကော်ဖီ", 1500)
        add_expense(conn, "ကားခ", 1000)

        # Test getting all expenses
        print("\n--- All Expenses ---")
        expenses = get_all_expenses(conn)
        if expenses:
            for exp in expenses:
                print(f"ID: {exp[0]}, Item: {exp[1]}, Amount: {exp[2]}, Time: {exp[3]}")
        else:
            print("No expenses found.")

        # Test deleting an expense (example: delete the first one found)
        if expenses:
            id_to_delete = expenses[0][0] # Get the ID of the first expense
            print(f"\n--- Deleting Expense with ID: {id_to_delete} ---")
            if delete_expense_by_id(conn, id_to_delete):
                print(f"Expense ID {id_to_delete} deleted.")
            else:
                print(f"Failed to delete expense ID {id_to_delete}.")
        
        # Test getting all expenses again after deletion
        print("\n--- All Expenses After Deletion ---")
        expenses_after_delete = get_all_expenses(conn)
        if expenses_after_delete:
            for exp in expenses_after_delete:
                print(f"ID: {exp[0]}, Item: {exp[1]}, Amount: {exp[2]}, Time: {exp[3]}")
        else:
            print("No expenses found after deletion.")

        # Test clearing all expenses (UNCOMMENT TO TEST CLEARING ALL)
        # print("\n--- Clearing All Expenses ---")
        # if clear_all_expenses(conn):
        #     print("All expenses cleared.")
        # else:
        #     print("Failed to clear all expenses.")
            
        close_db(conn)
    else:
        print("Could not connect to database for testing.")

