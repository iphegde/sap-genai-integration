import streamlit as st
import requests
import base64
from io import BytesIO

# Set FastAPI backend URL
FASTAPI_URL = "http://localhost:8000"  # Update with your FastAPI server URL

# Streamlit App Configuration
st.set_page_config(page_title="Invoice Processing and Comparison", layout="wide")

# Streamlit App Title
st.title("Invoice Processing and Comparison")

# Sidebar with App Description and Navigation at the Top
st.sidebar.title("Navigation")
options = st.sidebar.radio("Choose Functionality", ["Process Invoice", "Compare Invoice"])

# Add a separator for a clean layout
st.sidebar.markdown("---")

# Sidebar with Application Description
st.sidebar.title("About the Application")
st.sidebar.write(
    """
    This application allows you to upload PDF invoices to extract and compare their details.

    **How to Use:**
    - **Process Invoice**: Upload a PDF file to extract invoice details and store them in the database.
    - **Compare Invoice**: Upload a PDF file to compare it with existing invoices in the database to identify potential duplicates.
    
    **FastAPI Routes:**
    - `/process_invoice/` : Processes the uploaded invoice and extracts its details.
    - `/compare_invoice/` : Compares the uploaded invoice with existing invoices in the database.

    The backend is powered by **FastAPI**, ensuring fast and efficient processing.
    """
)

# Function to upload and process invoice
def process_invoice(file):
    """
    Function to upload an invoice to the FastAPI backend for processing.
    """
    try:
        files = {'file': (file.name, file.getvalue(), "application/pdf")}
        response = requests.post(f"{FASTAPI_URL}/process_invoice/", files=files)
        if response.status_code == 200:
            st.success("Invoice processed and stored successfully.")
            # Display the extracted JSON details
            response_data = response.json()
            with col2:
                st.subheader("Extracted Invoice Details:")
                st.json(response_data.get("extracted_data", {}))  # Access the 'extracted_data' field from response
        else:
            with col2:
                st.error(f"Error: {response.json()['detail']}")
    except Exception as e:
        with col2:
            st.error(f"Failed to process the invoice: {e}")



# Function to display the uploaded PDF file
def display_pdf(file):
    """
    Function to display the uploaded PDF file in the UI using an iframe.
    """
    try:
        # Convert the uploaded file to a base64-encoded string
        base64_pdf = base64.b64encode(file.getvalue()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600px"></iframe>'
        with col1:
            st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception as e:
        with col2:
            st.error(f"Failed to display the PDF: {e}")

# Define columns for side-by-side layout with default placeholders
col1, col2 = st.columns(2)

with col1:
    st.subheader("Uploaded PDF Preview")
    st.markdown("Upload a PDF file to preview it here.")

with col2:
    st.subheader("JSON Output")
    st.markdown("Extracted or comparison results will be displayed here.")

# Automatically process and display invoice upon upload
if options == "Process Invoice":
    st.header("Process Invoice")
    st.write("Upload a PDF invoice to extract and store its details in the database.")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        display_pdf(uploaded_file)
        with col2:
            with st.spinner("Processing..."):
                process_invoice(uploaded_file)

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
