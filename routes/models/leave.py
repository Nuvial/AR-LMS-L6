from db import get_db
from flask_login import current_user

def getLeave(employee_id=None):
    """
    Get all employee leave or a specific employee's leave, scoped by the caller's role.
    """
    try:
        query = """
            SELECT
                el.*,
                e.pk_employee_id,
                e.first_name,
                e.last_name
            FROM Employees e
            LEFT JOIN EmployeeLeave el ON el.fk_employee_id = e.pk_employee_id
            LEFT JOIN Team t ON e.fk_team_id = t.pk_team_id
        """
        values = ()
        conditions = []

        if employee_id:
            conditions.append("el.fk_employee_id = ?")
            values += (employee_id,)

        if not current_user.admin and employee_id != current_user.employee_id:
            # Managers see their team; employees see only themselves
            conditions.append("(t.fk_manager_id = ? OR el.fk_employee_id = ?)")
            values += (current_user.employee_id, current_user.employee_id)

        if conditions:
            query += f"WHERE {' AND '.join(conditions)};"

        db = get_db()
        leave = db.execute(query, values).fetchall()
        return {'message': 'success', 'leave': [dict(row) for row in leave]}
    except Exception as e:
        return {'message': 'error', 'error': str(e)}


def getRemainingLeave(employee_id=None):
    """
    Get the remaining sick and annual leave for an employee, scoped by the caller's role.
    """
    try:
        query = """
            SELECT
                e.pk_employee_id as fk_employee_id,
                e.default_leave_balance -
                    IFNULL((
                        SELECT SUM(julianday(end_date) - julianday(start_date) + 1)
                        FROM EmployeeLeave
                        WHERE fk_employee_id = e.pk_employee_id
                        AND leave_type = 'Annual Leave'
                        AND (status = 'Approved' or status = 'Pending')
                        AND strftime('%Y', start_date) = strftime('%Y', 'now')
                    ), 0) AS leave_remaining,
                e.default_sick_leave_balance -
                    IFNULL((
                        SELECT SUM(julianday(end_date) - julianday(start_date) + 1)
                        FROM EmployeeLeave
                        WHERE fk_employee_id = e.pk_employee_id
                        AND leave_type = 'Sick Leave'
                        AND status = 'Approved'
                        AND strftime('%Y', start_date) = strftime('%Y', 'now')
                    ), 0) AS sick_leave_remaining
            FROM Employees e
            LEFT JOIN Team t ON e.fk_team_id = t.pk_team_id
        """
        values = ()
        conditions = []

        if employee_id:
            conditions.append("e.pk_employee_id = ?")
            values += (employee_id,)

        if not current_user.admin and employee_id != current_user.employee_id:
            conditions.append("(t.fk_manager_id = ? OR e.pk_employee_id = ?)")
            values += (current_user.employee_id, current_user.employee_id)

        if conditions:
            query += f"WHERE {' AND '.join(conditions)};"

        db = get_db()
        stats = db.execute(query, values).fetchall()
        return [dict(row) for row in stats] if stats else None
    except Exception as e:
        raise Exception(f"An error occurred: {e}")


def getRequestedLeave(employee_id=None):
    """
    Return employee IDs that have pending leave requests, scoped by the caller's role.
    """
    try:
        query = """
            SELECT
                el.fk_employee_id,
                el.status
            FROM EmployeeLeave el
            JOIN Employees e ON el.fk_employee_id = e.pk_employee_id
            LEFT JOIN Team t ON e.fk_team_id = t.pk_team_id
            WHERE status = 'Pending'
        """
        values = ()
        conditions = []

        if employee_id:
            conditions.append("el.fk_employee_id = ?")
            values = (employee_id,)

        if not current_user.admin and employee_id != current_user.employee_id:
            conditions.append("(t.fk_manager_id = ? OR e.pk_employee_id = ?)")
            values += (current_user.employee_id, current_user.employee_id)

        if conditions:
            query += f" AND {' AND '.join(conditions)};"

        db = get_db()
        employees = db.execute(query, values).fetchall()
        return [dict(row) for row in employees]
    except Exception as e:
        raise Exception(f"An error occurred: {e}")


def isLeaveInManagerTeam(leave_id, manager_employee_id):
    """
    Returns True if the leave request belongs to an employee in the manager's team
    and the leave owner is not an admin (managers cannot approve admin leave).
    """
    try:
        db = get_db()
        query = """
            SELECT el.pk_leave_id
            FROM EmployeeLeave el
            JOIN Employees e ON el.fk_employee_id = e.pk_employee_id
            JOIN Roles r ON e.fk_role_id = r.pk_role_id
            JOIN Team t ON e.fk_team_id = t.pk_team_id
            WHERE el.pk_leave_id = ?
              AND t.fk_manager_id = ?
              AND r.name != 'admin'
        """
        return db.execute(query, (leave_id, manager_employee_id)).fetchone() is not None
    except Exception:
        return False


def getLeaveOwnerRole(leave_id):
    """
    Returns the role name of the employee who owns this leave request.
    """
    try:
        db = get_db()
        query = """
            SELECT r.name
            FROM EmployeeLeave el
            JOIN Employees e ON el.fk_employee_id = e.pk_employee_id
            JOIN Roles r ON e.fk_role_id = r.pk_role_id
            WHERE el.pk_leave_id = ?
        """
        row = db.execute(query, (leave_id,)).fetchone()
        return row[0] if row else None
    except Exception:
        return None


def approveLeave(id, comment=None):
    try:
        query = """
            UPDATE EmployeeLeave
            SET status = 'Approved', comment_admin = ?
            WHERE pk_leave_id = ?
        """
        db = get_db()
        db.execute(query, (comment, id))
        db.commit()
        return 'success'
    except Exception as e:
        raise Exception(f"An error occurred: {e}")


def denyLeave(id, comment=None):
    try:
        query = """
            UPDATE EmployeeLeave
            SET status = 'Rejected', comment_admin = ?
            WHERE pk_leave_id = ?
        """
        db = get_db()
        db.execute(query, (comment, id))
        db.commit()
        return 'success'
    except Exception as e:
        raise Exception(f"An error occurred: {e}")


def requestLeave(fk_employee_id, leave_type, start_date, end_date, comment_employee):
    try:
        query = """
            INSERT INTO EmployeeLeave(fk_employee_id, leave_type, start_date, end_date, status, comment_employee)
            VALUES (?, ?, ?, ?, 'Pending', ?)
        """
        db = get_db()
        db.execute(query, (fk_employee_id, leave_type, start_date, end_date, comment_employee))
        db.commit()
        return 'success'
    except Exception as e:
        raise Exception(f"An error occurred: {e}")


def deleteRequest(leave_id, employee_id):
    try:
        query = """
            DELETE FROM EmployeeLeave
            WHERE pk_leave_id = ?
              AND fk_employee_id = ?
              AND (status = 'Pending' OR (status = 'Approved' AND date(start_date) > date('now')))
        """
        db = get_db()
        db.execute(query, (leave_id, employee_id))
        db.commit()
        return 'success'
    except Exception as e:
        raise Exception(f"An error occurred: {e}")
