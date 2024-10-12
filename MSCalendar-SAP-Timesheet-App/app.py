# import streamlit as st
# import requests
# import base64
# from io import BytesIO

# # Set FastAPI backend URL
# FASTAPI_URL = "http://localhost:8000"  # Update with your FastAPI server URL

# # Streamlit App Configuration
# st.set_page_config(page_title="Invoice Processing and Comparison", layout="wide")

# # Streamlit App Title
# st.title("Invoice Processing and Comparison")

# # Sidebar with App Description and Navigation at the Top
# st.sidebar.title("Navigation")
# options = st.sidebar.radio("Choose Functionality", ["Process Invoice", "Compare Invoice"])

# # Add a separator for a clean layout
# st.sidebar.markdown("---")

# # Sidebar with Application Description
# st.sidebar.title("About the Application")
# st.sidebar.write(
#     """
#     This application allows you to upload PDF invoices to extract and compare their details.

#     **How to Use:**
#     - **Process Invoice**: Upload a PDF file to extract invoice details and store them in the database.
#     - **Compare Invoice**: Upload a PDF file to compare it with existing invoices in the database to identify potential duplicates.
    
#     **FastAPI Routes:**
#     - `/process_invoice/` : Processes the uploaded invoice and extracts its details.
#     - `/compare_invoice/` : Compares the uploaded invoice with existing invoices in the database.

#     The backend is powered by **FastAPI**, ensuring fast and efficient processing.
#     """
# )

# # Function to upload and process invoice
# def process_invoice(file):
#     """
#     Function to upload an invoice to the FastAPI backend for processing.
#     """
#     try:
#         files = {'file': (file.name, file.getvalue(), "application/pdf")}
#         response = requests.post(f"{FASTAPI_URL}/process_invoice/", files=files)
#         if response.status_code == 200:
#             st.success("Invoice processed and stored successfully.")
#             # Display the extracted JSON details
#             response_data = response.json()
#             with col2:
#                 st.subheader("Extracted Invoice Details:")
#                 st.json(response_data.get("extracted_data", {}))  # Access the 'extracted_data' field from response
#         else:
#             with col2:
#                 st.error(f"Error: {response.json()['detail']}")
#     except Exception as e:
#         with col2:
#             st.error(f"Failed to process the invoice: {e}")



# # Function to display the uploaded PDF file
# def display_pdf(file):
#     """
#     Function to display the uploaded PDF file in the UI using an iframe.
#     """
#     try:
#         # Convert the uploaded file to a base64-encoded string
#         base64_pdf = base64.b64encode(file.getvalue()).decode('utf-8')
#         pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600px"></iframe>'
#         with col1:
#             st.markdown(pdf_display, unsafe_allow_html=True)
#     except Exception as e:
#         with col2:
#             st.error(f"Failed to display the PDF: {e}")

# # Define columns for side-by-side layout with default placeholders
# col1, col2 = st.columns(2)

# with col1:
#     st.subheader("Uploaded PDF Preview")
#     st.markdown("Upload a PDF file to preview it here.")

# with col2:
#     st.subheader("JSON Output")
#     st.markdown("Extracted or comparison results will be displayed here.")

# # Automatically process and display invoice upon upload
# if options == "Process Invoice":
#     st.header("Process Invoice")
#     st.write("Upload a PDF invoice to extract and store its details in the database.")
#     uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

#     if uploaded_file is not None:
#         display_pdf(uploaded_file)
#         with col2:
#             with st.spinner("Processing..."):
#                 process_invoice(uploaded_file)

# # Automatically process and compare invoice upon upload
# elif options == "Compare Invoice":
#     st.header("Compare Invoice")
#     st.write("Upload a PDF invoice to compare it with the existing invoices in the database.")
#     uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

#     if uploaded_file is not None:
#         display_pdf(uploaded_file)
        # with col2:
        #     with st.spinner("Comparing..."):
        #         compare_invoice(uploaded_file)


import streamlit as st
import json
# from streamlit_ace import st_ace
import requests
import pandas as pd
import sys
import os
from pathlib import Path

# Add project root (parent directory of 'frontend') to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(sys.path)
from Utilities.Microsoft import get_calendar_of_user

# Set FastAPI backend URL
FASTAPI_URL = "http://localhost:8000"  # Update with your FastAPI server URL


def write_logs(file_path = "logfile.txt" , text=None):
    try:
        # Open the file in append mode ('a') to write logs
        with open(file_path, "a") as file:
            file.write(text + "\n")  # Write the text and add a newline character
        print(f"Log written to {file_path}")
    except Exception as e:
        print(f"Error writing to file: {e}")





