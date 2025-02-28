from flask import Flask, request, jsonify
from database import get_db_connection
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Create root endpoint
@app.route('/')
def home():
    return jsonify({"message": "Expense Tracker API is running"}), 200

# Create (Add Expense)
from datetime import datetime

@app.route('/expense', methods=['POST'])
def add_expense():
    data = request.json
    cost, date, category, description = data['cost'], data['date'], data['category'], data.get('description', '')

    # Handle Unix timestamp (float) and string formats
    if isinstance(date, (int, float)):
        date_obj = datetime.fromtimestamp(date)  # Convert Unix timestamp to datetime
    elif isinstance(date, str):
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")  # Default format
        except ValueError:
            try:
                date_obj = datetime.strptime(date, "%Y/%m/%d")  # Alternative format
            except ValueError:
                return jsonify({"error": "Invalid date format. Expected YYYY-MM-DD."}), 400
    else:
        return jsonify({"error": "Invalid date type"}), 400

    formatted_date = date_obj.strftime("%Y-%m-%d")  # Ensure YYYY-MM-DD format

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO expenses (cost, date, category, description) VALUES (?, ?, ?, ?)",
                   (cost, formatted_date, category, description))
    conn.commit()
    conn.close()

    return jsonify({"message": "Expense added successfully"}), 201


# Read (Get All Expenses)
@app.route('/expenses', methods=['GET'])
def get_expenses():
    month = request.args.get('month')
    year = request.args.get('year')
    category = request.args.get('category')

    query = "SELECT * FROM expenses WHERE 1=1"
    params = []

    if month and year:
        query += " AND date BETWEEN ? AND ?"
        start_date = f"{year}-{int(month):02d}-01"
        end_date = f"{year}-{int(month):02d}-31"  # Covers all days in the month
        params.extend([start_date, end_date])

    if category:
        query += " AND category = ?"
        params.append(category)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    expenses = cursor.fetchall()
    conn.close()

    return jsonify([dict(exp) for exp in expenses])



# Read (Get Monthly Summary)
@app.route('/summary', methods=['GET'])
def get_summary():
    month = request.args.get('month')
    year = request.args.get('year')

    if not month or not year:
        return jsonify({"error": "Month and Year parameters are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get expenses grouped by category
    cursor.execute("""
        SELECT category, SUM(cost) as total_cost 
        FROM expenses 
        WHERE strftime('%m', date) = ? AND strftime('%Y', date) = ?
        GROUP BY category
    """, (month.zfill(2), year))  # Ensure month is two digits

    category_totals = [{"category": row[0], "total_cost": row[1]} for row in cursor.fetchall()]

    # Calculate overall total
    cursor.execute("""
        SELECT SUM(cost) as total_cost
        FROM expenses 
        WHERE strftime('%m', date) = ? AND strftime('%Y', date) = ?
    """, (month.zfill(2), year))

    overall_total = cursor.fetchone()[0] or 0  # Fetch value correctly

    conn.close()

    return jsonify({
        "category_totals": category_totals,
        "overall_total": overall_total
    })

    return jsonify({
        "category_totals": category_totals,
        "overall_total": overall_total
    })


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