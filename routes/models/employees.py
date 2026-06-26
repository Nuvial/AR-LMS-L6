from db import get_db
from flask_login import current_user

# Employee Table CRUD operations
def add_employee(data):
    """
    Add a new employee to the database.
    Args:
        data (dict): A dictionary containing employee details.
            Required keys include:
            'first_name'
            'last_name'
            'default_leave_balance'
            'default_sick_leave_balance'
            'contracted_daily_hours'
            'contracted_weekly_hours'
    """
    try:
        first_name = data['first_name']
        last_name = data['last_name']
        leave_bal = data['default_leave_balance']
        sick_leave_bal = data['default_sick_leave_balance']
        daily_hours = data['contracted_daily_hours']
        weekly_hours = data['contracted_weekly_hours']

        query = """
            INSERT INTO Employees (first_name, last_name, default_leave_balance, default_sick_leave_balance,
                                   contracted_daily_hours, contracted_weekly_hours, fk_role_id)
            VALUES (?, ?, ?, ?, ?, ?, (SELECT pk_role_id FROM Roles WHERE name = 'employee'))
            """
        values = (first_name, last_name, leave_bal, sick_leave_bal, daily_hours, weekly_hours)

        db = get_db()
        cursor = db.execute(query, values)
        db.commit()
        new_id = cursor.lastrowid

        return {'status': 'success', 'employee_id': new_id}

    except KeyError as e:
        raise KeyError(f"Data must contain the key: {e}")
    except TypeError as e:
        raise TypeError(f"Data must be a dictionary: {e}")
    except Exception as e:
        raise Exception(f"An error occurred: {e}")

def get_employees(employee_id=None):
    """
    Get all employees from the database (based on permissions) or a specific employee by ID.
    Args:
        employee_id (int, optional): The ID of the employee to get.
    """
    try:
        query = """
            SELECT
                e.pk_employee_id,
                e.fk_team_id,
                e.fk_role_id,
                e.first_name,
                e.last_name,
                e.default_leave_balance,
                e.default_sick_leave_balance,
                e.contracted_daily_hours,
                e.contracted_weekly_hours,
                r.name AS role,
                t.name AS team_name,
                t.fk_manager_id,
                m.first_name AS manager_first_name,
                m.last_name AS manager_last_name
            FROM Employees e
            JOIN Roles r ON e.fk_role_id = r.pk_role_id
            LEFT JOIN Team t ON e.fk_team_id = t.pk_team_id
            LEFT JOIN Employees m ON m.pk_employee_id = t.fk_manager_id
        """
        values = ()
        conditions = []
        if employee_id:
            conditions.append("e.pk_employee_id = ?")
            values += (employee_id,)

        if current_user.is_authenticated and not current_user.admin and employee_id != current_user.employee_id:
            conditions.append("(t.fk_manager_id = ? OR e.pk_employee_id = ?)")
            values += (current_user.employee_id, current_user.employee_id)

        if conditions:
            query += f"WHERE {' AND '.join(conditions)};"

        db = get_db()
        employees_data = db.execute(query, values).fetchall()
        return [dict(row) for row in employees_data]
    except Exception as e:
        raise Exception(f"An error occurred: {e}")


def update_employee(employee_id, data):
    """
    Update an employee's details in the database.
    Args:
        employee_id (int): The ID of the employee to change.
        data (dict): A dictionary containing the employee fields to update.
            Valid keys include:
            'first_name'
            'last_name'
            'default_leave_balance'
            'default_sick_leave_balance'
            'contracted_daily_hours'
            'contracted_weekly_hours'
    """
    try:
        if not isinstance(data, dict):
            raise TypeError('Data must be a dictionary.')

        if employee_id == current_user.id and not current_user.admin:
            valid_fields = ['first_name', 'last_name']
        else:
            valid_fields = [
                'first_name',
                'last_name',
                'default_leave_balance',
                'default_sick_leave_balance',
                'contracted_daily_hours',
                'contracted_weekly_hours',
            ]

        fields_to_update = []
        values = []

        for key in valid_fields:
            if key in data:
                fields_to_update.append(f"{key} = ?")
                values.append(data[key])

        if not fields_to_update:
            raise ValueError('Data does not contain any valid fields to update.')

        set_clause = ', '.join(fields_to_update)
        query = f"UPDATE Employees SET {set_clause} WHERE pk_employee_id = ?"  # nosec B608 -- set_clause contains only column names from the server-side valid_fields whitelist; user values are in the parameterised `values` list
        values.append(employee_id)

        db = get_db()
        db.execute(query, values)
        db.commit()

        return 'success'

    except Exception as e:
        raise Exception(f"An error occurred: {e}")


def is_team_manager(employee_id):
    """Returns True if the employee is currently assigned as a manager of any team."""
    try:
        db = get_db()
        count = db.execute(
            "SELECT COUNT(*) AS count FROM Team WHERE fk_manager_id = ?",
            (employee_id,)
        ).fetchone()['count']
        return count > 0
    except Exception as e:
        raise e


def is_last_admin(employee_id):
    """Returns True if employee_id is an admin AND the only admin in the system."""
    try:
        db = get_db()
        admin_count = db.execute("""
            SELECT COUNT(*) as count FROM Employees e
            JOIN Roles r ON e.fk_role_id = r.pk_role_id
            WHERE r.name = 'admin'
        """).fetchone()['count']
        if admin_count > 1:
            return False
        is_admin = db.execute("""
            SELECT COUNT(*) as count FROM Employees e
            JOIN Roles r ON e.fk_role_id = r.pk_role_id
            WHERE e.pk_employee_id = ? AND r.name = 'admin'
        """, (employee_id,)).fetchone()['count']
        return is_admin > 0
    except Exception as e:
        raise e


def delete_employee(employee_id):
    """
    Delete an employee from the database.
    Args:
        employee_id (int): Employee ID to delete.
    """
    try:
        query = """
            DELETE FROM Employees
            WHERE pk_employee_id = ?
        """
        db = get_db()
        db.execute(query, (employee_id,))
        db.commit()
        return 'success'
    except Exception as e:
        raise Exception(f"An error occurred: {e}")
