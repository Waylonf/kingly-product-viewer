import io
import re
import streamlit as st
import pandas as pd

DATA_FILE = "MasterProducts_Expanded.xlsx"  # ensure this is in repo root


@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    try:
        return pd.read_excel(path)
    except Exception:
        # fallback sample so the app always runs
        data = {
            "REF": ["KS04", "KS04G", "KS04U"],
            "Category": ["Socks", "Socks", "Socks"],
            "Product Name": ["Standard Sock", "GOTS Organic Sock", "Upcycled Sock"],
            "Description_EN": ["custom knit", "organic cotton", "upcycled cotton"],
            "50_EU": [3.2, 3.6, 3.1],
            "100_EU": [2.9, 3.3, 2.85],
            "250_EU": [2.7, 3.1, 2.65],
            "50_UK": [2.9, 3.3, 2.8],
            "100_UK": [2.65, 3.05, 2.55],
            "250_UK": [2.45, 2.85, 2.35],
            "50_US": [3.5, 3.9, 3.4],
            "100_US": [3.2, 3.6, 3.1],
            "250_US": [3.0, 3.4, 2.9],
        }
        return pd.DataFrame(data)


df = load_data(DATA_FILE)

# -------------------------------
# Detect dynamic regions + qty/tier prefixes
# -------------------------------
price_cols = [c for c in df.columns if "_" in c]
region_map = {}  # {region: [prefix list]}

for col in price_cols:
    try:
        prefix, region = col.split("_", 1)
    except ValueError:
        continue
    region_map.setdefault(region, []).append(prefix)

regions = sorted(region_map.keys())

# -------------------------------
# Sidebar filters
# -------------------------------
st.sidebar.header("Filters")

selected_region = st.sidebar.selectbox(
    "Select Region",
    regions,
    index=0 if regions else None,
)

categories = sorted(df["Category"].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect(
    "Select Categories", categories, default=categories
)

# Search box
search_query = st.text_input("🔍 Search by REF, product name, or description")

# -------------------------------
# Filtering
# -------------------------------
filtered = df[df["Category"].isin(selected_categories)].copy()

if search_query:
    q = search_query.strip().lower()
    tokens = [t for t in re.split(r"\s+", q) if t]
    if tokens:
        hay = (
            filtered["REF"].astype(str).str.lower().fillna("")
            + " " + filtered["Product Name"].astype(str).str.lower().fillna("")
            + " " + filtered["Description_EN"].astype(str).str.lower().fillna("")
        )
        for t in tokens:
            filtered = filtered[hay.str.contains(re.escape(t), na=False)]

# -------------------------------
# Build the view
# -------------------------------
base_cols = [c for c in ["REF", "Category", "Product Name", "Description_EN"] if c in filtered.columns]
region_cols = []

if selected_region:
    region_cols = [
        f"{prefix}_{selected_region}"
        for prefix in region_map.get(selected_region, [])
        if f"{prefix}_{selected_region}" in filtered.columns
    ]

    # sort by numeric qty if possible
    def sort_key(col):
        prefix = col.split("_", 1)[0]
        return (0, int(prefix)) if prefix.isdigit() else (1, prefix)

    region_cols.sort(key=sort_key)

# Final export table
export_cols = base_cols + region_cols
export_df = filtered[export_cols].copy()

# Rename region cols safely → "50 (EU)", "Tier1 (US)"
rename_map = {c: f"{c.split('_', 1)[0]} ({selected_region})" for c in region_cols}
export_df = export_df.rename(columns=rename_map)

# -------------------------------
# Display + downloads
# -------------------------------
st.write(f"### Product View – Region: {selected_region}")
st.dataframe(export_df, use_container_width=True)

# CSV export
csv_bytes = export_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "📥 Download CSV",
    data=csv_bytes,
    file_name=f"Products_{selected_region}.csv",
    mime="text/csv",
)

# Excel export
excel_buf = io.BytesIO()
with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
    export_df.to_excel(writer, index=False, sheet_name="Products")
excel_buf.seek(0)

st.download_button(
    "📥 Download Excel (.xlsx)",
    data=excel_buf,
    file_name=f"Products_{selected_region}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
