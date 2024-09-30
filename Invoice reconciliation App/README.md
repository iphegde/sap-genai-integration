
## Goal = Convert Semi structured Data(pdf) into Structured Data(JSON)

## Semi-structured Data example
## Traditional ML/Computer Vision - Pytesseract
Data from pdf/image were exteacted using annotations - it was more a rul e based.

## Problem
You cannot judge everytime what data Vendor sends / what format you need to extract it from
So, you need a common logic which dynamically collect data from these semi structured Data.
---New vendor - annotate using Document extraction service in BTP
    its a tedious job to do it everytime.

## Use case
1. Post Invoices using API call
2. Compare invoices for similarities.
3. FIN  -- Extract Bank deatils and verity legit bank accounts before making payment.


## Run the backend
uvicorn backend.main:app --reload


## Run Frontend
streamlit run .\frontend\app.py