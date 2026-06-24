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
                e.pk_employee_id,
                e.first_name,
                e.last_name,
                r.name AS role
            FROM Employees e
            JOIN Roles r ON e.fk_role_id = r.pk_role_id
        """
        values = ()

        if (teamId):
            query += " WHERE e.fk_team_id = ?"
            values = (teamId,)
        else:
            query += """
                WHERE e.fk_team_id IS NULL AND r.name = 'employee'
            """
        
        # Execute the query
        db = get_db()
        employees = db.execute(query, values).fetchall()

        # Convert result into a dictionary
        employees = [dict(row) for row in employees]

        return {'message': 'success', 'employees': employees}
    except Exception as e:
        return {'message': 'error', 'error': e}

def getPossibleManagers():
    """
    Route to get all employees that are compatible to become a manager.
    """
    try:
        # Create base query — exclude current managers and admins
        query = """
            SELECT
                e.pk_employee_id,
                e.first_name,
                e.last_name,
                r.name AS role
            FROM Employees e
            JOIN Roles r ON e.fk_role_id = r.pk_role_id
            WHERE e.pk_employee_id NOT IN (
                SELECT fk_manager_id FROM Team WHERE fk_manager_id IS NOT NULL
            )
            AND r.name != 'admin';
        """

        # Execute the query
        db = get_db()
        employees = db.execute(query).fetchall()

        # Convert result into a dictionary
        employees = [dict(row) for row in employees]

        return {'message': 'success', 'employees': employees}
    except Exception as e:
        raise Exception(f"An error occurred: {e}")

def getEmployeeManager(employeeId):
    """
    Route to get an employees manager.
    """
    try:
        # Create base query
        query = """
            SELECT
                m.pk_employee_id,
                m.first_name,
                m.last_name,
                r.name AS role
            FROM Employees m
            JOIN Roles r ON m.fk_role_id = r.pk_role_id
            JOIN Team t on m.pk_employee_id = t.fk_manager_id
            JOIN Employees e on e.fk_team_id = t.pk_team_id
            WHERE e.pk_employee_id = ?
        """
        values = (employeeId,)

        # Execute the query
        db = get_db()
        manager = db.execute(query, values).fetchall()

        # Convert result into a dictionary
        manager = [dict(row) for row in manager]

        return manager
    except Exception as e:
        raise Exception(f"An error occurred: {e}")

def validate_create_team(managerId, employeeIds):
    """
    Validates input for creating a new team.
    Returns an error string if validation fails, or None if valid.
    """
    currentTeams = [str(team['fk_manager_id']) for team in getTeams()]
    teamFreeEmployees = [str(e['pk_employee_id']) for e in getEmployees()['employees']]

    if managerId in employeeIds:
        return 'Manager cannot be an employee to the team.'

    if managerId not in teamFreeEmployees:
        managers = [str(m['pk_employee_id']) for m in getEmployeeManager(managerId)]
        for manager in managers:
            if manager not in employeeIds:
                continue
            return 'A team member cannot be a manager of the assigned manager.'

    if managerId in currentTeams:
        return 'A manager can only manage one team at a time.'

    for employee in employeeIds:
        if str(employee) not in teamFreeEmployees:
            return 'One or more of the employees are already in a team. An employee can only be part of one team at a time.'

    if employeeIds:
        db = get_db()
        placeholders = ','.join('?' * len(employeeIds))
        if db.execute(
            f"SELECT e.pk_employee_id FROM Employees e"
            f" JOIN Roles r ON e.fk_role_id = r.pk_role_id"
            f" WHERE e.pk_employee_id IN ({placeholders}) AND r.name = 'admin'",
            [int(eid) for eid in employeeIds]
        ).fetchone():
            return 'Admins cannot be assigned as team employees.'

    return None


def createTeam(teamName, managerId, employeeIds):
    """
    Creates a team record in the Team table for a new team.
    """
    try:
        error = validate_create_team(managerId, employeeIds)
        if error:
            return {'message': 'error', 'error': error}

        db = get_db()

        # Create query for Team
        teamQuery = """
            INSERT INTO Team (fk_manager_id, name)
            VALUES (?, ?)
        """
        teamValues = (managerId, teamName)

        teamCursor = db.execute(teamQuery, teamValues)
        teamId = teamCursor.lastrowid

        # Create query for employees
        employeeQuery = """
            UPDATE Employees
            SET
                fk_team_id = ?
            WHERE pk_employee_id = ?
        """
        employeeValues = [(teamId, employeeId) for employeeId in employeeIds]

        db.executemany(employeeQuery, employeeValues)

        # Promote the manager to 'manager' role
        db.execute("""
            UPDATE Employees
            SET fk_role_id = (SELECT pk_role_id FROM Roles WHERE name = 'manager')
            WHERE pk_employee_id = ?
        """, (managerId,))

        db.commit()

        return {'message': 'success', 'pk_team_id': teamId}
    except Exception as e:
        return {'message': 'error', 'error': str(e)}

def validate_update_team(teamId, managerId, employeeIds):
    """
    Validates input for updating a team. employeeIds is a list of dicts with 'pk_employee_id'.
    Returns an error string if validation fails, or None if valid.
    """
    currentTeams = [{team['pk_team_id']: str(team['fk_manager_id'])} for team in getTeams()]
    teamFreeEmployees = [str(e['pk_employee_id']) for e in getEmployees()['employees']]
    thisTeamEmployees = [str(e['pk_employee_id']) for e in getEmployees(teamId)['employees']]
    emp_ids_as_str = [str(e['pk_employee_id']) for e in employeeIds]

    if str(managerId) in emp_ids_as_str:
        return 'Manager cannot be an employee to the team.'

    if managerId not in teamFreeEmployees:
        managers = [str(m['pk_employee_id']) for m in getEmployeeManager(managerId)]
        for manager in managers:
            if manager not in emp_ids_as_str:
                continue
            return 'A team member cannot be a manager of the assigned manager.'

    for team in currentTeams:
        for tId, mId in team.items():
            if managerId == mId and tId != teamId:
                return 'A manager can only manage one team at a time.'

    for employee in employeeIds:
        emp_id = str(employee['pk_employee_id'])
        if emp_id not in teamFreeEmployees and emp_id not in thisTeamEmployees:
            return 'One or more of the employees are already in a team. An employee can only be part of one team at a time.'

    if employeeIds:
        emp_id_list = [int(e['pk_employee_id']) for e in employeeIds]
        db = get_db()
        placeholders = ','.join('?' * len(emp_id_list))
        if db.execute(
            f"SELECT e.pk_employee_id FROM Employees e"
            f" JOIN Roles r ON e.fk_role_id = r.pk_role_id"
            f" WHERE e.pk_employee_id IN ({placeholders}) AND r.name = 'admin'",
            emp_id_list
        ).fetchone():
            return 'Admins cannot be assigned as team employees.'

    return None


def updateTeam(teamId, teamName, managerId, employeeIds):
    """
    Updates a team record in the Team table for a new team.
    """
    try:
        error = validate_update_team(teamId, managerId, employeeIds)
        if error:
            return {'message': 'error', 'error': error}

        existingTeam = getTeams(teamId)
        oldManagerId = existingTeam[0]['fk_manager_id'] if existingTeam else None

        db = get_db()

        # Create query for Team
        teamQuery = """
            UPDATE Team 
            SET
                fk_manager_id = ?,
                name = ?
            WHERE pk_team_id = ?
                
        """
        teamValues = (managerId, teamName, teamId)

        db.execute(teamQuery, teamValues)

        # Create query for employees to remove all references
        employeeQueryRemoval = """
            UPDATE Employees
            SET
                fk_team_id = NULL
            WHERE fk_team_id = ?;
        """
        # Create query for employees to re-update all to team
        employeeQuery = """
            UPDATE Employees
            SET
                fk_team_id = ?
            WHERE pk_employee_id = ?;
        """
        employeeRemovalValues = (teamId,)
        employeeValues = [(teamId, employeeId['pk_employee_id']) for employeeId in employeeIds]

        db.execute(employeeQueryRemoval, employeeRemovalValues)
        db.executemany(employeeQuery, employeeValues)

        # Sync roles if the manager changed
        if oldManagerId and int(oldManagerId) != int(managerId):
            db.execute("""
                UPDATE Employees
                SET fk_role_id = (SELECT pk_role_id FROM Roles WHERE name = 'employee')
                WHERE pk_employee_id = ?
            """, (oldManagerId,))
        db.execute("""
            UPDATE Employees
            SET fk_role_id = (SELECT pk_role_id FROM Roles WHERE name = 'manager')
            WHERE pk_employee_id = ?
        """, (managerId,))

        db.commit()

        return {'message': 'success', 'pk_team_id': teamId}
    except Exception as e:
        return {'message': 'error', 'error': str(e)}

def deleteTeam(teamId):
    """
    Deletes a team record in the Team table.
    """
    try:
        existingTeam = getTeams(teamId)
        managerId = existingTeam[0]['fk_manager_id'] if existingTeam else None

        db = get_db()

        # Reset manager back to 'employee' role before deletion
        if managerId:
            db.execute("""
                UPDATE Employees
                SET fk_role_id = (SELECT pk_role_id FROM Roles WHERE name = 'employee')
                WHERE pk_employee_id = ?
            """, (managerId,))

        # Create query for Team
        teamQuery = """
            DELETE FROM Team
            WHERE pk_team_id = ?

        """
        teamValues = (teamId,)

        db.execute(teamQuery, teamValues)
        db.commit()

        return {'message': 'success', 'pk_team_id': teamId}
    except Exception as e:
        return {'message': 'error', 'error': str(e)}
