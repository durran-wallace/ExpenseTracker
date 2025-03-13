import pytest
import requests
import time

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
    """Test dynamically creating and deleting an expense via API."""

    # Create a test expense
    test_expense = {
        "description": "Temporary Delete Test",
        "category": "Other",  # Ensure it's valid
        "cost": 10.00,
        "date": "2025-03-10"
    }
    create_response = requests.post(f"{API_URL}/expense", json=test_expense)
    assert create_response.status_code == 201, f"Failed to create test expense: {create_response.text}"

    # Extract the created expense ID
    expense_data = create_response.json()
    expense_id = expense_data.get("id")  # Check ID retrieval
    assert expense_id is not None, "API did not return a valid expense ID"
    print(f"✅ Created Expense ID: {expense_id}")


    # Proceed with DELETE request
    delete_response = requests.delete(f"{API_URL}/expense/{expense_id}")
    assert delete_response.status_code == 200, f"Failed to delete expense ID {expense_id}"




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