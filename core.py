"""AXEL core: shared data loading, feature engineering and machine-learning helpers.

Every dashboard flavour (Streamlit, Flask, Dash) uses this module so the data
pipeline and model logic live in exactly one place. Pipelines are cached to
disk (see ``load_engineered``) so apps start fast and do not retrain on every
launch.
"""

import base64
import io
import os
import sys
from collections import Counter

import matplotlib

matplotlib.use("Agg")  # headless-safe: works in servers and PyInstaller exes
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.model_selection import KFold, cross_val_score
from sklearn.preprocessing import StandardScaler

from config import (
    CV_FOLDS,
    GPA_LOW_THRESHOLD,
    KMEANS_MAX_K,
    KMEANS_MIN_K,
    RANDOM_STATE,
    RISK_ATTENDANCE_THRESHOLD,
    RISK_GPA_THRESHOLD,
)
from utils import cache_path, data_fingerprint, setup_logging

# ---------------------------------------------------------------------------
# Resources and metadata
# ---------------------------------------------------------------------------

def resource_path(relative_path):
    """Resolve ``relative_path`` against the app root (PyInstaller aware)."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


SEM1_PATH = resource_path("sem1 data set.csv")
SEM2_PATH = resource_path("sem2 data set.csv")

SUBJECTS_SEM1 = [
    "accounting",
    "management",
    "entrpreneurship development",
    "english",
    "constitutional studies",
]
SUBJECTS_SEM2 = [
    "cost accounting",
    "hr management",
    "economics",
    "english2",
    "life skill education",
]

PROFESSORS = {
    "accounting": ("Dr. Emily Davis", "emily.davis@university.edu"),
    "management": ("Dr. Daniel Thompson", "daniel.thompson@university.edu"),
    "entrepreneurship development": ("Dr. Karen White", "karen.white@university.edu"),
    "english": ("Dr. Michael Clark", "michael.clark@university.edu"),
    "constitutional studies": ("Dr. Linda Harris", "linda.harris@university.edu"),
    "cost accounting": ("Dr. Andrew Moore", "andrew.moore@university.edu"),
    "hr management": ("Dr. Patricia Wilson", "patricia.wilson@university.edu"),
    "economics": ("Dr. Sarah Johnson", "sarah.johnson@university.edu"),
    "english2": ("Dr. Christopher Taylor", "christopher.taylor@university.edu"),
    "life skill education": ("Dr. James Martin", "james.martin@university.edu"),
}

BOOK_COLUMNS = [
    "borrowed book 1_sem1",
    "borrowed book 2_sem1",
    "borrowed book 1_sem2",
    "borrowed book 2_sem2",
]

# Maps merged subject columns back to their canonical base name, and to the
# semester they belong to. Subject columns are *not* suffixed by the merge
# (only shared columns are), so the column name equals the subject name.
SUBJECT_BY_COLUMN = {}
SUBJECT_SEMESTER = {}
for _subject in SUBJECTS_SEM1:
    SUBJECT_BY_COLUMN[_subject] = _subject
    SUBJECT_SEMESTER[_subject] = "sem1"
for _subject in SUBJECTS_SEM2:
    SUBJECT_BY_COLUMN[_subject] = _subject
    SUBJECT_SEMESTER[_subject] = "sem2"


# ---------------------------------------------------------------------------
# Data loading and GPA
# ---------------------------------------------------------------------------

def load_data(sem1_path=None, sem2_path=None):
    """Load, clean and normalise the two semester CSVs."""
    sem1 = pd.read_csv(sem1_path or SEM1_PATH, encoding="ISO-8859-1")
    sem2 = pd.read_csv(sem2_path or SEM2_PATH, encoding="ISO-8859-1")
    for df in (sem1, sem2):
        df.columns = df.columns.str.strip()
        df.rename(columns={"attendence": "attendance"}, inplace=True)
    return sem1, sem2


def merge_data(sem1, sem2):
    """Merge semester frames on student id, suffixing their columns."""
    combined = pd.merge(sem1, sem2, on="student id", suffixes=("_sem1", "_sem2"))
    combined.columns = combined.columns.str.strip()
    return combined


def calculate_gpa(row, subjects):
    """GPA on a 10-point scale computed from percentage subject marks."""
    available = [s for s in subjects if s in row.index]
    if not available:
        return 0.0
    scores = pd.to_numeric(row[available], errors="coerce").dropna()
    if scores.empty:
        return 0.0
    return float((scores * 10 / 100).mean())


def build_dataset(sem1_path=None, sem2_path=None):
    """Load, merge and compute semester GPAs. Returns (sem1, sem2, combined)."""
    sem1, sem2 = load_data(sem1_path, sem2_path)
    combined = merge_data(sem1, sem2)
    combined["GPA_sem1"] = sem1.apply(lambda r: calculate_gpa(r, SUBJECTS_SEM1), axis=1)
    combined["GPA_sem2"] = sem2.apply(lambda r: calculate_gpa(r, SUBJECTS_SEM2), axis=1)
    # Overall GPA is the average of both semesters.
    combined["GPA"] = combined[["GPA_sem1", "GPA_sem2"]].mean(axis=1)
    combined["attendance"] = combined[["attendance_sem1", "attendance_sem2"]].mean(axis=1)
    return sem1, sem2, combined


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

def is_at_risk(gpa, attendance):
    """Transparent, rule-based risk check shared by every app."""
    return gpa < RISK_GPA_THRESHOLD or attendance < RISK_ATTENDANCE_THRESHOLD


def _gpa_candidates():
    """Candidate regressors for predicting the next-semester GPA."""
    from sklearn.ensemble import RandomForestRegressor

    return {
        "linear": LinearRegression(),
        "ridge": Ridge(alpha=1.0),
        "random_forest": RandomForestRegressor(
            n_estimators=100, random_state=RANDOM_STATE, n_jobs=-1
        ),
    }


def build_gpa_features(data):
    """Feature frame for GPA prediction: sem1 subject marks + attendance + interests."""
    features = pd.DataFrame(index=data.index)
    for subject in SUBJECTS_SEM1:
        features[subject] = pd.to_numeric(data[subject], errors="coerce").fillna(0)
    features["attendance_sem1"] = pd.to_numeric(data["attendance_sem1"], errors="coerce").fillna(0)
    interests = data.get("interests_sem1", pd.Series("", index=data.index)).fillna("").astype(str)
    dummies = pd.get_dummies(interests, prefix="interest").astype(float)
    return pd.concat([features, dummies], axis=1)


def train_gpa_predictor(features, target, folds=CV_FOLDS):
    """Fit the best candidate GPA regressor via K-fold CV.

    Returns (fitted_model, metrics) with ``gpa_r2``, ``gpa_mae`` (and their
    cross-fold standard deviations) plus the winning model name.
    """
    kfold = KFold(n_splits=folds, shuffle=True, random_state=RANDOM_STATE)
    results = []
    for name, model in _gpa_candidates().items():
        r2 = cross_val_score(model, features, target, cv=kfold, scoring="r2")
        mae = -cross_val_score(
            model, features, target, cv=kfold, scoring="neg_mean_absolute_error"
        )
        results.append((float(r2.mean()), name, model, r2, mae))

    results.sort(key=lambda item: item[0], reverse=True)
    _best_r2, best_name, best_model, r2_scores, mae_scores = results[0]
    best_model.fit(features, target)

    metrics = {
        "best_model": best_name,
        "gpa_r2": round(float(r2_scores.mean()), 3),
        "gpa_r2_std": round(float(r2_scores.std()), 3),
        "gpa_mae": round(float(mae_scores.mean()), 3),
        "gpa_mae_std": round(float(mae_scores.std()), 3),
    }
    return best_model, metrics


def train_risk_classifier(features, target, folds=CV_FOLDS):
    """Fit + evaluate a balanced risk classifier via K-fold CV.

    Returns (model, metrics) with ``risk_accuracy`` (+std) and class counts.
    ``model`` is None when there is no class diversity to learn from.
    """
    class_counts = target.value_counts().to_dict()
    if target.nunique() < 2:
        return None, {"risk_accuracy": None, "risk_accuracy_std": None, "risk_classes": class_counts}

    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    kfold = KFold(n_splits=folds, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_val_score(model, features, target, cv=kfold, scoring="accuracy")
    model.fit(features, target)

    metrics = {
        "risk_accuracy": round(float(scores.mean()), 3),
        "risk_accuracy_std": round(float(scores.std()), 3),
        "risk_classes": class_counts,
    }
    return model, metrics


def cluster_students(data, min_k=KMEANS_MIN_K, max_k=KMEANS_MAX_K):
    """Cluster students by GPA + attendance; choose K via silhouette score.

    Returns (labels, chosen_k).
    """
    from sklearn.metrics import silhouette_score

    scaled = StandardScaler().fit_transform(data[["GPA", "attendance"]].fillna(0))
    n = len(scaled)
    best_k, best_score, best_labels = 3, -1.0, None
    for k in range(max(2, min_k), min(max_k, n - 1) + 1):
        labels = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10).fit_predict(scaled)
        score = silhouette_score(scaled, labels)
        if score > best_score:
            best_k, best_score, best_labels = k, score, labels
    if best_labels is None:
        best_labels = KMeans(n_clusters=2, random_state=RANDOM_STATE, n_init=10).fit_predict(scaled)
        best_k = 2
    return best_labels, best_k


def train_models(combined):
    """Add every derived feature/column. Returns (enriched_frame, metrics, subject_difficulty)."""
    data = combined.copy()

    # Predict the *next* semester GPA from the full sem1 feature set.
    gpa_features = build_gpa_features(data)
    gpa_target = data["GPA_sem2"].fillna(0)
    gpa_model, gpa_metrics = train_gpa_predictor(gpa_features, gpa_target)
    data["Predicted_GPA"] = gpa_model.predict(gpa_features)

    # Semester trend columns.
    data["GPA_delta"] = data["GPA_sem2"] - data["GPA_sem1"]
    data["attendance_delta"] = data["attendance_sem2"] - data["attendance_sem1"]
    data["Improving"] = data["GPA_delta"] > 0

    # Transparent risk rule for each student.
    data["At_Risk"] = data.apply(lambda r: is_at_risk(r["GPA"], r["attendance"]), axis=1)

    # Risk classifier evaluated honestly via CV (not a black box over the rule).
    risk_target = data.apply(lambda r: is_at_risk(r["GPA_sem2"], r["attendance_sem2"]), axis=1)
    _risk_model, risk_metrics = train_risk_classifier(gpa_features, risk_target)

    # Study-group clustering with automatic K.
    data["Group"], cluster_k = cluster_students(data)

    # Weakest subjects (across both semesters).
    data["Weakest_Subjects"] = data.apply(weakest_subjects, axis=1)

    # Personalised book recommendations (top popular books not yet borrowed).
    book_counts = Counter()
    for col in BOOK_COLUMNS:
        book_counts.update(data[col].dropna().astype(str).tolist())
    data["Recommended_Books"] = data.apply(
        lambda r: recommend_books(book_counts, exclude=borrowed_books(r)), axis=1
    )

    data["Professor_Recommendations"] = data.apply(get_professor_recommendations, axis=1)

    subject_difficulty = build_subject_difficulty(data)

    metrics = {
        "students": int(len(data)),
        "cluster_k": int(cluster_k),
        "prediction_features": "5 sem1 subjects + attendance + interests",
        **gpa_metrics,
        **risk_metrics,
    }
    return data, metrics, subject_difficulty


def load_engineered(sem1_path=None, sem2_path=None):
    """Return ``(data, metrics, subject_difficulty)``, cached to disk by fingerprint."""
    import joblib

    log = setup_logging()
    _sem1, _sem2, combined = build_dataset(sem1_path, sem2_path)
    fingerprint = data_fingerprint(combined)
    path = cache_path("engineered", fingerprint)
    if path.exists():
        log.info("Loading cached pipeline (fingerprint=%s)", fingerprint)
        return joblib.load(path)
    log.info("Training pipeline (fingerprint=%s)", fingerprint)
    payload = train_models(combined)
    joblib.dump(payload, path)
    return payload


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

def borrowed_books(row):
    """Set of book titles already borrowed by a student."""
    books = set()
    for col in BOOK_COLUMNS:
        value = row.get(col)
        if isinstance(value, str) and value.strip():
            books.add(value.strip())
    return books


def recommend_books(book_counts, exclude=None, limit=3):
    """Top ``limit`` popular books, skipping any in ``exclude``."""
    exclude = exclude or set()
    counts = book_counts if isinstance(book_counts, Counter) else Counter(book_counts)
    return [book for book, _ in counts.most_common() if book not in exclude][:limit]


def _clean_subject(base):
    """Normalise the historic CSV typo to the canonical subject name."""
    return base.replace("entrpreneurship development", "entrepreneurship development")


def get_professor_recommendations(row):
    """Suggest a professor for each subject the student scores below threshold."""
    recommendations = []
    for column, base in SUBJECT_BY_COLUMN.items():
        if column not in row.index:
            continue
        score = pd.to_numeric(row.get(column), errors="coerce")
        if pd.isna(score) or score >= GPA_LOW_THRESHOLD:
            continue
        professor = PROFESSORS.get(_clean_subject(base))
        if professor:
            recommendations.append(f"{_clean_subject(base)}: {professor[0]} | Email: {professor[1]}")
    return recommendations[:3]


def weakest_subjects(row, limit=3):
    """The ``limit`` lowest-scoring subjects for a student, ordered worst-first."""
    scored = []
    for column, base in SUBJECT_BY_COLUMN.items():
        if column not in row.index:
            continue
        score = pd.to_numeric(row.get(column), errors="coerce")
        if pd.isna(score):
            continue
        scored.append((_clean_subject(base), float(score)))
    scored.sort(key=lambda item: item[1])
    return [name for name, _ in scored[:limit]]


def build_subject_difficulty(data):
    """Class-level mean/std/min/max per subject for cohort analytics."""
    rows = []
    for column, base in SUBJECT_BY_COLUMN.items():
        scores = pd.to_numeric(data[column], errors="coerce").dropna()
        if scores.empty:
            continue
        rows.append({
            "subject": _clean_subject(base),
            "semester": SUBJECT_SEMESTER[base],
            "mean": round(float(scores.mean()), 2),
            "std": round(float(scores.std()), 2),
            "min": round(float(scores.min()), 2),
            "max": round(float(scores.max()), 2),
        })
    return pd.DataFrame(rows)


def study_group(combined, student, n=3):
    """Top ``n`` students (by GPA) in the same study cluster as ``student``."""
    members = combined[combined["Group"] == student["Group"]].nlargest(n, "GPA")
    return members.to_dict(orient="records")


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

def plot_gpa_trend_figure(actual_gpas, predicted_gpa, labels=None, title="GPA Trends"):
    """Interactive Plotly figure of actual + predicted GPA."""
    import plotly.graph_objects as go

    actual = [float(x) for x in actual_gpas]
    n = len(actual)
    labels = labels or [f"Semester {i + 1}" for i in range(n)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(n)),
        y=actual,
        mode="lines+markers+text",
        name="Actual GPA",
        text=[f"{v:.2f}" for v in actual],
        textposition="top center",
        line=dict(color="#1f77b4", width=2),
    ))
    xs = [n - 1, n, n + 1]
    values = [actual[-1], predicted_gpa * 0.9, predicted_gpa]
    fig.add_trace(go.Scatter(
        x=xs,
        y=values,
        mode="lines+markers+text",
        name="Predicted GPA",
        text=[f"{v:.2f}" for v in values],
        textposition="top center",
        line=dict(color="#ff7f0e", width=2, dash="dash"),
    ))
    all_labels = labels + ["Predicted S+1", "Predicted S+2"]
    fig.update_xaxes(tickvals=list(range(len(all_labels))), ticktext=all_labels)
    fig.update_layout(
        title=title,
        xaxis_title="Semesters",
        yaxis_title="GPA",
        template="plotly_white",
        margin=dict(l=40, r=20, t=60, b=40),
    )
    return fig


def plot_gpa_trend(actual_gpas, predicted_gpa, labels=None, title="GPA Trends"):
    """Matplotlib figure of actual + predicted GPA (used for PDF reports)."""
    actual = [float(x) for x in actual_gpas]
    n = len(actual)
    labels = labels or [f"Semester {i + 1}" for i in range(n)]

    fig, ax = plt.subplots(figsize=(10, 6))
    xs_actual = list(range(n))
    xs_proj = [n - 1, n, n + 1]
    values_proj = [actual[-1], predicted_gpa * 0.9, predicted_gpa]

    ax.plot(xs_actual, actual, marker="o", label="Actual GPA", color="#1f77b4", linewidth=2)
    ax.plot(xs_proj, values_proj, marker="o", label="Predicted GPA",
            color="#ff7f0e", linewidth=2, linestyle="--")

    all_labels = labels + ["Predicted S+1", "Predicted S+2"]
    ax.set_xticks(range(len(all_labels)))
    ax.set_xticklabels(all_labels)
    for i, value in enumerate(actual):
        ax.text(i, value, f"{value:.2f}", fontsize=10, ha="center", va="bottom")
    for x, value in zip(xs_proj, values_proj, strict=True):
        ax.text(x, value, f"{value:.2f}", fontsize=10, ha="center", va="bottom")

    ax.set_title(title, fontsize=16)
    ax.set_xlabel("Semesters", fontsize=12)
    ax.set_ylabel("GPA", fontsize=12)
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    return fig


def plot_gpa_trend_base64(actual_gpas, predicted_gpa, labels=None, title="GPA Trends"):
    """Same matplotlib chart, encoded as a base64 PNG for web embedding."""
    fig = plot_gpa_trend(actual_gpas, predicted_gpa, labels=labels, title=title)
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def build_pdf_report(student, output_path=None):
    """Render a one-page PDF summary for a student.

    Returns the report bytes (or writes to ``output_path`` if provided).
    """
    from matplotlib.backends.backend_pdf import PdfPages

    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        fig, ax = plt.subplots(figsize=(8.27, 11.69))  # A4 portrait
        ax.axis("off")
        name = student.get("student name_sem1", f"Student {student['student id']}")
        lines = [
            "AXEL - Student Performance Report",
            "=" * 44,
            "",
            f"Student ID: {student['student id']}",
            f"Name: {name}",
            f"GPA: {student['GPA']:.2f} / 10",
            f"Attendance: {student['attendance']:.1f}%",
            f"Predicted GPA: {student['Predicted_GPA']:.2f}",
            f"Status: {'AT RISK' if student['At_Risk'] else 'On track'}",
            f"Study group: {student['Group']}",
            "",
            "Recommended books:",
        ]
        lines += [f"  - {book}" for book in student["Recommended_Books"]]
        lines += ["", "Professor recommendations:"]
        lines += [f"  - {rec}" for rec in student["Professor_Recommendations"]] or ["  - None"]
        lines += ["", "Weakest subjects:", ]
        lines += [f"  - {subject}" for subject in student["Weakest_Subjects"]] or ["  - None"]
        ax.text(0.02, 0.98, "\n".join(lines), va="top", ha="left",
                fontsize=10, family="monospace", transform=ax.transAxes)
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)
    data = buffer.getvalue()
    if output_path:
        with open(output_path, "wb") as handle:
            handle.write(data)
    return data
