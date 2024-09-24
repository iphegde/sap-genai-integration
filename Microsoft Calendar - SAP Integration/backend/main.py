from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
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
from requests.auth import HTTPBasicAuth
import json

import psycopg2
import pandas as pd
from psycopg2 import sql
from loguru import logger
import openai
import time
from tqdm import tqdm

# Load environment variables from the .env file
load_dotenv()

# Database connection settings retrieved from environment variables
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

SAP_API_KEY  = os.getenv("SAP_API_KEY") 

## Langmith tracking
# os.environ["LANGCHAIN_TRACING_V2"]="true"
# os.environ["LANGCHAIN_API_KEY"]=os.getenv("LANGCHAIN_API_KEY")

AICORE_AUTH_URL = os.getenv("AICORE_AUTH_URL")
AICORE_CLIENT_ID = os.getenv("AICORE_CLIENT_ID")
AICORE_CLIENT_SECRET = os.getenv("AICORE_CLIENT_SECRET")
AICORE_RESOURCE_GROUP = os.getenv("AICORE_RESOURCE_GROUP")
AICORE_BASE_URL = os.getenv("AICORE_BASE_URL")
EMB_DEPLOYMENT_ID = os.getenv("EMB_DEPLOYMENT_ID")

# PostgreSQL connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# Initialize the FastAPI app
app = FastAPI()



# Initialize the OpenAI LLM with API key
llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model="gpt-4")


prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an AI assistant specialized in extracting details from vendor invoices. You must return your response in valid JSON format."),
        ("user", """
        You need to extract the information from the invoice document given as text format and fill up the JSON as below output format.
        Ensure the JSON is properly formatted without additional text or explanation.
        
        Output format:

        {{
            "SupplierName": "",
            "invNumber": "",
            "vendor_address": "",
            "tax_id": "",
            "Invoice Date": "",
            "bill_to_name": "",
            "bill_to_address": "",
            "invoice_amount": "",
            "invoice_currency": "",
            "invoice_items": [
                {{
                    "description": "",
                    "item_no": "",
                    "unit_price": "",
                    "quantity": "",
                    "net_price": ""
                }}
            ]
        }}
        Text: {text}
        """)
    ]
)


output_parser = StrOutputParser()

