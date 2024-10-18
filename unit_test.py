import sqlite3
import pytest
import shutil
import os
from finance_managment import setup_db, create_user, login_user, add_transaction, delete_transaction, generate_monthly_report,set_budget,check_budget,backup_data,restore_data

# Fixture to set up the database before each test
@pytest.fixture
def setup_database():
    setup_db()
    yield
    # Teardown: close the connection and delete the database file
    conn = sqlite3.connect('finance.db')
    conn.execute('DROP TABLE IF EXISTS users')
    conn.execute('DROP TABLE IF EXISTS transactions')
    conn.execute('DROP TABLE IF EXISTS budgets')
    conn.commit()
    conn.close()

# Test create_user function
def test_create_user(setup_database):
    create_user("testuser", "testpassword")
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', ("testuser",))
    result = cursor.fetchone()
    assert result is not None
    assert result[1] == "testuser"
    conn.close()

# Test login_user function
def test_login_user(setup_database):
    create_user("testuser", "testpassword")
    user_id = login_user("testuser", "testpassword")
    assert user_id is not None

# Test add_transaction function
def test_add_transaction(setup_database):
    create_user("testuser", "testpassword")
    user_id = login_user("testuser", "testpassword")
    add_transaction(user_id, "income", "salary", 5000, "2023-10-01")
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transactions WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    assert result is not None
    assert result[2] == "income"
    assert result[3] == "salary"
    assert result[4] == 5000
    assert result[5] == "2023-10-01"
    conn.close()

# Test delete_transaction function
def test_delete_transaction(setup_database):
    create_user("testuser", "testpassword")
    user_id = login_user("testuser", "testpassword")
    add_transaction(user_id, "income", "salary", 5000, "2023-10-01")
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM transactions WHERE user_id = ?', (user_id,))
    transaction_id = cursor.fetchone()[0]
    conn.close()

    delete_transaction(user_id, transaction_id)
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,))
    result = cursor.fetchone()
    assert result is None
    conn.close()

# Test generate_monthly_report function
def test_generate_monthly_report(setup_database, capsys):
    create_user("testuser", "testpassword")
    user_id = login_user("testuser", "testpassword")
    add_transaction(user_id, "income", "salary", 5000, "2023-10-01")
    add_transaction(user_id, "expense", "rent", 1000, "2023-10-02")
    generate_monthly_report(user_id, 2023, 10)
    captured = capsys.readouterr()
    assert "Income: 5000.0, Expenses: 1000.0, Savings: 4000.0" in captured.out


# Test set_budget function
def test_set_budget(setup_database):
    create_user("testuser", "testpassword")
    user_id = login_user("testuser", "testpassword")
    set_budget(user_id, "rent", 1500)
    conn = sqlite3.connect('finance.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM budgets WHERE user_id = ? AND category = ?', (user_id, "rent"))
    result = cursor.fetchone()
    assert result is not None
    assert result[2] == "rent"
    assert result[3] == 1500
    conn.close()

# Test check_budget function
def test_check_budget(setup_database, capsys):
    create_user("testuser", "testpassword")
    user_id = login_user("testuser", "testpassword")
    set_budget(user_id, "rent", 1500)
    add_transaction(user_id, "expense", "rent", 2000, "2023-10-01")
    check_budget(user_id, "rent")
    captured = capsys.readouterr()
    assert "Warning: You've exceeded your budget for rent!" in captured.out

# Test backup_data function
def test_backup_data(setup_database, tmp_path):
    backup_file = tmp_path/"finance_backup.db"
    backup_data()
    assert os.path.exists("finance_backup.db")

# Test restore_data function
def test_restore_data(setup_database, tmp_path):
    backup_file = tmp_path / "finance_backup.db"
    shutil.copyfile('finance.db', backup_file)
    restore_data()
    assert os.path.exists('finance.db')
