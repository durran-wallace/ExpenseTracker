import sqlite3

DB_NAME = 'expense_tracker.db'

def get_db_connection():
    """Establish and return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

def build_db():
    """Create the expenses table if it does not exist."""
    conn = get_db_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cost REAL NOT NULL CHECK (cost > 0),
            date TEXT NOT NULL,
            category TEXT NOT NULL CHECK (category IN (
                'Rent/Mortgage', 'Utilities', 'Gas', 'Food', 'Entertainment', 'Savings', 'Insurance', 'Other'
            )),
            description TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    build_db()