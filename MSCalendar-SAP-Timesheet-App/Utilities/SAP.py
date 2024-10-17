import os
import requests
from dotenv import load_dotenv
from loguru import logger
import logging
import json
import streamlit as st

load_dotenv()

#cert_path = os.path.join(os.path.dirname(__file__), "SSLCert.cer")

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


# Global variables to cache the token and expiration time
sap_access_token_cache = {
    'token': None,
    'expires_at': None
}

def get_sap_access_token():
    try:

        url = BaseURL
        params = {
            "$filter": "(PersonWorkAgreementExternalID eq '00057665') and (TimeSheetDate ge datetime'2024-10-05T00:00:00' and TimeSheetDate le datetime'2024-10-15T23:59:59')",
            "$format": "json"
        }
        
        payload = ""
        headers = {
        'X-CSRF-TOKEN': 'fetch',
        'Authorization': f"{BasicAuth}",
        'Cookie': 'fetch'
        }

        response = requests.request("GET", url, headers=headers,params=params,  data=payload, verify=False)
        # Convert response text (JSON format) to Python dictionary
        #response_json = response.json()
        
        token=response.headers.get('X-CSRF-TOKEN')
        cookies = str(f"MYSAPSSO2={response.cookies.get('MYSAPSSO2')}; SAP_SESSIONID_ES0_460={response.cookies.get('SAP_SESSIONID_ES0_460')}; sap-usercontext={response.cookies.get('sap-usercontext')}")
        return token,cookies

    except Exception as e:
        logger.error(f"Error in Getting Acess Token: {e} ")
        raise





def post_cat2_timesheet_in_sap():
    
    sap_access_token,cookies = get_sap_access_token()
    
    #write_logs(text= f"Token Received = {sap_access_token} and Coockie Recieved: {cookies}")
    # write_logs(text= f"Token Received = {access_token_cache['token']}, UserID ={userId}")

    if not sap_access_token:
        logger.error("Access token could not be retrieved. Cannot proceed.")
        return

    try:

        url = BaseURL

        payload = json.dumps({
        "PersonWorkAgreementExternalID": "00057665",
        "CompanyCode": "4000",
        "TimeSheetRecord": "",
        "PersonWorkAgreement": "57665",
        "TimeSheetDate": "2024-10-17T00:00:00",
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
            "TimeSheetNote": "Time and Salary - Meetings From Code",
            "RecordedHours": "12.00",
            "RecordedQuantity": "12.000",
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

       

        post_headers = {
        'x-csrf-token': sap_access_token,
        'Content-Type': 'application/json',
        'Authorization': BasicAuth,
        'Accept': 'application/json',
        'Cookie': cookies
        }

        #write_logs(text= f"Final Data : URL {url} /// payload {payload} /// Headers: {post_headers} ")

        response = requests.request("POST", url, headers=post_headers, data=payload,verify=False)

        return(response)

    except Exception as e:
        logger.error(f"Error in Getting Acess Token: {e} ")
        raise