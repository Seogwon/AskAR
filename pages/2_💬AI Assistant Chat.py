import streamlit as st
import sqlite3
from datetime import datetime
import pytz
from langchain_experimental.sql import SQLDatabaseChain
from ibm_watson_machine_learning.foundation_models import Model
from ibm_watson_machine_learning.foundation_models.extensions.langchain import WatsonxLLM

import os
import pandas as pd

# 현재 스크립트 파일의 디렉토리 경로 가져오기
current_dir = os.path.dirname(__file__)
csv_file_path = os.path.join(current_dir, 'pages', 'transactions.csv')

# Define your credentials and parameters
my_credentials = {
    "url": "https://us-south.ml.cloud.ibm.com",
    "apikey": "hkEEsPjALuKUCakgA4IuR0SfTyVC9uT0qlQpA15Rcy8U"
}

params = {
    'MAX_NEW_TOKENS': 1000,
    'TEMPERATURE': 0.1,
}

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

# Function to load CSV file into SQLite database
def load_csv_to_database(csv_file_path):
    conn = get_db_connection()
    df = pd.read_csv(csv_file_path)
    df.to_sql('transactions', conn, if_exists='replace', index=False)
    conn.close()

# Initialize Streamlit app
def main():
    # Load CSV file into SQLite database
    load_csv_to_database(csv_file_path)
    
    st.title('Text-To-Watsonx : Engage AR')

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
        response = run_inquiry(inquiry)
        st.markdown(f"**Response:** {response}")

    # Display transactions table
    st.markdown("**Transactions:**")
    transactions = fetch_transactions()
    st.table(transactions)

# Function to handle inquiry submission
def run_inquiry(inquiry):
    conn = get_db_connection()
    cursor = conn.execute('SELECT id, * FROM transactions ORDER BY InvoiceDate DESC')
    transactions = [dict(ix) for ix in cursor.fetchall()]
    conn.close()

    prompt = QUERY.format(table_name='transactions', columns='', time=datetime.now(pytz.timezone('America/New_York')), inquiry=inquiry)
    response = db_chain.run(prompt)

    # Replace newline characters with HTML break tags
    response = response.replace('\n', '<br>')
    return response

# Function to fetch transactions from database
@st.cache(allow_output_mutation=True, hash_funcs={sqlite3.Connection: id})
def fetch_transactions():
    conn = get_db_connection()
    cursor = conn.execute('SELECT * FROM transactions ORDER BY InvoiceDate DESC')
    transactions = cursor.fetchall()
    conn.close()
    return transactions

if __name__ == '__main__':
    main()
