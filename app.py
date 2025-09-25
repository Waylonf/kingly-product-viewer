import streamlit as st
import pandas as pd

# 1. Load master dataset
@st.cache_data
def load_data():
    return pd.read_excel("MasterProducts.xlsx")

df = load_data()

# 2. Sidebar controls
regions = ["EU", "UK", "US", "DE", "FR", "IT", "ES"]
categories = df["Category"].unique().tolist()

st.sidebar.header("Filters")
selected_region = st.sidebar.selectbox("Select Region", regions)
selected_categories = st.sidebar.multiselect("Select Categories", categories, default=categories)

# 3. Filter products
filtered = df[df["Category"].isin(selected_categories)].copy()

# 4. Pick correct pricing columns
cols = ["REF", "Category", "Product Name", "Description_EN",
        f"Tier1_{selected_region}", f"Tier2_{selected_region}", f"Tier3_{selected_region}"]
export = filtered[cols]

# Rename pricing columns
export = export.rename(columns={
    f"Tier1_{selected_region}": "Tier 1",
    f"Tier2_{selected_region}": "Tier 2",
    f"Tier3_{selected_region}": "Tier 3"
})

# 5. Show table
st.write("### Product View", export)

# 6. Download as CSV
st.download_button(
    label="📥 Download Excel",
    data=export.to_csv(index=False).encode("utf-8"),
    file_name=f"Products_{selected_region}.csv",
    mime="text/csv",
)
