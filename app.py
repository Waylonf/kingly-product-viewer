import io
import re
import streamlit as st
import pandas as pd

DATA_FILE = "MasterProducts_Expanded.xlsx"  # put your file in repo root

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    try:
        return pd.read_excel(path)
    except Exception as e:
        # Fallback sample so the app always runs
        data = {
            "REF": ["KS04","KS04G","KS04U"],
            "Category": ["Socks","Socks","Socks"],
            "Product Name": ["Standard Sock","GOTS Organic Sock","Upcycled Sock"],
            "Description_EN": ["custom knit","organic cotton","upcycled cotton"],
            "Tier1_EU":[3.2,3.6,3.1], "Tier2_EU":[2.9,3.3,2.85], "Tier3_EU":[2.7,3.1,2.65],
            "Tier1_UK":[2.9,3.3,2.8], "Tier2_UK":[2.65,3.05,2.55], "Tier3_UK":[2.45,2.85,2.35],
            "50_US":[3.5,3.9,3.4], "100_US":[3.2,3.6,3.1], "250_US":[3.0,3.4,2.9],
        }
        return pd.DataFrame(data)

df = load_data(DATA_FILE)

# -------------------------------
# Detect pricing schema dynamically
# Supports "50_EU" and "Tier1_EU" styles
# -------------------------------
price_cols = [c for c in df.columns if "_" in c]  # e.g., "50_EU", "Tier1_EU"
region_map = {}   # {region: [prefix list]}
is_qty_numeric = {}  # {(prefix, region): bool}

for col in price_cols:
    try:
        prefix, region = col.split("_", 1)
    except ValueError:
        continue
    region_map.setdefault(region, []).append(prefix)
    # is the prefix a number like "50" or a label like "Tier1"
    is_qty_numeric[(prefix, region)] = bool(re.fullmatch(r"\d+", str(prefix)))

# dynamic regions
regions = sorted(region_map.keys())

# -------------------------------
# Sidebar controls
# -------------------------------
st.sidebar.header("Filters")

# Region default: first found, or empty if none
selected_region = st.sidebar.selectbox(
    "Select Region",
    regions,
    index=0 if regions else None
)

# Categories
categories = sorted(df["Category"].dropna().unique().tolist())
selected_categories = st.sidebar.multiselect(
    "Select Categories",
    categories,
    default=categories  # show ALL products on initial load
)

# Search box
search_query = st.text_input("🔍 Search by REF, product name, or description")

# -------------------------------
# Filtering pipeline
# -------------------------------
# 1) Start from full df, then filter by category
filtered = df[df["Category"].isin(selected_categories)].copy()

# 2) Apply search on the filtered set
if search_query:
    q = search_query.strip().lower()
    # match ALL tokens in any of the target columns
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
# Build the output view
# -------------------------------
base_cols = ["REF", "Category", "Product Name", "Description_EN"]
base_cols = [c for c in base_cols if c in filtered.columns]

# Region pricing columns for selected_region
region_cols = []
display_names = []

if selected_region:
    # find all columns that end with _selected_region
    for prefix in region_map.get(selected_region, []):
        col_name = f"{prefix}_{selected_region}"
        if col_name in filtered.columns:
            region_cols.append(col_name)
            # show just the prefix as the header, for numeric keep number, else keep label
            display_names.append(prefix)

    # sort by numeric qty if possible, else keep original order
    def sort_key(col):
        prefix = col.split("_", 1)[0]
        return (0, int(prefix)) if prefix.isdigit() else (1, prefix)

    region_cols.sort(key=sort_key)
    display_names = [c.split("_", 1)[0] for c in region_cols]

# Compose export table
export_cols = base_cols + region_cols
export_df = filtered[export_cols].copy()

# Rename region columns to show only the quantity or tier label
rename_map = {c: c.split("_", 1)[0] for c in region_cols}
export_df = export_df.rename(columns=rename_map)

st.write(f"### Product View{(' – Region: ' + selected_region) if selected_region else ''}")
st.dataframe(export_df, use_container_width=True)

# -------------------------------
# Download buttons
# -------------------------------
csv_bytes = export_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "📥 Download CSV",
    data=csv_bytes,
    file_name=f"Products_{selected_region or 'ALL'}.csv",
    mime="text/csv",
)

# also offer real Excel
excel_buf = io.BytesIO()
with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
    export_df.to_excel(writer, index=False, sheet_name="Products")
excel_buf.seek(0)

st.download_button(
    "📥 Download Excel (.xlsx)",
    data=excel_buf,
    file_name=f"Products_{selected_region or 'ALL'}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
