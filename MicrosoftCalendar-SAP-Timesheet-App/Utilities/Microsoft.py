import os
import requests
from loguru import logger
import logging
from dotenv import load_dotenv

load_dotenv()

# Database connection settings retrieved from environment variables
tenantid = os.getenv("Azuretenantid")
AzureAuthURL = os.getenv("AzureAuthURL")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import time


# def write_logs(file_path = "logfile_MS.txt" , text=None):
#     try:
#         # Open the file in append mode ('a') to write logs
#         with open(file_path, "a") as file:
#             file.write(text + "\n")  # Write the text and add a newline character
#         print(f"Log written to {file_path}")
#     except Exception as e:
#         print(f"Error writing to file: {e}")
# def write_logs(file_path = "logfile_MS.txt" , text=None):
#     try:
#         # Open the file in append mode ('a') to write logs
#         with open(file_path, "a") as file:
#             file.write(text + "\n")  # Write the text and add a newline character
#         print(f"Log written to {file_path}")
#     except Exception as e:
#         print(f"Error writing to file: {e}")


# Global variables to cache the token and expiration time
access_token_cache = {
    'token': None,
    'expires_at': None
}


def get_azure_access_token():
    global access_token_cache

    # If we have a valid token, reuse it
    if access_token_cache['token'] and access_token_cache['expires_at'] > time.time():
        return access_token_cache['token']

    try:

        url = f"https://login.microsoftonline.com/{tenantid}/oauth2/v2.0/token"

        payload = AzureAuthURL

        headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cookie': 'fpc=AlQ0mmNU0G9JmoJyj64yfpbbNZPjAQAAAJRgjt4OAAAA'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        # Convert response text (JSON format) to Python dictionary
        response_json = response.json()

        # Get the expiration time (access token usually lasts 3600 seconds)
        expires_in = response_json.get('expires_in', 3600)
        expiration_time = time.time() + expires_in

        # Cache the token and expiration time
        access_token_cache['token'] = response_json['access_token']
        access_token_cache['expires_at'] = expiration_time
        
        
        return access_token_cache['token']

        # # Print the access token
        # if 'access_token' in response_json:
        #     return response_json['access_token']
        # else:
        #     return print("Access token not found in the response")

    except Exception as e:
        logger.error(f"Error in Getting Acess Token: {e} ")
        raise





def get_calendar_of_user(userId):

    access_token = (get_azure_access_token())
    
    # write_logs(text= f"Token Received = {access_token_cache['token']}, UserID ={userId}")
    # write_logs(text= f"Token Received = {access_token_cache['token']}, UserID ={userId}")

    if not access_token:
        logger.error("Access token could not be retrieved. Cannot proceed.")
        return

    try:
        url = f"https://graph.microsoft.com/v1.0/users/{userId}/calendar/events?$select=subject,body,bodyPreview,start,end"

        payload = {}
        headers = {
          'Authorization': f'Bearer {access_token}',
          'Prefer': 'outlook.timezone="Eastern Standard Time"'
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        # Parse the JSON response
        response_json = response.json()

        # Return only the 'value' field
        if 'value' in response_json:
            return response_json['value']
        else:
            logger.error("No 'value' field found in the response")
            return None
    except Exception as e:
        logger.error(f"Error in Getting Acess Token: {e} ")
        raise

# print(get_calendar_of_user("d5ee5c06-a179-49a0-b406-3747410034db"))

# print(get_calendar_of_user("1ee8cad3-49cc-439e-8e36-6e72a1e0c596"))

# print(get_calendar_of_user("d5ee5c06-a179-49a0-b406-3747410034db"))



