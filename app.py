import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

@st.cache_data
def load_data():
    # Load credentials from Streamlit secrets
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    client = gspread.authorize(creds)

    # Replace with your sheet details
    SHEET_ID = "YOUR_SHEET_ID"   # from the Google Sheets URL
    TAB_NAME = "All Products"    # or whatever your sheet tab is called

    sheet = client.open_by_key(SHEET_ID).worksheet(TAB_NAME)
    data = sheet.get_all_records()

    return pd.DataFrame(data)

df = load_data()
