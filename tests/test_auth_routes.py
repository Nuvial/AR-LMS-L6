import pytest
from unittest.mock import patch
from conftest import login


class TestAdminOrManagerRequired:
    """Decorator sends regular employees to /dashboard."""

    def test_regular_user_cannot_approve_leave(self, user_client):
        resp = user_client.put(
            "/leave/update_leave/approve/1",
            json={"comment": ""},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_regular_user_cannot_deny_leave(self, user_client):
        resp = user_client.put(
            "/leave/update_leave/deny/1",
            json={"comment": ""},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]


class TestLoginEdgeCases:

    def test_already_authenticated_redirects_to_dashboard(self, admin_client):
        resp = admin_client.get("/login", follow_redirects=False)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_pending_user_sees_warning(self, app, client):
        """Login attempt by a user awaiting admin confirmation shows a flash."""
        with app.app_context():
            from db import get_db
            db = get_db()
            db.execute("UPDATE Users SET pending_confirmation = 1 WHERE username = 'user'")
            db.commit()

        resp = login(client, "user", "user")
        assert resp.status_code == 200
        data = resp.data.decode()
        assert "awaiting admin confirmation" in data.lower() or resp.status_code == 200

    def test_forced_reset_redirects_to_force_change_password(self, app, client):
        """After login with password_reset_required=1 the user is redirected."""
        with app.app_context():
            from db import get_db
            db = get_db()
            db.execute(
                "UPDATE Users SET password_reset_required = 1 WHERE username = 'user'"
            )
            db.commit()

        resp = login(client, "user", "user")
        assert resp.status_code == 302
        assert "force_change_password" in resp.headers["Location"]


class TestForceChangePassword:

    def test_get_without_session_redirects_to_login(self, client):
        resp = client.get("/force_change_password", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_get_with_valid_session_renders_form(self, app, client):
        with app.app_context():
            from db import get_db
            db = get_db()
            db.execute(
                "UPDATE Users SET password_reset_required = 1 WHERE pk_user_id = 2"
            )
            db.commit()

        with client.session_transaction() as sess:
            sess["pending_password_reset_user_id"] = 2

        resp = client.get("/force_change_password")
        assert resp.status_code == 200

    def test_post_mismatched_passwords_shows_error(self, app, client):
        with app.app_context():
            from db import get_db
            db = get_db()
            db.execute(
                "UPDATE Users SET password_reset_required = 1 WHERE pk_user_id = 2"
            )
            db.commit()

        with client.session_transaction() as sess:
            sess["pending_password_reset_user_id"] = 2

        resp = client.post(
            "/force_change_password",
            data={"password": "NewPassw0rd!1234", "confirm_password": "Different1!"},
        )
        assert resp.status_code == 200
        assert b"do not match" in resp.data

    def test_post_same_as_current_shows_error(self, app, client):
        with app.app_context():
            from db import get_db
            db = get_db()
            db.execute(
                "UPDATE Users SET password_reset_required = 1 WHERE pk_user_id = 2"
            )
            db.commit()

        with client.session_transaction() as sess:
            sess["pending_password_reset_user_id"] = 2

        resp = client.post(
            "/force_change_password",
            data={"password": "user", "confirm_password": "user"},
        )
        assert resp.status_code == 200

    def test_post_valid_new_password_changes_and_redirects(self, app, client):
        with app.app_context():
            from db import get_db
            db = get_db()
            db.execute(
                "UPDATE Users SET password_reset_required = 1 WHERE pk_user_id = 2"
            )
            db.commit()

        with client.session_transaction() as sess:
            sess["pending_password_reset_user_id"] = 2

        resp = client.post(
            "/force_change_password",
            data={"password": "BrandNewPass99!", "confirm_password": "BrandNewPass99!"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


class TestRegister:

    def test_get_register_renders_form(self, client):
        resp = client.get("/register")
        assert resp.status_code == 200

    def test_post_duplicate_username_shows_error(self, client):
        resp = client.post(
            "/register",
            data={"employee_id": 3, "username": "admin", "password": "Passw0rdOK!1234"},
        )
        assert resp.status_code == 200
        assert b"already exists" in resp.data

    def test_post_nonexistent_employee_id_shows_error(self, client):
        resp = client.post(
            "/register",
            data={"employee_id": 9999, "username": "newbie", "password": "Passw0rdOK!1234"},
        )
        assert resp.status_code == 200
        assert b"Employee ID does not exist" in resp.data

    def test_post_already_registered_employee_shows_error(self, client):
        resp = client.post(
            "/register",
            data={
                "employee_id": 1,
                "username": "dupeemployee",
                "password": "Passw0rdOK!1234",
            },
        )
        assert resp.status_code == 200
        assert b"already registered" in resp.data

    def test_post_valid_registration_creates_pending_user(self, client):
        resp = client.post(
            "/register",
            data={
                "employee_id": 3,
                "username": "cbridge",
                "password": "Passw0rdOK!1234",
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_post_breached_password_is_rejected_at_registration(self, client):
        with patch('routes.models.users._HIBP_ENABLED', True), \
                patch('routes.models.users._check_hibp', return_value=5000):
            resp = client.post(
                "/register",
                data={
                    "employee_id": 3,
                    "username": "cbridge",
                    "password": "Passw0rdOK!1234",
                },
            )
        assert resp.status_code == 200
        assert b"breach" in resp.data


class TestForgotPassword:

    def test_forgot_password_success(self, client, app):
        resp = client.post("/forgot_password/2")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "success"

    def test_forgot_password_invalid_id_still_returns_success(self, client):
        resp = client.post("/forgot_password/9999")
        assert resp.status_code == 200


class TestCheckUsers:

    def test_check_users_found(self, client):
        resp = client.get("/check_users/admin")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "user_id" in data
        assert data["user_id"] != ""

    def test_check_users_not_found(self, client):
        resp = client.get("/check_users/nonexistentuser")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["user_id"] == ""
