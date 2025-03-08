import pytest
import requests

API_URL = "http://127.0.0.1:5000"  # Ensure Flask server is running

# Test fetching expenses (GET /expenses)
def test_get_expenses():
    response = requests.get(f"{API_URL}/expenses")
    assert response.status_code == 200
    assert isinstance(response.json(), list)  # Should return a list of expenses

# Test adding an expense (POST /expense)
def test_add_expense():
    new_expense = {
        "description": "Test Expense",
        "category": "Food",
        "cost": 15.99,
        "date": "2025-03-07"
    }
    response = requests.post(f"{API_URL}/expense", json=new_expense)
    assert response.status_code == 201
    assert "message" in response.json()

# Test filtering expenses (GET /expenses with params)
def test_filter_expenses():
    response = requests.get(f"{API_URL}/expenses", params={"month": "3", "year": "2025"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)

# Test deleting an expense (DELETE /expense/<id>)
def test_delete_expense():
    expense_id = 1  # Ensure this ID exists in your test database
    response = requests.delete(f"{API_URL}/expense/{expense_id}")
    if response.status_code == 404:
        assert response.json()["error"] == "Expense not found"
    else:
        assert response.status_code == 200

# Test deleting a non-existent expense (DELETE /expense/<invalid_id>)
def test_delete_nonexistent_expense():
    invalid_id = 99999
    response = requests.delete(f"{API_URL}/expense/{invalid_id}")
    assert response.status_code == 404

    # Extract actual error message
    error_message = response.json()["error"]

    # Verify dynamic message format
    expected_message = f"Expense with ID {invalid_id} not found."
    assert error_message == expected_message


# Test retrieving monthly summary (GET /summary)
def test_get_summary():
    response = requests.get(f"{API_URL}/summary", params={"month": "3", "year": "2025"})
    assert response.status_code == 200
    assert "category_totals" in response.json()