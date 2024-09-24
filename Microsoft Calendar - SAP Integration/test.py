import requests

import os
import json
import psycopg2
import requests
import ast  # Import ast to safely evaluate string to list
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException

import psycopg2
import pandas as pd
from psycopg2 import sql
from loguru import logger
import openai
import time
from tqdm import tqdm
from requests.auth import HTTPBasicAuth
import json
from ai_api_client_sdk.ai_api_v2_client import AIAPIV2Client
# Load environment variables from the .env file
load_dotenv()

ai_api_url = os.getenv("AI_API_URL")
client_id = os.getenv("AICORE_CLIENT_ID")
client_secret = os.getenv("AICORE_CLIENT_SECRET")
AICORE_RESOURCE_GROUP = os.getenv("AICORE_RESOURCE_GROUP")
auth_base_url = os.getenv("AICORE_BASE_URL")
EMB_DEPLOYMENT_ID = os.getenv("EMB_DEPLOYMENT_ID")

# SAP_API_KEY  = os.getenv("SAP_API_KEY") 


# ai_api_client = AIAPIV2Client(
# base_url=auth_base_url, 
# auth_url= ai_api_url,
# client_id= client_id,
# client_secret= client_secret,
# resource_group= 'default'
# )
# print(ai_api_client.rest_client.get_token())



import requests
def get_sap_api_key(client_id, client_secret, url):
    # Set up the request parameters
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    # Send the POST request to get the access token
    response = requests.post(url, headers=headers, data=data)

    # Check if the request was successful
    if response.status_code == 200:
        # Extract the access token from the response
        access_token = response.json()["access_token"]
        return access_token
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


# Usage example
client_id = client_id
client_secret = client_secret
auth_base_url = f"{auth_base_url}/oauth/token"

api_key = get_sap_api_key(client_id, client_secret, auth_base_url)
if api_key:
            print(f"API Key: {api_key}")
        # You can now use this api_key to make requests to SAP AI Core
else:
            print("Failed to retrieve API key")




def get_embedding(text):
    """
    Generate an embedding for a given text using OpenAI's text-embedding-ada-002 model.
    """

    url2 = f"{ai_api_url}/v2/inference/deployments/{EMB_DEPLOYMENT_ID}"

    payload2 = json.dumps({
        "input": text,
        "model": "text-embedding-ada-002"
    })
    headers2 = {
        'Content-Type': 'application/json',
        'Authorization': (api_key)
    }
    # logger.info(f"Starting embedding for deployment ID: {EMB_DEPLOYMENT_ID}")
    # Make the API request
    try:
        response1 = requests.post(url2, headers=headers2, data=payload2)
        response1.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        logger.error(f"Response content: {e.response.content if e.response else 'No response content'}")
        raise


    # test_response = requests.get(AICORE_BASE_URL, auth=HTTPBasicAuth(AICORE_CLIENT_ID, AICORE_CLIENT_SECRET))
    # print(f"Test response status code: {test_response.status_code}")
    # print(f"Test response content: {test_response.content}")

    embeddings = response1.json()['data'][0]['embedding']
    logger.info("Embedding completed successfully")
    return embeddings

# Usage
output = get_embedding("test embedding")
print(output)



# def get_embedding(text, api_key, api_url):
#     headers = {
#         'Content-Type': 'application/json',
#         'Authorization': f'Bearer {api_key}'
#     }
    
#     payload = {
#         'text': text
#     }
    
#     try:
#         response = requests.post(api_url, headers=headers, data=json.dumps(payload))
#         response.raise_for_status()  # Raise an exception for bad status codes
        
#         result = response.json()
#         return result['embedding']
#     except requests.exceptions.HTTPError as e:
#         if e.response.status_code == 404:
#             print(f"Error 404: The API URL '{api_url}' was not found. Please check if the URL is correct.")
#         else:
#             print(f"HTTP Error occurred: {e}")
#     except requests.exceptions.RequestException as e:
#         print(f"An error occurred: {e}")
#     return None

#    # Replace these with your actual values
# API_KEY = api_key
# API_URL = f"{ai_api_url}/v2/inference/deployments/d0a7fd4ff34eb2d0"

#    # Example usage
# text_to_embed = "Hello, world!"
# embedding = get_embedding(text_to_embed, API_KEY, API_URL)

# if embedding:
#     print(f"Embedding for '{text_to_embed}':")
#     print(embedding)
# else:
#     print("Failed to get embedding.")

# # Verify the API URL
# def verify_api_url(url):
#     try:
#         response = requests.get(url)
#         print(f"Status code: {response.status_code}")
#         print(f"Response: {response.text[:100]}...")  # Print first 100 characters of response
#     except requests.exceptions.RequestException as e:
#         print(f"Error verifying URL: {e}")

# print("\nVerifying API URL:")
# verify_api_url(API_URL)
   



# "model": "text-embedding-ada-002"

# auth_url = os.getenv("AICORE_AUTH_URL")

# url1 = f"{AICORE_BASE_URL}/v2/inference/deployments/{EMB_DEPLOYMENT_ID}"
        
# payload1 = json.dumps({
#             "input": "Sample embedding"
#         })
# headers1 = {
#             'Content-Type': 'application/json',
#             'Authorization': f'Bearer {api_key}'
#         }
# logger.info(f"Embedding started:")
#         # Make the API request
# response1 = requests.post(url1, headers=headers1, data=payload1)
        
#     # Handle potential errors
# if response1.status_code != 200:
#      raise HTTPException(status_code=500, detail=f"Error generating embedding: {response1.status_code} - {response1.text}")
        

        # logger.info(f"Embedding started: { response1.json()['data'][0]['embedding'] }")
        # Parse and return the embedding
        # logger.info(f"Embedded Successfully")
# embeddings = response1.json()['data'][0]['embedding']
# print(embeddings)  