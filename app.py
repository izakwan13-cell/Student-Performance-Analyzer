import os
import joblib
import pandas as pd
import streamlit as st

st.set_page_config(page_title="School Admin Dashboard", layout="wide")
st.title("🏫 9-Subject Student Categorization & Teacher Support Portal")

# Load ML Assets with environment fallback checking
@st.cache_resource
def load_ml_assets():
    model_paths = ["student_model.pkl", "/kaggle/working/student_model.pkl"]
    feature_paths = ["model_features.pkl", "/kaggle/working/model_features.pkl"]

    model_file = next((p for p in model_paths if os.path.exists(p)), None)
    feature_file = next((p for p in feature_paths if os.path.exists(p)), None)

    if model_file and feature_file:
        try:
            model = joblib.load(model_file)
            features = joblib.load(feature_file)
            return model, features
        except Exception:
            return None, None
    return None, None

model, model_features = load_ml_assets()

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

    # --- ML PREDICTION SECTION ---
    if model is not None and model_features is not None:
        X_input = pd.get_dummies(df, drop_first=True)
        X_input = X_input.reindex(columns=model_features, fill_value=0)
        df["Attention Level"] = model.predict(X_input)
    else:
        st.warning("⚠️ ML Model artefacts ('student_model.pkl' & 'model_features.pkl') not found! Falling back to rule-based logic.")
        def get_level(row):
            score = row.get("Average / Overall Score", 100)
            if score < 40: return "🚨 High Attention Required"
            elif score < 60: return "🟡 Moderate Attention Required"
            elif score < 80: return "🔵 Minimal Attention Needed"
            return "🌟 On Track"
        df["Attention Level"] = df.apply(get_level, axis=1)

    global_att_col = next((c for c in df.columns if any(k in c.lower() for k in ["attendance", "kehadiran", "att_overall", "overall att"])), None)
    part_col = next((c for c in df.columns if "participation" in c.lower()), None)
    collab_col = next((c for c in df.columns if "collaborative" in c.lower() or "collab" in c.lower()), None)

    records = []
    for idx, row in df.iterrows():
        student_name = row["Student Name"]
        global_ml_level = row["Attention Level"]

        for subj, teacher in subject_teachers.items():
            subj_clean = subj.lower()
            matching_cols = [
                c for c in df.columns 
                if subj_clean in c.lower() 
                or (subj_clean == "malay" and ("bm" in c.lower() or "melayu" in c.lower()))
            ]

            score_col, att_col, subj_part_col, subj_collab_col = None, None, None, None

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
                if 0 < attendance <= 1.0:
                    attendance = attendance * 100
            except (ValueError, TypeError):
                attendance = 0.0

            if score < 40 or attendance < 70 or "High" in str(global_ml_level):
                subj_level = "🚨 High Attention Required"
            elif score < 60 or attendance < 85 or "Moderate" in str(global_ml_level):
                subj_level = "🟡 Moderate Attention Required"
            elif score < 80:
                subj_level = "🔵 Minimal Attention Needed"
            else:
                subj_level = "🌟 On Track"

            records.append({
                "Student Name": student_name,
                "Subject": subj,
                "Assigned Teacher": teacher,
                "Score / Marks": int(score) if score.is_integer() else score,
                "Attendance (%)": int(attendance) if attendance.is_integer() else attendance,
                "Participation Level": part_val,
                "Collaborative in Class": collab_val,
                "Attention Level": subj_level
            })

    processed_df = pd.DataFrame(records)

    center_column_config = {
        "Student Name": st.column_config.Column("Student Name", width="medium"),
        "Score / Marks": st.column_config.NumberColumn("Score / Marks", alignment="center"),
        "Attendance (%)": st.column_config.NumberColumn("Attendance (%)", alignment="center"),
        "Participation Level": st.column_config.Column("Participation Level", alignment="center"),
        "Collaborative in Class": st.column_config.Column("Collaborative in Class", alignment="center"),
        "Attention Level": st.column_config.Column("Attention Level", width="large")
    }

    if not processed_df.empty:
        high_students = processed_df[processed_df["Attention Level"].str.contains("High")]["Student Name"].nunique()
        mod_students = processed_df[processed_df["Attention Level"].str.contains("Moderate")]["Student Name"].nunique()
        low_students = processed_df[processed_df["Attention Level"].str.contains("Minimal")]["Student Name"].nunique()
    else:
        high_students, mod_students, low_students = 0, 0, 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Students Processed", len(df))
    col2.metric("🚨 High Attention", high_students)
    col3.metric("🟡 Moderate Attention", mod_students)
    col4.metric("🔵 Minimal Attention", low_students)

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
                "🚨 High Attention": h_c,
                "🟡 Moderate Attention": m_c,
                "🔵 Minimal Attention": l_c,
                "Total Flagged Students": h_c + m_c + l_c
            })

        summary_df = pd.DataFrame(teacher_summary).sort_values(by="🚨 High Attention", ascending=False)
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Actionable Student Lists by Subject")
        for subj, teacher in subject_teachers.items():
            subj_df = processed_df[processed_df["Subject"] == subj] if not processed_df.empty else pd.DataFrame()

            with st.expander(f"📘 **{subj}** — Teacher: **{teacher}** ({len(subj_df)} Processed)", expanded=False):
                if not subj_df.empty:
                    sorted_subj_df = subj_df.sort_values(by="Score / Marks", ascending=True)
                    st.dataframe(
                        sorted_subj_df[["Student Name", "Score / Marks", "Attendance (%)", "Participation Level", "Collaborative in Class", "Attention Level"]], 
                        column_config=center_column_config,
                        use_container_width=True, 
                        hide_index=True
                    )
                else:
                    st.success(f"🎉 No students logged in {subj}!")

    with tab3:
        st.dataframe(df, use_container_width=True)

else:
    st.info("👈 Upload your student Excel file via the sidebar to view teacher workloads.")
