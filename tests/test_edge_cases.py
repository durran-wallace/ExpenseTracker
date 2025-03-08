import sqlite3
import pytest
from database import get_db_connection, build_db
import requests

DB_PATH = "expense_tracker.db"

@pytest.fixture(scope="function")
def setup_db():
    """Setup and teardown for each test case."""
    build_db()  # Ensure DB exists before testing
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    yield conn, cursor
    conn.close()  # Clean up connection after test


def test_large_cost(setup_db):
    """Test inserting a very large expense cost."""
    conn, cursor = setup_db
    large_cost = 99999999.99
    cursor.execute(
        "INSERT INTO expenses (cost, date, category, description) VALUES (?, ?, ?, ?)",
        (large_cost, "2025-02-20", "Food", "Very expensive meal"),
    )
    conn.commit()
    cursor.execute("SELECT cost FROM expenses WHERE description='Very expensive meal'")
    result = cursor.fetchone()
    assert result is not None and result[0] == large_cost


def test_empty_description(setup_db):
    """Test inserting an expense with an empty description."""
    conn, cursor = setup_db
    cursor.execute(
        "INSERT INTO expenses (cost, date, category, description) VALUES (?, ?, ?, ?)",
        (15.75, "2025-02-21", "Gas", ""),
    )
    conn.commit()
    cursor.execute("SELECT description FROM expenses WHERE cost=15.75")
    result = cursor.fetchone()
    assert result is not None and result[0] == ""


def test_long_description(setup_db):
    """Test inserting an expense with a very long description."""
    conn, cursor = setup_db
    long_description = "A" * 300  # 300-character string
    cursor.execute(
        "INSERT INTO expenses (cost, date, category, description) VALUES (?, ?, ?, ?)",
        (20.00, "2025-02-22", "Entertainment", long_description),
    )
    conn.commit()
    cursor.execute("SELECT description FROM expenses WHERE cost=20.00")
    result = cursor.fetchone()
    assert result is not None and len(result[0]) == 300


def test_invalid_date():
    """Test inserting an expense with an invalid date format."""
    invalid_data = {
        "cost": 50.00,
        "date": "2025-02-30",  # Invalid date (Feb 30 doesn't exist)
        "category": "Food",
        "description": "Invalid Date"
    }

    response = requests.post("http://127.0.0.1:5000/expense", json=invalid_data)

    assert response.status_code == 400  # API should reject the request
    assert "Invalid date format" in response.json()["error"]



def test_non_existent_id_deletion(setup_db):
    """Test deleting an expense ID that does not exist."""
    conn, cursor = setup_db
    cursor.execute("DELETE FROM expenses WHERE id=99999")
    conn.commit()
    cursor.execute("SELECT * FROM expenses WHERE id=99999")
    result = cursor.fetchone()
    assert result is None  # No expense should be found


def test_invalid_category(setup_db):
    """Test inserting an expense with a category not in the predefined list."""
    conn, cursor = setup_db
    invalid_category = "RandomCategory"
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO expenses (cost, date, category, description) VALUES (?, ?, ?, ?)",
            (25.00, "2025-02-25", invalid_category, "Invalid category test"),
        )
        conn.commit()


def test_concurrent_transactions():
    """Test handling multiple inserts at the same time."""
    def insert_expense():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO expenses (cost, date, category, description) VALUES (?, ?, ?, ?)",
            (30.00, "2025-02-26", "Entertainment", "Concurrent test"),
        )
        conn.commit()
        conn.close()

    import threading

    thread1 = threading.Thread(target=insert_expense)
    thread2 = threading.Thread(target=insert_expense)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM expenses WHERE description='Concurrent test'")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 2  # Expecting 2 successful inserts from both threads


if __name__ == "__main__":
    pytest.main()
