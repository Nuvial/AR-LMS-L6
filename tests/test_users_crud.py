import pytest
from conftest import login


class TestUsersIndex:

    def test_admin_sees_users_page(self, admin_client):
        resp = admin_client.get("/users/")
        assert resp.status_code == 200

    def test_regular_user_redirected_to_settings(self, user_client):
        resp = user_client.get("/users/", follow_redirects=False)
        assert resp.status_code == 302
        assert "/users/settings" in resp.headers["Location"]

    def test_settings_page_renders(self, user_client):
        resp = user_client.get("/users/settings")
        assert resp.status_code == 200


class TestGetUsers:

    def test_admin_gets_all_users(self, admin_client):
        resp = admin_client.get("/users/get_users")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_admin_gets_specific_user(self, admin_client):
        resp = admin_client.get("/users/get_users/1")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["username"] == "admin"

    def test_get_current_user_self(self, user_client):
        resp = user_client.get("/users/get_users/self")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data[0]["username"] == "user"

    def test_get_nonexistent_user_returns_error(self, admin_client):
        resp = admin_client.get("/users/get_users/9999")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "error" in data or data == []


class TestIsRegistered:

    def test_registered_employee_returns_true(self, admin_client):
        resp = admin_client.get("/users/get_users/is_registered/1")
        assert resp.status_code == 200
        assert resp.get_json()["registered"] is True

    def test_unregistered_employee_returns_false(self, admin_client):
        resp = admin_client.get("/users/get_users/is_registered/11")
        assert resp.status_code == 200
        assert resp.get_json()["registered"] is False


class TestUsernameTaken:

    def test_existing_username_is_taken(self, admin_client):
        resp = admin_client.get("/users/get_users/username_taken?username=admin")
        assert resp.status_code == 200
        assert resp.get_json()["registered"] is True

    def test_unused_username_is_not_taken(self, admin_client):
        resp = admin_client.get("/users/get_users/username_taken?username=newperson")
        assert resp.status_code == 200
        assert resp.get_json()["registered"] is False