# Initialize session state
if 'config' not in st.session_state:
    st.session_state.config =   {
                                "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users('d5ee5c06-a179-49a0-b406-3747410034db')/calendar/events(subject,body,bodyPreview,start,end)",
                                "value": [
                                    {
                                        "@odata.etag": "W/\"7RhHqMbxvkOtxA7QqQ/XTAAABFMEjg==\"",
                                        "id": "AAMkAGRlYjIyODFkLWYwYjUtNDU0Yy1iY2YxLWM2NWNkMTk1MWMyOQBGAAAAAAAb-CM9bNhdRqCC_-_6-YPPBwDtGEeoxvG_Q63EDtCpD9dMAAAAAAENAADtGEeoxvG_Q63EDtCpD9dMAAAEVBerAAA=",
                                        "subject": "Follow up weekly meeting on HR Project",
                                        "bodyPreview": "Status of your Tasks",
                                        "body": {
                                            "contentType": "html",
                                            "content": "<html>\r\n<head>\r\n<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">\r\n</head>\r\n<body>\r\nStatus of your Tasks\r\n</body>\r\n</html>\r\n"
                                        },
                                        "start": {
                                            "dateTime": "2024-09-20T12:00:00.0000000",
                                            "timeZone": "Eastern Standard Time"
                                        },
                                        "end": {
                                            "dateTime": "2024-09-20T13:00:00.0000000",
                                            "timeZone": "Eastern Standard Time"
                                        }
                                    },
                                    {
                                        "@odata.etag": "W/\"7RhHqMbxvkOtxA7QqQ/XTAAABFL+aQ==\"",
                                        "id": "AAMkAGRlYjIyODFkLWYwYjUtNDU0Yy1iY2YxLWM2NWNkMTk1MWMyOQBGAAAAAAAb-CM9bNhdRqCC_-_6-YPPBwDtGEeoxvG_Q63EDtCpD9dMAAAAAAENAADtGEeoxvG_Q63EDtCpD9dMAAAEVBeqAAA=",
                                        "subject": "Meeting with Pooja",
                                        "bodyPreview": "Does noon work for you?",
                                        "body": {
                                            "contentType": "html",
                                            "content": "<html>\r\n<head>\r\n<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">\r\n</head>\r\n<body>\r\n<div>Does noon work for you?</div>\r\n</body>\r\n</html>\r\n"
                                        },
                                        "start": {
                                            "dateTime": "2024-09-20T15:00:00.0000000",
                                            "timeZone": "Eastern Standard Time"
                                        },
                                        "end": {
                                            "dateTime": "2024-09-20T17:00:00.0000000",
                                            "timeZone": "Eastern Standard Time"
                                        }
                                    },
                                    {
                                        "@odata.etag": "W/\"7RhHqMbxvkOtxA7QqQ/XTAAABFL5/Q==\"",
                                        "id": "AAMkAGRlYjIyODFkLWYwYjUtNDU0Yy1iY2YxLWM2NWNkMTk1MWMyOQBGAAAAAAAb-CM9bNhdRqCC_-_6-YPPBwDtGEeoxvG_Q63EDtCpD9dMAAAAAAENAADtGEeoxvG_Q63EDtCpD9dMAAAEVBepAAA=",
                                        "subject": "Meeting with Prasanna",
                                        "bodyPreview": "Does noon work for you?",
                                        "body": {
                                            "contentType": "html",
                                            "content": "<html>\r\n<head>\r\n<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">\r\n</head>\r\n<body>\r\nDoes noon work for you?\r\n</body>\r\n</html>\r\n"
                                        },
                                        "start": {
                                            "dateTime": "2024-09-21T15:00:00.0000000",
                                            "timeZone": "Eastern Standard Time"
                                        },
                                        "end": {
                                            "dateTime": "2024-09-21T17:00:00.0000000",
                                            "timeZone": "Eastern Standard Time"
                                        }
                                    }
                                    ]
                                }

if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Insert PSP Data"



calendarJson = {}
# Use st.session_state to track calendarJson changes
if 'calendarJson' not in st.session_state:
    st.session_state.calendarJson = calendarJson


# Format duration in the desired format
def format_duration(duration):
    total_minutes = duration.total_seconds() // 60  # Convert duration to total minutes
    hours = total_minutes // 60
    minutes = total_minutes % 60
    # Convert to decimal format: 0,00 for 0 hours; 0,50 for 30 mins; 1,00 for 1 hour; etc.
    # The conversion factor maps minutes to the decimal format:
    # 0 minutes = 0.00, 30 minutes = 0.50, 60 minutes = 1.00, 90 minutes = 1.50
    decimal_minutes = minutes / 60
    decimal_duration = hours + decimal_minutes

    return f"{decimal_duration:.2f}".replace('.', ',')  # Format and replace decimal point with a comma
    # Format as required
    # return f"{int(hours)},{int(minutes):02d}"  # Use two digits for minutes
