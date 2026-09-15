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

# Synonyms dictionary to bridge Malay/English Excel variations automatically
SUBJECT_SYNONYMS = {
    "physics": "Physics",
    "fizik": "Physics",
    "chemistry": "Chemistry",
    "kimia": "Chemistry",
    "biology": "Biology",
    "biologi": "Biology",
    "mathematics": "Mathematics",
    "matematik": "Mathematics",
    "additional mathematics": "Additional Mathematics",
    "add math": "Additional Mathematics",
    "matematik tambahan": "Additional Mathematics",
    "english": "English",
    "bahasa inggeris": "English",
    "history": "History",
    "sejarah": "History",
    "malay": "Malay",
    "bahasa melayu": "Malay",
    "bm": "Malay",
    "islamic education": "Islamic Education",
    "pendidikan islam": "Islamic Education",
    "pi": "Islamic Education"
}

uploaded_file = st.sidebar.file_uploader("Upload Student XLSX", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    # Clean Column Names
    df.columns = df.columns.str.strip()
    
    # Auto-detect key columns
    name_col = next((c for c in df.columns if "name" in str(c).lower() or "student" in str(c).lower()), df.columns[0])
    subj_col = next((c for c in df.columns if "subject" in str(c).lower() or "course" in str(c).lower() or "mata pelajaran" in str(c).lower()), None)
    score_col = next((c for c in df.columns if "score" in str(c).lower() or "average" in str(c).lower() or "mark" in str(c).lower() or "overall" in str(c).lower()), None)
    att_col = next((c for c in df.columns if "attendance" in str(c).lower() or "kehadiran" in str(c).lower()), None)

    df["Student Name"] = df[name_col]
    
    if subj_col:
        df["Raw_Subject"] = df[subj_col].astype(str).str.strip()
    else:
        st.sidebar.warning("⚠️ Select your Subject Column:")
        selected_col = st.sidebar.selectbox("Subject Column:", df.columns)
        df["Raw_Subject"] = df[selected_col].astype(str).str.strip()

    # Normalize Subject Names using Synonyms
    def normalize_subject(raw_subj):
        cleaned = str(raw_subj).strip().lower()
        if cleaned in SUBJECT_SYNONYMS:
            return SUBJECT_SYNONYMS[cleaned]
        # Fallback keyword match
        for key, standard_name in SUBJECT_SYNONYMS.items():
            if key in cleaned:
                return standard_name
        return raw_subj

    df["Normalized_Subject"] = df["Raw_Subject"].apply(normalize_subject)

    # Student Categorization Logic
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

    # Assign Teacher based on Normalized Subject
    df["Assigned Teacher"] = df["Normalized_Subject"].map(DEFAULT_SUBJECT_TEACHERS).fillna("Unassigned Teacher")

    # Metrics Dashboard
    high_att_df = df[df["Attention Level"].str.contains("High")]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Records", len(df))
    col2.metric("🚨 High Attention", len(high_att_df))
    col3.metric("🟡 Moderate", len(df[df["Attention Level"].str.contains("Moderate")]))
    col4.metric("🌟 Excellent", len(df[df["Attention Level"].str.contains("Excellent")]))

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs([
        "👩‍🏫 Teacher Intervention Workload", 
        "📚 Subject-Wise High Attention Rosters", 
        "📋 Full Dataset View"
    ])

    with tab1:
        st.subheader("Teacher Intervention Workload Summary")
        
        teacher_summary = []
        for std_subj, teacher in DEFAULT_SUBJECT_TEACHERS.items():
            assigned_students = high_att_df[high_att_df["Normalized_Subject"] == std_subj]
            teacher_summary.append({
                "Assigned Teacher": teacher,
                "Subject Taught": std_subj,
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
        
        for std_subj, teacher_name in DEFAULT_SUBJECT_TEACHERS.items():
            subj_high = high_att_df[high_att_df["Normalized_Subject"] == std_subj]
            
            with st.expander(f"📘 **{std_subj}** — Assigned Teacher: **{teacher_name}** ({len(subj_high)} Students Needing Help)", expanded=True):
                if not subj_high.empty:
                    st.dataframe(
                        subj_high[["Student Name", "Average / Overall Score", "Attendance Band", "Attention Level"]],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.success(f"🎉 No high-attention students in {std_subj}!")

    with tab3:
        st.subheader("Complete Records")
        st.dataframe(df, use_container_width=True)

else:
    st.info("👈 Upload your student Excel file via the sidebar to view the matched teacher intervention workloads.")
