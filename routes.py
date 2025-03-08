from flask import Flask, request, jsonify
from database import get_db_connection
import sqlite3
from datetime import datetime
import werkzeug.serving

app = Flask(__name__)

# ✅ Security Configurations
app.config['CSP'] = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self'; "
    "img-src 'self' data:; "
    "object-src 'none'; "
    "frame-ancestors 'none'; "
    "base-uri 'none';"
)


# ✅ Apply Security Headers Globally
@app.after_request
def apply_security_headers(response):
    response.headers["Content-Security-Policy"] = app.config['CSP']
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


# ✅ Suppress "Server" Header
werkzeug.serving.WSGIRequestHandler.server_version = "Secure-Server"
werkzeug.serving.WSGIRequestHandler.sys_version = ""


# ✅ Define Static Routes
@app.route('/robots.txt')
def robots():
    return "User-agent: *\nDisallow:", 200, {'Content-Type': 'text/plain'}


@app.route('/sitemap.xml')
def sitemap():
    return "", 200, {'Content-Type': 'application/xml'}


# ✅ Helper Functions
def validate_date(date_str):
    """Ensures the date format is YYYY-MM-DD and is a valid date."""
    try:
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
        return parsed_date.strftime("%Y-%m-%d")
    except ValueError:
        return None


def execute_query(query, params=(), fetch_one=False, fetch_all=False, commit=False):
    """Handles common database interactions."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if commit:
            conn.commit()
        if fetch_one:
            return cursor.fetchone()
        if fetch_all:
            return cursor.fetchall()
    except sqlite3.Error as e:
        conn.rollback()
        return {"error": f"Database error: {str(e)}"}
    finally:
        conn.close()


# ✅ Routes
@app.route('/')
def home():
    return jsonify({"message": "Expense Tracker API is running"}), 200


@app.route('/expense', methods=['POST'])
def add_expense():
    data = request.json
    cost = data.get('cost')
    date = data.get('date')
    category = data.get('category')
    description = data.get('description', '')

    # Ensure required fields are provided
    if cost is None or date is None or category is None:
        return jsonify({"error": "Missing required fields: cost, date, category"}), 400

    # Validate date format & ensure it's a real date
    def validate_date(date_str):
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            return parsed_date.strftime("%Y-%m-%d")  # Ensure YYYY-MM-DD format
        except ValueError:
            return None

    # Convert Unix timestamp or validate string date
    if isinstance(date, (int, float)):
        formatted_date = datetime.fromtimestamp(date).strftime("%Y-%m-%d")
    elif isinstance(date, str):
        formatted_date = validate_date(date)
        if formatted_date is None:
            return jsonify({"error": "Invalid date format or non-existent date (e.g., 2025-02-30). Expected YYYY-MM-DD."}), 400
    else:
        return jsonify({"error": "Invalid date type. Expected string or timestamp."}), 400

    # Insert into database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO expenses (cost, date, category, description) VALUES (?, ?, ?, ?)",
                   (cost, formatted_date, category, description))
    expense_id = cursor.lastrowid
    conn.commit()
    # 🛠 Debug: Fetch the last inserted expense
    cursor.execute("SELECT * FROM expenses ORDER BY id DESC LIMIT 1")
    latest_expense = cursor.fetchone()
    print("Latest expense in DB:", dict(latest_expense) if latest_expense else "No expense found")

    conn.close()
    return jsonify({"message": "Expense added successfully", "id": expense_id}), 201


@app.route('/expenses', methods=['GET'])
def get_expenses():
    month, year, category = request.args.get('month'), request.args.get('year'), request.args.get('category')

    query = "SELECT * FROM expenses WHERE 1=1"
    params = []

    if month and year:
        query += " AND date BETWEEN ? AND ?"
        params.extend([f"{year}-{int(month):02d}-01", f"{year}-{int(month):02d}-31"])

    if category:
        query += " AND category = ?"
        params.append(category)

    expenses = execute_query(query, params, fetch_all=True)
    return jsonify([dict(exp) for exp in expenses])


@app.route('/summary', methods=['GET'])
def get_summary():
    month, year = request.args.get('month'), request.args.get('year')
    if not month or not year:
        return jsonify({"error": "Month and Year parameters are required"}), 400

    # Get category-wise totals
    query = """
        SELECT category, SUM(cost) as total_cost 
        FROM expenses 
        WHERE strftime('%m', date) = ? AND strftime('%Y', date) = ?
        GROUP BY category
    """
    category_totals = execute_query(query, (month.zfill(2), year), fetch_all=True)

    # Get overall total
    total_query = "SELECT SUM(cost) as total_cost FROM expenses WHERE strftime('%m', date) = ? AND strftime('%Y', date) = ?"
    overall_total = execute_query(total_query, (month.zfill(2), year), fetch_one=True)

    return jsonify({
        "category_totals": [{"category": row[0], "total_cost": row[1]} for row in category_totals],
        "overall_total": overall_total[0] if overall_total else 0
    })


@app.route('/expense/<int:id>', methods=['GET'])
def get_expense(id):
    expense = execute_query("SELECT * FROM expenses WHERE id=?", (id,), fetch_one=True)
    return jsonify(dict(expense)) if expense else jsonify({"error": "Expense not found"}), 404


@app.route('/expense/<int:id>', methods=['PUT'])
def update_expense(id):
    data = request.json
    cost, date, category = data.get('cost'), data.get('date'), data.get('category')
    description = data.get('description', '')

    if None in [cost, date, category]:
        return jsonify({"error": "Missing required fields: cost, date, category"}), 400

    formatted_date = validate_date(date) if isinstance(date, str) else datetime.fromtimestamp(date).strftime("%Y-%m-%d")
    if not formatted_date:
        return jsonify({"error": "Invalid date format"}), 400

    query = "UPDATE expenses SET cost=?, date=?, category=?, description=? WHERE id=?"
    execute_query(query, (cost, formatted_date, category, description, id), commit=True)

    return jsonify({"message": "Expense updated successfully"})


@app.route('/expense/<int:id>', methods=['DELETE'])
def delete_expense(id):
    expense = execute_query("SELECT * FROM expenses WHERE id=?", (id,), fetch_one=True)
    if not expense:
        return jsonify({"error": f"Expense with ID {id} not found."}), 404

    execute_query("DELETE FROM expenses WHERE id=?", (id,), commit=True)
    return jsonify({"message": f"Expense with ID {id} deleted successfully."}), 200


if __name__ == "__main__":
    app.run(debug=True)
