import streamlit as st
import requests
import base64
from io import BytesIO
from streamlit_ace import st_ace
import json

# from backend.main import default_json

# Set FastAPI backend URL
# FASTAPI_URL = "http://localhost:8000"  # Update with your FastAPI server URL


FASTAPI_URL = "https://sap-genai-integration-invoice.onrender.com"

# Streamlit App Configuration
st.set_page_config(page_title="Invoice Processing and Comparison", layout="wide")

# Streamlit App Title
st.title("Invoice Processing and Comparison")

# Create a global dictionary to store the JSON format
# output_format = {}

# Sidebar with App Description and Navigation at the Top
st.sidebar.title("Navigation")
options = st.sidebar.radio("Choose Functionality", ["Process Invoice", "Compare Invoice"])

# Add a separator for a clean layout
st.sidebar.markdown("---")


# Default JSON schema
default_schema = {
    "VendorName": "",
    "InvoiceNumber": "",
    "vendor_address": "",
    "tax_id": "",
    "Invoice Date": "",
    "bill_to_name": "",
    "bill_to_address": "",
    "invoice_amount": "",
    "invoice_currency": "",
    "invoice_items": [
        {
            "description": "",
            "unit_price": "",
            "quantity": "",
            "net_price": ""
        }
    ]
}

# Create an editable JSON interface
# json_input = st_ace(
#     value=json.dumps(default_schema, indent=2),
#     language="json",
#     theme="monokai",
#     keybinding="vscode",
#     min_lines=20,
#     max_lines=None,
#     font_size=14,
#     tab_size=2,
#     wrap=True,
#     show_gutter=True,
#     show_print_margin=True,
#     auto_update=True,
# )

# Create an editable JSON interface in the sidebar using st_ace
# Create an editable JSON interface in the sidebar using st_ace
with st.sidebar:
 try:
    json_input = st_ace(
        value=json.dumps(default_schema, indent=2),
        language="json",
        theme="monokai",
        keybinding="vscode",
        min_lines=20,
        max_lines=None,
        font_size=14,
        tab_size=2,
        wrap=True,
        show_gutter=True,
        show_print_margin=True,
        auto_update=True,
        height=400,  # Set height for better display
    )
    
    if st.sidebar.button("Save JSON"):
        try:
            output_format = json.loads(json_input)  # Validate the JSON
            st.success("JSON format saved successfully!")
        except json.JSONDecodeError:
            st.error("Invalid JSON input!")
    else:
        output_format = json.loads(json_input)
    

 except json.JSONDecodeError:
            st.error("Invalid JSON input!")
    


# Store the parsed JSON input into the global variable
# if st.button("Save JSON"):
#     try:
#         output_format['data'] = json.loads(json_input)  # Update global dict
#         st.success("JSON format saved in global variable!")
#     except json.JSONDecodeError:
#         st.error("Invalid JSON input!")

# Save the JSON input to a file when a button is clicked





# # Initialize session state for saved_json
# if 'saved_json' not in st.session_state:
#     st.session_state['saved_json'] = {
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
#             {
#                 "description": "",
#                 "item_no": "",
#                 "unit_price": "",
#                 "quantity": "",
#                 "net_price": ""
#             }
#         ]
#     }

# # JSON Editor in sidebar
# st.subheader("JSON Template Editor")
# json_editor = st_ace(
# value=json.dumps(st.session_state['saved_json'], indent=2),
# language="json",
# theme="monokai",
# keybinding="vscode",
# min_lines=20,
# max_lines=30,
# font_size=12,
# key="json_editor"
# )
    
# if st.button("Save JSON Template"):
#     try:
#         new_template = json.loads(json_editor)
#         st.session_state['saved_json'] = new_template
#         st.success("JSON template saved successfully!")
#     except json.JSONDecodeError:
#         st.error("Invalid JSON format. Please check your input.")


# Add a separator for a clean layout
st.sidebar.markdown("---")

