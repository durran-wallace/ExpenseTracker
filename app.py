import requests
import gradio as gr
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
import io
import datetime

API_URL = "http://127.0.0.1:5000"

# Function to fetch expenses with optional filters
def fetch_expenses(month=None, year=None, category=None):
    params = {}
    if month and year:
        params['month'] = str(month)
        params['year'] = str(year)
    if category:
        params['category'] = category

    response = requests.get(f"{API_URL}/expenses", params=params)
    if response.status_code == 200:
        expenses = response.json()
        if expenses:
            df = pd.DataFrame(expenses)
            if not df.empty:
                df = df[["id", "description", "category", "cost", "date"]]  # Column order

            df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

            # Ensure delete column is not included in table display
            if "delete" in df.columns:
                df = df.drop(columns=["delete"])

            # Aggregate data for pie chart **ONLY by date (month & year)**
            if month and year:
                df_pie = df[(df["date"].str.startswith(f"{year}-{str(month).zfill(2)}"))]
                df_aggregated = df_pie.groupby('category', as_index=False)['cost'].sum()
            else:
                df_aggregated = df.groupby('category', as_index=False)['cost'].sum()

            return df, create_pie_chart(df_aggregated, month, year)  # Always update pie chart by date only

    return pd.DataFrame(columns=["Date", "Description", "Category", "Cost"]), None

# Function to filter expenses (Only updates Table)
def filter_table(m, y, c):
    filtered_table, _ = fetch_expenses(m, y, None if c == "All" else c)  # Filters table but NOT pie chart
    _, updated_chart = fetch_expenses(m, y, None)  # Always fetch full pie chart data for selected month/year
    return filtered_table, updated_chart  # Table filters, Pie Chart shows all categories

# Function to filter Pie Chart (Only updates Pie Chart)
def filter_pie_chart(m, y):
    _, updated_chart = fetch_expenses(m, y, None)
    return None, updated_chart  # Keeps table unchanged

# Function to show confirmation message before deletion
def confirm_delete(expense_id):
    """Show confirmation pop-up before deletion"""
    if not expense_id.strip():
        return "❌ Please enter a valid expense ID.", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
    return f"⚠️ Are you sure you want to delete expense ID **{expense_id}**?", gr.update(visible=True), gr.update(visible=True), gr.update(visible=True)


# Function to execute deletion after confirmation
def execute_delete(expense_id):
    """Execute deletion after confirmation"""
    if not expense_id.strip():
        return (
            "❌ No expense selected.",  # Error message
            gr.update(visible=False),  # Hide confirmation
        )

    response = requests.delete(f"{API_URL}/expense/{expense_id}")

    if response.status_code == 404:
        return (
            "❌ **Error:** Expense ID not found.",  # Error message
            gr.update(visible=False),  # Hide confirmation
            gr.update(visible=False),  # Hide "Yes, Delete" button
            gr.update(visible=False),  # Hide "Cancel" button
            gr.update(),  # Keep table unchanged
            gr.update()  # Keep pie chart unchanged
        )

    if response.status_code == 200:
        updated_table, updated_chart = fetch_expenses()
        return (
            "✅ **Success:** Expense deleted.",  # Success message
            gr.update(visible=False),  # Hide confirmation
            gr.update(visible=False),  # Hide "Yes, Delete" button
            gr.update(visible=False),  # Hide "Cancel" button
            gr.update(value=updated_table),  # Update table
            gr.update(value=updated_chart)  # Update pie chart
        )

    return (
        "❌ **Error:** Unable to delete expense.",  # Error message
        gr.update(visible=False),  # Hide confirmation
        gr.update(visible=False),  # Hide "Yes, Delete" button
        gr.update(visible=False),  # Hide "Cancel" button
        gr.update(),  # Keep table unchanged
        gr.update()  # Keep pie chart unchanged
    )

# Function to cancel deletion
def cancel_delete():
    # Hide confirmation if user cancels
    return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

