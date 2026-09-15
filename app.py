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
    df.columns = df.columns.astype(str).str.strip()

    name_col = next((c for c in df.columns if "name" in c.lower() or "student" in c.lower()), df.columns[0])
    df["Student Name"] = df[name_col]

    global_att_col = next((c for c in df.columns if any(k in c.lower() for k in ["attendance", "kehadiran", "att_overall", "overall att"])), None)
    
    # Detect global or subject participation / collaborative columns
    part_col = next((c for c in df.columns if "participation" in c.lower()), None)
    collab_col = next((c for c in df.columns if "collaborative" in c.lower() or "collab" in c.lower()), None)

    records = []
    
    for idx, row in df.iterrows():
        student_name = row["Student Name"]
        
        for subj, teacher in subject_teachers.items():
            subj_clean = subj.lower()
            
            matching_cols = [
                c for c in df.columns 
                if subj_clean in c.lower() 
                or (subj_clean == "malay" and ("bm" in c.lower() or "melayu" in c.lower()))
            ]

            score_col = None
            att_col = None
            subj_part_col = None
            subj_collab_col = None

            for col in matching_cols:
                c_lower = col.lower()
                if any(k in c_lower for k in ["attendance", "kehadiran", "att"]):
                    att_col = col
                elif "participation" in c_lower:
                    subj_part_col = col
                elif "collaborative" in c_lower or "collab" in c_lower:
                    subj_collab_col = col
                else:
                    score_col = col

            if not att_col:
                att_col = global_att_col
            
            # Fall back to global participation/collaborative columns if subject-specific not found
            final_part_col = subj_part_col if subj_part_col else part_col
            final_collab_col = subj_collab_col if subj_collab_col else collab_col

            score_val = row[score_col] if score_col and pd.notnull(row[score_col]) else None
            att_val = row[att_col] if att_col and pd.notnull(row[att_col]) else None
            part_val = row[final_part_col] if final_part_col and pd.notnull(row[final_part_col]) else "N/A"
            collab_val = row[final_collab_col] if final_collab_col and pd.notnull(row[final_collab_col]) else "N/A"

            if score_val is None:
                continue

            try:
                score = float(score_val)
            except (ValueError, TypeError):
                score = 0.0

            try:
                if isinstance(att_val, str):
                    att_val = att_val.replace("%", "").strip()
                attendance = float(att_val)
                if attendance <= 1.0 and attendance > 0:
                    attendance = attendance * 100
            except (ValueError, TypeError):
                attendance = 0.0

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
                    "Score / Marks": int(score) if score.is_integer() else score,
                    "Attendance (%)": int(attendance) if attendance.is_integer() else attendance,
                    "Participation Level": part_val,
                    "Collaborative in Class": collab_val,
                    "Attention Level": level
                })

    processed_df = pd.DataFrame(records)

    # Center-align table headers and contents
    center_column_config = {
        "Student Name": st.column_config.Column("Student Name", width="medium"),
        "Score / Marks": st.column_config.NumberColumn("Score / Marks", alignment="center"),
        "Attendance (%)": st.column_config.NumberColumn("Attendance (%)", alignment="center"),
        "Participation Level": st.column_config.Column("Participation Level", alignment="center"),
        "Collaborative in Class": st.column_config.Column("Collaborative in Class", alignment="center"),
        "Attention Level": st.column_config.Column("Attention Level", width="large")
    }

    # Summary Metrics
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
                "🔵 Minimal Attention (<80)": l_c,
                "Total Flagged Students": h_c + m_c + l_c
            })

        summary_df = pd.DataFrame(teacher_summary).sort_values(by="🚨 High (<40)", ascending=False)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Actionable Student Lists by Subject (Sorted Lowest to Highest Score)")
        for subj, teacher in subject_teachers.items():
            subj_df = processed_df[processed_df["Subject"] == subj] if not processed_df.empty else pd.DataFrame()
            
            with st.expander(f"📘 **{subj}** — Teacher: **{teacher}** ({len(subj_df)} Total Flagged)", expanded=False):
                if not subj_df.empty:
                    sorted_subj_df = subj_df.sort_values(by="Score / Marks", ascending=True)
                    st.dataframe(
                        sorted_subj_df[["Student Name", "Score / Marks", "Attendance (%)", "Participation Level", "Collaborative in Class", "Attention Level"]], 
                        column_config=center_column_config,
                        use_container_width=True, 
                        hide_index=True
                    )
                else:
                    st.success(f"🎉 No students requiring attention in {subj}!")

    with tab3:
        st.dataframe(df, use_container_width=True)

else:
    st.info("👈 Upload your student Excel file via the sidebar to view teacher workloads.")
