"""AXEL Streamlit dashboard (also packaged as axel.exe via axel.spec).

Run:  streamlit run axel.py
"""

import chardet
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import config
from core import (
    build_pdf_report,
    calculate_gpa,
    cluster_students,
    is_at_risk,
    load_engineered,
    plot_gpa_trend_figure,
    recommend_books,
    train_gpa_predictor,
    train_risk_classifier,
)

REQUIRED_FIELDS = ["student id", "attendance", "borrowed book 1", "borrowed book 2"]

NON_SUBJECT_COLUMNS = {
    "student id",
    "student name",
    "attendance",
    "interests",
    "borrowed book 1",
    "borrowed book 2",
}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def check_password():
    """Simple shared-password gate (password comes from config / env)."""
    if st.session_state.get("authed"):
        return True
    with st.sidebar.form("login_form"):
        st.sidebar.title(":lock: Login")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if password == config.AUTH_PASSWORD:
                st.session_state.authed = True
                return True
            st.sidebar.error("Incorrect password.")
    return False


# ---------------------------------------------------------------------------
# Upload flow (custom semester CSVs)
# ---------------------------------------------------------------------------

def detect_encoding(uploaded_file):
    raw = uploaded_file.read()
    uploaded_file.seek(0)
    return chardet.detect(raw)["encoding"]


def read_uploaded_csv(uploaded_file):
    if uploaded_file.size == 0:
        st.warning(f"{uploaded_file.name} is empty. Skipping.")
        return None
    try:
        return pd.read_csv(uploaded_file, encoding=detect_encoding(uploaded_file))
    except UnicodeDecodeError:
        try:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding="ISO-8859-1")
        except Exception as exc:
            st.error(f"Could not read {uploaded_file.name}: {exc}")
            return None
    except Exception as exc:
        st.error(f"Could not read {uploaded_file.name}: {exc}")
        return None


def ensure_required_columns(df):
    for field in REQUIRED_FIELDS:
        if field not in df.columns:
            if "attendance" in field.lower():
                df[field] = 50
            else:
                df[field] = ""
    return df


