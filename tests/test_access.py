import pytest

from conftest import login



class TestUnauthenticatedAccess:
    """Protected routes must not serve data to anonymous clients."""

    @pytest.mark.parametrize(
        "method,path",
        [
            ("get", "/employees/get_employees"),
            ("get", "/dashboard"),
            ("get", "/teams/get_teams"),
            ("get", "/users/get_users"),
            ("get", "/leave/get_leave"),
        ],
    )
    def test_protected_get_redirects_to_login(self, client, method, path):
        resp = getattr(client, method)(path, follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_add_employee_blocked_when_anonymous(self, client):
        resp = client.post("/employees/add_employee", json={"first_name": "X"})
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]



class TestRegularUserBlockedFromAdminRoutes:
    """ 
    A logged-in employee hitting an admin-only route is redirected to the dashboard by 
    the admin_required decorator.
    """

    def test_regular_user_cannot_list_teams(self, user_client):
        resp = user_client.get("/teams/get_teams", follow_redirects=False)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_regular_user_cannot_add_employee(self, user_client):
        resp = user_client.post(
            "/employees/add_employee",
            json={
                "first_name": "Mallory",
                "last_name": "Smith",
                "default_leave_balance": 100,
                "default_sick_leave_balance": 40,
                "contracted_daily_hours": 8,
                "contracted_weekly_hours": 40,
            },
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_regular_user_cannot_delete_employee(self, user_client):
        resp = user_client.delete("/employees/delete_employee/5", follow_redirects=False)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_regular_user_cannot_update_other_employee(self, user_client):
        resp = user_client.put(
            "/employees/update_employee/5",
            json={"first_name": "Hacked"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_regular_user_cannot_add_user_account(self, user_client):
        resp = user_client.post(
            "/users/add_user",
            json={"employee_id": 5, "username": "newbie", "password": "Sup3rSecret!"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_regular_user_cannot_promote_themselves(self, user_client):
        resp = user_client.put("/users/promote_user/2", follow_redirects=False)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_delete_attempt_by_regular_user_does_not_delete(self, user_client, admin_client):
        """The denied delete must have no side effect on the database."""
        user_client.delete("/employees/delete_employee/5", follow_redirects=False)
        remaining = admin_client.get("/employees/get_employees").get_json()
        ids = [e["pk_employee_id"] for e in remaining]
        assert 5 in ids, "Employee 5 must still exist after a denied delete"



class TestHorizontalDataIsolation:
    """A regular employee may only see and modify their own record."""

    def test_user_can_read_own_record(self, user_client):
        resp = user_client.get("/employees/get_employees/2")
        assert resp.status_code == 200
        assert resp.get_json()[0]["pk_employee_id"] == 2

    def test_user_cannot_read_another_employee(self, user_client):
        resp = user_client.get("/employees/get_employees/5")
        body = resp.get_json()
        if isinstance(body, dict):
            assert body.get("message") == "error"
        else:
            ids = [e["pk_employee_id"] for e in body]
            assert 5 not in ids

    def test_unscoped_listing_returns_only_own_record(self, user_client):
        """A bare get_employees for a lone employee returns just themselves."""
        data = user_client.get("/employees/get_employees").get_json()
        ids = [e["pk_employee_id"] for e in data]
        assert ids == [2]

    def test_user_cannot_escalate_own_leave_balance(self, user_client, admin_client):
        """
        Self-service updates are restricted to first/last name.
        """
        original = admin_client.get("/employees/get_employees/2").get_json()[0]["default_leave_balance"]

        user_client.put(
            "/employees/update_employee/self",
            json={"first_name": "Ryleigh", "default_leave_balance": original + 500},
        )

        after = admin_client.get("/employees/get_employees/2").get_json()[0]["default_leave_balance"]
        assert after == original, "A regular user must not change their own leave balance"

    def test_user_can_update_own_name(self, user_client):
        """The permitted half of self-service still works."""
        resp = user_client.put(
            "/employees/update_employee/self",
            json={"first_name": "Riley"},
        )
        assert resp.get_json()["message"] == "success"
        assert user_client.get("/employees/get_employees/2").get_json()[0]["first_name"] == "Riley"



class TestLoginFailures:

    def test_wrong_password_does_not_authenticate(self, app):
        client = app.test_client()
        login(client, "admin", "wrong-password")
        # Still anonymous > protected route redirects to login
        resp = client.get("/teams/get_teams", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_unknown_username_does_not_authenticate(self, app):
        client = app.test_client()
        login(client, "ghost", "whatever123")
        resp = client.get("/dashboard", follow_redirects=False)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]
