"""Regenerate the semester CSVs with varied, realistic marks.

The shipped CSVs were identical between semesters (same marks, same
attendance), which flattened every trend: GPA_delta == 0, no Improving
students, and a perfect-but-meaningless GPA model (R2 1.0, MAE 0.0).

This script rebuilds the two CSVs from a latent-factor model so the data
shows real change and patterns:

- each student has a hidden ability driving every subject,
- subjects have their own difficulty offsets,
- each student has a trajectory (improving / declining) between semesters,
- attendance is correlated with ability but drifts per semester.

Structure (columns, ids, names, interests, borrowed books) is preserved.

Run from the project root:

    env\\Scripts\\python.exe scripts\\generate_demo_data.py

Then refresh the frontend snapshot:

    env\\Scripts\\python.exe scripts\\export_json.py
"""

import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import core  # noqa: E402

SEM1_PATH = os.path.join(ROOT, "sem1 data set.csv")
SEM2_PATH = os.path.join(ROOT, "sem2 data set.csv")

SEED = 2026

# ---------------------------------------------------------------------------
# Generation parameters
# ---------------------------------------------------------------------------

BASE = 60.0                 # average percentage mark
ABILITY_SCALE = 15.0        # how strongly the latent ability moves marks
SUBJECT_NOISE = 6.0         # per student-subject wobble
SEMESTER_NOISE = 4.0        # extra per-semester wobble
TRAJECTORY_SCALE = 7.0      # mark points shifted between semesters per sd

# Harder subjects pull the class mean down (shown in the subject chart).
SUBJECT_DIFFICULTY = {
    "accounting": -2.0,
    "management": 1.0,
    "entrpreneurship development": 4.0,
    "english": 0.0,
    "constitutional studies": -3.0,
    "cost accounting": -2.0,
    "hr management": 2.0,
    "economics": 5.0,
    "english2": -1.0,
    "life skill education": 3.0,
}

# Attendance model: ability pulls it up, trajectory drifts it.
ATT_BASE = 62.0
ATT_ABILITY = 11.0
ATT_NOISE = 9.0
ATT_TRAJECTORY = 6.0

MARK_MIN, MARK_MAX = 18.0, 98.0
ATT_MIN, ATT_MAX = 15.0, 100.0


def clip_round(values, low, high, decimals=1):
    return np.round(np.clip(values, low, high), decimals)


def generate(seed=SEED):
    """Return (sem1_frame, sem2_frame) with fresh marks + attendance."""
    rng = np.random.default_rng(seed)

    sem1 = pd.read_csv(SEM1_PATH, encoding="ISO-8859-1")
    sem2 = pd.read_csv(SEM2_PATH, encoding="ISO-8859-1")
    sem1.columns = sem1.columns.str.strip()
    sem2.columns = sem2.columns.str.strip()

    n = len(sem1)
    assert n == len(sem2), "semester CSVs have different row counts"

    # Shared latent factors.
    ability = rng.normal(0.0, 1.0, n)          # student strength
    trajectory = rng.normal(0.0, 1.0, n)       # sem1 -> sem2 shift
    attendance = ATT_BASE + ability * ATT_ABILITY + rng.normal(0.0, ATT_NOISE, n)

    def marks_for(subjects, semester_shift):
        marks = pd.DataFrame(index=sem1.index)
        for subject in subjects:
            diff = SUBJECT_DIFFICULTY.get(subject, 0.0)
            noise = rng.normal(0.0, SUBJECT_NOISE, n) + rng.normal(0.0, SEMESTER_NOISE, n)
            raw = (
                BASE
                + ability * ABILITY_SCALE
                + diff
                + semester_shift
                + noise
            )
            marks[subject] = clip_round(raw, MARK_MIN, MARK_MAX, decimals=2)
        return marks

    # Fresh independent noise for the two semesters.
    sem1_marks = marks_for(core.SUBJECTS_SEM1, 0.0)
    sem2_marks = marks_for(core.SUBJECTS_SEM2, trajectory * TRAJECTORY_SCALE)

    sem1_attendance = clip_round(
        attendance + rng.normal(0.0, ATT_NOISE, n), ATT_MIN, ATT_MAX
    )
    sem2_attendance = clip_round(
        attendance + trajectory * ATT_TRAJECTORY + rng.normal(0.0, ATT_NOISE, n),
        ATT_MIN,
        ATT_MAX,
    )
    for df, marks, att in (
        (sem1, sem1_marks, sem1_attendance),
        (sem2, sem2_marks, sem2_attendance),
    ):
        for column in marks.columns:
            df[column] = marks[column].astype(float)
        df["attendence"] = att.astype(float)

    return sem1, sem2


def main():
    sem1, sem2 = generate()

    sem1.to_csv(SEM1_PATH, index=False, encoding="ISO-8859-1")
    sem2.to_csv(SEM2_PATH, index=False, encoding="ISO-8859-1")

    print(f"Wrote {SEM1_PATH} ({len(sem1)} students)")
    print(f"Wrote {SEM2_PATH} ({len(sem2)} students)")

    # Quick sanity report through the real pipeline.
    data, metrics, difficulty = core.load_engineered()
    improving = int(data["Improving"].sum())
    delta_std = float(data["GPA_delta"].std())
    at_risk = int(data["At_Risk"].sum())
    print(f"GPA model {metrics['best_model']}: R2={metrics['gpa_r2']} "
          f"(+/-{metrics['gpa_r2_std']}) MAE={metrics['gpa_mae']}")
    print(f"risk accuracy: {metrics['risk_accuracy']}  |  at risk: "
          f"{at_risk}/{len(data)}")
    print(f"improving: {improving}/{len(data)}  |  GPA_delta std: {delta_std:.3f}  "
          f"|  clusters: k={metrics['cluster_k']}")


if __name__ == "__main__":
    main()
