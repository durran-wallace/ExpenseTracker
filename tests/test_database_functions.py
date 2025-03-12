import sqlite3
import pytest
from database import DB_NAME, build_db

DB_PATH = "expense_tracker.db"  # Path to the database file

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Ensure the database is initialized before running tests.
    build_db()  # This will create the expenses table if it doesn’t exist

# Test 1: Verify Data Persistence
def test_database_persistence():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Insert a sample expense
    cursor.execute("INSERT INTO expenses (cost, date, category, description) VALUES (?, ?, ?, ?)",
                   (35.50, "2025-02-22", "Gas", "Fuel Refill"))
    conn.commit()

    # Restart database connection
    conn.close()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch the inserted record
    cursor.execute("SELECT * FROM expenses WHERE category=?", ("Gas",))
    expense = cursor.fetchone()

    assert expense is not None  # Expense should exist
    assert expense[3] == "Gas"  # Category should be "Gas"

    # Cleanup
    cursor.execute("DELETE FROM expenses WHERE category=?", ("Gas",))
    conn.commit()

    conn.close()


# Test 2: Ensure Unique IDs
def test_unique_ids():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE category=?", ("Entertainment",))
    conn.commit()

    cursor.execute("INSERT INTO expenses (cost, date, category, description) VALUES (?, ?, ?, ?)",
                   (20.00, "2025-02-21", "Entertainment", "Movie Ticket"))
    cursor.execute("INSERT INTO expenses (cost, date, category, description) VALUES (?, ?, ?, ?)",
                   (50.00, "2025-02-21", "Entertainment", "Concert Ticket"))
    conn.commit()

    cursor.execute("SELECT id FROM expenses WHERE category=?", ("Entertainment",))
    ids = [row[0] for row in cursor.fetchall()]

    assert len(ids) == 2
    assert ids[0] < ids[1]  # Auto-increment check

    cursor.execute("DELETE FROM expenses WHERE category=?", ("Entertainment",))
    conn.commit()

    conn.close()


# Test 3: Prevent Negative Costs
def test_invalid_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO expenses (cost, date, category, description) VALUES (?, ?, ?, ?)",
                       (-10.00, "2025-02-23", "Food", "Invalid Negative Cost"))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        invalid_inserted = False
    else:
        invalid_inserted = True

    assert not invalid_inserted

    cursor.execute("SELECT * FROM expenses WHERE cost < 0")
    assert cursor.fetchone() is None

    conn.close()
