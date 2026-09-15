import streamlit as st
import pandas as pd

st.set_page_config(page_title="School Admin Dashboard", layout="wide")
st.title("🏫 9-Subject Student Categorization & Teacher Support Portal")

# Fixed 9 Subjects mapped to Teachers
SUBJECT_TEACHERS = {
    "Physics": "Dr. Alex",
    "Chemistry": "Ms. Sarah",
    "Biology": "Mr. John",
    "Mathematics": "Mrs. Lee",
    "Additional Mathematics": "Mr. David",
    "English": "Ms. Emma",
    "History": "Mr. Robert",
    "Malay": "Pn. Nurul",
    "Islamic Education": "Ustaz Ahmad"
}

# Sidebar configuration
st.sidebar.header("⚙️ Teacher Roster Mapping")
subject_teachers = {}
for subj, default_teacher in SUBJECT_TEACHERS.items():
    subject_teachers[subj] = st.sidebar.text_input(f"{subj}:", value=default_teacher)

uploaded_file = st.sidebar.file_uploader("Upload Student XLSX", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # Detect Student Name Column
    name_col = next((c for c in df.columns if "name" in str(c).lower() or "student" in str(c).lower()), df.columns[0])
    df["Student Name"] = df[name_col]

    # Process High Attention Students across all columns
    records = []
    for idx, row in df.iterrows():
        student_name = row["Student Name"]
        
        for subj, teacher in subject_teachers.items():
            # Find subject-related score & attendance columns flexibly
            score_col = next((c for c in df.columns if subj.lower() in str(c).lower() and ("score" in str(c).lower() or "mark" in str(c).lower() or "grade" in str(c).lower())), None)
            att_col = next((c for c in df.columns if subj.lower() in str(c).lower() and "attendance" in str(c).lower()), None)
            
            # General fallback if subject names are directly in column headers
            if not score_col:
                score_col = next((c for c in df.columns if subj.lower() in str(c).lower()), None)
            
            score = row.get(score_col, 100) if score_col else 100
            attendance = row.get(att_col, 100) if att_col else 100

            try: score = float(score)
            except: score = 100
            try: attendance = float(attendance)
            except: attendance = 100

            if score < 50 or attendance < 70:
                records.append({
                    "Student Name": student_name,
                    "Subject": subj,
                    "Assigned Teacher": teacher,
                    "Score": score,
                    "Attendance Band": attendance,
                    "Attention Level": "🚨 High Attention Required"
                })

    high_att_df = pd.DataFrame(records)

    # Top Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Students Processed", len(df))
    col2.metric("Subjects Tracked", len(subject_teachers))
    col3.metric("🚨 Total High Attention Tasks", len(high_att_df))

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "👩‍🏫 Teacher Intervention Workload", 
        "📚 Subject-Wise High Attention Rosters", 
        "📋 Full Dataset View"
    ])

    with tab1:
        st.subheader("Teacher Intervention Workload Summary")
        teacher_summary = []
        
        for subj, teacher in subject_teachers.items():
            count = len(high_att_df[high_att_df["Subject"] == subj]) if not high_att_df.empty else 0
            teacher_summary.append({
                "Assigned Teacher": teacher,
                "Subject Taught": subj,
                "Students Needing Support": count
            })

        summary_df = pd.DataFrame(teacher_summary).sort_values(by="Students Needing Support", ascending=False)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Actionable Student Lists by Subject")
        for subj, teacher in subject_teachers.items():
            subj_high = high_att_df[high_att_df["Subject"] == subj] if not high_att_df.empty else pd.DataFrame()
            
            with st.expander(f"📘 **{subj}** — Teacher: **{teacher}** ({len(subj_high)} Needing Help)", expanded=True):
                if not subj_high.empty:
                    st.dataframe(subj_high[["Student Name", "Score", "Attendance Band", "Attention Level"]], use_container_width=True, hide_index=True)
                else:
                    st.success(f"🎉 No high-attention students in {subj}!")

    with tab3:
        st.dataframe(df, use_container_width=True)

else:
    st.info("👈 Upload your student Excel file via the sidebar to view teacher workloads.")
