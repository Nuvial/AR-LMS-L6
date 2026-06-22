from flask_login import current_user
from db import get_db

def getUsers(user_id=None):
    """
    Model to get all or specific user/s.
    Args:
        user_id (int, optional): User ID to get. If not provided, gets all users.
    """
    try:
        query = """
            SELECT
                a.pk_user_id,
                a.fk_employee_id,
                b.first_name,
                b.last_name,
                a.username,
                a.forgot_password,
                r.name AS role,
                CASE WHEN r.name = 'admin' THEN 1 ELSE 0 END AS admin
            FROM Users a
            JOIN Employees b ON a.fk_employee_id = b.pk_employee_id
            JOIN Roles r ON b.fk_role_id = r.pk_role_id
            LEFT JOIN Team t ON b.fk_team_id = t.pk_team_id
        """
        values = ()
        conditions = []

        if user_id:
            conditions.append("a.pk_user_id = ?")
            values += (user_id,)

        if not current_user.admin:
            # Managers see their team members; non-managers see only themselves
            conditions.append("(t.fk_manager_id = ? OR a.fk_employee_id = ?)")
            values += (current_user.employee_id, current_user.employee_id)

        if conditions:
            query += f" WHERE {' AND '.join(conditions)}"

        db = get_db()
        users = db.execute(query, values).fetchall()
        return [dict(row) for row in users]
    except Exception as e:
        raise Exception(f"An error occurred: {e}")

def isUserInManagerTeam(user_id, manager_employee_id):
    """
    Checks whether the given user account belongs to an employee in the manager's team.
    """
    try:
        db = get_db()
        query = """
            SELECT a.pk_user_id
            FROM Users a
            JOIN Employees b ON a.fk_employee_id = b.pk_employee_id
            JOIN Team t ON b.fk_team_id = t.pk_team_id
            WHERE a.pk_user_id = ? AND t.fk_manager_id = ?
        """
        return db.execute(query, (user_id, manager_employee_id)).fetchone() is not None
    except Exception:
        return False

def deleteUser(user_id=None):
    """
    Model to delete a specific user.
    Args:
        user_id (int): User ID to delete.
    """
    try:
        db = get_db()

        # Prevent deleting the last admin account
        if current_user.admin and user_id == current_user.id:
            validationQuery = """
                SELECT u.pk_user_id
                FROM Users u
                JOIN Employees e ON u.fk_employee_id = e.pk_employee_id
                JOIN Roles r ON e.fk_role_id = r.pk_role_id
                WHERE r.name = 'admin' AND u.pk_user_id != ?
            """
            otherAdmins = db.execute(validationQuery, (user_id,)).fetchall()
            if len(otherAdmins) == 0:
                return {'message': 'error', 'error': 'Unable to delete the only admin account. Please assign another admin before deleting this account.'}

        # Create base query
        query = """
            DELETE FROM Users
            WHERE pk_user_id = ?
        """
        values = (user_id,)
        
        # Execute the query
        db.execute(query, values)
        db.commit()

        return {'message': 'success'}
    except Exception as e:
        return {'message': 'error', 'error': str(e)}

def changePassword(id, password):
    """
    Changes a users password. The route should be protected by an admin-only login.
    Args:
        id (int): The User ID of the password to change.
        password (str): A hashed password to change to.
    """
    try:
        query = """
            UPDATE Users
            SET 
                password = ?,
                forgot_password = 0
            WHERE pk_user_id = ?
        """
        values = (password, id)

        db = get_db()
        db.execute(query, values)
        db.commit()

        return 'success'
    except Exception as e:
        raise e

def changeUsername(id, username):
    """
    Changes a users username. The route should be protected by an admin-only login.
    Args:
        id (int): The User ID of the username to change.
        username (str): The new username to change to.
    """
    try:
        query = """
            UPDATE Users
            SET 
                username = ?
            WHERE pk_user_id = ?
        """
        values = (username, id)

        db = get_db()
        db.execute(query, values)
        db.commit()

        return 'success'
    except Exception as e:
        raise e