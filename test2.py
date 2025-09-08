import streamlit as st
import pandas as pd
import zipfile
import chardet
import io
import os
import uuid
import time

st.title("📂 Call ID Search App (Persistent Uploads on Refresh)")

# Create a persistent folder for uploaded files
PERSISTENT_DIR = "persistent_uploads"
os.makedirs(PERSISTENT_DIR, exist_ok=True)

# Initialize session state for dataframes
if "df_csv" not in st.session_state:
    st.session_state.df_csv = None
if "df_excel" not in st.session_state:
    st.session_state.df_excel = None
if "csv_filename" not in st.session_state:
    st.session_state.csv_filename = None
if "excel_filename" not in st.session_state:
    st.session_state.excel_filename = None
if "selected_call_id" not in st.session_state:
    st.session_state.selected_call_id = None
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())[:8]

# Create user-specific directory
USER_DIR = os.path.join(PERSISTENT_DIR, f"user_{st.session_state.user_id}")
os.makedirs(USER_DIR, exist_ok=True)

# Load previously uploaded files for this user
def load_user_files():
    user_files = os.listdir(USER_DIR)
    csv_files = [f for f in user_files if f.endswith('.zip') or f.endswith('.csv')]
    excel_files = [f for f in user_files if f.endswith(('.xlsx', '.xls'))]
    
    if csv_files and not st.session_state.csv_filename:
        st.session_state.csv_filename = csv_files[0]
    if excel_files and not st.session_state.excel_filename:
        st.session_state.excel_filename = excel_files[0]

load_user_files()

