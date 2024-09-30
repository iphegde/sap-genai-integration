-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,  -- Auto-incrementing ID for each invoice
    vendor_name VARCHAR(255),  -- Vendor name, with a maximum length of 255 characters
    invoice_number VARCHAR(255),  -- Invoice number, with a maximum length of 255 characters
    vector VECTOR(1536),  -- Vector data type to store 1536-dimensional embeddings
    extracted_data JSONB  -- JSONB data type to store the extracted invoice details
);



select * from invoices;