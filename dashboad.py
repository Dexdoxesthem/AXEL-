"""AXEL Flask web dashboard (also packaged as dashboad.exe via dashboad.spec).

Run:  python dashboad.py   ->  http://localhost:5000
"""

import io
import os
from functools import wraps

import plotly.graph_objects as go
import plotly.io as pio
from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

import config
from core import (
    build_pdf_report,
    load_engineered,
    plot_gpa_trend_figure,
    study_group,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "axel-demo-secret-change-me")

# Data and models are loaded once at startup (cached to disk on first run).
combined_data, metrics, subject_difficulty = load_engineered()
STUDENT_IDS = sorted(combined_data["student id"].tolist())


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("authed"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == config.AUTH_PASSWORD:
            session["authed"] = True
            return redirect(url_for("index"))
        error = "Incorrect password."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("authed", None)
    return redirect(url_for("index"))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_student(student_id):
    match = combined_data[combined_data["student id"] == student_id]
    return None if match.empty else match.iloc[0]


def figure_html(figure, include_plotlyjs="cdn"):
    """Render a plotly figure as a standalone HTML fragment for templates."""
    return pio.to_html(figure, full_html=False, include_plotlyjs=include_plotlyjs)


def analytics_figures():
    """Build the plotly figures used by the cohort analytics page."""
    gpa_hist = go.Figure(go.Histogram(x=combined_data["GPA"], nbinsx=20))
    gpa_hist.update_layout(title="GPA distribution", template="plotly_white")

    attendance_hist = go.Figure(go.Histogram(x=combined_data["attendance"], nbinsx=20))
    attendance_hist.update_layout(title="Attendance distribution", template="plotly_white")

    difficulty = subject_difficulty.sort_values("mean")
    subject_bar = go.Figure(go.Bar(
        x=difficulty["subject"],
        y=difficulty["mean"],
        marker_color="rgba(255,152,0,0.8)",
        error_y=dict(type="data", array=difficulty["std"], visible=True),
    ))
    subject_bar.update_layout(
        title="Class average per subject (+/- std)",
        template="plotly_white",
        xaxis_tickangle=-35,
    )

    at_risk_counts = combined_data["At_Risk"].value_counts().reindex([False, True], fill_value=0)
    donut = go.Figure(go.Pie(
        labels=["On track", "At risk"],
        values=list(at_risk_counts.values),
        hole=0.5,
        marker=dict(colors=["#43a047", "#e53935"]),
    ))
    donut.update_layout(title="At-risk vs on-track students", template="plotly_white")

    top10 = combined_data.nlargest(10, "GPA")[
        ["student id", "student name_sem1", "GPA", "attendance"]
    ].reset_index(drop=True)

    return gpa_hist, attendance_hist, subject_bar, donut, top10


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template(
        "index.html",
        student_ids=STUDENT_IDS,
        metrics=metrics,
        authed=session.get("authed", False),
    )


@app.route("/student", methods=["POST"])
@login_required
def student_dashboard():
    raw = request.form.get("student_id", "").strip()
    try:
        student_id = int(raw)
    except ValueError:
        abort(400, description="Invalid Student ID!")

    student = find_student(student_id)
    if student is None:
        abort(404, description="Student not found!")

    chart_html = figure_html(
        plot_gpa_trend_figure(
            [student["GPA_sem1"], student["GPA_sem2"]],
            student["Predicted_GPA"],
            title=f"GPA Trends for {student['student name_sem1']}",
        ),
        include_plotlyjs=True,
    )

    return render_template(
        "student_dashboard.html",
        student_id=student_id,
        student_name=student["student name_sem1"],
        gpa=round(student["GPA"], 2),
        attendance=round(student["attendance"], 1),
        at_risk="Yes" if student["At_Risk"] else "No",
        predicted_gpa=round(student["Predicted_GPA"], 2),
        gpa_delta=round(student["GPA_delta"], 2),
        improving="Yes" if student["Improving"] else "No",
        recommended_books=student["Recommended_Books"],
        study_group=study_group(combined_data, student),
        professor_recommendations=student["Professor_Recommendations"],
        weakest_subjects=student["Weakest_Subjects"],
        chart_html=chart_html,
    )


@app.route("/analytics")
@login_required
def analytics():
    gpa_hist, attendance_hist, subject_bar, donut, top10 = analytics_figures()
    return render_template(
        "analytics.html",
        metrics=metrics,
        gpa_hist_html=figure_html(gpa_hist, include_plotlyjs=True),
        attendance_hist_html=figure_html(attendance_hist),
        subject_bar_html=figure_html(subject_bar),
        donut_html=figure_html(donut),
        top10=top10.to_html(classes="table table-striped", index=False),
    )


@app.route("/compare", methods=["GET", "POST"])
@login_required
def compare():
    rows = []
    chart_html = None
    selected = request.form.getlist("sids") if request.method == "POST" else []

    ids = []
    for raw in selected:
        try:
            ids.append(int(raw))
        except ValueError:
            continue
    ids = list(dict.fromkeys(ids))[:3]

    for student_id in ids:
        student = find_student(student_id)
        if student is not None:
            rows.append({
                "id": int(student["student id"]),
                "name": student["student name_sem1"],
                "gpa": round(student["GPA"], 2),
                "attendance": round(student["attendance"], 1),
                "predicted": round(student["Predicted_GPA"], 2),
                "at_risk": bool(student["At_Risk"]),
            })

    if len(rows) >= 2:
        fig = go.Figure()
        for row in rows:
            student = find_student(row["id"])
            fig.add_trace(go.Bar(
                x=["GPA", "Predicted GPA", "Attendance/10"],
                y=[student["GPA"], student["Predicted_GPA"], student["attendance"] / 10],
                name=row["name"],
            ))
        fig.update_layout(
            title="Side-by-side comparison",
            template="plotly_white",
            barmode="group",
        )
        chart_html = figure_html(fig, include_plotlyjs=True)

    return render_template(
        "compare.html",
        student_ids=STUDENT_IDS,
        rows=rows,
        chart_html=chart_html,
    )


@app.route("/export")
@login_required
def export_csv():
    csv_bytes = combined_data.to_csv(index=False).encode("utf-8-sig")
    return send_file(
        io.BytesIO(csv_bytes),
        mimetype="text/csv",
        as_attachment=True,
        download_name="axel_students.csv",
    )


@app.route("/report/<int:student_id>")
@login_required
def student_report(student_id):
    student = find_student(student_id)
    if student is None:
        abort(404, description="Student not found!")
    pdf_bytes = build_pdf_report(student)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"axel_student_{student_id}.pdf",
    )


@app.route("/api/student/<int:student_id>")
@login_required
def api_student(student_id):
    student = find_student(student_id)
    if student is None:
        return jsonify({"error": "Student not found!"}), 404
    return jsonify({
        "student_id": int(student["student id"]),
        "name": student["student name_sem1"],
        "gpa": round(float(student["GPA"]), 2),
        "attendance": round(float(student["attendance"]), 1),
        "at_risk": bool(student["At_Risk"]),
        "predicted_gpa": round(float(student["Predicted_GPA"]), 2),
        "group": int(student["Group"]),
        "recommended_books": student["Recommended_Books"],
        "professor_recommendations": student["Professor_Recommendations"],
    })


if __name__ == "__main__":
    app.run(host=config.DEFAULT_HOST, port=config.FLASK_PORT, debug=config.DEBUG)
