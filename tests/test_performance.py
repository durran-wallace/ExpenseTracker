import pytest
import requests
import random
import time

API_URL = "http://127.0.0.1:5000"


# 🔹 1️⃣ Benchmark Adding an Expense
@pytest.mark.benchmark
def test_add_expense_performance(benchmark):
    # Test how long it takes to add an expense.
    test_expense = {
        "cost": round(random.uniform(10, 500), 2),
        "date": "2025-03-10",
        "category": "Food",
        "description": "Performance Test Expense"
    }

    result = benchmark(lambda: requests.post(f"{API_URL}/expense", json=test_expense))
    assert result.status_code == 201


# 🔹 2️⃣ Benchmark Fetching Expenses (Simulating Load)
@pytest.mark.benchmark
def test_fetch_expenses_performance(benchmark):
    # Test how long it takes to fetch all expenses.
    result = benchmark(lambda: requests.get(f"{API_URL}/expenses?month=3&year=2025"))
    assert result.status_code == 200

# 🔹 4️⃣ Load Testing: Adding Multiple Expenses
@pytest.mark.benchmark
@pytest.mark.parametrize("num_requests", [10, 50, 100])  # Test different load levels
def test_bulk_add_expenses(benchmark, num_requests):
    # Test adding multiple expenses to simulate high load.

    def bulk_insert():
        for _ in range(num_requests):
            requests.post(f"{API_URL}/expense", json={
                "cost": round(random.uniform(5, 500), 2),
                "date": "2025-03-10",
                "category": "Gas",
                "description": "Load Test Expense"
            })

    benchmark(bulk_insert)


# 🔹 5️⃣ Load Testing: Fetching Large Dataset
@pytest.mark.benchmark
@pytest.mark.parametrize("month, year", [(3, 2025), (12, 2024)])  # Test multiple dates
def test_bulk_fetch_expenses(benchmark, month, year):
    # Test fetching large expense data.
    result = benchmark(lambda: requests.get(f"{API_URL}/expenses?month={month}&year={year}"))
    assert result.status_code == 200
