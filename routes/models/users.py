from db import get_db

def getUsers(user_id=None):
    """
    Model to get all or specific user/s.
    Args:
        user_id (int, optional): User ID to get. If not provided, gets all users.
    """
    try:
        # Create base query
        query = """
            SELECT
                a.pk_user_id,
                a.fk_employee_id,
                b.first_name,
                b.last_name,
                a.username,
                a.forgot_password,
                a.admin
            FROM Users a
            JOIN Employees b on a.fk_employee_id = b.pk_employee_id
        """
        values = ()

        if (user_id):
            # Add condition to base query if id is provided
            query += " WHERE pk_user_id = ?"
            values = (user_id,)
        
        # Execute the query
        db = get_db()
        users = db.execute(query, values).fetchall()

        # Convert result into a dictionary
        users = [dict(row) for row in users]

        return users
    except Exception as e:
        raise Exception(f"An error occurred: {e}")

def deleteUser(user_id=None):
    """
    Model to delete a specific user.
    Args:
        user_id (int): User ID to delete.
    """
    try:
        # Create base query
        query = """
            DELETE FROM Users
            WHERE pk_user_id = ?
        """
        values = (user_id,)
        
        # Execute the query
        db = get_db()
        db.execute(query, values)
        db.commit()

        return 'success'
    except Exception as e:
        raise Exception(f"An error occurred: {e}")

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