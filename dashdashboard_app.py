"""AXEL Dash dashboard.

Run:  python dashdashboard_app.py   ->  http://localhost:8050
"""

import base64
import os

import dash
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html

import config
from core import (
    build_pdf_report,
    load_engineered,
    plot_gpa_trend_figure,
    resource_path,
    study_group,
)

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "AXEL - Student Performance Dashboard"
app.server.secret_key = os.environ.get("SECRET_KEY", "axel-demo-secret-change-me")

# Data and models are loaded once at startup (cached to disk on first run).
combined_data, metrics, subject_difficulty = load_engineered()

STUDENT_OPTIONS = [
    {"label": str(sid), "value": sid} for sid in sorted(combined_data["student id"].tolist())
]


def asset_src(relative_path):
    """Base64 data URI for an image, or None if the file is missing."""
    try:
        with open(resource_path(relative_path), "rb") as handle:
            return "data:image/png;base64," + base64.b64encode(handle.read()).decode("utf-8")
    except OSError:
        return None


LOGO_SRC = asset_src("env/assets/logo.png")
BACKGROUND_SRC = asset_src("env/assets/background.jpg")


def find_student(student_id):
    match = combined_data[combined_data["student id"] == int(student_id)]
    return None if match.empty else match.iloc[0]


# ---------------------------------------------------------------------------
# Component builders
# ---------------------------------------------------------------------------

def login_card():
    return dbc.Card(
        dbc.CardBody([
            html.H3("AXEL Student Dashboard", className="card-title"),
            dbc.Input(id="password-input", type="password", placeholder="Password",
                      className="mb-3"),
            dbc.Button("Login", id="login-button", color="primary", className="w-100"),
            html.Div(id="login-error", className="text-danger mt-2"),
        ]),
        className="mx-auto mt-5",
        style={"max-width": "380px"},
    )


def lookup_tab():
    return dbc.Row([
        dbc.Col(dcc.Dropdown(id="student-select", options=STUDENT_OPTIONS,
                             placeholder="Select Student ID", clearable=True), width=6),
        dbc.Col(dbc.Button("Search", id="search-button", color="primary"), width="auto"),
    ], className="mt-3 align-items-center")


def render_student(student):
    group = study_group(combined_data, student)
    return dbc.Card(dbc.CardBody([
        html.H3(student["student name_sem1"]),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div(f"{student['GPA']:.2f}", className="fs-3 fw-bold"),
                html.Small("GPA"),
            ])), width=3),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div(f"{student['attendance']:.1f}%", className="fs-3 fw-bold"),
                html.Small("Attendance"),
            ])), width=3),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div(f"{student['Predicted_GPA']:.2f}", className="fs-3 fw-bold"),
                html.Small("Predicted GPA"),
            ])), width=3),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div(f"{student['GPA_delta']:+.2f}", className="fs-3 fw-bold"),
                html.Small("GPA change"),
            ])), width=3),
        ], className="mt-2"),
        dbc.Badge("AT RISK" if student["At_Risk"] else "ON TRACK",
                  color="danger" if student["At_Risk"] else "success",
                  className="mt-3"),
        dcc.Graph(figure=plot_gpa_trend_figure(
            [student["GPA_sem1"], student["GPA_sem2"]],
            student["Predicted_GPA"],
            title=f"GPA Trends for {student['student name_sem1']}",
        ), className="mt-3"),
        dbc.Row([
            dbc.Col(html.Div([
                html.H5(":books: Recommended Books"),
                html.Ul([html.Li(book) for book in student["Recommended_Books"]]),
            ])),
            dbc.Col(html.Div([
                html.H5(":handshake: Study Group"),
                html.Ul([html.Li(
                    f"{member['student name_sem1']} | GPA: {member['GPA']:.2f} | "
                    f"Attendance: {member['attendance']:.1f}%"
                ) for member in group]),
            ])),
            dbc.Col(html.Div([
                html.H5(":mortar_board: Professor Help"),
                html.Ul([html.Li(rec) for rec in student["Professor_Recommendations"]] or [html.Li("None")]),
            ])),
        ], className="mt-3"),
        dbc.Row([
            dbc.Col(dbc.Button("Download PDF report", id="pdf-button", color="secondary"), width="auto"),
            dbc.Col(dbc.Button("Export CSV", id="export-button", color="secondary"), width="auto"),
        ], className="mt-3"),
    ]), className="mt-3")


