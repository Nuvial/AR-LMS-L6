import hashlib
import os
import urllib.request
import urllib.error

from flask_login import current_user
from flask_bcrypt import Bcrypt as _Bcrypt
from db import get_db

_bcrypt = _Bcrypt()

_HIBP_ENABLED = os.getenv('HIBP_ENABLED', 'true').strip().lower() not in ('false', '0', 'no')
_HIBP_TIMEOUT = 3  # seconds


def _check_hibp(password):
    """
    K-anonymity check against the HIBP Pwned Passwords API (OWASP ASVS V2.1.7).

    Only the first 5 hex characters of the SHA-1 hash are sent to HIBP;
    the remaining 35 characters never leave this process, so the plaintext
    password is never exposed.

    Returns the breach count for this password (0 = not found in any breach).
    Raises RuntimeError if the API is unreachable or returns an unexpected status,
    allowing the caller to decide whether to fail open or closed.
    """
    sha1 = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]

    req = urllib.request.Request(
        f'https://api.pwnedpasswords.com/range/{prefix}',
        headers={'User-Agent': 'employee-management-app'},
    )
    try:
        with urllib.request.urlopen(req, timeout=_HIBP_TIMEOUT) as resp:
            if resp.status != 200:
                raise RuntimeError(f'HIBP returned HTTP {resp.status}')
            body = resp.read().decode('utf-8')
    except urllib.error.URLError as exc:
        raise RuntimeError(f'HIBP unreachable: {exc}')

    for line in body.splitlines():
        parts = line.split(':')
        if len(parts) == 2 and parts[0] == suffix:
            return int(parts[1])
    return 0


def validate_password(password, current_hash=None):
    """
    OWASP-aligned password validation (NIST SP 800-63B / OWASP ASVS V2.1).
    Returns a list of error strings; an empty list means the password is valid.

    HIBP failure policy: fail open if the API is unreachable the check is
    skipped rather than blocking the user.
    """
    errors = []
    if not password:
        errors.append('Password is required.')
        return errors
    if len(password) < 8:
        errors.append('Password must be at least 8 characters.')
    if len(password) > 128:
        errors.append('Password must not exceed 128 characters.')
    if current_hash and not errors:
        if _bcrypt.check_password_hash(current_hash, password):
            errors.append('New password must be different from the current password.')
    if not errors and _HIBP_ENABLED:
        try:
            breach_count = _check_hibp(password)
            if breach_count > 0:
                errors.append(
                    f'This password has appeared in {breach_count:,} known data breach(es) '
                    f'and cannot be used. Please choose a different password.'
                )
        except RuntimeError:
            pass  # Fail open: HIBP unavailable; allow the password through
    return errors


def getUserPasswordHash(user_id):
    """Returns the stored password hash for a user, or None if not found."""
    db = get_db()
    row = db.execute("SELECT password FROM Users WHERE pk_user_id = ?", (user_id,)).fetchone()
    return row['password'] if row else None

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
        conditions = ["a.pending_confirmation = 0"]

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

def changePassword(id, password, reset_required=False):
    """
    Changes a users password.
    Args:
        id (int): The User ID of the password to change.
        password (str): A hashed password to change to.
        reset_required (bool): If True, forces the user to change password on next login.
    """
    try:
        query = """
            UPDATE Users
            SET
                password = ?,
                forgot_password = 0,
                password_reset_required = ?
            WHERE pk_user_id = ?
        """
        values = (password, 1 if reset_required else 0, id)

        db = get_db()
        db.execute(query, values)
        db.commit()

        return 'success'
    except Exception as e:
        raise e

def getUnregisteredEmployees():
    """Returns employees who have no login account (active or pending)."""
    try:
        db = get_db()
        query = """
            SELECT e.pk_employee_id, e.first_name, e.last_name
            FROM Employees e
            WHERE e.pk_employee_id NOT IN (SELECT fk_employee_id FROM Users)
            ORDER BY e.pk_employee_id
        """
        return [dict(row) for row in db.execute(query).fetchall()]
    except Exception as e:
        raise Exception(f"An error occurred: {e}")


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