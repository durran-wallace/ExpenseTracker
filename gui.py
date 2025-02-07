import gradio as gr
import pandas as pd
import plotly.express as px


# Define a function to handle the form submission
def handle_submission(description, date, cost, category):
    # Create a dictionary to store the input data
    data = {
        "Date": [date],
        "Description": [description],
        "Category": [category],
        "Cost": [cost]
    }
    # Convert the dictionary to a DataFrame
    df = pd.DataFrame(data)
    # Return the DataFrame for the table output
    return df, create_pie_chart(df)


# Function to create a pie chart from the DataFrame
def create_pie_chart(df):
    fig = px.pie(df, values='Cost', names='Category', title='Expense Distribution')
    return fig


# Create a Gradio interface
with gr.Blocks() as demo:
    # Input fields
    description_input = gr.Textbox(label="Description")
    date_input = gr.DateTime(label="Date", include_time=False)
    cost_input = gr.Number(label="Cost", step=.01, precision=2)
    category_input = gr.Radio(
        ["Rent/Mortgage", "Utilities", "Gas", "Food", "Entertainment", "Other"],
        label="Category"
    )

    # Output fields
    table_output = gr.Dataframe(headers=["Date", "Description", "Category", "Cost"], type="pandas")
    pie_chart_output = gr.Plot()

    # Button to submit the form
    submit_button = gr.Button("Submit")

    # Event listener for the button click
    submit_button.click(
        fn=handle_submission,
        inputs=[description_input, date_input, cost_input, category_input],
        outputs=[table_output, pie_chart_output]
    )

# Launch the Gradio app
demo.launch(show_error=True)