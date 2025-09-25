import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials

@st.cache_data
def load_data():
    # Load and parse JSON string from secrets
    creds_json = st.secrets["gcp_service_account"]
    if isinstance(creds_json, str):
        creds_dict = json.loads(creds_json)
    else:
        creds_dict = creds_json  # already dict

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    client = gspread.authorize(creds)

    SHEET_ID = "YOUR_SHEET_ID"   # replace with actual sheet ID
    TAB_NAME = "All Products"    # replace with your tab name

    sheet = client.open_by_key(SHEET_ID).worksheet(TAB_NAME)
    data = sheet.get_all_records()

    return pd.DataFrame(data)