# Function to insert data into the PostgreSQL database
def insert_data(conn, psp_element, network_number, description, detailed_description, final_gpt_text, embedding):
#     """
#     Insert data into PostgreSQL with embedding
#     """
    with conn.cursor() as cursor:
        insert_query = """
            INSERT INTO psp_data (psp_element, network_number, description, detailed_description, final_gpt_text, embedding)
            VALUES (%s, %s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (psp_element, network_number, description, detailed_description, final_gpt_text, embedding))
        conn.commit()

# Function to create embeddings using OpenAI's ada model
def get_embedding(text):
    """
    Generate an embedding for a given text using OpenAI's text-embedding-ada-002 model.
    """



    url1 = "https://api.openai.com/v1/embeddings"
    # url1 = f"{AICORE_BASE_URL}/v2/inference/deployments/{EMB_DEPLOYMENT_ID}"
    payload1 = json.dumps({
        "input": text,
        "model": "text-embedding-ada-002"
    })
    headers1 = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_API_KEY}'
    }
    logger.info(f"Embedding started:")
    # Make the API request
    response1 = requests.post(url1, headers=headers1, data=payload1)
    
    # Handle potential errors
    if response1.status_code != 200:
        raise HTTPException(status_code=500, detail=f"Error generating embedding: {response1.status_code} - {response1.text}")
    

    # logger.info(f"Embedding started: { response1.json()['data'][0]['embedding'] }")
    # Parse and return the embedding
    # logger.info(f"Embedded Successfully")
    embeddings = response1.json()['data'][0]['embedding']
    return embeddings

def chat_completions(system, text, max_retries=5):
    url= "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role":"system", "content": system},
            {"role":"user", "content": text}
        ]
    }

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {OPENAI_API_KEY}'
    }

    for attempt in range(max_retries):
        try:
            # logger.info(f"Generating chat completions for text: { text }, attempt { attempt + 1 }")
            response = requests.post(url, json=payload, headers=headers, timeout=30)  #Set timeout
            response.raise_for_status()
            json_data = response.json()
            return json_data['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in Chat Completions: {e}")
            if attempt < max_retries - 1:
                wait_time  = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise

# Function to process the CSV and store embeddings
def get_final_gpt_text_chatcomp( psp_element,network_number,description,detailed_description ):
    try:

        item = {
            "psp_element": psp_element,
            "network_number":network_number,
            "text": f"Description: { description }, Detailed Description: { detailed_description }" 
        }
        # desc = f"Description: { description }, Detailed Description: { detailed_description }" 
        # logger.info("Local text value", {desc})
        # text_value = item["text"]

        system = """You are a smart assistant who can predict all possible Texts/sentences/words
        that can be used in a Calandar meeting event"""

        prompt_text = f"""
            Predict the possible texts/sentences/words that the Microsoft teams meeting subject/title 
            or body may includes from the text paragraph give here.
            
            TEXT: {item["text"]}
            Commands: Skip header and footer in your reply.
            
            Output format:

            ### Subjects/Titles:
            1. Time and Salary Project Time Booking
            2. HR Project Status Call
            3. Team Meeting: Retrospectives and KTs
            4. Team Outing Planning
            5. Travel Arrangements Discussion
            6. 1:1 Feedback Session
            7. Go/No-Go Meeting
            8. Important Tags: T&S, T&L, TogL, Tid og løn, Time & Salary, HR Project

            ### Body Texts:
            1. **Time and Salary Project Time Booking:**
            - Agenda: Discuss time booking for the Time and Salary project.
            - Important Tags: T&S, T&L, TogL, Tid og løn, Time & Salary, HR Project.

            2. **HR Project Status Call:**
            - Agenda: Review the current status of HR projects, including time booking and team meetings.
            - Important Tags: HR Project, Status Call.

            3. **Team Meeting: Retrospectives and KTs:**
            - Agenda: Conduct retrospectives and knowledge transfer sessions.
            - Important Tags: Team Meeting, Retrospectives, KTs.

            ###Important Tags
            T&S, T&L, TogL, Tid og løn, Time & Salary, HR Project
            + item['text']
            """
        
        final_gpt_text  = chat_completions(system,prompt_text)
        return final_gpt_text 
    except Exception as e:
        print(f"Chat completion LLM error: {e}")
        return None

    
# Function to connect to PostgreSQL database
def connect_to_db():
    try:
        conn = psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

# Function to process the CSV and store embeddings
def process_csv_and_store_embeddings(csv_file_path):
    # Load the CSV file into a DataFrame
    df = pd.read_csv(csv_file_path, delimiter=',', encoding='utf-8')
    # Assuming you have your DataFrame `df` and a connection `conn`
    total_rows = len(df)
    #pd.read_csv(csv_file_path)
    # logger.info(f"CSV Read - {df}")

    # Connect to the database
    conn = connect_to_db()
    
    if conn is None:
        print("Failed to connect to the database. Exiting.")
        return
    # Iterate over the DataFrame rows
    for index, row in tqdm(df.iterrows(), total=total_rows, desc="Processing Data", ncols=100):
        psp_element = row['PSP Element']
        network_number = row['Network Number']
        description = row['Description']
        detailed_description = row['Detailed Description']
        final_gpt_text = get_final_gpt_text_chatcomp( psp_element,network_number,description,detailed_description)
        
        # Log the extracted data for the current row
        logger.debug(f"Processing row {index + 1}/{total_rows}: {psp_element}")

        # logger.info(f"DATA row - {psp_element} , {network_number} , {description} , {detailed_description}, {final_gpt_text}")
        fulltext = f"{ description },{ detailed_description },{ final_gpt_text }"

        # logger.info(fulltext)
        # Get the embedding for the detailed description
        embedding = get_embedding(fulltext)
        # embedding_dd = get_embedding(detailed_description)
        # Log the embedding vector
        logger.debug(f"Generated embedding for row {index + 1}")
        # logger.info("Inserting Vectors into DB", {embedding})
        # Insert data into PostgreSQL
        insert_data(conn, psp_element, network_number, description, detailed_description, final_gpt_text, embedding)
        
        # Calculate percentage completion
        # Log percentage completion at intervals (e.g., every 10%)
        if (index + 1) % (total_rows) == 0:  # Log every 10%
            percentage_complete = ((index + 1) / total_rows) * 100
            logger.info(f"Progress: {percentage_complete:.2f}% complete")
    # Close the database connection
    conn.close()

    logger.info("Data processing and database insertion completed!")


@app.post("/insert_psp_data_to_db") 
async def insert_psp_data_to_db():
    try:
        csv_file_path = 'Data/PSP Sample Data.csv'
        logger.info(f"CSV Found {csv_file_path}")

        # Process the CSV and store embeddings
        process_csv_and_store_embeddings(csv_file_path)

        # Explicitly return the extracted data in the response
        return {"message": "PSP Data processed and stored successfully."}        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing the PSP File.")


@app.post("/networkvectors/vectorize") 
async def networkvectors():
    try:
        logger.info("Fetching distinct Network from psp_data table")
        listofnetwork = execute_query("SELECT DISTINCT network FROM psp_data")
        logger.info(f"Network numbers fetched: {listofnetwork}")

        if not listofnetwork:
            logger.warning("No Network numbers found in the psp_data table")
            return {"status":"warning","message":"No Network Numders found"}
        
        for network in listofnetwork:
            network_name = network['network_number'] if isinstance(network,dict) else network[0]
            embedding = get_embedding(network_name)
            statement = f"INSERT INTO "


            # @@@Continue from here

    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing the PSP File.")


@app.post("/predict_psp_as_per_calendar_data") 
async def predict_psp_as_per_calendar_data(query: Query):
    try:
        return
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing the PSP File.")


@app.get("/")
async def root():
    return {"message": "BTP PostgresSQL vector store and Similarity.", "docs":"/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)