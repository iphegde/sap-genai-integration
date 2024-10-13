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
import io
from psycopg2 import sql
from loguru import logger
import openai
import time
from tqdm import tqdm
from fastapi.middleware.cors import CORSMiddleware
import logging
from pydantic import BaseModel
from typing import List
from fuzzywuzzy import fuzz
# from frontend.app import write_logs

from supabase import create_client, Client



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

def write_logs(file_path = "logfile_main.txt" , text=None):
    try:
        # Open the file in append mode ('a') to write logs
        with open(file_path, "a") as file:
            file.write(text + "\n")  # Write the text and add a newline character
        print(f"Log written to {file_path}")
    except Exception as e:
        print(f"Error writing to file: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Query(BaseModel):
    title:str
    body:str

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
        "model": "gpt-4o",
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
        # logger.info(f"DB Connection: host={DB_HOST}, dbname={DB_NAME}, user={DB_USER}, password={DB_PASSWORD} > Connection: {conn}")
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

# Function to process the CSV and store embeddings
def process_csv_and_store_embeddings(df):
    # Load the CSV file into a DataFrame
    # df = pd.read_csv(csv_file_path, delimiter=',', encoding='utf-8')
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

def execute_query(statement):
    try:
        conn = connect_to_db()
        logger.info(f"conn value: {conn}")
        cursor = conn.cursor()
        logger.info(f"cursor value: {cursor}")
        cursor.execute(statement)
        rows = ''
        if 'SELECT' in statement:
            rows = cursor.fetchall()
        conn.commit()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"Error in execute_query: {e}")
        raise

def fetch_pspdescription_from_title(title,  listofpspdescription):
    try:
        system = f"""This is the list of PSP Description: {str(listofpspdescription)}. 
        Retain the ID (example:P-00494-01-01 as it is) and try to Find a meaningful description/category from the text except the ID and respond within 4 words"""
        text=title
        pspdescriptionfromspecs = chat_completions(system,text)
        return pspdescriptionfromspecs
    except Exception as e:
        logger.error(f"Error in fetch_pspdescription_from_title: {e} ")
        raise

def fuzzypspdesc(listofpspdescription, pspdescriptionfromtitle):
    try:
        if not listofpspdescription:
            raise ValueError("The list of PSP Description is empty.")
        
        fuzz_score = []
        for pspdescription in listofpspdescription:
            
            fuzz_unique = {
                "pspdescription": pspdescription[0],
                "score": fuzz.ratio(pspdescription[0],pspdescriptionfromtitle)
            }
            fuzz_score.append(fuzz_unique)

        if not fuzz_score:
            raise ValueError("No fuzzy matches found.")
        
        sorted_data = sorted(fuzz_score, key=lambda x: x['score'],reverse=True)

        # sorted_data = []
        return sorted_data[0]['pspdescription']
    except Exception as e:
        logger.error(f"Error in fuzzypspdesc: {e}")
        raise

# Function to fetch data
# def get_psp_data(description: str, embedding: str):
#     # Query data from 'psp_data' table with matching description
#     try:
#         # Initialize Supabase client
#         url: str = os.environ.get("SUPABASE_URL")
#         key: str = os.environ.get("SUPABASE_KEY")
#         supabase: Client = create_client(url, key)

#         # Supabase query example
#         response = supabase.from_("psp_data").select("*").eq("description", description).limit(3).execute()
        
#         if response.data:
#             # Here you'd need to handle the embedding <-> vector logic separately
#             # Supabase might not support such vector operations directly via SQL, so this requires further handling
#             write_logs(text= f"success {response.data}")
#             return response.data
#         else:
#             write_logs(text= f"No data found")
#             return {"message": "No data found"}
    
#     except Exception as e:
#         print(f"Error occurred: {e}")
#         return {"message": "Failed to fetch data"}


def fetch_prediction_vector_from_db(description:str ,embedding:list):
    try:

        conn = connect_to_db()
        cursor = conn.cursor()
        
        # logger.info(f"Conn: {conn}, Cursor> {cursor}")

        # write_logs(text= f"Conn: {conn}, Cursor> {cursor}")

        # If description is provided, use it in the WHERE clause
        if description:
            query = """
            SELECT * FROM psp_data
            WHERE description = %s
            ORDER BY embedding <-> %s::vector
            LIMIT 3
            """
            # logger.info(f"Query> {query}")
            cursor.execute(query, (description, embedding))
        else:
            # If description is not provided, exclude the WHERE clause
            query = """
            SELECT * FROM psp_data
            ORDER BY embedding <-> %s::vector
            LIMIT 3
            """
            cursor.execute(query, (embedding,))

        # WHERE description = %s
        # logger.info(f"Executing query for Precting PSP: {query}")

        # cursor.execute(query, (pspdescription, embedding))
        # cursor.execute(query, (embedding,))
        rows = cursor.fetchall()
        conn.commit()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        logger.error(f"Error in fetch_prediction_vector_from_db: {e}")
        raise

