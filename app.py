import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    return pd.read_excel("MasterProducts_Expanded.xlsx")

df = load_data()

# --- Detect dynamic region + tier columns ---
price_cols = [c for c in df.columns if "_" in c]
region_map = {}  # {region: [qty list]}
for col in price_cols:
    qty, region = col.split("_", 1)
    region_map.setdefault(region, []).append(qty)

# Sidebar filters
regions = sorted(region_map.keys())
categories = df["Category"].unique().tolist()

st.sidebar.header("Filters")
selected_region = st.sidebar.selectbox("Select Region", regions)
selected_categories = st.sidebar.multiselect("Select Categories", categories, default=categories)

# Search box
search_query = st.text_input("🔍 Search by REF, product name, or description:")

# Filter by categories
filtered = df[df["Category"].isin(selected_categories)].copy()

# Apply search if provided
if search_query:
    search_query = search_query.lower()
    mask = (
        df["REF"].astype(str).str.lower().str.contains(search_query)
        | df["Product Name"].str.lower().str.contains(search_query)
        | df["Description_EN"].str.lower().str.contains(search_query)
    )
    filtered = df[mask]

# Pick correct pricing columns dynamically for selected region
region_cols = [f"{qty}_{selected_region}" for qty in region_map[selected_region]]
cols = ["REF", "Category", "Product Name", "Description_EN"] + region_cols

export = filtered[cols].copy()

# Rename columns to show qty only (e.g. 50, 100,
