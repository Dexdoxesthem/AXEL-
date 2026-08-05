"""End-to-end app tests: Flask routes (incl. auth), Dash layout/callbacks."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config

# ---------------------------------------------------------------------------
# Flask
# ---------------------------------------------------------------------------

def test_flask_routes_require_auth():
    import dashboad

    client = dashboad.app.test_client()
    for url in ["/export", "/analytics", "/compare", "/report/1", "/api/student/1"]:
        response = client.get(url)
        assert response.status_code == 302, f"{url} should redirect when unauthenticated"
        assert response.headers["Location"].endswith("/login")


def test_flask_login_flow():
    import dashboad

    client = dashboad.app.test_client()
    response = client.post("/login", data={"password": "wrong"})
    assert response.status_code == 200

    response = client.post("/login", data={"password": config.AUTH_PASSWORD})
    assert response.status_code == 302

    assert client.get("/export").status_code == 200
    assert client.get("/api/student/1").status_code == 200
    assert client.get("/analytics").status_code == 200
    assert client.get("/report/1").status_code == 200
    assert client.get("/report/1").content_type == "application/pdf"


def test_flask_student_route():
    import dashboad

    client = dashboad.app.test_client()
    client.post("/login", data={"password": config.AUTH_PASSWORD})

    response = client.post("/student", data={"student_id": "1"})
    assert response.status_code == 200
    assert "GPA" in response.get_data(as_text=True)

    response = client.post("/student", data={"student_id": "abc"})
    assert response.status_code == 400

    response = client.post("/student", data={"student_id": "99999"})
    assert response.status_code == 404


def test_flask_compare_route():
    import dashboad

    client = dashboad.app.test_client()
    client.post("/login", data={"password": config.AUTH_PASSWORD})
    response = client.post("/compare", data={"sids": ["1", "2", "3"]})
    assert response.status_code == 200
    assert "Comparison" in response.get_data(as_text=True)


def test_flask_export_csv_content():
    import dashboad

    client = dashboad.app.test_client()
    client.post("/login", data={"password": config.AUTH_PASSWORD})
    response = client.get("/export")
    assert response.status_code == 200
    assert "student id" in response.get_data(as_text=True)


# ---------------------------------------------------------------------------
# Dash
# ---------------------------------------------------------------------------

def test_dash_app_builds_layout():
    import dashdashboard_app as dash_app

    assert dash_app.app.title == "AXEL - Student Performance Dashboard"
    layout_str = str(dash_app.app.layout)
    assert "gate-content" in layout_str
    assert "session" in layout_str


def test_dash_render_student():
    import dashdashboard_app as dash_app

    student = dash_app.find_student(1)
    assert student is not None
    card = dash_app.render_student(student)
    assert card is not None