# Function to update calendarJson in session state
def convert_json_to_table():

    df = pd.DataFrame(st.session_state.calendarJson)

    if 'start' in df:
        # Convert start and end columns to datetime
        # Extract datetime strings from dictionaries
        df['start'] = df['start'].apply(lambda x: x['dateTime'])
        df['end'] = df['end'].apply(lambda x: x['dateTime'])

        # Now convert to datetime
        df['start'] = pd.to_datetime(df['start'])
        df['end'] = pd.to_datetime(df['end'])
        # Extract date from start column and calculate time difference  
        df['date'] = df['start'].dt.date  # Get date part
        df['duration'] = df['end'] - df['start']  # Calculate time difference
        # Apply formatting function
        df['Time Spent'] = df['duration'].apply(format_duration)
        
        return df[['subject', 'bodyPreview', 'date', 'Time Spent' ]]
    else:
        return df

# Function to update calendarJson in session state
def update_calendar(user_id):
    # Fetch new calendar data
    new_calendarJson = get_calendar_of_user(user_id)  # API call to get data for selected user
    # Update session state with new data
    st.session_state.calendarJson = new_calendarJson

# Function to call API endpoints
def call_api(endpoint, data):
    # Replace with your actual API URL
    base_url ="http://localhost:8000"
    response = requests.post(f"{base_url}/{endpoint}", json=data)
    return response.json()

# Main app
st.set_page_config(layout="wide")

# Sidebar
with st.sidebar:
    st.title("PSP Predictor App")
    st.subheader("Gen AI Powered")

    # Service provider selection
    service_provider = st.selectbox(
        "Select Service Provider",
        ["OpenAI", "AzureOpenAI", "SAP OpenAI", "Github Copilot"]
    )

    # Model selection based on service provider
    models = {
        "OpenAI": ["GPT-3.5", "GPT-4", "DALL-E"],
        "AzureOpenAI": ["Azure-GPT-3", "Azure-GPT-4"],
        "SAP OpenAI": ["SAP-AI-Core", "SAP-Conversational-AI"],
        "Github Copilot": ["Copilot"]
    }
    selected_model = st.selectbox("Select Model", models[service_provider])

    # Display current configuration
    # st.subheader("Current Configuration")
    # st.json(st.session_state.config)


def get_psp_network(subject, bodyPreview):
    """
    Function to upload an CSV to the FastAPI backend for processing.
    """
    try:
        # Prepare the file data for the request
            # files = {'file': (uploaded_file.name, uploaded_file, "text/csv")}
            # files = {'file': (file.name, file.getvalue(), "text/csv")}
            # write_logs(text= f"values = {type(files)} ,  {files} ")

            payload = {
                "title": subject,  # Directly assign the string value
                "body": bodyPreview     # Directly assign the string value
            }

            # Make the POST request to the FastAPI endpoint
            response = requests.post(f"{FASTAPI_URL}/predict_psp_as_per_calendar_data/", json=payload)
            # Check the response status
            if response.status_code == 200:
                # st.success("File processed and stored successfully.")
                return response.json()
                # # Display the extracted JSON details
                # response_data = response.json()
                # st.json(response_data)  # Display JSON response for better readability
            else:
                st.error("Error processing the Calendar.")
                st.write(f"Status code: {response.status_code}, Message: {response.text}")
    except Exception as e:
        with tab1:
            st.error(f"Failed to process the Calendar.: {e}")

# Function to upload and process invoice
def process_document(file):
    """
    Function to upload an CSV to the FastAPI backend for processing.
    """
    try:
        if uploaded_file is not None:
        # Prepare the file data for the request
            # files = {'file': (uploaded_file.name, uploaded_file, "text/csv")}
            files = {'file': (file.name, file.getvalue(), "text/csv")}
            # write_logs(text= f"values = {type(files)} ,  {files} ")
            response = requests.post(f"{FASTAPI_URL}/insert_psp_data_to_db/", files=files)
            # Check the response status
            if response.status_code == 200:
                st.success("File processed and stored successfully.")
                
                # # Display the extracted JSON details
                # response_data = response.json()
                # st.json(response_data)  # Display JSON response for better readability
            else:
                st.error("Error processing the file.")
                st.write(f"Status code: {response.status_code}, Message: {response.text}")
    except Exception as e:
        with tab1:
            st.error(f"Failed to process the CSV File: {e}")


output_format = {}
st.title("AI Powered - Time Booking App")
# Main content
tab1, tab2, tab3 = st.tabs(["Insert PSP Data", "Get PSP Vectors", "Predict PSP"])

