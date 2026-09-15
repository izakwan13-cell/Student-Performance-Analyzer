import streamlit as st
import pandas as pd

st.set_page_config(page_title="School Admin Dashboard", layout="wide")
st.title("🏫 9-Subject Student Categorization & Teacher Support Portal")

# Default 9 Subjects and assigned Primary Teachers
DEFAULT_SUBJECT_TEACHERS = {
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

# Sidebar configuration for available support teachers
st.sidebar.header("⚙️ Teacher Roster & Subject Mapping")
st.sidebar.caption("Adjust primary teachers per subject if needed:")

subject_teachers = {}
for subj, default_teacher in DEFAULT_SUBJECT_TEACHERS.items():
    subject_teachers[subj] = st.sidebar.text_input(f"{subj}:", value=default_teacher)

uploaded_file = st.sidebar.file_uploader("Upload Student XLSX", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    # 1. Clean Column Headers
    df.columns = df.columns.str.strip()
    
    # Auto-detect columns
    name_col = next((c for c in df.columns if "name" in str(c).lower() or "student" in str(c).lower()), df.columns[0])
    subj_col = next((c for c in df.columns if "subject" in str(c).lower() or "course" in str(c).lower()), None)
    score_col = next((c for c in df.columns if "score" in str(c).lower() or "average" in str(c).lower() or "mark" in str(c).lower()), None)
    att_col = next((c for c in df.columns if "attendance" in str(c).lower()), None)

    df["Student Name"] = df[name_col]
    
    if subj_col:
        df["Subject"] = df[subj_col].astype(str).str.strip()
    else:
        st.sidebar.warning("⚠️ Select your Subject Column:")
        df["Subject"] = st.sidebar.selectbox("Subject Column:", df.columns)

    # 2. Student Categorization Logic
    def categorize(row):
        score = row.get(score_col, 0) if score_col else 0
        attendance = row.get(att_col, 0) if att_col else 0
        
        try:
            score = float(score)
        except (ValueError, TypeError):
            score = 0
            
        try:
            attendance = float(attendance)
        except (ValueError, TypeError):
            attendance = 0

        if score < 50 or attendance < 70:
            return "🚨 High Attention Required"
        elif score >= 75 and attendance >= 85:
            return "🌟 Excellent (Minimal Attention)"
        else:
            return "🟡 Moderate Monitoring"

    df["Attention Level"] = df.apply(categorize, axis=1)

    # 3. Assign Teacher based on Subject Mapping
    df["Assigned Teacher"] = df["Subject"].map(subject_teachers).fillna("Unassigned Teacher")

    # 4. Metrics Dashboard
    high_att_df = df[df["Attention Level"].str.contains("High")]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Records", len(df))
    col2.metric("🚨 High Attention", len(high_att_df))
    col3.metric("🟡 Moderate", len(df[df["Attention Level"].str.contains("Moderate")]))
    col4.metric("🌟 Excellent", len(df[df["Attention Level"].str.contains("Excellent")]))

    st.markdown("---")

    # 5. Tab Views for Workload Management
    tab1, tab2, tab3 = st.tabs([
        "👩‍🏫 Teacher Intervention Workload", 
        "📚 Subject-Wise High Attention Rosters", 
        "📋 Full Dataset View"
    ])

    with tab1:
        st.subheader("Teacher Intervention Workload Summary")
        
        # Summary table grouped by teacher
        teacher_summary = []
        for subj, teacher in subject_teachers.items():
            assigned_students = high_att_df[high_att_df["Subject"] == subj]
            teacher_summary.append({
                "Assigned Teacher": teacher,
                "Subject Taught": subj,
                "Students Needing Support": len(assigned_students)
            })
            
        summary_df = pd.DataFrame(teacher_summary)
        summary_df = summary_df.sort_values(by="Students Needing Support", ascending=False)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        # Highlight highest priority teacher
        if not summary_df.empty and summary_df["Students Needing Support"].iloc[0] > 0:
            top_teacher = summary_df.iloc[0]["Assigned Teacher"]
            top_subject = summary_df.iloc[0]["Subject Taught"]
            top_count = summary_df.iloc[0]["Students Needing Support"]
            st.error(f"⚠️ **Highest Priority Support Needed:** **{top_teacher}** ({top_subject}) has {top_count} high-attention students requiring immediate intervention.")

    with tab2:
        st.subheader("Actionable Student Lists by Subject & Assigned Teacher")
        
        for subj in df["Subject"].unique():
            subj_high = high_att_df[high_att_df["Subject"] == subj]
            teacher_name = subject_teachers.get(subj, "Unassigned Teacher")
            
            with st.expander(f"📘 **{subj}** — Assigned Teacher: **{teacher_name}** ({len(subj_high)} Students Needing Help)", expanded=True):
                if not subj_high.empty:
                    st.dataframe(
                        subj_high[["Student Name", "Average / Overall Score", "Attendance Band", "Attention Level"]],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.success(f"🎉 No high-attention students in {subj}!")

    with tab3:
        st.subheader("Complete Records")
        st.dataframe(df, use_container_width=True)

else:
    st.info("👈 Upload your student Excel file via the sidebar to automatically match subjects and populate the teacher intervention workloads.")
