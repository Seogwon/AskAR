import streamlit as st
import sqlite3
from datetime import datetime
import pytz
import csv
import os

# Define your credentials and parameters
my_credentials = {
    "url": "https://us-south.ml.cloud.ibm.com",
    "apikey": "hkEEsPjALuKUCakgA4IuR0SfTyVC9uT0qlQpA15Rcy8U"
}

params = {
    'MAX_NEW_TOKENS': 1000,
    'TEMPERATURE': 0.1,
}

# Define path to CSV file
csv_file_path = os.path.join(os.path.dirname(__file__), 'pages', 'transactions.csv')

LLAMA2_model = Model(
    model_id='meta-llama/llama-2-70b-chat',
    credentials=my_credentials,
    params=params,
    project_id="16acfdcc-378f-4268-a2f4-ba04ca7eca08",
)

llm = WatsonxLLM(LLAMA2_model)

# Connect to SQLite database
@st.cache(allow_output_mutation=True, hash_funcs={sqlite3.Connection: id})
def get_db_connection():
    conn = sqlite3.connect('history.db', check_same_thread=False)
    return conn

# Function to create transactions table if not exists
def create_transactions_table(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY,
            InvoiceDate TEXT,
            -- Add other columns as needed
        )
    ''')
    conn.commit()

# Function to insert data from CSV file into SQLite database
def insert_data_from_csv(conn, csv_file_path):
    create_transactions_table(conn)

    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f)
            next(csv_reader)  # Skip header row
            for row in csv_reader:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO transactions (InvoiceDate, ...)  -- Add other columns
                    VALUES (?, ...)  -- Match CSV columns
                ''', tuple(row))
        conn.commit()
    except FileNotFoundError:
        st.error(f"CSV file '{csv_file_path}' not found.")
    except Exception as e:
        st.error(f"Error inserting data from CSV: {str(e)}")

# Initialize Streamlit app
def main():
    st.title('Text-To-Watsonx : Engage AR')

    # Connect to SQLite database
    conn = get_db_connection()

    # Insert data from CSV file into SQLite database
    insert_data_from_csv(conn, csv_file_path)

    # Introduction section
    st.markdown("""
        Welcome to the Text-To-Watsonx : Engage AR.
        Here, you can inquire about various aspects of Engage AR transactions.
        Use the example queries as a guide to format your questions.
        **Important: AI responses can vary, you might need to fine-tune your prompt template or LLM for improved results.**
    """)

    # Example inquiries section (optional)
    st.markdown("**Example Inquiries:**")
    st.markdown("- What are the items with a due date after today?")
    st.markdown("- Show me the list where the collector is Lisa and the category is Yellow.")

    # Form for inquiry submission
    inquiry = st.text_input('Submit an Inquiry:', '')

    if st.button('Submit'):
        response = run_inquiry(inquiry, conn)
        st.markdown(f"**Response:** {response}")

    # Display transactions table
    st.markdown("**Transactions:**")
    transactions = fetch_transactions(conn)
    st.table(transactions)

    # Close database connection
    conn.close()

# Function to handle inquiry submission
def run_inquiry(inquiry, conn):
    cursor = conn.execute('SELECT id, * FROM transactions ORDER BY InvoiceDate DESC')
    transactions = [dict(ix) for ix in cursor.fetchall()]

    prompt = QUERY.format(table_name='transactions', columns='', time=datetime.now(pytz.timezone('America/New_York')), inquiry=inquiry)
    response = db_chain.run(prompt)

    # Replace newline characters with HTML break tags
    response = response.replace('\n', '<br>')
    return response

# Function to fetch transactions from database
@st.cache(allow_output_mutation=True, hash_funcs={sqlite3.Connection: id})
def fetch_transactions(conn):
    cursor = conn.execute('SELECT * FROM transactions ORDER BY InvoiceDate DESC')
    transactions = cursor.fetchall()
    return transactions

if __name__ == '__main__':
    main()
