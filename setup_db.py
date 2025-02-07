import sqlite3
from venv import create

from rich.table import Table

DB_NAME = 'expense_tracker.db'

def build_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cost REAL NOT NULL,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT
            )
        """)

    conn.commit()
    conn.close()

    print("Database created successfully")

if __name__ == "__main__": build_db()