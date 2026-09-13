import streamlit as st
import pandas as pd

st.set_page_config(page_title="School Admin Dashboard", layout="wide")
st.title("🏫 Student Categorization & Actionable Teacher Workload")

uploaded_file = st.sidebar.file_uploader("Upload Student XLSX", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    # 1. Column Auto-Detection / User Selection
    def get_column(options, default_label):
        for col in df.columns:
            if str(col).strip().lower() in options:
                return col
        return st.sidebar.selectbox(f"Select '{default_label}' Column:", df.columns)

    teacher_col = get_column(["teacher", "teacher name", "class teacher", "educator", "instructor"], "Teacher")
    subject_col = get_column(["subject", "course", "class", "module"], "Subject")
    name_col = get_column(["student name", "name", "student", "full name"], "Student Name")

    df["Teacher_Clean"] = df[teacher_col].fillna("Unassigned")
    df["Subject_Clean"] = df[subject_col].fillna("General")
    df["Name_Clean"] = df[name_col].fillna("Unknown Student")

    # 2. Student Categorization Logic
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

    # 3. Overall Summary Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Students", len(df))
    col2.metric("🚨 High Attention", len(df[df["Attention Level"].str.contains("High")]))
    col3.metric("🟡 Moderate", len(df[df["Attention Level"].str.contains("Moderate")]))
    col4.metric("🌟 Excellent", len(df[df["Attention Level"].str.contains("Excellent")]))

    st.markdown("---")

    # 4. Tabs View
    tab1, tab2 = st.tabs(["👩‍🏫 Teacher & Subject Student Rosters", "📋 Full Student Dataset"])

    with tab1:
        st.subheader("Students Requiring Intervention (Grouped by Teacher & Subject)")
        
        # Filter for high-attention students only
        high_attention_df = df[df["Attention Level"].str.contains("High")]

        if high_attention_df.empty:
            st.success("🎉 No students currently require high-attention intervention!")
        else:
            # Group by Teacher
            teachers = high_attention_df["Teacher_Clean"].unique()
            
            for teacher in teachers:
                teacher_df = high_attention_df[high_attention_df["Teacher_Clean"] == teacher]
                total_teacher_high = len(teacher_df)
                
                # Expandable card per teacher
                with st.expander(f"👩‍🏫 **{teacher}** — {total_teacher_high} Student(s) Needing Attention", expanded=True):
                    
                    # Group by Subject under each teacher
                    subjects = teacher_df["Subject_Clean"].unique()
                    
                    for subject in subjects:
                        subject_df = teacher_df[teacher_df["Subject_Clean"] == subject]
                        st.markdown(f"#### 📘 Subject: **{subject}** ({len(subject_df)} students)")
                        
                        # Display table of student names and metrics for that subject
                        st.dataframe(
                            subject_df[[name_col, "Average / Overall Score", "Attendance Band", "Attention Level"]],
                            use_container_width=True,
                            hide_index=True
                        )

    with tab2:
        st.subheader("Complete Data View")
        st.dataframe(df, use_container_width=True)

else:
    st.info("👈 Upload an Excel file via the sidebar to view student categorizations and intervention rosters.")