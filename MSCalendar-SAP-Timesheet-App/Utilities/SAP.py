import os
import requests
from dotenv import load_dotenv
from loguru import logger
import logging
import json

load_dotenv()

# Database connection settings retrieved from environment variables
BaseURL = os.getenv("BaseURL")
BasicAuth = os.getenv("BasicAuth")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import time


def write_logs(file_path = "logfile_SAP.txt" , text=None):
    try:
        # Open the file in append mode ('a') to write logs
        with open(file_path, "a") as file:
            file.write(text + "\n")  # Write the text and add a newline character
        print(f"Log written to {file_path}")
    except Exception as e:
        print(f"Error writing to file: {e}")
# def write_logs(file_path = "logfile_MS.txt" , text=None):
#     try:
#         # Open the file in append mode ('a') to write logs
#         with open(file_path, "a") as file:
#             file.write(text + "\n")  # Write the text and add a newline character
#         print(f"Log written to {file_path}")
#     except Exception as e:
#         print(f"Error writing to file: {e}")


# Global variables to cache the token and expiration time
sap_access_token_cache = {
    'token': None,
    'expires_at': None
}

def get_sap_access_token():
    global sap_access_token_cache

    # If we have a valid token, reuse it
    if sap_access_token_cache['token'] and sap_access_token_cache['expires_at'] > time.time():
        return sap_access_token_cache['token']

    try:

        url = BaseURL

        params = {
            "$filter": "(PersonWorkAgreementExternalID eq '00057665') and (TimeSheetDate ge datetime'2024-10-05T00:00:00' and TimeSheetDate le datetime'2024-10-15T23:59:59')",
            "$format": "json"
        }
        
        payload = {}
        headers = {
        'X-CSRF-TOKEN': 'fetch',
        'Authorization': BasicAuth
        }

        response = requests.request("GET", url, headers=headers,params=params,  data=payload)
        # Convert response text (JSON format) to Python dictionary
        response_json = response.json()

        # Get the expiration time (access token usually lasts 3600 seconds)
        expires_in = response_json.get('expires_in', 3600)
        expiration_time = time.time() + expires_in

        # Cache the token and expiration time
        sap_access_token_cache['token'] = response.headers.get('X-CSRF-TOKEN')
        sap_access_token_cache['expires_at'] = expiration_time
        
        
        return sap_access_token_cache['token']

        # # Print the access token
        # if 'access_token' in response_json:
        #     return response_json['access_token']
        # else:
        #     return print("Access token not found in the response")

    except Exception as e:
        logger.error(f"Error in Getting Acess Token: {e} ")
        raise





def post_cat2_timesheet_in_sap():
    
    write_logs(text= f"im in SAP.py")
    access_token = get_sap_access_token()
    
    write_logs(text= f"Token Received = {access_token}")
    # write_logs(text= f"Token Received = {access_token_cache['token']}, UserID ={userId}")

    if not access_token:
        logger.error("Access token could not be retrieved. Cannot proceed.")
        return

    try:
        # url = f"https://graph.microsoft.com/v1.0/users/{userId}/calendar/events?$select=subject,body,bodyPreview,start,end"

        # payload = {}
        # headers = {
        #   'Authorization': f'Bearer {access_token}',
        #   'Prefer': 'outlook.timezone="Eastern Standard Time"'
        # }

        # response = requests.request("GET", url, headers=headers, data=payload)
        # # Parse the JSON response
        # response_json = response.json()

        # # Return only the 'value' field
        # if 'value' in response_json:
        #     return response_json['value']
        # else:
        #     logger.error("No 'value' field found in the response")
        #     return None
        url = BaseURL

        payload = json.dumps({
        "PersonWorkAgreementExternalID": "00057665",
        "CompanyCode": "4000",
        "TimeSheetRecord": "",
        "PersonWorkAgreement": "57665",
        "TimeSheetDate": "2024-10-16T00:00:00",
        "TimeSheetIsReleasedOnSave": False,
        "TimeSheetPredecessorRecord": "",
        "TimeSheetStatus": "",
        "TimeSheetIsExecutedInTestRun": False,
        "TimeSheetOperation": "C",
        "TimeSheetDataFields": {
            "ControllingArea": "1000",
            "SenderCostCenter": "2063503",
            "ReceiverCostCenter": "",
            "InternalOrder": "",
            "ActivityType": "D10009",
            "WBSElement": "",
            "WorkItem": "",
            "BillingControlCategory": "20",
            "PurchaseOrder": "",
            "PurchaseOrderItem": "0",
            "TimeSheetTaskType": "",
            "TimeSheetTaskLevel": "",
            "TimeSheetTaskComponent": "",
            "TimeSheetNote": "Time and Salary - Meetings",
            "RecordedHours": "8.00",
            "RecordedQuantity": "8.000",
            "HoursUnitOfMeasure": "H",
            "RejectionReason": "",
            "TimeSheetWrkLocCode": "",
            "TimeSheetOvertimeCategory": "",
            "SenderPubSecFund": "",
            "SendingPubSecFunctionalArea": "",
            "SenderPubSecGrant": "",
            "SenderPubSecBudgetPeriod": "",
            "ReceiverPubSecFund": "",
            "ReceiverPubSecFuncnlArea": "",
            "ReceiverPubSecGrant": "",
            "ReceiverPubSecBudgetPeriod": ""
        }
        })

        headers = {
        'x-csrf-token': access_token,
        'Content-Type': 'application/json',
        'Authorization': BasicAuth
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        return(response.text)

    except Exception as e:
        logger.error(f"Error in Getting Acess Token: {e} ")
        raise


