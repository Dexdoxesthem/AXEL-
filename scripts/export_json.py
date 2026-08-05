"""Export the engineered pipeline to JSON for the Next.js frontend.

Run from the project root:

    env\\Scripts\\python.exe scripts\\export_json.py

Writes frontend/data/engineered.json with metrics, per-student records and
the class-level subject difficulty table. The frontend is fully offline once
this file exists.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import core  # noqa: E402


def _student_record(data, row, study_group):
    """One flat JSON-friendly record per student."""
    return {
        "id": int(row["student id"]),
        "name": str(row.get("student name_sem1", f"Student {row['student id']}")),
        "gpa_sem1": round(float(row["GPA_sem1"]), 2),
        "gpa_sem2": round(float(row["GPA_sem2"]), 2),
        "gpa": round(float(row["GPA"]), 2),
        "attendance": round(float(row["attendance"]), 1),
        "predicted_gpa": round(float(row["Predicted_GPA"]), 2),
        "gpa_delta": round(float(row["GPA_delta"]), 2),
        "attendance_delta": round(float(row["attendance_delta"]), 1),
        "improving": bool(row["Improving"]),
        "at_risk": bool(row["At_Risk"]),
        "group": int(row["Group"]),
        "recommended_books": list(row["Recommended_Books"]),
        "professors": list(row["Professor_Recommendations"]),
        "weakest_subjects": list(row["Weakest_Subjects"]),
        "study_group": [
            {
                "id": int(member["student id"]),
                "name": str(member.get("student name_sem1", "")),
                "gpa": round(float(member["GPA"]), 2),
                "attendance": round(float(member["attendance"]), 1),
            }
            for member in study_group
        ],
    }


def main():
    data, metrics, difficulty = core.load_engineered()

    study_group_cache = {}
    records = []
    for _, row in data.iterrows():
        key = int(row["student id"])
        members = study_group_cache.setdefault(
            key,
            core.study_group(data, row, n=3),
        )
        records.append(_student_record(data, row, members))

    at_risk = metrics.get("risk_classes", {})
    payload = {
        "generated_by": "scripts/export_json.py",
        "metrics": {
            "students": metrics["students"],
            "cluster_k": metrics["cluster_k"],
            "prediction_features": metrics["prediction_features"],
            "best_model": metrics["best_model"],
            "gpa_r2": metrics["gpa_r2"],
            "gpa_r2_std": metrics["gpa_r2_std"],
            "gpa_mae": metrics["gpa_mae"],
            "gpa_mae_std": metrics["gpa_mae_std"],
            "risk_accuracy": metrics["risk_accuracy"],
            "risk_accuracy_std": metrics["risk_accuracy_std"],
            "at_risk_count": int(at_risk.get(True, 0)),
            "on_track_count": int(at_risk.get(False, 0)),
        },
        "students": records,
        "subject_difficulty": difficulty.to_dict(orient="records"),
    }

    out_dir = os.path.join(ROOT, "frontend", "data")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "engineered.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)

    print(f"Wrote {os.path.abspath(out)} ({len(records)} students)")
    print(f"GPA model {metrics['best_model']}  R2={metrics['gpa_r2']}  "
          f"MAE={metrics['gpa_mae']}  |  risk acc={metrics['risk_accuracy']}"
          f"  |  at risk={at_risk.get(True, 0)}/{metrics['students']}")


if __name__ == "__main__":
    main()
