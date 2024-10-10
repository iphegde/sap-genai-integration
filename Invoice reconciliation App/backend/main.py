from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException,Form
from typing import Any
import pdfplumber
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy import create_engine, Column, Integer, String, JSON, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sklearn.metrics.pairwise import cosine_similarity
import os
import json
import psycopg2
import requests
import ast  # Import ast to safely evaluate string to list
from streamlit_ace import st_ace
from pathlib import Path
import streamlit as st
# import frontend.app as app # Import app.py to access the global variable



# Load environment variables from the .env file
load_dotenv()

# Database connection settings retrieved from environment variables
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

## Langmith tracking
os.environ["LANGCHAIN_TRACING_V2"]="true"
os.environ["LANGCHAIN_API_KEY"]=os.getenv("LANGCHAIN_API_KEY")


# PostgreSQL connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Initialize the FastAPI app
app = FastAPI()

# Initialize the OpenAI LLM with API key
llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-4")




# output_format = """
#         {
#             "SupplierName": "",
#             "invNumber": "",
#             "vendor_address": "",
#             "tax_id": "",
#             "Invoice Date": "",
#             "bill_to_name": "",
#             "bill_to_address": "",
#             "invoice_amount": "",
#             "invoice_currency": "",
#             "invoice_items": [
#                 {
#                     "description": "",
#                     "item_no": "",
#                     "unit_price": "",
#                     "quantity": "",
#                     "net_price": ""
#                 }
#             ]
#         }
#  """

# Now you can use the loaded JSON schema in main.py
# Access the global output_format variable from app.py
# output_format = app.output_format.get('data')
# Now you can use the loaded JSON schema in main.py


prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an AI assistant specialized in extracting details from vendor invoices. You must return your response in valid JSON format."),
        ("user", """
        You need to extract the information from the invoice document given as text format and fill up the JSON as below output format.
        Ensure the JSON is properly formatted without additional text or explanation.
        
        Output format:
        {output_format}
        Text: {text}
        Important Note: Do not show "ERROR" json tags
        """)
    ]
)



# {
#             "SupplierName": "",
#             "invNumber": "",
#             "vendor_address": "",
#             "tax_id": "",
#             "Invoice Date": "",
#             "bill_to_name": "",
#             "bill_to_address": "",
#             "invoice_amount": "",
#             "invoice_currency": "",
#             "invoice_items": [
#                 {{
#                     "description": "",
#                     "item_no": "",
#                     "unit_price": "",
#                     "quantity": "",
#                     "net_price": ""
#                 }}
#             ]
#         }



#      = {
#         "SupplierName": "",
#         "invNumber": "",
#         "vendor_address": "",
#         "tax_id": "",
#         "Invoice Date": "",
#         "bill_to_name": "",
#         "bill_to_address": "",
#         "invoice_amount": "",
#         "invoice_currency": "",
#         "invoice_items": [
#             {{
#                 "description": "",
#                 "item_no": "",
#                 "unit_price": "",
#                 "quantity": "",
#                 "net_price": ""
#             }}
#         ]
#     }



output_parser = StrOutputParser()

# CONFIG_PATH = Path("config.json")

# def load_config():
#     if CONFIG_PATH.exists():
#         with open(CONFIG_PATH, "r") as f:
#             return json.load(f)
#     return {"prompt_template": {}}

# def save_config(config):
#     with open(CONFIG_PATH, "w") as f:
#         json.dump(config, f, indent=2)


# def update_prompt_template(new_template):
#     config = load_config()
#     config["prompt_template"] = new_template
#     save_config(config)
#     return config

# def get_prompt_template():
#     config = load_config()
#     return config["prompt_template"]


def write_logs(file_path = "logfile.txt" , text=None):
    try:
        # Open the file in append mode ('a') to write logs
        with open(file_path, "a") as file:
            file.write(text + "\n")  # Write the text and add a newline character
        print(f"Log written to {file_path}")
    except Exception as e:
        print(f"Error writing to file: {e}")



def extract_invoice_text(pdf_file: UploadFile) -> str:
    try:
        with pdfplumber.open(pdf_file.file) as pdf:
            text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text() is not None)
            print({text})
        if not text:
            raise ValueError("No text could be extracted from the PDF.")
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract text from the PDF file: {e}")




def extract_fields_from_text(text: str , output_format: dict) -> dict:
    try:

        write_logs(text= f"values = {type(output_format)} ,  {output_format} ")
        # formatted_prompt = prompt_template.format(output_format=output_format, text=text)
        chain = prompt_template| llm | output_parser
        response = chain.invoke({"text": text , "output_format": output_format })
        try:
            parsed_response = json.loads(response)
            return parsed_response
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Failed to parse JSON response: {response}. Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract fields from text: {e}")




def get_embedding(text):
    """
    Generate an embedding for a given text using OpenAI's text-embedding-ada-002 model.
    """
    url = "https://api.openai.com/v1/embeddings"
    payload = json.dumps({
        "input": text,
        "model": "text-embedding-ada-002"
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_API_KEY}'
    }

    # Make the API request
    response = requests.post(url, headers=headers, data=payload)
    
    # Handle potential errors
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Error generating embedding: {response.status_code} - {response.text}")
    
    # Parse and return the embedding
    embedding = response.json()['data'][0]['embedding']
    return embedding




def insert_invoice_data_to_db(data: dict):
    """
    Insert invoice data into PostgreSQL with embedding and JSON extraction.
    """
    try:
        conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cursor = conn.cursor()
        query = """
        INSERT INTO invoices (vendor_name, invoice_number, vector, extracted_data)
        VALUES (%s, %s, %s::float8[], %s::jsonb)
        """
        cursor.execute(query, (data['vendor_name'], data['invoice_number'], data['vector'], json.dumps(data['extracted_data'])))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inserting invoice data into the database: {e}")







@app.post("/process_invoice/")
async def process_invoice(file: UploadFile = File(...), output_format: str = Form(...) ):
    try:
        # write_logs(text= f"values = {type(output_format)} ,  {output_format} ")
        # Parse output_format from JSON if needed
        output_format = json.loads(output_format)
        # write_logs(text= f"values = {type(output_format)} ,  {output_format} ")
        text = extract_invoice_text(file)
        extracted_fields = extract_fields_from_text(text , output_format)

        # Generate embedding using OpenAI's embedding model
        embedding = get_embedding(json.dumps(extracted_fields))
        write_logs(text= f"values = { embedding}  ")
        # Insert invoice data into PostgreSQL
        insert_invoice_data_to_db({
            'vendor_name': extracted_fields.get("vendor_name"),
            'invoice_number': extracted_fields.get("invoice_number"),
            'vector': embedding,
            'extracted_data': extracted_fields  # Save the extracted data as JSON
        })

        # return {"message": "Invoice processed and stored successfully."}
        # Explicitly return the extracted data in the response
        return {"message": "Invoice processed and stored successfully.", "extracted_data": extracted_fields}        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing the invoice.")