class TestAddUser:

    def test_add_user_success(self, admin_client):
        # Employee 3 has no account yet
        resp = admin_client.post(
            "/users/add_user",
            json={
                "employee_id": 3,
                "username": "cbridge",
                "password": "Passw0rdOK!1234",
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_add_user_missing_body(self, admin_client):
        resp = admin_client.post("/users/add_user", json={})
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "error"

    def test_add_user_missing_fields(self, admin_client):
        resp = admin_client.post(
            "/users/add_user",
            json={"employee_id": 3},
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "error"

    def test_add_user_invalid_username(self, admin_client):
        resp = admin_client.post(
            "/users/add_user",
            json={
                "employee_id": 3,
                "username": "bad user!",
                "password": "Passw0rdOK!1234",
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "error"

    def test_add_user_nonexistent_employee(self, admin_client):
        resp = admin_client.post(
            "/users/add_user",
            json={
                "employee_id": 9999,
                "username": "nobody",
                "password": "Passw0rdOK!1234",
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "error"

    def test_add_user_already_registered_employee(self, admin_client):
        resp = admin_client.post(
            "/users/add_user",
            json={
                "employee_id": 1,
                "username": "dupeacc",
                "password": "Passw0rdOK!1234",
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "error"

    def test_add_user_duplicate_username(self, admin_client):
        resp = admin_client.post(
            "/users/add_user",
            json={
                "employee_id": 3,
                "username": "admin",
                "password": "Passw0rdOK!1234",
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "error"

    def test_add_admin_user(self, admin_client):
        resp = admin_client.post(
            "/users/add_user",
            json={
                "employee_id": 3,
                "username": "cbridge",
                "password": "Passw0rdOK!1234",
                "admin": True,
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"


class TestPromoteAndDemoteUser:

    def test_promote_user_to_admin(self, admin_client):
        resp = admin_client.put("/users/promote_user/2")
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_demote_only_admin_fails(self, admin_client):
        resp = admin_client.put("/users/demote_user/1")
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "error"
        assert "only admin" in resp.get_json()["error"].lower()

    def test_promote_then_demote_succeeds(self, admin_client):
        # Promote user 2 to admin
        admin_client.put("/users/promote_user/2")
        # Now demote user 1 (there are two admins now)
        resp = admin_client.put("/users/demote_user/1")
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_promote_team_manager_fails(self, admin_client):
        """A manager of a team cannot be promoted until removed from management."""
        # Create a team with employee 3 as manager
        admin_client.post(
            "/teams/add_team",
            json={"teamName": "T1", "managerId": "3", "employees": ["4"]},
        )
        admin_client.post(
            "/users/add_user",
            json={"employee_id": 3, "username": "emp3", "password": "Passw0rdOK!1234"},
        )

        users = admin_client.get("/users/get_users").get_json()
        emp3_user = next((u for u in users if u["fk_employee_id"] == 3), None)
        assert emp3_user, "Employee 3 should have a user account now"
        uid = emp3_user["pk_user_id"]
        resp = admin_client.put(f"/users/promote_user/{uid}")
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "error"


class TestDeleteUser:

    def test_user_deletes_self(self, user_client):
        resp = user_client.delete("/users/delete_user/self")
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_admin_deletes_another_user(self, admin_client):
        resp = admin_client.delete("/users/delete_user/2")
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_admin_cannot_delete_self_when_only_admin(self, admin_client):
        resp = admin_client.delete("/users/delete_user/1")
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "error"


class TestChangePassword:

    def test_admin_changes_own_password(self, admin_client):
        resp = admin_client.put(
            "/users/change_password/1",
            json={"password": "NewPassw0rd!1234"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_user_changes_own_password(self, user_client):
        resp = user_client.put(
            "/users/change_password/2",
            json={"password": "NewPassw0rd!1234"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_change_password_missing_body_returns_error(self, admin_client):
        resp = admin_client.put("/users/change_password/1", json={})
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "error"

    def test_user_cannot_change_others_password(self, user_client):
        resp = user_client.put(
            "/users/change_password/1",
            json={"password": "NewPassw0rd!1234"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "error"


class TestChangeUsername:

    def test_user_changes_own_username(self, user_client):
        resp = user_client.put(
            "/users/change_username/self",
            json={"username": "newusername"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_change_username_self_missing_body(self, user_client):
        resp = user_client.put("/users/change_username/self", json={})
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "error"

    def test_change_username_taken_returns_error(self, user_client):
        resp = user_client.put(
            "/users/change_username/self",
            json={"username": "admin"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "error"

    def test_admin_changes_another_users_username(self, admin_client):
        resp = admin_client.put(
            "/users/change_username/2",
            json={"username": "ryleigh"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_change_username_invalid_format(self, user_client):
        resp = user_client.put(
            "/users/change_username/self",
            json={"username": "bad user!"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "error"


class TestUnregisteredAndPendingUsers:

    def test_get_unregistered_employees(self, admin_client):
        resp = admin_client.get("/users/get_unregistered_employees")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) >= 9

    def test_pending_registrations_initially_empty(self, admin_client):
        resp = admin_client.get("/users/pending_registrations")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_confirm_registration(self, admin_client):
        from conftest import login
        client = admin_client 


        client.post(
            "/register",
            data={
                "employee_id": 3,
                "username": "cbridge",
                "password": "Passw0rdOK!1234",
            },
        )
        pending = admin_client.get("/users/pending_registrations").get_json()
        assert len(pending) == 1
        uid = pending[0]["pk_user_id"]

        resp = admin_client.put(f"/users/confirm_registration/{uid}")
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_deny_registration(self, admin_client):
        admin_client.post(
            "/register",
            data={
                "employee_id": 4,
                "username": "kbuckley",
                "password": "Passw0rdOK!1234",
            },
        )
        pending = admin_client.get("/users/pending_registrations").get_json()
        uid = pending[0]["pk_user_id"]

        resp = admin_client.delete(f"/users/deny_registration/{uid}")
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"
