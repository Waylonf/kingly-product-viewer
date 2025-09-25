import io
import re
import json
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ---------------------------------------------------
# Load Data from Google Sheets
# ---------------------------------------------------
@st.cache_data
def load_data():
    # Load and parse credentials from Streamlit secrets
    creds_json = st.secrets["gcp_service_account"]
    if isinstance(creds_json, str):
        creds_dict = json.loads(creds_json)
    else:
        creds_dict = creds_json

    # Debug: show which account is being used
    st.write("🔑 Loaded credentials for:", creds_dict.get("client_email", "??"))

    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    client = gspread.authorize(creds)

    # TODO: replace with your real values
    SHEET_ID = "1054802323"  # from the Google Sheets URL
    TAB_NAME = "All Products"        # must exactly match the tab name

    st.write("📄 Trying to load sheet:", SHEET_ID, "Tab:", TAB_NAME)

    sheet = client.open_by_key(SHEET_ID).worksheet(TAB_NAME)
    data = sheet.get_all_records()

    st.write("✅ Loaded rows:", len(data))

    return pd.DataFrame(data)


# ---------------------------------------------------
# App UI
# ---------------------------------------------------
st.set_page_config(page_title="Kingly Product Viewer", layout="wide")

df = load_data()

# -------------------------------
# Sidebar controls
# -------------------------------
st.sidebar.header("Controls")

# Column toggles
all_columns = df.columns.tolist()
default_cols = [c for c in ["REF", "Primary Category", "Sub-Category", "Title"] if c in all_columns]

visible_cols = st.sidebar.multiselect(
    "Choose columns to display",
    all_columns,
    default=default_cols or all_columns[:8],
)

# Search box
search_query = st.text_input("🔍 Search by REF, title, description, or tags")

# -------------------------------
# Filtering
# -------------------------------
filtered = df.copy()

if search_query:
    q = search_query.strip().lower()
    tokens = [t for t in re.split(r"\s+", q) if t]
    if tokens:
        # candidate columns to search
        search_cols = [
            c
            for c in ["REF", "Title", "Raw Short Description", "Raw Long Description", "Tags"]
            if c in df.columns
        ]
        if search_cols:
            hay = (
                df[search_cols].astype(str).apply(lambda x: " ".join(x), axis=1).str.lower()
            )
            for t in tokens:
                filtered = filtered[hay.str.contains(re.escape(t), na=False)]

# Apply column visibility
if visible_cols:
    view_df = filtered[visible_cols].copy()
else:
    view_df = filtered.copy()

# -------------------------------
# Display
# -------------------------------
st.write("### Product View")
st.dataframe(view_df, use_container_width=True)

# -------------------------------
# Download buttons
# -------------------------------
csv_bytes = view_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "📥 Download CSV",
    data=csv_bytes,
    file_name="Products_View.csv",
    mime="text/csv",
)

excel_buf = io.BytesIO()
with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
    view_df.to_excel(writer, index=False, sheet_name="Products")
excel_buf.seek(0)

st.download_button(
    "📥 Download Excel (.xlsx)",
    data=excel_buf,
    file_name="Products_View.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
