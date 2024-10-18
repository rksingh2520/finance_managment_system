import sqlite3
import pytest  #for unit testing
import pandas   #to get the output in table format 
import pwinput   #for password hiding
import hashlib 
from datetime import datetime
import shutil   #for backup of database

# setting up the data base
def setup_db():
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            category TEXT,
            amount REAL,
            date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            budget REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

# User registration
def create_user(username, password):
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    try:
        conn = sqlite3.connect('finance.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        conn.close()
        print("welcome! Now you are succesfully registerd")
    except sqlite3.IntegrityError as e:
        print("username already exist, Please try another username")
# user login
def login_user(username, password):
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, password FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result and hashlib.sha256(password.encode()).hexdigest() == result[1]:
        print("Login successful!")
        return result[0]  # return user_id
    else:
        print("Invalid username or password.")
        return None

# Add transaction (income/expense)
def add_transaction(user_id, transaction_type, category, amount, date):
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO transactions (user_id, type, category, amount, date) VALUES (?, ?, ?, ?, ?)', 
                   (user_id, transaction_type, category, amount, date))
    conn.commit()
    conn.close()
    check_budget(user_id,category)

# show transactions
def show_all_transactions(user_id):
    conn=sqlite3.connect('finance.db')
    pandas.set_option("display.max_rows",None)
    print(pandas.read_sql_query(f"SELECT * FROM transactions WHERE user_id = {user_id}",conn))
    conn.commit()
    conn.close()

#show specific transactions
def show_specific_transaction(user_id,category):
    conn=sqlite3.connect('finance.db')
    pandas.set_option("display.max_rows",None)
    df=pandas.read_sql_query(f"SELECT * FROM transactions WHERE user_id={user_id}",conn)
    print(df[df['category']==category])
    conn.commit()
    conn.close()

# Delete transaction
def delete_transaction(user_id,transaction_id):
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transactions WHERE user_id = ? AND id=?', (user_id,transaction_id,))
    conn.commit()
    if cursor.rowcount == 0:
        print(f"No transaction found with transaction_id {transaction_id} in YOUR ACCOUNT")
    else:
        print(f"Deleted transaction with transaction_id {transaction_id} in YOUR ACCOUNT")
        print("Transaction deleted successfully.")
    conn.close()

