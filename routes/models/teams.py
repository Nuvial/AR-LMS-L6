from db import get_db

def getTeams(teamId=None):
    """
    Model to get all or specific team/s.
    Args:
        teamId (int, optional): Team ID to get. If not provided, gets all teams.
    """
    try:
        # Create base query
        query = """
            SELECT 
                t.*,
                e.first_name AS 'manager_first_name',
                e.last_name AS 'manager_last_name',
                (
                    SELECT count(*) FROM Employees WHERE fk_team_id = t.pk_team_id
                ) AS 'employee_count'
            FROM Team t
            LEFT JOIN Employees e on fk_manager_id = pk_employee_id
        """
        values = ()

        if (teamId):
            # Add condition to base query if id is provided
            query += " WHERE pk_team_id = ?"
            values = (teamId,)
        
        # Execute the query
        db = get_db()
        teams = db.execute(query, values).fetchall()

        # Convert result into a dictionary
        teams = [dict(row) for row in teams]

        return teams
    except Exception as e:
        raise Exception(f"An error occurred: {e}")

def getEmployees(teamId=None):
    """
    Route to get all employees either in a specific team if teamId is provided, or all employees
    NOT in a team if no teamId is provided.
    Args:
        teamId (int, optional): TeamID to get employees for, if not provided gets all employees NOT in a team.
    """
    try:
        # Create base query
        query = """
            SELECT
                pk_employee_id,
                first_name,
                last_name,
                employee_position
            FROM Employees
        """
        values = ()

        if (teamId):
            # Add condition to base query if id is provided
            query += " WHERE fk_team_id = ?"
            values = (teamId,)
        else:
            query += " WHERE fk_team_id IS null"
        
        # Execute the query
        db = get_db()
        employees = db.execute(query, values).fetchall()

        # Convert result into a dictionary
        employees = [dict(row) for row in employees]

        return employees
    except Exception as e:
        raise Exception(f"An error occurred: {e}")

# def deleteUser(user_id=None):
#     """
#     Model to delete a specific user.
#     Args:
#         user_id (int): User ID to delete.
#     """
#     try:
#         # Create base query
#         query = """
#             DELETE FROM Users
#             WHERE pk_user_id = ?
#         """
#         values = (user_id,)
        
#         # Execute the query
#         db = get_db()
#         db.execute("PRAGMA foreign_keys = ON") # Enable foreign keys for this connection

#         db.execute(query, values)
#         db.commit()

#         return 'success'
#     except Exception as e:
#         raise Exception(f"An error occurred: {e}")

# def changePassword(id, password):
#     """
#     Changes a users password. The route should be protected by an admin-only login.
#     Args:
#         id (int): The User ID of the password to change.
#         password (str): A hashed password to change to.
#     """
#     try:
#         query = """
#             UPDATE Users
#             SET 
#                 password = ?,
#                 forgot_password = 0
#             WHERE pk_user_id = ?
#         """
#         values = (password, id)

#         db = get_db()
#         db.execute(query, values)
#         db.commit()

#         return 'success'
#     except Exception as e:
#         raise e

# def changeUsername(id, username):
#     """
#     Changes a users username. The route should be protected by an admin-only login.
#     Args:
#         id (int): The User ID of the username to change.
#         username (str): The new username to change to.
#     """
#     try:
#         query = """
#             UPDATE Users
#             SET 
#                 username = ?
#             WHERE pk_user_id = ?
#         """
#         values = (username, id)

#         db = get_db()
#         db.execute(query, values)
#         db.commit()

#         return 'success'
#     except Exception as e:
#         raise e