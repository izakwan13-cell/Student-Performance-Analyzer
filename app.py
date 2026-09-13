import streamlit as st
import pandas as pd

st.set_page_config(page_title="School Admin Dashboard", layout="wide")
st.title("🏫 Student Attention & Performance Tracker")

# 1. File Upload Section
uploaded_file = st.sidebar.file_uploader("Upload Student XLSX", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    # 2. Categorization Rules
    def categorize(row):
        score = row.get("Average / Overall Score", 0)
        attendance = row.get("Attendance Band", 0)
        
        if score < 50 or attendance < 70:
            return "🚨 Needs High Attention"
        elif score >= 75 and attendance >= 85:
            return "🌟 Excellent (Minimal Attention)"
        else:
            return "🟡 Moderate Attention"

    df["Attention Level"] = df.apply(categorize, axis=1)

    # 3. Sidebar Filtering
    selected = st.sidebar.selectbox("Filter Group", ["All"] + list(df["Attention Level"].unique()))
    filtered_df = df if selected == "All" else df[df["Attention Level"] == selected]

    # 4. KPI Metrics Cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Students", len(df))
    col2.metric("High Attention", len(df[df["Attention Level"].str.contains("High")]))
    col3.metric("Moderate", len(df[df["Attention Level"].str.contains("Moderate")]))
    col4.metric("Excellent", len(df[df["Attention Level"].str.contains("Excellent")]))

    st.markdown("---")

    # 5. Interactive Table View
    st.subheader(f"Student Records ({len(filtered_df)})")
    st.dataframe(filtered_df, use_container_width=True)
else:
    st.info("👈 Please upload an Excel file via the sidebar to view student analytics.")