# Function to update current tab
def update_current_tab(tab_name):
    st.session_state.current_tab = tab_name

# Tab 1: Insert PSP data


with tab1:
    update_current_tab("Insert PSP Data")
    st.header("Insert PSP data into Database")

    st.write("Upload a CSV to extract and store its details in the database.")
    uploaded_file = st.file_uploader("Choose a csv file", type="csv")

    # Check if a file has been uploaded
    if uploaded_file is not None:
        # Read the CSV file into a DataFrame
        df = pd.read_csv(uploaded_file)
        
        # Display the DataFrame
        st.write("CSV Data:")
        st.dataframe(df)

    # psp_data = st.text_area("Enter PSP data:")
    # if st.button("Submit", key="insert_submit"):
    #     result = call_api("insert_psp", {"data": psp_data})
    #     st.json(result)

# Tab 2: Get PSP short Vectors
with tab2:
    update_current_tab("Get PSP Vectors")
    st.header("Get PSP short Vectors")
    psp_id = st.text_input("Enter PSP ID:")
    if st.button("Get Vectors", key="get_vectors"):
        result = call_api("get_psp_vectors", {"id": psp_id})
        st.json(result)

# Tab 3: Predict PSP
with tab3:
    update_current_tab("Predict PSP")

    # user_data = pd.read_csv("Data/AzureUsers.csv")
    user_data = pd.read_csv(Path("Data") / "AzureUsers.csv")

    st.subheader("Select a user")
    # Extract DisplayName list for the dropdown
    display_names =  ['Select a user'] + user_data['displayName'].tolist()
    # Streamlit dropdown for selecting a DisplayName
    selected_name = st.selectbox( '', display_names)
    if selected_name == 'Select a user':
        st.warning("Please select a user to proceed.")
    else:
        user_id = user_data[user_data['displayName'] == selected_name]['id'].values[0]
        # st.write(f"{user_id}")
        # return user_id

        # Call function to update calendarJson when user selection changes
        update_calendar(user_id)

        # write_logs(text= f"CalenderJson {user_id} {st.session_state.calendarJson}")
        # st.header("Predict PSP from Meeting Data")
            
        displayTable = convert_json_to_table()

        st.subheader("Calendar Data")
        st.write(displayTable)

        # Add new columns for PSP element, Network Number, and PSP Short Description
        displayTable['PSP Element'] = ""
        displayTable['Network Number'] = ""
        displayTable['PSP Short Description'] = ""

        # Check if displayTable is not None and button is clicked
        if displayTable is not None and st.button("Get PSP Element and Network from Vector Data"):
         with st.spinner("Processing..."):
            try:
                # Iterate over rows using itertuples and update new columns with predictions
                for idx, row in enumerate(displayTable.itertuples(index=False)):
                    subject = row.subject
                    bodyPreview = row.bodyPreview

                    # Log the extracted values
                    # write_logs(text=f"values --------------------------> = {subject} and {bodyPreview}")

                    # Get predictions (assumed function call to get the response)
                    predictions = get_psp_network(subject, bodyPreview)

                    # Extract predictions from response
                    psp_element = predictions.get("PSP Element", "")
                    network_number = predictions.get("Network Number", "")
                    psp_short_description = predictions.get("PSP Short Description", "")

                    # Add the predictions back to the DataFrame
                    displayTable.at[idx, 'PSP Element'] = psp_element
                    displayTable.at[idx, 'Network Number'] = network_number
                    displayTable.at[idx, 'PSP Short Description'] = psp_short_description

                # Display the updated table with new columns
                st.subheader("Updated Calendar Data with PSP and Network Information")
                st.write(displayTable)

            except Exception as e:
                st.error(f"An error occurred: {e}")
        # if displayTable is not None and st.button("Book time in SAP"):
        #     try:
                
        #         st.success("Configuration saved successfully!")
        #     except json.JSONDecodeError:
        #         st.error("Invalid JSON. Please check your configuration.")

    # # with right_col:
    # st.subheader("Predict PSP")
    # title = st.text_input("Title")
    # body = st.text_area("Body")
    
    # if st.button("Predict PSP", key="predict_psp"):
    #     result = call_api("predict_psp", {"title": title, "body": body})
    #     st.json(result)


with tab1:
    # Only process invoice if the button is clicked
    # Display PDF only if uploaded
    # if uploaded_file is not None:
        #  display_pdf(uploaded_file)
    # Create a global dictionary to store the JSON format

    if st.button("Process Document") and uploaded_file is not None:
        with st.spinner("Processing..."):
            process_document(uploaded_file)  # Call your processing function
            # st.json(result)  # Display the processed JSON data