# Sidebar with Application Description
st.sidebar.title("About the Application")
st.sidebar.write(
    """
    This application allows you to upload PDF invoices to extract and compare their details.
    For details about test data and other details, use README.md file from the git repo.
    For more details Visit. https://iphegde.com
    
    **How to Use:**
    - **Process Invoice**: Upload a PDF file to extract invoice details and store them in the database.
    You can modify the json structure above and enter any desired field you want to see and save it. Click on "Process Document" again
    to see your field as output.
    - **Compare Invoice**: Upload a PDF file to compare it with existing invoices in the database to identify potential duplicates.
    
    **FastAPI Routes:**
    - `/process_invoice/` : Processes the uploaded invoice and extracts its details.
    - `/compare_invoice/` : Compares the uploaded invoice with existing invoices in the database.

    The backend is powered by **FastAPI**, ensuring fast and efficient processing.
    If you notice delay in output, its due to the public webservice provider. Thats not the real App performance."""
)
# Add a separator for a clean layout
st.sidebar.markdown("---")

# Function to upload and process invoice
def process_invoice(file , output_format):
    """
    Function to upload an invoice to the FastAPI backend for processing.
    """
    try:

        data = {
            "output_format": json.dumps(output_format),  # Convert output_format to a string if it's a dictionary
        }

        files = {'file': (file.name, file.getvalue(), "application/pdf")}

        # st.success(f"Im here {data}")
        response = requests.post(f"{FASTAPI_URL}/process_invoice/", files=files , data=data)
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

if options == "Process Invoice":
    st.header("Process Invoice")
    st.write("Upload a PDF invoice to extract and store its details in the database.")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")


    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Uploaded PDF Preview")
        st.markdown("Upload a PDF file to preview it here.")

    # Column 2 will always show these elements
    with col2:
        st.subheader("JSON Output")
        st.markdown("Extracted or comparison results will be displayed here.")


    with col1:
        # Only process invoice if the button is clicked
        # Display PDF only if uploaded
        if uploaded_file is not None:
            display_pdf(uploaded_file)

        if st.button("Process Document") and uploaded_file is not None:
            with col2:
                with st.spinner("Processing..."):
                    result = process_invoice(uploaded_file, output_format)  # Call your processing function

                # Store the result in session state to maintain its value across reruns
                    # st.session_state.result = result
                    st.json(result)  # Display the processed JSON data


# Automatically process and compare invoice upon upload 
elif options == "Compare Invoice":
    st.header("Compare Invoice")
    st.write("Coming Soon!! Under Development...")

        # st.write("Upload a PDF invoice to compare it with the existing invoices in the database.")
        # uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

        # if uploaded_file is not None:
        #     display_pdf(uploaded_file)
        #     with col2:
        #         with st.spinner("Comparing..."):
        #             compare_invoice(uploaded_file)


# Column 2 will always show these elements
# with col2:

#     # Check if the result exists in session state and display it
#     if 'result' in st.session_state:
#         st.json(st.session_state.result)  # Display the processed JSON data
#     else:
#         st.markdown("No results yet. Please process the invoice.")



# with col1:
#     st.subheader("Uploaded PDF Preview")
#     st.markdown("Upload a PDF file to preview it here.")

#     if st.button("Process Invoice") and uploaded_file is not None :
#             with col2:
#                 st.subheader("JSON Output")
#                 st.markdown("Extracted or comparison results will be displayed here.")
#                 with st.spinner("Processing..."):
#                     process_invoice(uploaded_file , output_format)


# with col2:
#     st.subheader("JSON Output")
#     st.markdown("Extracted or comparison results will be displayed here.")

# # Automatically process and display invoice upon upload
#     if uploaded_file is not None:
#         display_pdf(uploaded_file)


# with col1:

#     if st.button("Process Invoice") and uploaded_file is not None :
#             with col2:
#                 with st.spinner("Processing..."):
#                     process_invoice(uploaded_file , output_format)




    # if uploaded_file is not None:
    #     display_pdf(uploaded_file)
    #     with col2:
    #         with st.spinner("Processing..."):
    #             process_invoice(uploaded_file , output_format)






