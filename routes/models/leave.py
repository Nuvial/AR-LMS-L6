from db import get_db
from flask_login import current_user

def getLeave(employee_id=None):
    """
    Get all employee's leave from the database or a specific employee by ID.
    Args:
        employee_id (int, optional): The ID of the employee to get.
    """
    try:
        # Create base query
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

        if (employee_id):
            # Add condition to base query if id is provided
            conditions.append("el.fk_employee_id = ?")
            values += (employee_id,)
        
        if (not current_user.admin and employee_id != current_user.employee_id):
            # Only return members who are part of the logged in users team (and the employee themselves)
            conditions.append("(t.fk_manager_id = ? OR el.fk_employee_id = ?)")
            values += (current_user.employee_id, current_user.employee_id)
        
        if (conditions):
            query += f"WHERE {" AND ".join(conditions)};"

        # Execute the query
        db = get_db()
        leave = db.execute(query, values).fetchall()

        # Convert result into a dictionary
        leave = [dict(row) for row in leave]

        return {'message': 'success', 'leave': leave}
    except Exception as e:
        return {'message': 'error', 'error': str(e)}

def getRemainingLeave(employee_id=None):
    """
    Get the remaining sick and annual leave for a specific employee.
    Args:
        employee_id (int): The ID of the employee to get remaining leave for.
    """
    try:
        # Create query to get remaining leave
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
            LEFT JOIN Team t on e.fk_team_id = t.pk_team_id
        """
        values = ()
        conditions = []

        if (employee_id):
            # Add condition to base query if id is provided
            conditions.append("e.pk_employee_id = ?")
            values += (employee_id,)

        if (not current_user.admin and employee_id != current_user.employee_id):
            # Only return members who are part of the logged in users team (and the employee themselves)
            conditions.append("(t.fk_manager_id = ? OR e.pk_employee_id = ?)")
            values += (current_user.employee_id, current_user.employee_id)
        
        if (conditions):
            query += f"WHERE {" AND ".join(conditions)};"

        # Execute the query
        db = get_db()
        stats = db.execute(query, values).fetchall()

        if stats:
            return [dict(row) for row in stats]
        else:
            return None
    except Exception as e:
        raise Exception(f"An error occurred: {e}")

def getRequestedLeave(employee_id=None):
    """
    Returns:
        employee_id (array): Employee ID's with requsted leave.
    """
    try:
        # Create base query
        query = """
            SELECT 
                el.fk_employee_id, 
                el.status
            FROM EmployeeLeave el
            JOIN Employees e on el.fk_employee_id = e.pk_employee_id
            LEFT JOIN Team t on e.fk_team_id = t.pk_team_id
            WHERE status == 'Pending'
        """
        values = ()
        conditions = []

        if (employee_id):
            # Add condition to base query if id is provided
            conditions.append("el.fk_employee_id = ?")
            values = (employee_id,)
        
        if (not current_user.admin and employee_id != current_user.employee_id):
            # Only return members who are part of the logged in users team (and the employee themselves)
            conditions.append("(t.fk_manager_id = ? OR e.pk_employee_id = ?)")
            values += (current_user.employee_id, current_user.employee_id)
        
        if (conditions):
            query += f"AND {" AND ".join(conditions)};"

        # Execute the query
        db = get_db()
        employees = db.execute(query, values).fetchall()

        # Convert result into a dictionary
        employees = [dict(row) for row in employees]

        return employees
    except Exception as e:
        raise Exception(f"An error occurred: {e}")



def isLeaveInManagerTeam(leave_id, manager_employee_id):
    """
    Checks if the employee who made the leave request is in the manager's team.
    """
    try:
        db = get_db()
        query = """
            SELECT 
                el.pk_leave_id
            FROM EmployeeLeave el
            JOIN Employees e ON el.fk_employee_id = e.pk_employee_id
            JOIN Team t ON e.fk_team_id = t.pk_team_id
            WHERE el.pk_leave_id = ? AND t.fk_manager_id = ?
        """
        return db.execute(query, (leave_id, manager_employee_id)).fetchone() is not None
    except Exception as e:
        return False

def approveLeave(id, comment=None):
    """
    Args:
        leave_id (int): Specific leave ID to approve.
        comment (str): (Optional) admin comment on leave.
    """
    try:
        # Create base query
        query = """
            UPDATE EmployeeLeave
            SET
                status = 'Approved',
                comment_admin = ?
            WHERE pk_leave_id = ?
        """
        values = (comment, id)
        
        # Execute the query
        db = get_db()
        db.execute(query, values)
        db.commit()

        return 'success'
    
    except Exception as e:
        raise Exception(f"An error occurred: {e}")

def denyLeave(id, comment=None):
    """
    Args:
        leave_id (int): Specific leave ID to deny.
        comment (str): (Optional) admin comment on leave.
    """
    try:
        # Create base query
        query = """
            UPDATE EmployeeLeave
            SET
                status = 'Rejected',
                comment_admin = ?
            WHERE pk_leave_id = ?
        """
        values = (comment, id)
        
        # Execute the query
        db = get_db()
        db.execute(query, values)
        db.commit()

        return 'success'
    
    except Exception as e:
        raise Exception(f"An error occurred: {e}")

def requestLeave(fk_employee_id, leave_type, start_date, end_date, comment_employee):
    try:
        # Create base query
        query = """
            INSERT INTO EmployeeLeave(fk_employee_id, leave_type, start_date, end_date, status, comment_employee)
            VALUES (
                ?,
                ?,
                ?,
                ?,
                'Pending',
                ?
            )
        """
        values = (fk_employee_id, leave_type, start_date, end_date, comment_employee)

        # Execute the query
        db = get_db()
        db.execute(query, values)
        db.commit()

        return 'success'
    
    except Exception as e:
        raise Exception(f"An error occurred: {e}")

def deleteRequest(leave_id, employee_id):
    try:
        # Create base query
        query = """
            DELETE FROM EmployeeLeave
            WHERE 
                pk_leave_id = ? AND
                fk_employee_id = ? AND
                (status = 'Pending' OR (status = 'Approved' AND date(start_date) > date('now')))
        """
        values = (leave_id, employee_id)
        # Execute the query
        db = get_db()
        db.execute(query, values)
        db.commit()

        return 'success'
    
    except Exception as e:
        raise Exception(f"An error occurred: {e}")