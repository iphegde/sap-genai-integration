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
from streamlit_ace import st_ace
import requests



# Set FastAPI backend URL
FASTAPI_URL = "http://localhost:8000"  # Update with your FastAPI server URL


# Initialize session state
if 'config' not in st.session_state:
    st.session_state.config = {
        "api_key": "",
        "model_parameters": {}
    }
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "Insert PSP Data"

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


# Function to upload and process invoice
def process_document(file , output_format):
    """
    Function to upload an invoice to the FastAPI backend for processing.
    """
    try:

        data = {
            "output_format": json.dumps(output_format),  # Convert output_format to a string if it's a dictionary
        }

        files = {'file': (file.name, file.getvalue(), "application/pdf")}
        response = requests.post(f"{FASTAPI_URL}/process_invoice/", files=files , data=data)
        if response.status_code == 200:
            st.success("Invoice processed and stored successfully.")
            # Display the extracted JSON details
            response_data = response.json()
            with tab1:
                st.subheader("Extracted Invoice Details:")
                st.json(response_data.get("extracted_data", {}))  # Access the 'extracted_data' field from response
        else:
            with tab2:
                st.error(f"Error: {response.json()['detail']}")
    except Exception as e:
        with tab1:
            st.error(f"Failed to process the invoice: {e}")


output_format = {}

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
    st.header("Predict PSP from Meeting Data")
    
    # Left column for JSON configuration
    left_col, right_col = st.columns([1, 2])
    
    with left_col:
        st.subheader("JSON Configuration")
        config_json = st_ace(
            value=json.dumps(st.session_state.config, indent=2),
            language="json",
            theme="monokai",
            keybinding="vscode",
            min_lines=20,
            max_lines=None,
            font_size=14,
            key="json_editor"
        )

        if st.button("Save Configuration"):
            try:
                st.session_state.config = json.loads(config_json)
                st.success("Configuration saved successfully!")
            except json.JSONDecodeError:
                st.error("Invalid JSON. Please check your configuration.")

    with right_col:
        st.subheader("Predict PSP")
        title = st.text_input("Title")
        body = st.text_area("Body")
        
        if st.button("Predict PSP", key="predict_psp"):
            result = call_api("predict_psp", {"title": title, "body": body})
            st.json(result)


with tab1:
    # Only process invoice if the button is clicked
    # Display PDF only if uploaded
    # if uploaded_file is not None:
        #  display_pdf(uploaded_file)
    # Create a global dictionary to store the JSON format

    if st.button("Process Document") and uploaded_file is not None:
         with tab1:
            with st.spinner("Processing..."):
                result = process_document(uploaded_file, output_format)  # Call your processing function
                st.json(result)  # Display the processed JSON data