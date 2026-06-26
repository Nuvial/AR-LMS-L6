def _valid_employee_payload(**overrides):
    payload = {
        "first_name": "Grace",
        "last_name": "Hopper",
        "default_leave_balance": 200,
        "default_sick_leave_balance": 40,
        "contracted_daily_hours": 8,
        "contracted_weekly_hours": 40,
    }
    payload.update(overrides)
    return payload


# ===========================================================================
# Browse (Read)
# ===========================================================================

class TestBrowseEmployees:

    def test_admin_sees_all_seeded_employees(self, admin_client):
        resp = admin_client.get("/employees/get_employees")
        assert resp.status_code == 200
        data = resp.get_json()
        # schema.sql seeds 11 employees
        assert len(data) == 11

    def test_get_single_employee_by_id(self, admin_client):
        resp = admin_client.get("/employees/get_employees/2")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["first_name"] == "Ryleigh"
        assert data[0]["last_name"] == "Frost"

    def test_employee_record_exposes_expected_columns(self, admin_client):
        resp = admin_client.get("/employees/get_employees/2")
        record = resp.get_json()[0]
        for column in (
            "pk_employee_id",
            "first_name",
            "last_name",
            "default_leave_balance",
            "contracted_weekly_hours",
            "role",
        ):
            assert column in record

    def test_self_endpoint_returns_own_record(self, user_client):
        # The seeded 'user' account is employee 2 (Ryleigh Frost)
        resp = user_client.get("/employees/get_employees/self")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data[0]["first_name"] == "Ryleigh"




class TestAddEmployee:

    def test_add_employee_persists_and_returns_id(self, admin_client):
        resp = admin_client.post("/employees/add_employee", json=_valid_employee_payload())
        body = resp.get_json()
        assert body["message"] == "success"
        new_id = body["employee_id"]

        # Confirm it can be read back
        fetched = admin_client.get(f"/employees/get_employees/{new_id}").get_json()
        assert fetched[0]["first_name"] == "Grace"
        assert fetched[0]["last_name"] == "Hopper"

    def test_add_employee_increases_total_count(self, admin_client):
        before = len(admin_client.get("/employees/get_employees").get_json())
        admin_client.post("/employees/add_employee", json=_valid_employee_payload())
        after = len(admin_client.get("/employees/get_employees").get_json())
        assert after == before + 1

    def test_add_employee_defaults_to_employee_role(self, admin_client):
        resp = admin_client.post("/employees/add_employee", json=_valid_employee_payload())
        new_id = resp.get_json()["employee_id"]
        fetched = admin_client.get(f"/employees/get_employees/{new_id}").get_json()
        assert fetched[0]["role"] == "employee"

    def test_add_employee_rejects_invalid_name(self, admin_client):
        resp = admin_client.post(
            "/employees/add_employee",
            json=_valid_employee_payload(first_name="Gr4ce!"),
        )
        body = resp.get_json()
        assert body["message"] == "error"
        assert "First name" in body["error"]

    def test_add_employee_rejects_missing_fields(self, admin_client):
        resp = admin_client.post("/employees/add_employee", json={"first_name": "OnlyName"})
        body = resp.get_json()
        assert body["message"] == "error"
        assert body["error"] == "Missing required fields"

    def test_add_employee_rejects_empty_body(self, admin_client):
        resp = admin_client.post("/employees/add_employee", json={})
        body = resp.get_json()
        assert body["message"] == "error"
        assert body["error"] == "Missing request body"

    def test_invalid_add_does_not_create_a_record(self, admin_client):
        before = len(admin_client.get("/employees/get_employees").get_json())
        admin_client.post(
            "/employees/add_employee",
            json=_valid_employee_payload(contracted_weekly_hours=999),
        )
        after = len(admin_client.get("/employees/get_employees").get_json())
        assert after == before



