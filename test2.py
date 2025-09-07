import streamlit as st
import pandas as pd
import zipfile
import chardet
import io
import os

st.title("📂 Call ID Search App (Persistent Uploads on Refresh)")

# Create a temp folder for caching uploaded files
CACHE_DIR = ".streamlit_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Initialize session state for dataframes
if "df_csv" not in st.session_state:
    st.session_state.df_csv = None
if "df_excel" not in st.session_state:
    st.session_state.df_excel = None
if "csv_path" not in st.session_state:
    st.session_state.csv_path = None
if "excel_path" not in st.session_state:
    st.session_state.excel_path = None

# --- Upload ZIP or any file ---
# Check if we already have a file path cached BEFORE showing the uploader
if st.session_state.csv_path and os.path.exists(st.session_state.csv_path):
    st.write(f"📁 **Loaded File:** `{os.path.basename(st.session_state.csv_path)}`")
    if st.button("🗑️ Remove CSV File"):
        # Clear the cache and session state for the CSV
        os.remove(st.session_state.csv_path)
        st.session_state.csv_path = None
        st.session_state.df_csv = None
        st.rerun()
else:
    # Only show the uploader if no file is cached
    uploaded_zip = st.file_uploader("Upload a file containing a CSV", type=None)
    if uploaded_zip is not None:
        zip_path = os.path.join(CACHE_DIR, uploaded_zip.name)
        # Save the uploaded file to disk
        with open(zip_path, "wb") as f:
            f.write(uploaded_zip.getbuffer())
        st.session_state.csv_path = zip_path
        st.rerun() # Trigger a rerun to immediately load the file

# If a file path exists in session_state, load it
if st.session_state.csv_path:
    try:
        with zipfile.ZipFile(st.session_state.csv_path, "r") as zip_ref:
            csv_files = [f for f in zip_ref.namelist() if f.endswith(".csv")]
            if csv_files:
                csv_name = csv_files[0]
                with zip_ref.open(csv_name) as csvfile:
                    raw_data = csvfile.read()
                    result = chardet.detect(raw_data)
                    encoding = result["encoding"]
                    st.session_state.df_csv = pd.read_csv(io.StringIO(raw_data.decode(encoding)))
                    st.session_state.df_csv.columns = [c.strip().lower() for c in st.session_state.df_csv.columns]
                    st.success(f"✅ Loaded {csv_name} (encoding: {encoding})")
            else:
                st.error("❌ No CSV file found inside the ZIP.")
    except zipfile.BadZipFile:
        st.error("❌ Not a ZIP file. Please upload a proper ZIP containing CSV.")
    except Exception as e:
        st.error(f"Error reading file: {e}")

# Show CSV preview if loaded (Top 10 by Ageing, specific columns)
if st.session_state.df_csv is not None:
    preview_cols = ["call id", "centre", "center", "warranty", "model", "call stage", "ageing", "pending parts", "pending parts desc", "pending parts date"]
    available_cols = [c for c in preview_cols if c in st.session_state.df_csv.columns]
    df_preview = st.session_state.df_csv[available_cols].copy()
    
    # Ensure "centre" and "center" are unified as "centre"
    if "center" in df_preview.columns:
        df_preview.rename(columns={"center": "centre"}, inplace=True)
    
    if "ageing" in df_preview.columns:
        df_preview = df_preview.sort_values(by="ageing", ascending=False).head(10)
    else:
        df_preview = df_preview.head(10)
    
    st.dataframe(df_preview)

# --- Upload Excel file ---
# Check if we already have a file path cached BEFORE showing the uploader
if st.session_state.excel_path and os.path.exists(st.session_state.excel_path):
    st.write(f"📁 **Loaded File:** `{os.path.basename(st.session_state.excel_path)}`")
    if st.button("🗑️ Remove Excel File"):
        # Clear the cache and session state for the Excel
        os.remove(st.session_state.excel_path)
        st.session_state.excel_path = None
        st.session_state.df_excel = None
        st.rerun()
else:
    # Only show the uploader if no file is cached
    uploaded_excel = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])
    if uploaded_excel is not None:
        excel_path = os.path.join(CACHE_DIR, uploaded_excel.name)
        with open(excel_path, "wb") as f:
            f.write(uploaded_excel.getbuffer())
        st.session_state.excel_path = excel_path
        st.rerun() # Trigger a rerun to immediately load the file

# If Excel path exists in session_state, load it
if st.session_state.excel_path:
    try:
        st.session_state.df_excel = pd.read_excel(st.session_state.excel_path)
        st.session_state.df_excel.columns = [c.strip().lower() for c in st.session_state.df_excel.columns]
        st.success(f"✅ Loaded Excel with {len(st.session_state.df_excel)} rows")
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")

# Show Excel preview if loaded (Top 10 by Ageing, specific columns)
if st.session_state.df_excel is not None:
    preview_cols = ["call id", "centre", "center", "warranty", "model", "call stage", "ageing", "pending parts", "pending parts desc", "pending parts date"]
    available_cols = [c for c in preview_cols if c in st.session_state.df_excel.columns]
    df_preview = st.session_state.df_excel[available_cols].copy()
    
    # Ensure "centre" and "center" are unified as "centre"
    if "center" in df_preview.columns:
        df_preview.rename(columns={"center": "centre"}, inplace=True)
    
    if "ageing" in df_preview.columns:
        df_preview = df_preview.sort_values(by="ageing", ascending=False).head(10)
    else:
        df_preview = df_preview.head(10)
    
    st.dataframe(df_preview)

# --- Search section ---
call_id = st.text_input("🔍 Enter Call ID to search (e.g., KOL128082500012)")

if call_id:
    # Search in CSV (if available)
    if st.session_state.df_csv is not None:
        match_csv = st.session_state.df_csv[
            st.session_state.df_csv["call id"].astype(str).str.strip() == call_id.strip()
        ]
        if not match_csv.empty:
            st.write("### 🎯 Result from CSV (ZIP)")
            st.write("**Centre:**", match_csv.iloc[0].get("centre", match_csv.iloc[0].get("center", "Not Found")))
            st.write("**Call Stage:**", match_csv.iloc[0].get("call stage", "Not Found"))
            st.write("**Registration Remarks:**", match_csv.iloc[0].get("registration remarks", "Not Found"))
        else:
            st.info("ℹ️ Call ID not found in CSV data.")

    # Search in Excel (if available)
    if st.session_state.df_excel is not None:
        match_excel = st.session_state.df_excel[
            st.session_state.df_excel["call id"].astype(str).str.strip() == call_id.strip()
        ]
        if not match_excel.empty:
            st.write("### 🎯 Result from Excel file")

            # Multi-select for columns (max 5)
            available_cols = [c for c in st.session_state.df_excel.columns if c != "call id"]
            selected_cols = st.multiselect(
                "📊 Select up to 5 columns to view (from Excel)",
                options=available_cols,
                max_selections=5
            )

            if selected_cols:
                st.write(f"#### Results for Call ID: {call_id}")
                for col in selected_cols:
                    label = "Centre" if col in ["centre", "center"] else col.title()
                    st.write(f"**{label}:**", match_excel.iloc[0].get(col, "Not Found"))
        else:
            st.info("ℹ️ Call ID not found in Excel data.")
