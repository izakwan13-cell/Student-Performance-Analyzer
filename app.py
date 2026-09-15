import streamlit as st
import pandas as pd

st.set_page_config(page_title="All-Subject Teacher Workload Portal", layout="wide")
st.title("🏫 Multi-Subject Student Categorization & Teacher Assignment")

# Sidebar Teacher Pool Setup
st.sidebar.header("Teacher Roster Pool")
teacher_input = st.sidebar.text_area(
    "Available Teachers (one per line):", 
    value="Mr. John\nMs. Sarah\nDr. Alex\nMrs. Lee\nMr. David"
)
available_teachers = [t.strip() for t in teacher_input.split("\n") if t.strip()]

uploaded_file = st.sidebar.file_uploader("Upload Student XLSX", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    
    # 1. Automatic Column Identification
    name_col = next((c for c in df.columns if "name" in str(c).lower() or "student" in str(c).lower()), df.columns[0])
    subject_col = next((c for c in df.columns if "subject" in str(c).lower() or "course" in str(c).lower() or "class" in str(c).lower()), None)
    
    df["Student Name"] = df[name_col]
    
    if subject_col:
        df["Subject"] = df[subject_col]
    else:
        st.sidebar.warning("⚠️ No 'Subject' column detected automatically.")
        df["Subject"] = st.sidebar.selectbox("Select Subject Column:", df.columns)

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

    # 3. Auto-Assign Teachers Per Subject for High-Attention Students (Round-Robin)
    df["Assigned Teacher"] = "Unassigned"
    
    if len(available_teachers) > 0:
        for subject, subject_group in df.groupby("Subject"):
            high_attention_idx = subject_group[subject_group["Attention Level"].str.contains("High")].index
            
            for i, idx in enumerate(high_attention_idx):
                assigned = available_teachers[i % len(available_teachers)]
                df.loc[idx, "Assigned Teacher"] = assigned

    # 4. Summary Metrics
    high_att_total = len(df[df["Attention Level"].str.contains("High")])
    subjects_count = df["Subject"].nunique()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Records", len(df))
    col2.metric("Subjects Tracked", subjects_count)
    col3.metric("🚨 Total High Attention Needs", high_att_total)

    st.markdown("---")

    # 5. Dynamic Tabs
    tab1, tab2 = st.tabs(["📘 Breakdown by Subject", "👩‍🏫 Breakdown by Assigned Teacher"])

    with tab1:
        st.subheader("Subject-Wise Intervention Lists")
        all_subjects = df["Subject"].unique()
        
        for subj in all_subjects:
            subj_df = df[(df["Subject"] == subj) & (df["Attention Level"].str.contains("High"))]
            
            with st.expander(f"📚 **{subj}** — {len(subj_df)} High Attention Student(s)", expanded=False):
                if not subj_df.empty:
                    st.dataframe(
                        subj_df[["Student Name", "Assigned Teacher", "Average / Overall Score", "Attendance Band", "Attention Level"]],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.success("🎉 No high-attention students in this subject!")

    with tab2:
        st.subheader("Teacher Workload Overview Across All Subjects")
        for teacher in available_teachers:
            teacher_df = df[(df["Assigned Teacher"] == teacher) & (df["Attention Level"].str.contains("High"))]
            
            with st.expander(f"👩‍🏫 **{teacher}** — Assigned {len(teacher_df)} Student Task(s) Across Subjects", expanded=False):
                if not teacher_df.empty:
                    st.dataframe(
                        teacher_df[["Student Name", "Subject", "Average / Overall Score", "Attendance Band", "Attention Level"]],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.write("No high-attention students assigned.")

else:
    st.info("👈 Upload your student Excel file via the sidebar to process all subjects.")
