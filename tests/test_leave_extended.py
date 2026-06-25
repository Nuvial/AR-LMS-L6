import pytest


class TestLeaveIndex:

    def test_leave_index_renders(self, user_client):
        resp = user_client.get("/leave/")
        assert resp.status_code == 200


class TestGetLeave:

    def test_admin_gets_all_leave(self, admin_client):
        resp = admin_client.get("/leave/get_leave")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["message"] == "success"
        assert isinstance(data["leave"], list)
        assert len(data["leave"]) >= 1

    def test_admin_gets_leave_for_specific_employee(self, admin_client):
        resp = admin_client.get("/leave/get_leave/2")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["message"] == "success"

    def test_user_gets_own_leave(self, user_client):
        resp = user_client.get("/leave/get_leave/2")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["message"] == "success"


class TestGetRemainingLeave:

    def test_admin_gets_remaining_leave_all(self, admin_client):
        resp = admin_client.get("/leave/get_leave/remaining")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_admin_gets_remaining_leave_for_employee(self, admin_client):
        resp = admin_client.get("/leave/get_leave/remaining/2")
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) == 1

    def test_user_gets_own_remaining_leave(self, user_client):
        resp = user_client.get("/leave/get_leave/remaining/2")
        assert resp.status_code == 200


class TestGetRequestedLeave:

    def test_admin_gets_requested_leave(self, admin_client):
        resp = admin_client.get("/leave/get_leave/requested")
        assert resp.status_code == 200
        data = resp.get_json()
        # There are pending leave records in seeded data
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_user_gets_requested_leave(self, user_client):
        resp = user_client.get("/leave/get_leave/requested")
        assert resp.status_code == 200


class TestApproveLeave:

    def test_admin_approves_pending_leave(self, admin_client):
        # Leave 3: employee 6, Pending
        resp = admin_client.put(
            "/leave/update_leave/approve/3",
            json={"comment": "Approved."},
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_admin_approves_with_no_comment(self, admin_client):
        resp = admin_client.put(
            "/leave/update_leave/approve/5",
            json={"comment": ""},
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_regular_user_cannot_approve(self, user_client):
        """user has role='employee' → admin_or_manager_required redirects."""
        resp = user_client.put(
            "/leave/update_leave/approve/3",
            json={"comment": ""},
            follow_redirects=False,
        )
        assert resp.status_code == 302


class TestDenyLeave:

    def test_admin_denies_pending_leave(self, admin_client):
        # Leave 7: employee 4, Pending (Sick Leave)
        resp = admin_client.put(
            "/leave/update_leave/deny/7",
            json={"comment": "Denied."},
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_regular_user_cannot_deny(self, user_client):
        resp = user_client.put(
            "/leave/update_leave/deny/3",
            json={"comment": ""},
            follow_redirects=False,
        )
        assert resp.status_code == 302


class TestDeleteLeave:

    def test_user_can_delete_own_pending_leave(self, user_client, app):
        """Request new leave then delete it."""
        # First submit a future leave request
        user_client.post(
            "/leave/request_leave",
            json={
                "leave_type": "Annual Leave",
                "start_date": "2026-09-01",
                "end_date": "2026-09-05",
                "hours_requested": 40,
                "employee_comments": "",
            },
        )
        # Retrieve to get the pk_leave_id for the new pending record
        leave_resp = user_client.get("/leave/get_leave/2")
        leave_data = leave_resp.get_json()["leave"]
        pending = [l for l in leave_data if l["status"] == "Pending"]
        assert pending, "Expected at least one pending leave for employee 2 after request"
        leave_id = pending[0]["pk_leave_id"]

        resp = user_client.delete(f"/leave/update_leave/delete/{leave_id}")
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_delete_nonexistent_leave_returns_success(self, user_client):
        # deleteRequest commits with 0 rows affected and still returns 'success'
        resp = user_client.delete("/leave/update_leave/delete/9999")
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"


class TestRequestLeave:

    def test_valid_annual_leave_request(self, user_client):
        resp = user_client.post(
            "/leave/request_leave",
            json={
                "leave_type": "Annual Leave",
                "start_date": "2026-10-01",
                "end_date": "2026-10-05",
                "hours_requested": 40,
                "employee_comments": "Holiday",
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_valid_sick_leave_request(self, user_client):
        resp = user_client.post(
            "/leave/request_leave",
            json={
                "leave_type": "Sick Leave",
                "start_date": "2026-11-01",
                "end_date": "2026-11-01",
                "hours_requested": 8,
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "success"

    def test_missing_body_returns_error(self, user_client):
        resp = user_client.post("/leave/request_leave", json={})
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "error"

    def test_invalid_leave_type_returns_error(self, user_client):
        resp = user_client.post(
            "/leave/request_leave",
            json={
                "leave_type": "Holiday",
                "start_date": "2026-10-01",
                "end_date": "2026-10-05",
                "hours_requested": 40,
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "error"

    def test_overlapping_leave_returns_error(self, user_client):
        user_client.post(
            "/leave/request_leave",
            json={
                "leave_type": "Annual Leave",
                "start_date": "2026-12-01",
                "end_date": "2026-12-05",
                "hours_requested": 40,
            },
        )
        # Try to book an overlapping period
        resp = user_client.post(
            "/leave/request_leave",
            json={
                "leave_type": "Annual Leave",
                "start_date": "2026-12-03",
                "end_date": "2026-12-07",
                "hours_requested": 40,
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["message"] == "error"
        assert "already have leave" in resp.get_json()["error"].lower()