# Generate monthly report
def generate_monthly_report(user_id, year, month):
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT type, SUM(amount) 
        FROM transactions 
        WHERE user_id = ? AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
        GROUP BY type
    ''', (user_id, str(year), str(month).zfill(2)))

    result = cursor.fetchall()
    
    income = sum([r[1] for r in result if r[0] == 'income'])
    expenses = sum([r[1] for r in result if r[0] == 'expense'])
    savings = income - expenses
    
    print(f"Income: {income}, Expenses: {expenses}, Savings: {savings}")
    conn.close()

# Set budget for a category
def set_budget(user_id, category, budget):
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO budgets (user_id, category, budget) VALUES (?, ?, ?)', 
                   (user_id, category, budget))
    conn.commit()
    conn.close()

# Check if budget exceeded for a category
def check_budget(user_id, category):
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT budget FROM budgets WHERE user_id = ? AND category = ?', (user_id, category))
    budget = cursor.fetchone()
    
    if budget:
        cursor.execute('SELECT SUM(amount) FROM transactions WHERE user_id = ? AND category = ? AND type = "expense"', 
                       (user_id, category))
        spent = cursor.fetchone()[0] or 0
        if spent > budget[0]:
            print(f"Warning: You've exceeded your budget for {category}!")
    conn.close()

# Backup and restore functions

def backup_data():
    shutil.copyfile('finance.db', 'finance_backup.db')
    print("Backup completed.")

def restore_data():
    shutil.copyfile('finance_backup.db', 'finance.db')
    print("Data restored from backup.")

def delete_account(username):
    conn=sqlite3.connect('finance.db')
    cursor=conn.cursor()
    cursor.execute('DELETE FROM users WHERE username= ?',(username,))
    conn.commit()
    conn.close()

def input_date():
    while True:
        try:    
            year=int(input("Enter Year(YYYY):"))
            if len(str(year))==4 :
                break
            else:
                print("invalid year")
        except ValueError:
            print("please enter in number only")
    while True:
        try:
            month=int(input("Enter month(MM):"))
            if 00<month<=12 :
                if len(str(month)) == 1 :
                    month=(str(month).zfill(2))
                    print(month)
                break
            else:
                print("please enter valid month ranging from (1-12)")
        except ValueError:
            print("please enter in number only")
            
    while True:
        try:
            days=[0,31,28,31,30,31,30,31,31,30,31,30,31]
            date=int(input("Enter date(DD):"))
            if 00<date<=days[int(month)] :
                if len(str(date)) == 1 :
                    date = (str(date).zfill(2))
                break
            else:
                    print("please enter valid date")
        except ValueError:
                print("please enter in number only")

    return (f"{year}-{month}-{date}")

# Command-line interface (CLI)
def main():
    setup_db()
    print("*"*50)
    print("Welcome to the Personal Finance Management System")
    print("*"*50)
    
    while True:
        print("Options:\n1)register\n2)login\n3)exit")
        print("?"*50)
        action = input("Choose an option: ")
        if action.isdigit():
            action=int(action)
        else:
            action=action.lower()

        if action == "register" or action == 1:
            print("-"*50)
            username = input("Enter username: ")
            password = pwinput.pwinput("Enter password: ")
            print("-"*50)
            create_user(username, password)
        
        elif action == 2  or action == "login":
            print("-"*50)
            username = input("Enter username: ")
            password = pwinput.pwinput("Enter password: ")
            print("-"*50)
            user_id = login_user(username, password)
            
            if user_id:
                while True:
                    print()
                    print("#"*50)
                    print("Options:\n1) add_transaction\n2) show_transactions\n3) delete_transaction\n4) monthly_report\n5) set_budget\n6) check_budget\n7) backup\n8) restore\n9) logout\n10)delete account")
                    user_action = input("Choose an option: ")
                    print("?"*50)

                    if user_action.isdigit():
                        user_action=int(user_action)
                    else:
                        user_action=user_action.lower()


                    if user_action == "add_transaction" or user_action == 1:
                        while True:
                            t_type = input("Type of Transaction\n1) income\n2) expense\nEnter your choice:  ").lower()
                            if t_type=="income" or t_type=="1" :
                                t_type="income"
                                break
                            elif t_type=="2" or t_type=="expense":
                                t_type="expense"
                                break
                            else:
                                print("Enter correct  choice number or spelling")

                        category = input("Enter category: ")
                        amount = float(input("Enter amount: "))
                        date = input_date()
                        add_transaction(user_id, t_type, category, amount, date)
                        print("Transaction added.")

                    elif user_action == "show_transactions" or user_action == 2:
                        option=input("Options:\n 1)Show all transactions\n 2)show specific category\n Enter your option: ").lower()
                        if option=="1" or option=="show all transactions":
                            show_all_transactions(user_id)
                        elif option=="2" or option =="show specific category":
                            category=input("Enter the Category: ").lower()
                            show_specific_transaction(user_id,category)
                    
                    elif user_action == "delete_transaction" or user_action == 3:
                        t_id = int(input("Enter transaction ID to delete: "))
                        delete_transaction(user_id,t_id)
                        print("Transaction deleted.")

                    elif user_action == "monthly_report" or user_action == 4:
                        year = int(input("Enter year (YYYY): "))
                        month = int(input("Enter month (MM): "))
                        generate_monthly_report(user_id, year, month)

                    elif user_action == "set_budget" or user_action == 5:
                        category = input("Enter category: ").lower()
                        budget = float(input("Enter budget amount: "))
                        set_budget(user_id, category, budget)
                        print(f"Budget set for {category}.")

                    elif user_action == "check_budget" or user_action ==6:
                        category = input("Enter category: ").lower()
                        check_budget(user_id, category)

                    elif user_action == "backup" or user_action == 7:
                        backup_data()

                    elif user_action == "restore" or user_action == 8:
                        restore_data()

                    elif user_action == "logout" or user_action == 9:
                        print("Logged out! Thank you for using our service.")
                        break
                    
                    elif user_action == "delete account" or user_action == 10:
                        password = pwinput.pwinput("Enter your password to confirm deletion : ")
                        user_id = login_user(username, password)
                        if user_id:
                            delete_account(username)
                            print('your account had been successfully removed')
                            break
                        else:
                            print('Invalid credentials')

        elif action == 3 or action == "exit":
            print("bye! have a nice day")
            break
        else: 
            print("invalid option!")
if __name__ == "__main__":
    main()