# Define a function to handle the form submission
def handle_submission(description, date, cost, category):
    # If any field is empty
    if not description or not cost or not category:
        # Re-fetch table & chart (default month/year)
        current_table, current_chart = fetch_expenses(month=current_month, year=current_year, category=None)
        return ("❌ Please fill in all fields before submitting.", current_table, current_chart, date or "")
    elif not date:
        # Re-fetch table & chart (default month/year)
        current_table, current_chart = fetch_expenses(month=current_month, year=current_year, category=None)
        return ("❌ Please enter valid date using calendar date picker.", current_table, current_chart, date or "")
    elif len(description) > 25:
        # Re-fetch table & chart (default month/year)
        current_table, current_chart = fetch_expenses(month=current_month, year=current_year, category=None)
        return ("❌ No more than 25 characters may be entered for the description.", current_table, current_chart, date or "")

    # Otherwise, create a dictionary
    data = {
        "cost": cost,
        "date": date,
        "category": category,
        "description": description,
    }

    # Send POST request
    response = requests.post(f"{API_URL}/expense", json=data)
    if response.status_code == 201:
        updated_table, updated_chart = fetch_expenses()  # or pass current filters if you have them
        return ("✅ Expense added successfully!", updated_table, updated_chart, "")
    else:
        # Keep existing data if adding fails
        existing_table, existing_chart = fetch_expenses()
        return ("❌ Error: Unable to add expense.", existing_table, existing_chart, date or "")


# Function to create a pie chart with title including month and year
def create_pie_chart(df_aggregated, month, year):
    fig = go.Figure(data=[go.Pie(
        labels=df_aggregated['category'],
        values=df_aggregated['cost'],
        textinfo='label+percent',  # Shows category name + percentage
        hoverinfo='label+value+percent',  # Tooltip shows value & percentage
        textposition='inside',
        pull=[0.1] * len(df_aggregated)
    )])

    title = f"Expense Distribution - {datetime.date(1900, int(month), 1).strftime('%B')} {year}" if month and year else "Expense Distribution"
    fig.update_layout(title=title)

    img_bytes = fig.to_image(format="png", scale=2)
    img = Image.open(io.BytesIO(img_bytes))

    return img

# Function to fetch monthly summary
def fetch_summary(month, year):
    response = requests.get(f"{API_URL}/summary", params={"month": month, "year": year})

    if response.status_code == 200:
        data = response.json()
        summary_df = pd.DataFrame(data["category_totals"])

        if not summary_df.empty:
            summary_df.columns = ["Category", "Total Cost"]
            summary_df["Total Cost"] = summary_df["Total Cost"].apply(lambda x: f"${x:.2f}")

            # Add a "Total" row at the bottom
            total_row = pd.DataFrame([["TOTAL", f"${data['overall_total']:.2f}"]], columns=["Category", "Total Cost"])
            summary_df = pd.concat([summary_df, total_row], ignore_index=True)

        return summary_df

    # If no data is available, return an empty table with a $0.00 total row
    return pd.concat([
        pd.DataFrame(columns=["Category", "Total Cost"]),
        pd.DataFrame([{"Category": "TOTAL", "Total Cost": "$0.00"}])
    ])


# Get current month and year for initial load
current_month = datetime.datetime.now().month
current_year = datetime.datetime.now().year

