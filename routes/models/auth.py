from flask_login import UserMixin

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from wtforms.validators import InputRequired, Length

from db import get_db


class User(UserMixin):
    def __init__(self, id, employee_id, username, password, role):
        self.id = id
        self.employee_id = employee_id
        self.username = username
        self.password = password
        self.role = role  # 'admin' | 'manager' | 'employee'

    @property
    def admin(self):
        return self.role == 'admin'

    @property
    def is_manager(self):
        return self.role == 'manager'

    @staticmethod
    def get(username):
        user_data = getUserData(username)
        if user_data:
            return User(
                user_data['pk_user_id'],
                user_data['fk_employee_id'],
                user_data['username'],
                user_data['password'],
                user_data['role']
            )
        return None


class LoginForm(FlaskForm):
    username = StringField('Username:', validators=[InputRequired(), Length(min=3)])
    password = PasswordField('Password:', validators=[InputRequired()])
    submit = SubmitField('Login')


class RegisterForm(FlaskForm):
    employee_id = IntegerField('Employee ID:', validators=[InputRequired()])
    username = StringField('Username:', validators=[InputRequired(), Length(min=3, max=25)])
    password = PasswordField('Password:', validators=[InputRequired(), Length(min=6)])
    submit = SubmitField('Register')


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def getUserData(username):
    db = get_db()
    query = """
        SELECT u.*, r.name AS role
        FROM Users u
        JOIN Employees e ON u.fk_employee_id = e.pk_employee_id
        JOIN Roles r ON e.fk_role_id = r.pk_role_id
        WHERE u.username = ?
    """
    return db.execute(query, (username,)).fetchone()


def isEmployeeIdRegistered(id):
    db = get_db()
    query = "SELECT username FROM Users WHERE fk_employee_id = ?"
    return db.execute(query, (id,)).fetchone() is not None


def usernameTaken(username):
    db = get_db()
    query = "SELECT pk_user_id FROM Users WHERE username = ?"
    return db.execute(query, (username,)).fetchone() is not None


def registerUser(data):
    try:
        query = """
            INSERT INTO Users (fk_employee_id, username, password)
            VALUES (?, ?, ?)
        """
        values = (data['employee_id'], data['username'], data['hashed_password'])

        db = get_db()
        cursor = db.execute(query, values)
        db.commit()
        return {'message': 'success', 'pk_user_id': cursor.lastrowid}
    except Exception as e:
        return {'message': 'error', 'error': e}


def upgradeUser(user_id):
    """Promote a user to admin by updating their role in Employees."""
    try:
        db = get_db()

        is_team_manager = db.execute("""
            SELECT pk_team_id FROM Team
            WHERE fk_manager_id = (SELECT fk_employee_id FROM Users WHERE pk_user_id = ?)
        """, (user_id,)).fetchone()
        if is_team_manager:
            return {'message': 'error', 'error': 'Cannot promote a team manager to admin. Remove them from team management first.'}

        is_team_member = db.execute("""
            SELECT fk_team_id FROM Employees e
            WHERE fk_team_id IS NOT NULL AND pk_employee_id = (SELECT fk_employee_id FROM Users where pk_user_id = ?)
        """, (user_id,)).fetchone()
        if is_team_member:
            return {'message': 'error', 'error': 'Cannot promote a team member to admin. Remove them from the team first.'}

        db.execute("""
            UPDATE Employees
            SET fk_role_id = (SELECT pk_role_id FROM Roles WHERE name = 'admin')
            WHERE pk_employee_id = (SELECT fk_employee_id FROM Users WHERE pk_user_id = ?)
        """, (user_id,))
        db.commit()

        return {'message': 'success'}
    except Exception as e:
        raise e


def demoteUser(user_id):
    """Demote a user back to employee by updating their role in Employees."""
    try:
        db = get_db()
        admin_count = db.execute("""
            SELECT COUNT(*) as count
            FROM Users u
            JOIN Employees e ON u.fk_employee_id = e.pk_employee_id
            JOIN Roles r ON e.fk_role_id = r.pk_role_id
            WHERE r.name = 'admin'
        """).fetchone()['count']
        if admin_count <= 1:
            return {'message': 'error', 'error': 'Cannot demote the only admin account. Please assign another admin first.'}

        db.execute("""
            UPDATE Employees
            SET fk_role_id = (SELECT pk_role_id FROM Roles WHERE name = 'employee')
            WHERE pk_employee_id = (SELECT fk_employee_id FROM Users WHERE pk_user_id = ?)
        """, (user_id,))
        db.commit()
        return {'message': 'success'}
    except Exception as e:
        raise e


def forgotPassword(id):
    try:
        db = get_db()
        db.execute("UPDATE Users SET forgot_password = 1 WHERE pk_user_id = ?", (id,))
        db.commit()
        return 'success'
    except Exception as e:
        raise e


def unForgotPassword(id):
    try:
        db = get_db()
        db.execute("UPDATE Users SET forgot_password = 0 WHERE pk_user_id = ?", (id,))
        db.commit()
        return 'success'
    except Exception as e:
        raise e
