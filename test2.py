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
if "selected_call_id" not in st.session_state:
    st.session_state.selected_call_id = None

# --- Upload ZIP or any file ---
# Check if we already have a file path cached BEFORE showing the uploader
if st.session_state.csv_path and os.path.exists(st.session_state.csv_path):
    st.write(f"📁 **Loaded File:** `{os.path.basename(st.session_state.csv_path)}`")
    if st.button("🗑️ Remove CSV File"):
        # Clear the cache and session state for the CSV
        os.remove(st.session_state.csv_path)
        st.session_state.csv_path = None
        st.session_state.df_csv = None
        st.session_state.selected_call_id = None
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
    
    # Display the preview with clickable Call IDs
    st.write("### 📋 CSV Preview (Click on a Call ID to view details)")
    
    # Create a formatted dataframe with clickable call IDs
    display_df = df_preview.copy()
    if "call id" in display_df.columns:
        # Make call IDs clickable
        display_df["call id"] = display_df["call id"].apply(lambda x: f"🔍 {x}")
    
    st.dataframe(display_df, use_container_width=True)
    
    # Create buttons for each call ID
    if "call id" in df_preview.columns:
        st.write("### 🔍 Select a Call ID to view details:")
        call_ids = df_preview["call id"].astype(str).tolist()
        cols = st.columns(3)  # Create 3 columns for buttons
        
        for i, call_id in enumerate(call_ids):
            with cols[i % 3]:  # Distribute buttons across columns
                if st.button(f"{call_id}", key=f"btn_{call_id}"):
                    st.session_state.selected_call_id = call_id
                    st.rerun()

# --- Upload Excel file ---
# Check if we already have a file path cached BEFORE showing the uploader
if st.session_state.excel_path and os.path.exists(st.session_state.excel_path):
    st.write(f"📁 **Loaded File:** `{os.path.basename(st.session_state.excel_path)}`")
    if st.button("🗑️ Remove Excel File", key="remove_excel_btn"):
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

# --- Display shipping information when a Call ID is selected ---
if st.session_state.selected_call_id:
    call_id = st.session_state.selected_call_id
    st.write(f"### 📦 Shipping Information for Call ID: {call_id}")
    
    # Search in CSV (if available)
    if st.session_state.df_csv is not None:
        match_csv = st.session_state.df_csv[
            st.session_state.df_csv["call id"].astype(str).str.strip() == call_id.strip()
        ]
        if not match_csv.empty:
            st.write("#### From CSV Data:")
            st.write("**Centre:**", match_csv.iloc[0].get("centre", match_csv.iloc[0].get("center", "Not Found")))
            st.write("**Call Stage:**", match_csv.iloc[0].get("call stage", "Not Found"))
            st.write("**Registration Remarks:**", match_csv.iloc[0].get("registration remarks", "Not Found"))
    
    # Search in Excel (if available) for shipping information
    if st.session_state.df_excel is not None:
        match_excel = st.session_state.df_excel[
            st.session_state.df_excel["call id"].astype(str).str.strip() == call_id.strip()
        ]
        if not match_excel.empty:
            st.write("#### From Excel Data:")
            
            # Display shipping information
            shipping_info_cols = ["billing stock", "courier", "docket no", "date"]
            shipping_data = {}
            
            for col in shipping_info_cols:
                if col in st.session_state.df_excel.columns:
                    shipping_data[col.title()] = match_excel.iloc[0].get(col, "Not Found")
                else:
                    shipping_data[col.title()] = "Column not found"
            
            # Display shipping information in a formatted way
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Billing Stock:** {shipping_data['Billing Stock']}")
                st.write(f"**Courier:** {shipping_data['Courier']}")
            with col2:
                st.write(f"**Docket No:** {shipping_data['Docket No']}")
                st.write(f"**Date:** {shipping_data['Date']}")
        else:
            st.info("ℹ️ Call ID not found in Excel data.")
    
    # Clear selection button
    if st.button("Clear Selection"):
        st.session_state.selected_call_id = None
        st.rerun()

# --- Manual search section (optional backup) ---
st.write("---")
call_id_manual = st.text_input("🔍 Or manually enter Call ID to search (e.g., KOL128082500012)")

if call_id_manual:
    # Set the selected call ID and trigger display
    st.session_state.selected_call_id = call_id_manual
    st.rerun()
