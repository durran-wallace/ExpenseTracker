from flask import Flask, request, jsonify
from database import get_db_connection

app = Flask(__name__)

# Create root endpoint
@app.route('/')
def home():
    return jsonify({"message": "Expense Tracker API is running"}), 200

# Create (Add Expense)
@app.route('/expense', methods=['POST'])
def add_expense():
    data = request.json
    cost, date, category, description = data['cost'], data['date'], data['category'], data.get('description', '')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO expenses (cost, date, category, description) VALUES (?, ?, ?, ?)",
                   (cost, date, category, description))
    conn.commit()
    conn.close()

    return jsonify({"message": "Expense added successfully"}), 201

# Read (Get All Expenses)
@app.route('/expenses', methods=['GET'])
def get_expenses():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()
    conn.close()

    return jsonify([dict(exp) for exp in expenses])

# Read (Get Single Expense by ID)
@app.route('/expense/<int:id>', methods=['GET'])
def get_expense(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses WHERE id=?", (id,))
    expense = cursor.fetchone()
    conn.close()

    if expense:
        return jsonify(dict(expense))
    return jsonify({"error": "Expense not found"}), 404

# Update (Edit Expense)
@app.route('/expense/<int:id>', methods=['PUT'])
def update_expense(id):
    data = request.json
    cost, date, category, description = data['cost'], data['date'], data['category'], data.get('description', '')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE expenses SET cost=?, date=?, category=?, description=? WHERE id=?",
                   (cost, date, category, description, id))
    conn.commit()
    conn.close()

    return jsonify({"message": "Expense updated successfully"})

# Delete (Remove Expense)
@app.route('/expense/<int:id>', methods=['DELETE'])
def delete_expense(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return jsonify({"message": "Expense deleted successfully"})

if __name__ == "__main__":
    app.run(debug=True)