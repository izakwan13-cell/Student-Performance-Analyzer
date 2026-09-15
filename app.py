import streamlit as st
import pandas as pd

st.set_page_config(page_title="9-Subject Teacher Workload Portal", layout="wide")
st.title("🏫 9-Subject Student Categorization & Specialist Teacher Roster")

# Default mapping template
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

uploaded_file = st.sidebar.file_uploader("Upload Student XLSX", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    # 1. Clean Column Names
    df.columns = df.columns.str.strip()
    
    # Auto-detect Student Name & Subject columns
    name_col = next((c for c in df.columns if "name" in str(c).lower() or "student" in str(c).lower()), df.columns[0])
    subject_col = next((c for c in df.columns if "subject" in str(c).lower() or "course" in str(c).lower() or "class" in str(c).lower()), None)
    
    df["Student Name"] = df[name_col]
    
    if subject_col:
        df["Subject"] = df[subject_col].astype(str).str.strip()
    else:
        st.sidebar.warning("⚠️ Select your Subject column:")
        df["Subject"] = st.sidebar.selectbox("Subject Column:", df.columns).astype(str).str.strip()

    # 2. Flexible Categorization Logic
    score_col = next((c for c in df.columns if "score" in str(c).lower() or "mark" in str(c).lower() or "average" in str(c).lower()), None)
    att_col = next((c for c in df.columns if "attendance" in str(c).lower()), None)

    def categorize(row):
        score = row.get(score_col, 100) if score_col else 100
        attendance = row.get(att_col, 100) if att_col else 100
        
        # Convert numeric values safely
        try:
            score = float(score)
        except (ValueError, TypeError):
            score = 100
            
        try:
            attendance = float(attendance)
        except (ValueError, TypeError):
            attendance = 100

        if score < 50 or attendance < 70:
            return "🚨 High Attention Required"
        elif score >= 75 and attendance >= 85:
            return "🌟 Excellent (Minimal Attention)"
        else:
            return "🟡 Moderate Monitoring"

    df["Attention Level"] = df.apply(categorize, axis=1)

    # 3. Dynamic Sidebar Mapping for Actual Excel Subjects
    st.sidebar.header("⚙️ Assigned Teachers")
    actual_subjects = df["Subject"].unique()
    teacher_mapping = {}

    for subj in actual_subjects:
        # Match default teacher if subject exists in dictionary, else default to "Unassigned"
        matched_default = next((v for k, v in DEFAULT_TEACHER_MAPPING.items() if k.lower() in subj.lower()), "Unassigned Teacher")
        teacher_mapping[subj] = st.sidebar.text_input(f"Teacher for '{subj}':", value=matched_default)

    # Assign Teachers
    df["Assigned Teacher"] = df["Subject"].map(teacher_mapping)

    # 4. Metrics & Workload Breakdown
    high_att_df = df[df["Attention Level"].str.contains("High")]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Records", len(df))
    col2.metric("Subjects Found", len(actual_subjects))
    col3.metric("🚨 Total High Attention Students", len(high_att_df))

    st.markdown("---")

    tab1, tab2 = st.tabs(["👩‍🏫 Teacher Intervention Workload", "📋 Full Dataset View"])

    with tab1:
        st.subheader("Teacher Intervention Workload Overview")
        teacher_summary = []
        
        for subj in actual_subjects:
            t_name = teacher_mapping[subj]
            count = len(high_att_df[high_att_df["Subject"] == subj])
            teacher_summary.append({"Teacher": t_name, "Subject Taught": subj, "High Attention Students": count})
            
        summary_df = pd.DataFrame(teacher_summary)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

    with tab2:
        st.dataframe(df, use_container_width=True)

else:
    st.info("👈 Upload your student Excel file via the sidebar to automatically match subjects and teachers.")
