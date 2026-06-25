import pytest


def _create_team(admin_client, name="Alpha Team", manager_id="3", employees=None):
    """POST /teams/add_team and return the response."""
    if employees is None:
        employees = ["4", "5"]
    return admin_client.post(
        "/teams/add_team",
        json={"teamName": name, "managerId": manager_id, "employees": employees},
    )


class TestTeamsIndex:

    def test_admin_sees_teams_page(self, admin_client):
        resp = admin_client.get("/teams/")
        assert resp.status_code == 200

    def test_non_admin_blocked(self, user_client):
        resp = user_client.get("/teams/", follow_redirects=False)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]



class TestGetTeams:

    def test_get_all_teams_initially_empty(self, admin_client):
        resp = admin_client.get("/teams/get_teams")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_get_teams_returns_created_team(self, admin_client):
        _create_team(admin_client)
        resp = admin_client.get("/teams/get_teams")
        assert resp.status_code == 200
        teams = resp.get_json()
        assert len(teams) == 1
        assert teams[0]["name"] == "Alpha Team"

    def test_non_admin_blocked(self, user_client):
        resp = user_client.get("/teams/get_teams", follow_redirects=False)
        assert resp.status_code == 302



class TestGetEmployees:

    def test_get_employees_not_in_team(self, admin_client):
        resp = admin_client.get("/teams/get_employees/")
        assert resp.status_code == 200
        employees = resp.get_json()
        assert isinstance(employees, list)
        assert len(employees) >= 1

    def test_get_employees_post_multiple_teams(self, admin_client):
        _create_team(admin_client)
        resp = admin_client.post(
            "/teams/get_employees/",
            json={"teamIds": [1]},
        )
        assert resp.status_code == 200



class TestGetPotentialManagers:

    def test_get_potential_managers(self, admin_client):
        resp = admin_client.get("/teams/get_potential_managers/")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        # Admin employee should not appear
        ids = [e["pk_employee_id"] for e in data]
        assert 1 not in ids

    def test_manager_excluded_after_team_creation(self, admin_client):
        _create_team(admin_client, manager_id="3")
        resp = admin_client.get("/teams/get_potential_managers/")
        managers = resp.get_json()
        ids = [m["pk_employee_id"] for m in managers]
        # Employee 3 is now a manager and must not appear as potential manager
        assert 3 not in ids



class TestAddTeam:

    def test_create_team_success(self, admin_client):
        resp = _create_team(admin_client)
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_create_team_manager_cannot_be_employee(self, admin_client):
        resp = admin_client.post(
            "/teams/add_team",
            json={
                "teamName": "Bad Team",
                "managerId": "3",
                "employees": ["3", "4"],
            },
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["message"] == "error"
        assert "Manager cannot be an employee" in data["error"]

    def test_create_team_duplicate_manager_fails(self, admin_client):
        _create_team(admin_client, manager_id="3", employees=["4"])

        resp = admin_client.post(
            "/teams/add_team",
            json={"teamName": "Second Team", "managerId": "3", "employees": ["5"]},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["message"] == "error"

    def test_create_team_employee_already_in_team_fails(self, admin_client):
        _create_team(admin_client, manager_id="3", employees=["4"])

        resp = admin_client.post(
            "/teams/add_team",
            json={"teamName": "Second Team", "managerId": "6", "employees": ["4"]},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["message"] == "error"



class TestUpdateTeam:

    def test_update_team_success(self, admin_client):
        _create_team(admin_client, manager_id="3", employees=["4"])
        resp = admin_client.post(
            "/teams/update_team/1",
            json={
                "teamName": "Renamed Team",
                "managerId": "3",
                "employees": [{"pk_employee_id": 4}, {"pk_employee_id": 5}],
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_update_team_change_manager(self, admin_client):
        _create_team(admin_client, manager_id="3", employees=["4"])

        resp = admin_client.post(
            "/teams/update_team/1",
            json={
                "teamName": "Alpha Team",
                "managerId": "6",
                "employees": [{"pk_employee_id": 4}],
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_update_team_manager_in_employees_fails(self, admin_client):
        _create_team(admin_client, manager_id="3", employees=["4"])
        resp = admin_client.post(
            "/teams/update_team/1",
            json={
                "teamName": "Alpha Team",
                "managerId": "3",
                "employees": [{"pk_employee_id": 3}],  # manager also as employee
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "error"



class TestDeleteTeam:

    def test_delete_team_success(self, admin_client):
        _create_team(admin_client)
        resp = admin_client.delete("/teams/delete_team/1")
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_delete_team_releases_manager_role(self, admin_client):
        _create_team(admin_client, manager_id="3")
        admin_client.delete("/teams/delete_team/1")

        resp = admin_client.get("/employees/get_employees/3")
        emp = resp.get_json()[0]
        assert emp["role"] == "employee"

    def test_delete_nonexistent_team_succeeds_gracefully(self, admin_client):
        resp = admin_client.delete("/teams/delete_team/9999")
        assert resp.status_code == 200

        assert resp.get_json()["message"] == "success"