def run_upload_flow():
    st.sidebar.title(":wrench: Configuration")
    uploaded_files = st.sidebar.file_uploader(
        "Upload Semester CSV files (at least 1)", accept_multiple_files=True, type=["csv"]
    )
    if not uploaded_files:
        st.info("Upload semester files to get started.")
        return

    semesters = []
    combined = None
    book_columns = []

    for idx, file in enumerate(uploaded_files, start=1):
        sem = f"sem{idx}"
        df = read_uploaded_csv(file)
        if df is None:
            continue
        df.columns = df.columns.str.strip()
        df = ensure_required_columns(df)
        df = df.rename(columns={c: f"{c}_{sem}" for c in df.columns if c != "student id"})
        subject_cols = [
            c for c in df.columns
            if c.endswith(f"_{sem}")
            and "attendance" not in c
            and "interests" not in c
            and "student name" not in c
            and "borrowed book" not in c
        ]
        df[f"GPA_{sem}"] = df.apply(
            lambda r, subjects=subject_cols: calculate_gpa(r, subjects), axis=1
        )
        book_columns.extend([c for c in df.columns if "borrowed book" in c])
        semesters.append(sem)
        combined = df if combined is None else pd.merge(combined, df, on="student id", how="outer")

    if combined is None:
        st.error("No valid data was processed. Check your uploaded files.")
        return

    combined["GPA"] = combined[[f"GPA_{s}" for s in semesters]].mean(axis=1)
    combined["attendance"] = combined[[c for c in combined.columns if "attendance" in c]].mean(axis=1)
    combined["At_Risk"] = combined.apply(lambda r: is_at_risk(r["GPA"], r["attendance"]), axis=1)

    risk_features = combined[["GPA", "attendance"]].fillna(0)
    risk_target = combined.apply(lambda r: is_at_risk(r["GPA"], r["attendance"]), axis=1)
    _risk_model, risk_metrics = train_risk_classifier(risk_features, risk_target)

    if len(semesters) >= 2:
        gpa_features = combined[[f"GPA_{semesters[0]}", "attendance"]].fillna(0)
        gpa_target = combined[f"GPA_{semesters[-1]}"].fillna(0)
        gpa_model, gpa_metrics = train_gpa_predictor(gpa_features, gpa_target)
        combined["Predicted_GPA"] = gpa_model.predict(gpa_features)
    else:
        combined["Predicted_GPA"] = combined["GPA"]
        gpa_metrics = {"best_model": "n/a", "gpa_r2": None}

    combined["Group"], cluster_k = cluster_students(combined)

    book_counts = pd.Series(
        pd.concat([combined[c].dropna() for c in book_columns], ignore_index=True)
        .astype(str)
    ).value_counts().to_dict()

    def borrowed_for(row):
        return {row[c] for c in book_columns if isinstance(row.get(c), str) and row[c].strip()}

    combined["Recommended_Books"] = combined.apply(
        lambda r: recommend_books(book_counts, exclude=borrowed_for(r)), axis=1
    )

    st.subheader("Combined data preview")
    st.dataframe(combined.head(50))

    with st.expander("Model quality"):
        st.write(f"- Students loaded: **{len(combined)}**")
        st.write(f"- Risk-classifier accuracy: **{risk_metrics['risk_accuracy']}** "
                 f"(classes: {risk_metrics['risk_classes']})")
        st.write(f"- GPA-predictor ({gpa_metrics['best_model']}) R^2: "
                 f"**{gpa_metrics.get('gpa_r2')}**")

    st.subheader(":mag: Student lookup")
    student_id = st.selectbox("Select Student ID", sorted(combined["student id"].dropna().tolist()))
    student = combined[combined["student id"] == student_id].iloc[0]

    name = student.get("student name_sem1") or f"Student {student_id}"
    st.write(f"### {name}")
    col1, col2, col3 = st.columns(3)
    col1.metric("GPA", f"{student['GPA']:.2f}")
    col2.metric("Attendance", f"{student['attendance']:.1f}%")
    col3.metric("Predicted GPA", f"{student['Predicted_GPA']:.2f}")
    if student["At_Risk"]:
        st.error(":rotating_light: At risk of low performance.")
    else:
        st.success("On track.")

    st.plotly_chart(plot_gpa_trend_figure(
        [student[f"GPA_{s}"] for s in semesters],
        student["Predicted_GPA"],
        title=f"GPA Trends for {name}",
    ), use_container_width=True)

    st.write("### :books: Recommended Books")
    for book in student["Recommended_Books"]:
        st.write(f"- :open_book: {book}")

    st.write("### :handshake: Study Group")
    group = combined[combined["Group"] == student["Group"]].nlargest(3, "GPA")
    for _, member in group.iterrows():
        member_name = member.get("student name_sem1") or f"Student {member['student id']}"
        st.write(f"- **{member_name}** | GPA: {member['GPA']:.2f} | "
                 f"Attendance: {member['attendance']:.1f}%")

    st.download_button(
        ":arrow_down: Export results (CSV)",
        combined.to_csv(index=False).encode("utf-8-sig"),
        "axel_results.csv",
        "text/csv",
    )


# ---------------------------------------------------------------------------
# Built-in dataset flow
# ---------------------------------------------------------------------------