class TestUpdateEmployee:

    def test_admin_updates_employee_name(self, admin_client):
        resp = admin_client.put(
            "/employees/update_employee/3",
            json={"first_name": "Clara", "last_name": "Barton"},
        )
        assert resp.get_json()["message"] == "success"

        fetched = admin_client.get("/employees/get_employees/3").get_json()
        assert fetched[0]["first_name"] == "Clara"
        assert fetched[0]["last_name"] == "Barton"

    def test_admin_updates_leave_balance(self, admin_client):
        admin_client.put("/employees/update_employee/3", json={"default_leave_balance": 123})
        fetched = admin_client.get("/employees/get_employees/3").get_json()
        assert fetched[0]["default_leave_balance"] == 123

    def test_update_rejects_invalid_value(self, admin_client):
        resp = admin_client.put(
            "/employees/update_employee/3",
            json={"default_leave_balance": "lots"},
        )
        body = resp.get_json()
        assert body["message"] == "error"

    def test_update_rejects_empty_body(self, admin_client):
        resp = admin_client.put("/employees/update_employee/3", json={})
        assert resp.get_json()["message"] == "error"

    def test_invalid_update_does_not_change_record(self, admin_client):
        before = admin_client.get("/employees/get_employees/3").get_json()[0]["default_leave_balance"]
        admin_client.put("/employees/update_employee/3", json={"default_leave_balance": -50})
        after = admin_client.get("/employees/get_employees/3").get_json()[0]["default_leave_balance"]
        assert after == before



class TestDeleteEmployee:

    def test_admin_deletes_employee(self, admin_client):
        resp = admin_client.delete("/employees/delete_employee/11")
        assert resp.get_json()["message"] == "success"

        # The record should no longer be returned
        remaining = admin_client.get("/employees/get_employees").get_json()
        ids = [e["pk_employee_id"] for e in remaining]
        assert 11 not in ids

    def test_delete_reduces_total_count(self, admin_client):
        before = len(admin_client.get("/employees/get_employees").get_json())
        admin_client.delete("/employees/delete_employee/11")
        after = len(admin_client.get("/employees/get_employees").get_json())
        assert after == before - 1

    def test_admin_cannot_delete_own_last_admin_account(self, admin_client):
        # The seeded admin is employee 1 and is the only admin -> must be blocked
        resp = admin_client.delete("/employees/delete_employee/1")
        body = resp.get_json()
        assert body["message"] == "error"
        assert "only admin" in body["error"]

    def test_cannot_delete_employee_who_is_a_manager(self, admin_client):
        # Assign employee 3 as manager of a team, then attempt to delete them
        admin_client.post(
            "/teams/add_team",
            json={"teamName": "Alpha Team", "managerId": "3", "employees": ["4"]},
        )
        resp = admin_client.delete("/employees/delete_employee/3")
        body = resp.get_json()
        assert body["message"] == "error"
        assert "manager" in body["error"].lower()



class TestLeaveRequest:

    def test_employee_can_book_leave(self, user_client):
        resp = user_client.post(
            "/leave/request_leave",
            json={
                "leave_type": "Annual Leave",
                "start_date": "2026-03-02",
                "end_date": "2026-03-06",
                "hours_requested": 40,
            },
        )
        assert resp.get_json()["message"] == "success"

    def test_booked_leave_is_retrievable(self, user_client):
        user_client.post(
            "/leave/request_leave",
            json={
                "leave_type": "Annual Leave",
                "start_date": "2026-04-06",
                "end_date": "2026-04-10",
                "hours_requested": 40,
            },
        )
        leave = user_client.get("/leave/get_leave").get_json()["leave"]
        booked = [row for row in leave if row.get("start_date") == "2026-04-06"]
        assert booked, "Newly booked leave should be retrievable"
        assert booked[0]["status"] == "Pending"

    def test_overlapping_leave_is_rejected(self, user_client):
        payload = {
            "leave_type": "Annual Leave",
            "start_date": "2026-05-04",
            "end_date": "2026-05-08",
            "hours_requested": 40,
        }
        first = user_client.post("/leave/request_leave", json=payload)
        assert first.get_json()["message"] == "success"

        second = user_client.post("/leave/request_leave", json=payload)
        body = second.get_json()
        assert body["message"] == "error"
        assert "already have leave" in body["error"]

    def test_invalid_leave_type_rejected(self, user_client):
        resp = user_client.post(
            "/leave/request_leave",
            json={
                "leave_type": "Vacation",
                "start_date": "2026-06-01",
                "end_date": "2026-06-05",
                "hours_requested": 40,
            },
        )
        body = resp.get_json()
        assert body["message"] == "error"
        assert "Invalid leave type" in body["error"]
