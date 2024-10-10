-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE psp_data (
    id SERIAL PRIMARY KEY,  -- Auto-incrementing ID for each invoice
    psp_element VARCHAR(255),  -- Vendor name, with a maximum length of 255 characters
    network_number VARCHAR(255),  -- Invoice number, with a maximum length of 255 characters
    description TEXT,
    detailed_description TEXT,
    final_gpt_text TEXT,
    embedding VECTOR(1536)  -- Vector data type to store 1536-dimensional embeddings
);