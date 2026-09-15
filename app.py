import streamlit as st
import pandas as pd

st.set_page_config(page_title="School Admin Dashboard", layout="wide")
st.title("🏫 9-Subject Student Categorization & Teacher Support Portal")

# 9 Subjects mapped to Teachers
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

st.sidebar.header("⚙️ Teacher Roster Mapping")
subject_teachers = {}
for subj, default_teacher in SUBJECT_TEACHERS.items():
    subject_teachers[subj] = st.sidebar.text_input(f"{subj}:", value=default_teacher)

uploaded_file = st.sidebar.file_uploader("Upload Student XLSX", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    name_col = next((c for c in df.columns if "name" in str(c).lower() or "student" in str(c).lower()), df.columns[0])
    df["Student Name"] = df[name_col]

    records = []
    for idx, row in df.iterrows():
        student_name = row["Student Name"]
        
        for subj, teacher in subject_teachers.items():
            score_col = next((c for c in df.columns if subj.lower() in str(c).lower() and ("score" in str(c).lower() or "mark" in str(c).lower() or "grade" in str(c).lower())), None)
            att_col = next((c for c in df.columns if subj.lower() in str(c).lower() and "attendance" in str(c).lower()), None)
            
            if not score_col:
                score_col = next((c for c in df.columns if subj.lower() in str(c).lower()), None)
            
            score = row.get(score_col, 100) if score_col else 100
            attendance = row.get(att_col, 100) if att_col else 100

            try: score = float(score)
            except: score = 100
            try: attendance = float(attendance)
            except: attendance = 100

            # Categorization Logic based on score thresholds
            if score < 40 or attendance < 70:
                level = "🚨 High Attention Required (<40)"
            elif score < 60:
                level = "🟡 Moderate Attention Required (<60)"
            elif score < 80:
                level = "🔵 Minimal Attention Needed (<80)"
            else:
                level = "🌟 Excellent / On Track"

            if score < 80 or attendance < 70:
                records.append({
                    "Student Name": student_name,
                    "Subject": subj,
                    "Assigned Teacher": teacher,
                    "Score / Marks": score,
                    "Attendance (%)": attendance,
                    "Attention Level": level
                })

    processed_df = pd.DataFrame(records)

    # Top Summary Metrics
    high_count = len(processed_df[processed_df["Attention Level"].str.contains("High")]) if not processed_df.empty else 0
    mod_count = len(processed_df[processed_df["Attention Level"].str.contains("Moderate")]) if not processed_df.empty else 0
    low_count = len(processed_df[processed_df["Attention Level"].str.contains("Minimal")]) if not processed_df.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Students Processed", len(df))
    col2.metric("🚨 High Attention (<40)", high_count)
    col3.metric("🟡 Moderate Attention (<60)", mod_count)
    col4.metric("🔵 Minimal Attention (<80)", low_count)

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs([
        "👩‍🏫 Teacher Intervention Workload", 
        "📚 Subject-Wise Rosters", 
        "📋 Full Dataset View"
    ])

    with tab1:
        st.subheader("Teacher Intervention Workload Breakdown")
        teacher_summary = []
        
        for subj, teacher in subject_teachers.items():
            subj_df = processed_df[processed_df["Subject"] == subj] if not processed_df.empty else pd.DataFrame()
            
            h_c = len(subj_df[subj_df["Attention Level"].str.contains("High")]) if not subj_df.empty else 0
            m_c = len(subj_df[subj_df["Attention Level"].str.contains("Moderate")]) if not subj_df.empty else 0
            l_c = len(subj_df[subj_df["Attention Level"].str.contains("Minimal")]) if not subj_df.empty else 0

            teacher_summary.append({
                "Assigned Teacher": teacher,
                "Subject Taught": subj,
                "🚨 High (<40)": h_c,
                "🟡 Moderate (<60)": m_c,
                "🔵 Minimal (<80)": l_c,
                "Total Flagged Students": h_c + m_c + l_c
            })

        summary_df = pd.DataFrame(teacher_summary).sort_values(by="🚨 High (<40)", ascending=False)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Actionable Student Lists by Subject")
        for subj, teacher in subject_teachers.items():
            subj_df = processed_df[processed_df["Subject"] == subj] if not processed_df.empty else pd.DataFrame()
            
            with st.expander(f"📘 **{subj}** — Teacher: **{teacher}** ({len(subj_df)} Total Flagged)", expanded=False):
                if not subj_df.empty:
                    # Displays Student Name, Score/Marks, and Attendance side-by-side
                    st.dataframe(
                        subj_df[["Student Name", "Score / Marks", "Attendance (%)", "Attention Level"]], 
                        use_container_width=True, 
                        hide_index=True
                    )
                else:
                    st.success(f"🎉 No students requiring attention in {subj}!")

    with tab3:
        st.dataframe(df, use_container_width=True)

else:
    st.info("👈 Upload your student Excel file via the sidebar to view teacher workloads.")
