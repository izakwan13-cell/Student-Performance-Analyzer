import streamlit as st
import pandas as pd

st.set_page_config(page_title="School Admin Dashboard", layout="wide")
st.title("🏫 Student Categorization & Teacher Workload Portal")

# File Upload Section
uploaded_file = st.sidebar.file_uploader("Upload Student XLSX", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    # Check if 'Teacher' column exists, otherwise assign default
    if "Teacher" not in df.columns:
        df["Teacher"] = "Unassigned"

    # 1. Student Categorization Logic
    def categorize(row):
        score = row.get("Average / Overall Score", 0)
        attendance = row.get("Attendance Band", 0)
        
        if score < 50 or attendance < 70:
            return "🚨 High Attention Required"
        elif score >= 75 and attendance >= 85:
            return "🌟 Excellent (Minimal Attention)"
        else:
            return "🟡 Moderate Monitoring"

    df["Attention Level"] = df.apply(categorize, axis=1)

    # 2. Overall Summary Metrics Cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Students", len(df))
    col2.metric("🚨 High Attention", len(df[df["Attention Level"].str.contains("High")]))
    col3.metric("🟡 Moderate", len(df[df["Attention Level"].str.contains("Moderate")]))
    col4.metric("🌟 Excellent", len(df[df["Attention Level"].str.contains("Excellent")]))

    st.markdown("---")

    # 3. Dedicated Tabs View
    tab1, tab2 = st.tabs(["👩‍🏫 Teacher Intervention Workload", "📋 Full Student List"])

    with tab1:
        st.subheader("Teacher Workload Breakdown")
        
        # Group data by Teacher and count Attention Levels
        teacher_summary = df.groupby(["Teacher", "Attention Level"]).size().unstack(fill_value=0)
        
        # Ensure all category columns exist in table
        for category in ["🚨 High Attention Required", "🟡 Moderate Monitoring", "🌟 Excellent (Minimal Attention)"]:
            if category not in teacher_summary.columns:
                teacher_summary[category] = 0

        # Sort teachers by who has the most "High Attention Required" students
        teacher_summary["Total Students"] = teacher_summary.sum(axis=1)
        teacher_summary = teacher_summary.sort_values(by="🚨 High Attention Required", ascending=False)
        
        # Display aggregated summary table
        st.dataframe(
            teacher_summary[["🚨 High Attention Required", "🟡 Moderate Monitoring", "🌟 Excellent (Minimal Attention)", "Total Students"]],
            use_container_width=True
        )

        # High priority highlight alert
        top_teacher = teacher_summary.index[0]
        high_count = teacher_summary.loc[top_teacher, "🚨 High Attention Required"]
        st.error(f"⚠️ **Attention Needed:** **{top_teacher}** has the highest number of intervention-level students ({high_count} High Attention students).")

    with tab2:
        st.subheader("Filter Students by Teacher")
        selected_teacher = st.selectbox("Select Teacher", ["All"] + list(df["Teacher"].unique()))
        
        filtered_df = df if selected_teacher == "All" else df[df["Teacher"] == selected_teacher]
        st.dataframe(filtered_df, use_container_width=True)

else:
    st.info("👈 Upload an Excel file via the sidebar to view student categorizations and teacher workloads.")