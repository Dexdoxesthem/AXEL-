# AXEL — Student Performance Dashboard

An NAAC college project that analyses student semester results, flags at-risk
students, predicts the next-semester GPA, recommends books and study groups,
and suggests professors for weak subjects.

## Project layout

| Path | Purpose |
|------|---------|
| `core.py` | Shared pipeline: data loading, GPA, models, recommendations, charts |
| `axel.py` | Streamlit dashboard (packaged as `axel.exe`) |
| `AXELV2.PY` | Thin wrapper that runs the Streamlit app in `axel.py` |
| `dashboad.py` | Flask web dashboard (packaged as `dashboad.exe`) |
| `dashdashboard_app.py` | Dash dashboard |
| `templates/` | HTML templates used by the Flask app |
| `sem1 data set.csv`, `sem2 data set.csv` | Semester result data (909 students) |
| `combined_data.csv` | Pre-merged example output |
| `frontend/` | Next.js web app styled with the Dell 1996 design language |
| `scripts/export_json.py` | Regenerates `frontend/data/engineered.json` from the pipeline |
| `tests/` | Tests for `core.py` |

## Setup

```powershell
python -m venv env
.\env\Scripts\activate
pip install -r requirements.txt
```

Install the extras only for the dashboard you use:

```powershell
pip install -r requirements-streamlit.txt   # Streamlit
pip install -r requirements-flask.txt       # Flask
pip install -r requirements-dash.txt        # Dash
```

## Running

```powershell
streamlit run axel.py                       # Streamlit
python AXELV2.PY                            # same app, v2 entry point
python dashboad.py                          # Flask  -> http://localhost:5000
python dashdashboard_app.py                 # Dash   -> http://localhost:8050
```

Enable debug (development only) with the `FLASK_DEBUG` / `DASH_DEBUG` env var.

## Features

- Per-semester GPA on a 10-point scale (`mean(score/10)` per subject).
- Overall GPA = average of both semesters.
- **At-risk flag**: rule-based (`GPA < 5.0` or `attendance < 55%`) plus an
  honestly evaluated logistic-regression classifier (train/test split accuracy).
- **GPA prediction**: linear regression of the next semester GPA from the
  previous semester GPA + attendance (R² reported).
- **Study groups**: KMeans clustering (3 groups) over GPA + attendance.
- **Book recommendations**: top popular books the student has not borrowed.
- **Professor recommendations**: for subjects scored below 40%.
- CSV export in every app.

## Tests

```powershell
python tests/test_core.py        # no dependencies beyond the project's
python -m pytest tests/ -v       # or with pytest installed
```

## Next.js frontend

A self-contained web app in `frontend/` that renders the same pipeline data
with a 1996 Dell catalog aesthetic (black page frame, ribbon cards, yellow
stickers, Arial Black/Helvetica/Times type).

```powershell
cd frontend
npm install
npm run dev                     # http://localhost:3000  (password: axel123)
```

Pages: login gate, student lookup, per-student dashboard, cohort analytics,
student comparison, a printable report, and CSV export. The data snapshot is
`frontend/data/engineered.json`, regenerated from the Python pipeline with:

```powershell
python scripts/export_json.py   # or: cd frontend; npm run export:data
```

Override the demo password with an `AXEL_PASSWORD` env var (checked on the
server via `app/api/auth/route.ts`). Production build:

```powershell
npm run build && npm start
```

### Deploying to Vercel

`vercel.json` at the repo root sets the Next.js framework and build commands.
Because the app lives in `frontend/` (a monorepo), set the project's **Root
Directory to `frontend`** — this is configured in the Vercel dashboard
(Project &rarr; Settings &rarr; General &rarr; Root Directory), not in
`vercel.json` (the `rootDirectory` key is no longer accepted there).

Import the repo at vercel.com/new, then set one environment variable:

| Name           | Value                          |
|----------------|--------------------------------|
| `AXEL_PASSWORD`| your secure login password (optional; defaults to `axel123`) |

Or deploy straight from the CLI (run from `frontend/`, or link the project
and set its Root Directory to `frontend`):

```powershell
npx vercel              # preview deployment
npx vercel --prod       # production deployment
```

The static snapshot `frontend/data/engineered.json` is committed, so no Python
is needed on the server. Regenerate it locally before pushing when the CSVs
change (`python scripts/export_json.py`).

## Building a standalone .exe (PyInstaller)

```powershell
pyinstaller axel.spec                    # Streamlit app  -> dist\axel.exe
pyinstaller dashboad.spec                # Flask app      -> dist\dashboad.exe
pyinstaller student_dashboard.spec       # Flask app      -> dist\student_dashboard.exe
```

The specs bundle the CSVs (and templates, where needed) automatically. Rebuild
`build/` and `dist/` after changing the source.