def run_builtin_flow():
    data, metrics, difficulty = load_engineered()

    st.subheader(":bar_chart: Enhanced Student Performance Dashboard")
    summary = st.columns(5)
    summary[0].metric("Students", metrics["students"])
    summary[1].metric("At risk", metrics["risk_classes"].get(True, 0))
    summary[2].metric("Clusters", metrics["cluster_k"])
    summary[3].metric("GPA model", metrics["best_model"])
    summary[4].metric("R^2", metrics["gpa_r2"])

    lookup_tab, analytics_tab, compare_tab = st.tabs(
        ["Student Lookup", "Cohort Analytics", "Compare Students"]
    )

    with lookup_tab:
        student_id = st.selectbox("Select Student ID", sorted(data["student id"].tolist()))
        student = data[data["student id"] == student_id].iloc[0]
        name = student.get("student name_sem1") or f"Student {student_id}"
        st.write(f"### {name}")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("GPA", f"{student['GPA']:.2f}")
        col2.metric("Attendance", f"{student['attendance']:.1f}%")
        col3.metric("Predicted GPA", f"{student['Predicted_GPA']:.2f}")
        col4.metric("GPA change", f"{student['GPA_delta']:+.2f}")

        if student["At_Risk"]:
            st.error(":rotating_light: At risk of low performance.")
        else:
            st.success("On track.")

        st.plotly_chart(plot_gpa_trend_figure(
            [student["GPA_sem1"], student["GPA_sem2"]],
            student["Predicted_GPA"],
            title=f"GPA Trends for {name}",
        ), use_container_width=True)

        book_col, group_col, prof_col = st.columns(3)
        with book_col:
            st.write("### :books: Recommended Books")
            for book in student["Recommended_Books"]:
                st.write(f"- :open_book: {book}")
        with group_col:
            st.write("### :handshake: Study Group")
            for member in _study_group_display(data, student):
                st.write(f"- {member}")
        with prof_col:
            st.write("### :mortar_board: Professor Help")
            for rec in student["Professor_Recommendations"] or ["None"]:
                st.write(f"- {rec}")

        st.download_button(
            ":page_facing_up: Download PDF report",
            build_pdf_report(student),
            file_name=f"axel_student_{student_id}.pdf",
            mime="application/pdf",
        )
        st.download_button(
            ":arrow_down: Export dataset (CSV)",
            data.to_csv(index=False).encode("utf-8-sig"),
            "axel_students.csv",
            "text/csv",
        )

    with analytics_tab:
        _render_analytics(data, difficulty, metrics)

    with compare_tab:
        _render_compare(data)


def _study_group_display(data, student):
    members = data[data["Group"] == student["Group"]].nlargest(3, "GPA")
    return [
        f"**{m.get('student name_sem1', m['student id'])}** | "
        f"GPA: {m['GPA']:.2f} | Attendance: {m['attendance']:.1f}%"
        for _, m in members.iterrows()
    ]


def _render_analytics(data, difficulty, metrics):
    st.write("### Cohort overview")
    st.plotly_chart(go.Figure(go.Histogram(x=data["GPA"], nbinsx=20)).update_layout(
        title="GPA distribution", template="plotly_white"
    ), use_container_width=True)

    st.plotly_chart(go.Figure(go.Histogram(x=data["attendance"], nbinsx=20)).update_layout(
        title="Attendance distribution", template="plotly_white"
    ), use_container_width=True)

    df = difficulty.sort_values("mean")
    st.plotly_chart(go.Figure(go.Bar(
        x=df["subject"], y=df["mean"],
        error_y=dict(type="data", array=df["std"], visible=True),
        marker_color="rgba(255,152,0,0.8)",
    )).update_layout(
        title="Class average per subject (+/- std)",
        template="plotly_white",
        xaxis_tickangle=-35,
    ), use_container_width=True)

    st.write("### Top 10 students")
    top10 = data.nlargest(10, "GPA")[
        ["student id", "student name_sem1", "GPA", "attendance"]
    ].reset_index(drop=True)
    st.dataframe(top10)


def _render_compare(data):
    st.write("### Compare students (pick 2-3)")
    ids = st.multiselect(
        "Students", sorted(data["student id"].tolist()), default=None
    )[:3]
    if len(ids) >= 2:
        rows = data[data["student id"].isin(ids)]
        st.dataframe(rows[["student id", "student name_sem1", "GPA", "attendance",
                           "Predicted_GPA", "At_Risk"]].reset_index(drop=True))

        fig = go.Figure()
        for _, row in rows.iterrows():
            fig.add_trace(go.Bar(
                x=["GPA", "Predicted GPA", "Attendance/10"],
                y=[row["GPA"], row["Predicted_GPA"], row["attendance"] / 10],
                name=row["student name_sem1"],
            ))
        fig.update_layout(title="Side-by-side comparison", template="plotly_white", barmode="group")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Select at least 2 students to compare.")


def main():
    st.set_page_config(page_title="AXEL Student Dashboard", page_icon=":bar_chart:", layout="wide")
    if not check_password():
        st.stop()

    mode = st.sidebar.radio("Data source", ["Built-in dataset", "Upload semester CSVs"])
    if mode == "Upload semester CSVs":
        run_upload_flow()
    else:
        run_builtin_flow()


if __name__ == "__main__":
    main()
