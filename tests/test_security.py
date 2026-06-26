import sqlite3

import pytest

from db import get_db


def _query(app, sql, params=()):
    """Run a read-only query against the test database via the app context."""
    with app.app_context():
        return get_db().execute(sql, params).fetchall()



 
class TestSQLInjection:
    _PAYLOADS = [
        "admin' --",
        "admin'--",
        "' OR '1'='1",
        "' OR 1=1 --",
        "'; DROP TABLE Users; --",
        "admin' OR '1'='1' --",
    ]

    @pytest.mark.parametrize("payload", _PAYLOADS)
    def test_login_injection_does_not_authenticate(self, app, payload):
        client = app.test_client()
        client.post(
            "/login",
            data={"username": payload, "password": "irrelevant"},
            follow_redirects=False,
        )
        # A protected route must still bounce to login > no session granted
        resp = client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_drop_table_payload_leaves_schema_intact(self, app):
        client = app.test_client()
        client.post(
            "/login",
            data={"username": "'; DROP TABLE Users; --", "password": "x"},
            follow_redirects=False,
        )

        rows = _query(app, "SELECT COUNT(*) AS c FROM Users")
        assert rows[0]["c"] >= 2

        good = app.test_client()
        good.post("/login", data={"username": "admin", "password": "admin"})
        assert good.get("/dashboard", follow_redirects=False).status_code == 200

    def test_injection_in_username_lookup_is_treated_as_literal(self, admin_client):
        resp = admin_client.get("/users/get_users/username_taken?username=' OR '1'='1")
        assert resp.status_code == 200
        assert resp.get_json()["registered"] is False




class TestSecurityHeaders:
    """
    Authenticated HTML must not be cached, otherwise the browser back-button could redisplay a logged-out user's data from cache.
    """

    def test_login_page_sets_no_store_cache_headers(self, client):
        resp = client.get("/login")
        cache_control = resp.headers.get("Cache-Control", "")
        assert "no-store" in cache_control
        assert "no-cache" in cache_control
        assert resp.headers.get("Pragma") == "no-cache"
        assert resp.headers.get("Expires") == "0"

    def test_authenticated_html_page_is_not_cacheable(self, admin_client):
        resp = admin_client.get("/dashboard")
        assert resp.status_code == 200
        assert "no-store" in resp.headers.get("Cache-Control", "")

    def test_logout_clears_session(self, admin_client):
        assert admin_client.get("/dashboard", follow_redirects=False).status_code == 200
        admin_client.get("/logout", follow_redirects=False)
        resp = admin_client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]





class TestCSRFProtection:
    """
    POST that lacks a valid token must not establish a session.
    """

    def test_login_without_csrf_token_is_rejected(self, app):
        app.config["WTF_CSRF_ENABLED"] = True
        try:
            client = app.test_client()
            # Correct credentials, but no CSRF token in the payload
            client.post("/login", data={"username": "admin", "password": "admin"})
            resp = client.get("/dashboard", follow_redirects=False)
            assert resp.status_code == 302
            assert "/login" in resp.headers["Location"]
        finally:
            app.config["WTF_CSRF_ENABLED"] = False





class TestPasswordStorage:


    def test_seeded_password_is_bcrypt_hashed(self, app):
        rows = _query(app, "SELECT password FROM Users WHERE username = ?", ("admin",))
        stored = rows[0]["password"]
        assert stored != "admin", "Password must not be stored in plaintext"
        assert stored.startswith("$2b$"), "Password must be a bcrypt hash"

    def test_newly_created_user_password_is_hashed(self, app, admin_client):
        resp = admin_client.post(
            "/users/add_user",
            json={"employee_id": 3, "username": "newaccount", "password": "TestingPass12345"},
        )
        assert resp.get_json()["message"] == "success"

        rows = _query(app, "SELECT password FROM Users WHERE username = ?", ("newaccount",))
        stored = rows[0]["password"]
        assert stored != "Testing1234"
        assert stored.startswith("$2b$")





class TestErrorHandlingDoesNotLeak:
    """
    Bad input should produce a JSON error, not raw stack trace
    """

    def test_missing_body_returns_friendly_error(self, admin_client):
        resp = admin_client.post("/employees/add_employee", json={})
        body = resp.get_json()
        assert body["message"] == "error"
        assert "Traceback" not in str(body)

    def test_invalid_field_error_message_is_human_readable(self, admin_client):
        resp = admin_client.post(
            "/employees/add_employee",
            json={
                "first_name": "Bad",
                "last_name": "Input",
                "default_leave_balance": "not-a-number",
                "default_sick_leave_balance": 40,
                "contracted_daily_hours": 8,
                "contracted_weekly_hours": 40,
            },
        )
        body = resp.get_json()
        assert body["message"] == "error"
        # Not a Python exception dump
        assert "must be a number" in body["error"]
        assert "Traceback" not in body["error"]
