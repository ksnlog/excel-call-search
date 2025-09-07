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
