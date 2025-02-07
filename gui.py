import requests
import gradio as gr
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
import io
import plotly.io as pio


API_URL = "http://127.0.0.1:5000"

# Function to fetch all expenses
def fetch_expenses():
    response = requests.get(f"{API_URL}/expenses")
    if response.status_code == 200:
        expenses = response.json()
        if expenses:
            df = pd.DataFrame(expenses)
            # Aggregating the data by category and summing the costs
            df_aggregated = df.groupby('category', as_index=False)['cost'].sum()
            df_aggregated['cost'] = pd.to_numeric(df_aggregated['cost'], errors='coerce')
            return df_aggregated, create_pie_chart(df_aggregated)  # Return aggregated DataFrame and plot
    return pd.DataFrame(columns=["Date", "Description", "Category", "Cost"]), None

# Define a function to handle the form submission
def handle_submission(description, date, cost, category):
    # Create a dictionary to store the input data
    data = {
        "cost": cost,
        "date": date,
        "category": category,
        "description": description,
    }

    response = requests.post(f"{API_URL}/expense", json=data)

    if response.status_code == 201:
        return fetch_expenses()

    return pd.DataFrame(columns=["Date", "Description", "Category", "Cost"]), None

# Function to create a pie chart from the DataFrame
def create_pie_chart(df_aggregated):
    fig = go.Figure(data=[go.Pie(
        labels=df_aggregated['category'],
        values=df_aggregated['cost'],
        textinfo='label+value',  # Show both label and value (total cost)
        hoverinfo='label+value',  # Show label and value on hover as well
        textposition='inside',  # Position the text inside the slices
        pull=[0.1, 0.1, 0.1, 0.1, 0.1, 0.1]  # Optional: Pull slices out for visual effect
    )])
    fig.update_layout(title="Expense Distribution")

    # Save the figure as a PNG with a higher resolution
    img_bytes = fig.to_image(format="png", scale=2)
    img = Image.open(io.BytesIO(img_bytes))

    return img

# Create a Gradio interface
with gr.Blocks() as gui:
    # Title
    gr.Markdown("### Expense Tracker")

    # Input fields
    description_input = gr.Textbox(label="Description")
    date_input = gr.Textbox(label="Date (YYYY-MM-DD)")
    cost_input = gr.Number(label="Cost", step=.01, precision=2)
    category_input = gr.Dropdown(
        ["Rent/Mortgage", "Utilities", "Gas", "Food", "Entertainment", "Savings", "Insurance", "Other"],
        label="Category"
    )

    # Button to submit the form
    submit_button = gr.Button("Add Expense")

    # Output fields
    table_output = gr.Dataframe(headers=["Date", "Description", "Category", "Cost"], type="pandas")
    pie_chart_output = gr.Image()

    # Load initial data
    table_output.value, pie_chart_output.value = fetch_expenses()

    # Event listener for the button click
    submit_button.click(
        fn=handle_submission,
        inputs=[description_input, date_input, cost_input, category_input],
        outputs=[table_output, pie_chart_output]
    )

# Launch the Gradio app
gui.launch(show_error=True)