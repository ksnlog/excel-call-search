import streamlit as st
import pandas as pd
import zipfile
import chardet
import io

st.title("📂 Call ID Search App")

df_csv = None
df_excel = None

# Upload ZIP file (CSV) - allow all file types for mobile compatibility
uploaded_zip = st.file_uploader("Upload a ZIP file containing a CSV", type=None)

if uploaded_zip is not None:
    try:
        with zipfile.ZipFile(uploaded_zip, "r") as zip_ref:
            csv_files = [f for f in zip_ref.namelist() if f.endswith(".csv")]
            if not csv_files:
                st.error("❌ No CSV file found inside the ZIP.")
            else:
                csv_name = csv_files[0]
                with zip_ref.open(csv_name) as csvfile:
                    raw_data = csvfile.read()
                    result = chardet.detect(raw_data)
                    encoding = result["encoding"]
                    df_csv = pd.read_csv(io.StringIO(raw_data.decode(encoding)))
                    df_csv.columns = [c.strip().lower() for c in df_csv.columns]
                    st.success(f"✅ Loaded {csv_name} (encoding: {encoding})")
                    st.dataframe(df_csv.head())
    except zipfile.BadZipFile:
        st.error("❌ The uploaded file is not a valid ZIP file.")

# Upload Excel file
uploaded_excel = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])

if uploaded_excel is not None:
    df_excel = pd.read_excel(uploaded_excel)
    df_excel.columns = [c.strip().lower() for c in df_excel.columns]
    st.success(f"✅ Loaded Excel with {len(df_excel)} rows")
    st.dataframe(df_excel.head())

# Search section
call_id = st.text_input("🔍 Enter Call ID to search (e.g., KOL128082500012)")

if call_id:
    # Search in CSV (if available)
    if df_csv is not None:
        match_csv = df_csv[df_csv["call id"].astype(str).str.strip() == call_id.strip()]
        if not match_csv.empty:
            st.write("### 🎯 Result from CSV (ZIP)")
            st.write("**Centre:**", match_csv.iloc[0].get("centre", match_csv.iloc[0].get("center", "Not Found")))
            st.write("**Call Stage:**", match_csv.iloc[0].get("call stage", "Not Found"))
            st.write("**Registration Remarks:**", match_csv.iloc[0].get("registration remarks", "Not Found"))
        else:
            st.info("ℹ️ Call ID not found in CSV data.")

    # Search in Excel (if available)
    if df_excel is not None:
        match_excel = df_excel[df_excel["call id"].astype(str).str.strip() == call_id.strip()]
        if not match_excel.empty:
            st.write("### 🎯 Result from Excel file")

            # Multi-select for columns (max 5)
            available_cols = [c for c in df_excel.columns if c != "call id"]
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