def analytics_layout():
    gpa_hist = go.Figure(go.Histogram(x=combined_data["GPA"], nbinsx=20))
    gpa_hist.update_layout(title="GPA distribution", template="plotly_white")
    att_hist = go.Figure(go.Histogram(x=combined_data["attendance"], nbinsx=20))
    att_hist.update_layout(title="Attendance distribution", template="plotly_white")

    difficulty = subject_difficulty.sort_values("mean")
    subject_bar = go.Figure(go.Bar(
        x=difficulty["subject"], y=difficulty["mean"],
        error_y=dict(type="data", array=difficulty["std"], visible=True),
        marker_color="rgba(255,152,0,0.8)",
    ))
    subject_bar.update_layout(title="Class average per subject (+/- std)",
                              template="plotly_white", xaxis_tickangle=-35)

    top10 = combined_data.nlargest(10, "GPA")[
        ["student id", "student name_sem1", "GPA", "attendance"]
    ].reset_index(drop=True)

    return html.Div([
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div(str(metrics["students"]), className="fs-3 fw-bold"),
                html.Small("Students"),
            ]))),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div(str(metrics["risk_classes"].get(True, 0)), className="fs-3 fw-bold text-danger"),
                html.Small("At risk"),
            ]))),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div(str(metrics["risk_classes"].get(False, 0)), className="fs-3 fw-bold text-success"),
                html.Small("On track"),
            ]))),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.Div(str(metrics["cluster_k"]), className="fs-3 fw-bold"),
                html.Small("Study clusters"),
            ]))),
        ], className="mt-3"),
        dcc.Graph(figure=gpa_hist, className="mt-3"),
        dcc.Graph(figure=att_hist),
        dcc.Graph(figure=subject_bar),
        html.H5("Top 10 students", className="mt-3"),
        dbc.Table.from_dataframe(top10, striped=True, bordered=True, hover=True),
    ])


def compare_layout():
    return html.Div([
        dbc.Row([
            dbc.Col(dcc.Dropdown(id="compare-select", options=STUDENT_OPTIONS, multi=True,
                                 placeholder="Select 2-3 students"), width=6),
            dbc.Col(dbc.Button("Compare", id="compare-button", color="primary"), width="auto"),
        ], className="mt-3 align-items-center"),
        html.Div(id="compare-output", className="mt-3"),
    ])


def main_dashboard():
    return html.Div([
        html.H3("Enhanced Student Performance Dashboard", className="text-center mt-3"),
        dcc.Tabs(id="tabs", value="lookup", className="mt-3", children=[
            dcc.Tab(label="Student Lookup", value="lookup"),
            dcc.Tab(label="Cohort Analytics", value="analytics"),
            dcc.Tab(label="Compare Students", value="compare"),
        ]),
        html.Div(id="lookup-content"),
        html.Div(id="analytics-content"),
        html.Div(id="compare-content"),
        dbc.Alert(
            f"{metrics['students']} students · GPA model {metrics['best_model']} "
            f"(R^2 {metrics['gpa_r2']} ± {metrics['gpa_r2_std']}, MAE {metrics['gpa_mae']}) · "
            f"Risk accuracy {metrics['risk_accuracy']} ± {metrics['risk_accuracy_std']}",
            color="info",
            className="mt-4",
        ),
    ])


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

header = dbc.Row(
    [
        dbc.Col(html.Img(src=LOGO_SRC, style={"height": "70px"}), width="auto") if LOGO_SRC else None,
        dbc.Col(html.H3("AXEL", className="mb-0"), className="text-center"),
    ],
    className="align-items-center",
    justify="center",
)

app.layout = html.Div(
    style={
        "background-image": f"url({BACKGROUND_SRC})" if BACKGROUND_SRC else None,
        "background-size": "cover",
        "min-height": "100vh",
        "color": "#0b1622",
        "padding": "20px",
    },
    children=[
        dbc.Container([
            header,
            html.Div(id="gate-content"),
            dcc.Store(id="session", data={"authed": False}),
            dcc.Store(id="selected-student"),
            dcc.Download(id="download"),
        ]),
    ],
)


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------

