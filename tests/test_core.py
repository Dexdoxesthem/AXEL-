"""Tests for core.py.

Run with:  python -m pytest tests/ -v
Or directly: python tests/test_core.py
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core


def assert_close(actual, expected, tol=1e-6):
    assert abs(actual - expected) < tol, f"{actual} != {expected}"


# --- GPA -------------------------------------------------------------------

def test_calculate_gpa_average():
    row = pd.Series({"a": 50, "b": 60, "c": None})
    assert_close(core.calculate_gpa(row, ["a", "b", "c"]), 5.5)


def test_calculate_gpa_missing_subject_ignored():
    row = pd.Series({"a": 80})
    assert_close(core.calculate_gpa(row, ["a", "b"]), 8.0)


def test_calculate_gpa_no_subjects():
    row = pd.Series({})
    assert core.calculate_gpa(row, ["a"]) == 0.0


# --- Risk rule -------------------------------------------------------------

def test_is_at_risk_thresholds():
    assert core.is_at_risk(4.9, 90) is True
    assert core.is_at_risk(6.0, 54) is True
    assert core.is_at_risk(5.0, 55) is False
    assert core.is_at_risk(7.5, 80) is False


# --- Books ----------------------------------------------------------------

def test_recommend_books_excludes_borrowed():
    counts = {"A": 10, "B": 8, "C": 6, "D": 4}
    assert core.recommend_books(counts, exclude={"B"}) == ["A", "C", "D"]


def test_recommend_books_accepts_plain_dict():
    counts = {"A": 10, "B": 8, "C": 6}
    assert core.recommend_books(counts) == ["A", "B", "C"]


def test_borrowed_books_reads_columns():
    row = pd.Series({
        "borrowed book 1_sem1": "X",
        "borrowed book 2_sem1": None,
        "borrowed book 1_sem2": "Y",
        "borrowed book 2_sem2": "X",
    })
    assert core.borrowed_books(row) == {"X", "Y"}


# --- Professors -----------------------------------------------------------

def test_professor_recommendations_low_score():
    row = pd.Series({"accounting": 25, "management": 70})
    recs = core.get_professor_recommendations(row)
    assert len(recs) == 1
    assert "Dr. Emily Davis" in recs[0]


def test_professor_recommendations_none_when_high():
    row = pd.Series({"accounting": 90, "management": 85})
    assert core.get_professor_recommendations(row) == []


def test_professor_normalizes_typo_subject():
    row = pd.Series({"entrpreneurship development": 30})
    recs = core.get_professor_recommendations(row)
    assert len(recs) == 1
    assert "entrepreneurship development" in recs[0]


# --- Weakest subjects -----------------------------------------------------

def test_weakest_subjects_ordering():
    row = pd.Series({"accounting": 90, "management": 30, "economics": 50})
    assert core.weakest_subjects(row) == ["management", "economics", "accounting"]


# --- Dataset + models -----------------------------------------------------

def test_build_dataset_shape():
    _sem1, _sem2, combined = core.build_dataset()
    assert not combined.empty
    for col in ["GPA_sem1", "GPA_sem2", "GPA", "attendance"]:
        assert col in combined.columns
    assert combined["GPA"].between(0, 10).all()


def test_train_models_adds_features():
    _s1, _s2, combined = core.build_dataset()
    data, metrics, difficulty = core.train_models(combined)
    for col in ["Predicted_GPA", "At_Risk", "Group", "Recommended_Books",
                "Professor_Recommendations", "GPA_delta", "attendance_delta",
                "Improving", "Weakest_Subjects"]:
        assert col in data.columns
    for key in ["gpa_r2", "gpa_mae", "risk_accuracy", "cluster_k", "best_model"]:
        assert key in metrics
    assert 2 <= metrics["cluster_k"] <= 6
    assert data["At_Risk"].isin([True, False]).all()
    assert not difficulty.empty


def test_cluster_students_returns_labels_and_k():
    _s1, _s2, combined = core.build_dataset()
    labels, k = core.cluster_students(combined)
    assert len(labels) == len(combined)
    assert 2 <= k <= 6


def test_load_engineered_returns_payload():
    data, metrics, difficulty = core.load_engineered()
    assert "Predicted_GPA" in data.columns
    assert "gpa_r2" in metrics


# --- Charts ---------------------------------------------------------------

def test_plot_gpa_trend_figure_returns_figure():
    fig = core.plot_gpa_trend_figure([6.0, 7.2], 7.8)
    assert fig is not None


def test_plot_gpa_trend_returns_figure():
    fig = core.plot_gpa_trend([6.0, 7.2], 7.8)
    assert fig is not None


def test_plot_gpa_trend_base64():
    encoded = core.plot_gpa_trend_base64([6.0, 7.2], 7.8)
    assert isinstance(encoded, str) and len(encoded) > 100


def test_build_pdf_report():
    _s1, _s2, combined = core.build_dataset()
    data, _metrics, _diff = core.train_models(combined)
    pdf = core.build_pdf_report(data.iloc[0])
    assert pdf[:4] == b"%PDF"


# --- Resources ------------------------------------------------------------

def test_resource_path_absolute():
    path = core.resource_path("sem1 data set.csv")
    assert os.path.isabs(path)


def _run_all():
    tests = [obj for name, obj in list(globals().items())
             if name.startswith("test_") and callable(obj)]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL  {test.__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} tests passed")
    return failures


if __name__ == "__main__":
    sys.exit(1 if _run_all() else 0)
