"""Data-integrity checks against the real semester CSVs."""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core


def test_no_duplicate_student_ids():
    _s1, _s2, combined = core.build_dataset()
    assert not combined["student id"].duplicated().any()


def test_marks_within_range():
    _s1, _s2, combined = core.build_dataset()
    for column in core.SUBJECT_BY_COLUMN:
        scores = pd.to_numeric(combined[column], errors="coerce")
        assert scores.min() >= 0, f"{column} has marks below 0"
        assert scores.max() <= 100, f"{column} has marks above 100"


def test_attendance_within_range():
    _s1, _s2, combined = core.build_dataset()
    for column in ["attendance_sem1", "attendance_sem2", "attendance"]:
        scores = pd.to_numeric(combined[column], errors="coerce")
        assert scores.min() >= 0
        assert scores.max() <= 100


def test_gpa_within_range():
    _s1, _s2, combined = core.build_dataset()
    assert combined["GPA"].between(0, 10).all()
    assert combined["GPA_sem1"].between(0, 10).all()
    assert combined["GPA_sem2"].between(0, 10).all()


def test_subject_difficulty_covers_all_subjects():
    _s1, _s2, combined = core.build_dataset()
    _data, _metrics, difficulty = core.train_models(combined)
    assert len(difficulty) == len(core.SUBJECT_BY_COLUMN)


def test_combined_has_expected_columns():
    _s1, _s2, combined = core.build_dataset()
    expected = {"student id", "student name_sem1", "attendance_sem1", "attendance_sem2"}
    assert expected.issubset(set(combined.columns))