@app.post("/insert_psp_data_to_db") 
async def insert_psp_data_to_db(file: UploadFile = File(...)):
    try:
        # write_logs(text= f"Im inside API Call")
        # Read the uploaded file
        # write_logs(text= f"Received file: {file.filename}, content_type: {file.content_type}")
        contents = await file.read()

        # write_logs(text= f"File contents length: {len(contents)}") 
        # Use pandas to read the CSV from the bytes
        # Convert the byte stream to a string using UTF-8 decoding
        contents_str = contents.decode('utf-8')

        # Use pandas to read the CSV from the decoded string
        df = pd.read_csv(io.StringIO(contents_str))
        # write_logs(text= f"df:{df}")


        # write_logs(text= f"Im inside API Call = {contents} ,  {df} ")

        # csv_file_path = 'Data/PSP Sample Data.csv'
        # logger.info(f"CSV Found {csv_file_path}")

       # Process the CSV and store embeddings
        process_csv_and_store_embeddings(df)

        # Explicitly return the extracted data in the response
        return {"message": "PSP Data processed and stored successfully."}        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing the PSP File.")


@app.post("/pspshortdescvectors/vectorize") 
async def pspshortdescvectors():
    try:
        logger.info("Fetching distinct PSP based on description from psp_data table")
        listofpspdescription = execute_query("SELECT DISTINCT description FROM psp_data")
        logger.info(f"Network numbers fetched: {listofpspdescription}")

        if not listofpspdescription:
            logger.warning("No PSP Descriptions found in the psp_data table")
            return {"status":"warning","message":"No PSP Descriptions found"}
        
        for pspdescription in listofpspdescription:
            description_name = pspdescription['description'] if isinstance(pspdescription,dict) else pspdescription[0]
            embedding = get_embedding(description_name)
            # statement = f"INSERT INTO description_text_embeddings '{description_name}' with embedding: {embedding}"

            statement = f"INSERT INTO description_text_embeddings (description, embedding) VALUES ('{description_name}', '{embedding}')"

            logger.info(f"Inserting PSP Description '{description_name}'with embedding")
            execute_query(statement)

            # @@@Continue from here

    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing the PSP File.")


@app.post("/predict_psp_as_per_calendar_data") 
async def predict_psp_as_per_calendar_data(query: Query):
    try:
        # write_logs(text= f"Received query: {query}")
        logger.info(f"Received query: {query}")
        combined_text = f"{query.title} {query.body}"
        embedding = get_embedding(combined_text)
        # title_embedding = get_embedding(query.title)
        # Concatenate the two embeddings (lists)
        # embedding = title_embedding + body_embedding
        # embedding_str = "[" + ",".join(map(str, embedding )) + "]"

        # listofpspdescription = execute_query("SELECT DISTINCT description FROM description_text_embeddings")
        # logger.info(f"PSP Descriptions fetched: {listofpspdescription}")

        # if not listofpspdescription:
        #     logger.warning("No PSP description found in the description_text_embeddings table")
        #     return{"status": "warning", "message":"No PSP Descriptions found"}
        
        # pspdescriptionfromtitle = fetch_pspdescription_from_title(query.title, listofpspdescription)
        # logger.info(f"fetch_pspdescription_from_specs: {pspdescriptionfromtitle}")
        # pspdescription = fuzzypspdesc(listofpspdescription, pspdescriptionfromtitle)
        # logger.info(f"Desc Value: {pspdescription}")
        
        pspdescription=None

        # FastAPI Route
        # @app.post("/search")
        # def search_data(description: str, embedding: str):
        # test = get_psp_data(pspdescription, embedding)
        # return test
        


        predictions = fetch_prediction_vector_from_db(pspdescription,embedding)

        # Extract the relevant values (2nd, 3rd, and 4th)
        # Assuming you are working with the first sub-list from api_response
        return{
           "PSP Element": predictions[0][1],  # 2nd element in the list
           "Network Number": predictions[0][2],  # 3rd element in the list
           "PSP Short Description": predictions[0][3]   # 4th element in the list
        }


        # return {"Prediction": predictions, "PSP Description": pspdescription}
    except Exception as e:
        logger.error(f"Error fetching prediction of PSP: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/")
async def root():
    return {"message": "BTP PostgresSQL vector store and Similarity.", "docs":"/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)