# Create a Gradio interface
with gr.Blocks(css_paths="styles.css") as gui:
    # Title (Centered)
    gr.HTML('<h1>Expense Tracker</h1>')

    # First row: Expense Input Form (Left) & Filters (Right)
    with gr.Row():
        with gr.Group(elem_id="group"):
            with gr.Column(scale=1, min_width=400):
                gr.HTML("<h2 style='text-align: center;'>Add Expense</h2>")
                description_input = gr.Textbox(label="Description", placeholder="max 25 characters")
                date_input = gr.DateTime(label="Date", include_time=False)
                cost_input = gr.Number(label="Cost", step=0.01, precision=2)
                category_input = gr.Dropdown(
                    ["Rent/Mortgage", "Utilities", "Gas", "Food", "Entertainment", "Savings", "Insurance", "Other"],
                    label="Category")
                submit_button = gr.Button("Add Expense")
                submit_error_message = gr.Markdown()

        with gr.Group():
            with gr.Column(scale=1, min_width=400):
                gr.HTML("<h2 style='text-align: center;'>Filter Expenses</h2>")
                month_input = gr.Dropdown(choices=[str(i) for i in range(1, 13)], label="Month",
                                          value=str(current_month))
                year_input = gr.Dropdown(choices=[str(y) for y in range(current_year - 20, current_year + 1)],
                                         label="Year", value=str(current_year))
                category_filter = gr.Dropdown(
                    choices=["All", "Rent/Mortgage", "Utilities", "Gas", "Food", "Entertainment", "Savings",
                             "Insurance", "Other"], label="Category", value="All")
                filter_button = gr.Button("Filter Expenses")

    # Second row: Expense Table (Full Width)
    table_output = gr.Dataframe(headers=["Date", "Description", "Category", "Cost"], type="pandas")

    #Third row: Delete Expense
    with gr.Group():
        with gr.Column(scale=1, min_width=400):
            gr.HTML("<h2 style='text-align: center;'>Delete an Expense</h2>")
            delete_button = gr.Textbox(label="Enter Expense ID to Delete")
        delete_action = gr.Button("Delete", elem_id="delete")
        delete_error_message = gr.Markdown()
        delete_confirmation = gr.Markdown()
        confirm_delete_button = gr.Button("Confirm Delete", visible=False)
        cancel_delete_button = gr.Button("Cancel", visible=False)

    # Fourth row: Pie Chart (Left) & Monthly Summary (Right)
    with gr.Row():
        with gr.Group():  # Left Column - Pie Chart
            with gr.Column(scale=1, min_width=400):
                pie_chart_output = gr.Image()
        with gr.Group():  # Right Column - Monthly Summary
            with gr.Column(scale=1, min_width=400):
                # Monthly Summary Title (Centered)
                gr.HTML("<h2 style='text-align: center;'>Monthly Summary</h2>")
                summary_output = gr.Dataframe(headers=["Category", "Total Cost"], interactive= False, scale=1, type="pandas")

    # Delete button click (Shows confirmation pop-up)
    delete_action.click(
        fn=confirm_delete,
        inputs=[delete_button],
        outputs=[delete_error_message, delete_confirmation, confirm_delete_button, cancel_delete_button]
    )

    # If user confirms deletion
    confirm_delete_button.click(
        fn=execute_delete,
        inputs=[delete_button],
        outputs=[delete_error_message, delete_confirmation, confirm_delete_button, cancel_delete_button, table_output,
                 pie_chart_output]
    )

    # If user cancels deletion
    cancel_delete_button.click(
        fn=lambda: ("", gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)),
        inputs=[],
        outputs=[delete_error_message, delete_confirmation, confirm_delete_button, cancel_delete_button]
    )

    # Load initial data (Table, Pie Chart, and Summary)
    gui.load(
        fn=lambda: (*fetch_expenses(current_month, current_year, None), fetch_summary(current_month, current_year)),
        inputs=[],
        outputs=[table_output, pie_chart_output, summary_output]
    )

    # Event listeners
    submit_button.click(
        fn=handle_submission,
        inputs=[description_input, date_input, cost_input, category_input],
        outputs=[submit_error_message, table_output, pie_chart_output, date_input]  # 3 outputs
    )

    # Update Table, Pie Chart, and Monthly Summary when filtering
    filter_button.click(
        fn=lambda m, y, c: (*filter_table(m, y, c), fetch_summary(m, y)),
        inputs=[month_input, year_input, category_filter],
        outputs=[table_output, pie_chart_output, summary_output]
    )

# Launch the Gradio app
gui.launch(show_error=True)