@app.callback(
    Output("session", "data"),
    Output("login-error", "children"),
    Input("login-button", "n_clicks"),
    State("password-input", "value"),
    State("session", "data"),
    prevent_initial_call=True,
)
def do_login(n_clicks, password, session_data):
    session_data = session_data or {"authed": False}
    if not n_clicks:
        return session_data, ""
    if password == config.AUTH_PASSWORD:
        return {"authed": True}, ""
    return {"authed": False}, "Incorrect password."


@app.callback(
    Output("gate-content", "children"),
    Input("session", "data"),
    prevent_initial_call=True,
)
def render_gate(session_data):
    if session_data and session_data.get("authed"):
        return main_dashboard()
    return login_card()


@app.callback(
    Output("lookup-content", "children"),
    Output("selected-student", "data"),
    Output("download", "data"),
    Input("search-button", "n_clicks"),
    Input("pdf-button", "n_clicks"),
    State("student-select", "value"),
    State("selected-student", "data"),
    State("session", "data"),
    prevent_initial_call=True,
)
def update_lookup(search_clicks, pdf_clicks, student_id, selected, session_data):
    if not (session_data or {}).get("authed"):
        return html.Div(), None, dash.no_update
    triggered = dash.callback_context.triggered[0]["prop_id"]

    if triggered == "pdf-button.n_clicks" and pdf_clicks and selected:
        student = find_student(selected)
        if student is None:
            return html.Div("Student not found!", className="text-danger"), selected, dash.no_update
        return (
            html.Div(),
            selected,
            dcc.send_bytes(build_pdf_report(student), f"axel_student_{selected}.pdf"),
        )

    if triggered == "search-button.n_clicks" and search_clicks and student_id:
        student = find_student(student_id)
        if student is None:
            return html.Div("Student not found!", className="text-danger"), None, dash.no_update
        return render_student(student), student_id, dash.no_update

    return html.Div("Select a student and press Search.", className="text-muted"), None, dash.no_update


@app.callback(
    Output("analytics-content", "children"),
    Input("tabs", "value"),
    State("session", "data"),
    prevent_initial_call=True,
)
def update_analytics(tab, session_data):
    if tab == "analytics" and (session_data or {}).get("authed"):
        return analytics_layout()
    return html.Div()


@app.callback(
    Output("compare-content", "children"),
    Input("tabs", "value"),
    State("session", "data"),
    prevent_initial_call=True,
)
def update_compare(tab, session_data):
    if tab == "compare" and (session_data or {}).get("authed"):
        return compare_layout()
    return html.Div()


@app.callback(
    Output("compare-output", "children"),
    Input("compare-button", "n_clicks"),
    State("compare-select", "value"),
    State("session", "data"),
    prevent_initial_call=True,
)
def run_compare(n_clicks, ids, session_data):
    if not (session_data or {}).get("authed") or not n_clicks:
        return html.Div()
    ids = list(dict.fromkeys(ids or []))[:3]
    if len(ids) < 2:
        return html.Div("Select at least 2 students to compare.", className="text-muted")
    rows = combined_data[combined_data["student id"].isin(ids)]

    fig = go.Figure()
    for _, row in rows.iterrows():
        fig.add_trace(go.Bar(
            x=["GPA", "Predicted GPA", "Attendance/10"],
            y=[row["GPA"], row["Predicted_GPA"], row["attendance"] / 10],
            name=row["student name_sem1"],
        ))
    fig.update_layout(title="Side-by-side comparison", template="plotly_white", barmode="group")

    return html.Div([
        dbc.Table.from_dataframe(
            rows[["student id", "student name_sem1", "GPA", "attendance",
                  "Predicted_GPA", "At_Risk"]].reset_index(drop=True),
            striped=True, bordered=True, hover=True,
        ),
        dcc.Graph(figure=fig, className="mt-3"),
    ])


@app.callback(
    Output("download", "data"),
    Input("export-button", "n_clicks"),
    State("session", "data"),
    prevent_initial_call=True,
)
def export_csv(n_clicks, session_data):
    if not (session_data or {}).get("authed") or not n_clicks:
        return dash.no_update
    return dcc.send_data_frame(combined_data.to_csv, "axel_students.csv", index=False)


if __name__ == "__main__":
    app.run(host=config.DEFAULT_HOST, port=config.DASH_PORT, debug=config.DEBUG)