# --- Upload ZIP or any file ---
if st.session_state.csv_filename and os.path.exists(os.path.join(USER_DIR, st.session_state.csv_filename)):
    st.write(f"📁 **Loaded File:** `{st.session_state.csv_filename}`")
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🔄 Replace CSV File", key="replace_csv"):
            st.session_state.csv_filename = None
            st.rerun()
    with col2:
        if st.button("🗑️ Remove CSV File", key="remove_csv"):
            file_path = os.path.join(USER_DIR, st.session_state.csv_filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            st.session_state.csv_filename = None
            st.session_state.df_csv = None
            st.rerun()
else:
    uploaded_zip = st.file_uploader("Upload a file containing a CSV", type=None, key="csv_uploader")
    if uploaded_zip is not None:
        file_ext = os.path.splitext(uploaded_zip.name)[1]
        unique_filename = f"{st.session_state.user_id}_{uploaded_zip.name}"
        zip_path = os.path.join(USER_DIR, unique_filename)
        
        with open(zip_path, "wb") as f:
            f.write(uploaded_zip.getbuffer())
        st.session_state.csv_filename = unique_filename
        st.rerun()

# If a file path exists in session_state, load it
if st.session_state.csv_filename:
    csv_path = os.path.join(USER_DIR, st.session_state.csv_filename)
    try:
        if st.session_state.csv_filename.endswith('.zip'):
            with zipfile.ZipFile(csv_path, "r") as zip_ref:
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
        else:
            # Direct CSV file
            with open(csv_path, "rb") as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
                encoding = result["encoding"]
                st.session_state.df_csv = pd.read_csv(io.StringIO(raw_data.decode(encoding)))
                st.session_state.df_csv.columns = [c.strip().lower() for c in st.session_state.df_csv.columns]
                st.success(f"✅ Loaded CSV file (encoding: {encoding})")
    except zipfile.BadZipFile:
        st.error("❌ Not a ZIP file. Please upload a proper ZIP containing CSV.")
    except Exception as e:
        st.error(f"Error reading file: {e}")

# Show CSV preview if loaded
if st.session_state.df_csv is not None:
    preview_cols = ["call id", "centre", "center", "warranty", "model", "call stage", "ageing", "pending parts", "pending parts desc", "pending parts date"]
    available_cols = [c for c in preview_cols if c in st.session_state.df_csv.columns]
    df_preview = st.session_state.df_csv[available_cols].copy()
    
    if "center" in df_preview.columns:
        df_preview.rename(columns={"center": "centre"}, inplace=True)
    
    if "ageing" in df_preview.columns:
        df_preview = df_preview.sort_values(by="ageing", ascending=False).head(10)
    else:
        df_preview = df_preview.head(10)
    
    st.write("### 📋 CSV Preview (Click on a Call ID to view details)")
    
    display_df = df_preview.copy()
    if "call id" in display_df.columns:
        display_df["call id"] = display_df["call id"].apply(lambda x: f"🔍 {x}")
    
    st.dataframe(display_df)
    
    if "call id" in df_preview.columns:
        st.write("### 🔍 Select a Call ID to view details:")
        call_ids = df_preview["call id"].astype(str).tolist()
        cols = st.columns(3)
        
        for i, call_id in enumerate(call_ids):
            with cols[i % 3]:
                if st.button(f"{call_id}", key=f"btn_{call_id}"):
                    st.session_state.selected_call_id = call_id
                    st.rerun()

# --- Upload Excel file ---
if st.session_state.excel_filename and os.path.exists(os.path.join(USER_DIR, st.session_state.excel_filename)):
    st.write(f"📁 **Loaded File:** `{st.session_state.excel_filename}`")
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("🔄 Replace Excel File", key="replace_excel"):
            st.session_state.excel_filename = None
            st.rerun()
    with col2:
        if st.button("🗑️ Remove Excel File", key="remove_excel"):
            file_path = os.path.join(USER_DIR, st.session_state.excel_filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            st.session_state.excel_filename = None
            st.session_state.df_excel = None
            st.rerun()
else:
    uploaded_excel = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"], key="excel_uploader")
    if uploaded_excel is not None:
        unique_filename = f"{st.session_state.user_id}_{uploaded_excel.name}"
        excel_path = os.path.join(USER_DIR, unique_filename)
        with open(excel_path, "wb") as f:
            f.write(uploaded_excel.getbuffer())
        st.session_state.excel_filename = unique_filename
        st.rerun()

# If Excel path exists in session_state, load it
if st.session_state.excel_filename:
    excel_path = os.path.join(USER_DIR, st.session_state.excel_filename)
    try:
        st.session_state.df_excel = pd.read_excel(excel_path)
        st.session_state.df_excel.columns = [c.strip().lower() for c in st.session_state.df_excel.columns]
        st.success(f"✅ Loaded Excel with {len(st.session_state.df_excel)} rows")
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")

# --- Display shipping information when a Call ID is selected ---
if st.session_state.selected_call_id:
    call_id = st.session_state.selected_call_id
    st.write(f"### 📦 Shipping Information for Call ID: {call_id}")
    
    if st.session_state.df_csv is not None:
        match_csv = st.session_state.df_csv[
            st.session_state.df_csv["call id"].astype(str).str.strip() == call_id.strip()
        ]
        if not match_csv.empty:
            st.write("#### From CSV Data:")
            st.write("**Centre:**", match_csv.iloc[0].get("centre", match_csv.iloc[0].get("center", "Not Found")))
            st.write("**Call Stage:**", match_csv.iloc[0].get("call stage", "Not Found"))
            st.write("**Registration Remarks:**", match_csv.iloc[0].get("registration remarks", "Not Found"))
    
    if st.session_state.df_excel is not None:
        match_excel = st.session_state.df_excel[
            st.session_state.df_excel["call id"].astype(str).str.strip() == call_id.strip()
        ]
        if not match_excel.empty:
            st.write("#### From Excel Data:")
            
            shipping_info_cols = ["billing stock", "courier", "docket no", "date"]
            shipping_data = {}
            
            for col in shipping_info_cols:
                if col in st.session_state.df_excel.columns:
                    shipping_data[col.title()] = match_excel.iloc[0].get(col, "Not Found")
                else:
                    shipping_data[col.title()] = "Column not found"
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Billing Stock:** {shipping_data['Billing Stock']}")
                st.write(f"**Courier:** {shipping_data['Courier']}")
            with col2:
                st.write(f"**Docket No:** {shipping_data['Docket No']}")
                st.write(f"**Date:** {shipping_data['Date']}")
        else:
            st.info("ℹ️ Call ID not found in Excel data.")
    
    if st.button("Clear Selection"):
        st.session_state.selected_call_id = None
        st.rerun()

# --- Manual search section ---
st.write("---")
call_id_manual = st.text_input("🔍 Or manually enter Call ID to search (e.g., KOL128082500012)")

if call_id_manual:
    st.session_state.selected_call_id = call_id_manual
    st.rerun()

# --- Cleanup old files (runs occasionally) ---
if st.session_state.get('cleanup_counter', 0) % 10 == 0:  # Run cleanup every 10 interactions
    try:
        # Remove files older than 24 hours
        for user_folder in os.listdir(PERSISTENT_DIR):
            user_path = os.path.join(PERSISTENT_DIR, user_folder)
            if os.path.isdir(user_path):
                for file in os.listdir(user_path):
                    file_path = os.path.join(user_path, file)
                    # Remove files older than 24 hours
                    if os.path.getmtime(file_path) < (time.time() - 24 * 3600):
                        os.remove(file_path)
                # Remove empty user folders
                if not os.listdir(user_path):
                    os.rmdir(user_path)
    except:
        pass  # Silent cleanup failure

st.session_state.cleanup_counter = st.session_state.get('cleanup_counter', 0) + 1
