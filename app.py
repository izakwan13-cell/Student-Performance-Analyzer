import streamlit as st
import pandas as pd

st.set_page_config(page_title="9-Subject Teacher Workload Portal", layout="wide")
st.title("🏫 9-Subject Student Categorization & Specialist Teacher Roster")

# Default 9 Subjects and Assigned Specialist Teachers
DEFAULT_TEACHER_MAPPING = {
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

st.sidebar.header("⚙️ Subject-Teacher Mapping")
st.sidebar.caption("Assigned specialist teachers per subject:")

# Allow real-time editing of teachers per subject in sidebar
teacher_mapping = {}
for subject, default_teacher in DEFAULT_TEACHER_MAPPING.items():
    teacher_mapping[subject] = st.sidebar.text_input(f"{subject}:", value=default_teacher)

uploaded_file = st.sidebar.file_uploader("Upload Student XLSX", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    # Auto-detect Student Name & Subject columns
    name_col = next((c for c in df.columns if "name" in str(c).lower() or "student" in str(c).lower()), df.columns[0])
    subject_col = next((c for c in df.columns if "subject" in str(c).lower() or "course" in str(c).lower() or "class" in str(c).lower()), None)
    
    df["Student Name"] = df[name_col]
    
    if subject_col:
        df["Subject"] = df[subject_col]
    else:
        st.sidebar.warning("⚠️ No 'Subject' column detected automatically.")
        df["Subject"] = st.sidebar.selectbox("Select Subject Column:", df.columns)

    # Student Categorization Logic
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

    # Assign Teacher based on Subject Mapping
    df["Assigned Teacher"] = df["Subject"].map(teacher_mapping).fillna("Unassigned Teacher")

    # Metrics Overview
    high_att_df = df[df["Attention Level"].str.contains("High")]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Student Records", len(df))
    col2.metric("Subjects Tracked", df["Subject"].nunique())
    col3.metric("🚨 Total High Attention Students", len(high_att_df))

    st.markdown("---")

    # Tabs View
    tab1, tab2, tab3 = st.tabs([
        "📚 High Attention by Subject & Teacher", 
        "👩‍🏫 Teacher Roster Summary", 
        "📋 Full Student Dataset"
    ])

    with tab1:
        st.subheader("High Attention Students Grouped by Subject & Assigned Teacher")
        
        if high_att_df.empty:
            st.success("🎉 No high-attention students across any of the subjects!")
        else:
            for subject_name in df["Subject"].unique():
                subj_df = high_att_df[high_att_df["Subject"] == subject_name]
                assigned_teacher = teacher_mapping.get(subject_name, "Unassigned")
                
                with st.expander(f"📘 **{subject_name}** — Teacher: **{assigned_teacher}** ({len(subj_df)} Needing Help)", expanded=False):
                    if not subj_df.empty:
                        st.dataframe(
                            subj_df[["Student Name", "Average / Overall Score", "Attendance Band", "Attention Level"]],
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.write("No high-attention students in this subject.")

    with tab2:
        st.subheader("Teacher Intervention Workload Overview")
        teacher_summary = []
        
        for subj, t_name in teacher_mapping.items():
            count = len(high_att_df[(high_att_df["Subject"] == subj) & (high_att_df["Assigned Teacher"] == t_name)])
            teacher_summary.append({"Teacher": t_name, "Subject Taught": subj, "High Attention Students": count})
            
        summary_df = pd.DataFrame(teacher_summary)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("Complete Records")
        st.dataframe(df, use_container_width=True)

else:
    st.info("👈 Upload your student Excel file via the sidebar to view the subject-teacher assignments.")
