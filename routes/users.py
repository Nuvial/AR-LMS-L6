import re

from flask import request, jsonify, Blueprint, render_template
from flask_login import login_required, current_user
from flask_bcrypt import Bcrypt

from .models.users import getUsers, deleteUser, changePassword, changeUsername, isUserInManagerTeam
from .models.auth import isEmployeeIdRegistered, usernameTaken, registerUser, upgradeUser, demoteUser
from .models.employees import get_employees
from .auth import admin_required, admin_or_manager_required

users = Blueprint('users', __name__)
bcrypt = Bcrypt()

_USERNAME_RE = re.compile(r'^[a-zA-Z0-9]+$')

def _validate_username(username):
    """Returns an error string or None if valid."""
    if not username or not _USERNAME_RE.match(str(username)):
        return 'Username must be alphanumeric.'
    if not (3 <= len(str(username)) <= 25):
        return 'Username must be between 3 and 25 characters.'
    return None

def _validate_password(password):
    """Returns an error string or None if valid."""
    if not password or len(str(password)) < 6:
        return 'Password must be at least 6 characters.'
    return None


@users.route('/')
@login_required
def index():
    return render_template('pages/users.html', active_page='modify_login')

@users.route('/settings')
@login_required
def settings():
    return render_template('pages/profile-settings.html', active_page='profile_settings')

@users.route('/get_users/self')
@login_required
def get_current_user():
    return getEmployeesRoute(current_user.id)

@users.route('/get_users', methods=['GET'])
@users.route('/get_users/<int:user_id>', methods=['GET'])
@login_required
def getEmployeesRoute(user_id=None):
    if request.method == 'GET':
        if current_user.admin or current_user.is_manager:
            users_data = getUsers(user_id)
        else:
            users_data = getUsers(current_user.id)

        if users_data:
            return jsonify(users_data)
        else:
            return jsonify({'message': 'error', 'error': 'No users found'})

@users.route('/get_users/is_registered/<int:employee_id>', methods=['GET'])
@login_required
def getIsRegisteredRoute(employee_id):
    registered = isEmployeeIdRegistered(employee_id)
    return jsonify({'registered': registered})

@users.route('/get_users/username_taken', methods=['GET'])
@login_required
def getUsernameTakenRoute():
    username = request.args.get('username')
    taken = usernameTaken(username)
    return jsonify({'registered': taken})

@users.route('/add_user', methods=['POST'])
@login_required
@admin_required
def addUser():
    args = request.get_json()
    if not args:
        return jsonify({'message': 'error', 'error': 'Missing request body'})

    employee_id = args.get('employee_id')
    username = args.get('username')
    password = args.get('password')
    admin = args.get('admin', False)

    if not employee_id or not username or not password:
        return jsonify({'message': 'error', 'error': 'Missing required fields'})

    username_err = _validate_username(username)
    if username_err:
        return jsonify({'message': 'error', 'error': username_err})

    password_err = _validate_password(password)
    if password_err:
        return jsonify({'message': 'error', 'error': password_err})

    if not get_employees(int(employee_id)):
        return jsonify({'message': 'error', 'error': 'Employee ID does not exist'})

    if isEmployeeIdRegistered(int(employee_id)):
        return jsonify({'message': 'error', 'error': 'This employee already has an account'})

    if usernameTaken(str(username)):
        return jsonify({'message': 'error', 'error': 'Username is already taken'})

    hashed_password = bcrypt.generate_password_hash(str(password)).decode('utf-8')
    register = registerUser({
        'employee_id': int(employee_id),
        'username': str(username),
        'hashed_password': hashed_password
    })

    if register['message'] != 'success':
        return jsonify({'message': 'error', 'error': 'Failed to create account'})

    if admin:
        upgrade = upgradeUser(register['pk_user_id'])
        if upgrade['message'] != 'success':
            return jsonify({'message': 'error', 'error': upgrade.get('error', 'Failed to upgrade account to admin')})

    return jsonify({'message': 'success'})

@users.route('/promote_user/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def promoteUserRoute(user_id):
    if request.method == 'PUT':
        upgrade = upgradeUser(user_id)
        if upgrade['message'] == 'success':
            return jsonify({'message': 'success'})
        else:
            return jsonify({'message': 'error', 'error': upgrade['error']})

@users.route('/demote_user/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def demoteUserRoute(user_id):
    if request.method == 'PUT':
        demote = demoteUser(user_id)
        if demote['message'] == 'success':
            return jsonify({'message': 'success'})
        else:
            return jsonify({'message': 'error', 'error': demote['error']})

@users.route('/delete_user/self', methods=['DELETE'])
@login_required
def deleteUserSelf():
    if request.method == 'DELETE':
        delete = deleteUser(current_user.id)
        if delete['message'] == 'success':
            return jsonify({'message': 'success'})
        else:
            return jsonify({'message': 'error', 'error': delete['error']})

@users.route('/delete_user/<int:user_id>', methods=['DELETE'])
@login_required
@admin_or_manager_required
def deleteUserRoute(user_id):
    if request.method == 'DELETE':
        if not current_user.admin and not isUserInManagerTeam(user_id, current_user.employee_id):
            return jsonify({'message': 'error', 'error': 'You can only delete accounts for employees in your team.'})
        delete = deleteUser(user_id)
        if delete['message'] == 'success':
            return jsonify({'message': 'success'})
        else:
            return jsonify({'message': 'error', 'error': delete['error']})

@users.route('/change_password/<int:user_id>', methods=['PUT'])
@login_required
def changePasswordRoute(user_id):
    if request.method == 'PUT':
        if not current_user.admin and user_id != current_user.id:
            if not current_user.is_manager or not isUserInManagerTeam(user_id, current_user.employee_id):
                return jsonify({'message': 'error', 'error': 'You can only change passwords for employees in your team.'})

        data = request.get_json()
        if not data or not data.get('password'):
            return jsonify({'message': 'error', 'error': 'Missing password'})

        password_err = _validate_password(data['password'])
        if password_err:
            return jsonify({'message': 'error', 'error': password_err})

        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        change = changePassword(user_id, hashed_password)
        if change == 'success':
            return jsonify({'message': 'success'})
        else:
            return jsonify({'message': 'error', 'error': 'Failed to change password'})

@users.route('/change_username/self', methods=['PUT'])
@login_required
def changeUsernameSelf():
    if request.method == 'PUT':
        data = request.get_json()
        if not data or not data.get('username'):
            return jsonify({'message': 'error', 'error': 'Missing username'})

        username = data['username']

        username_err = _validate_username(username)
        if username_err:
            return jsonify({'message': 'error', 'error': username_err})

        if usernameTaken(username) and username != current_user.username:
            return jsonify({'message': 'error', 'error': 'Username is already taken'})

        change = changeUsername(current_user.id, username)
        if change == 'success':
            return jsonify({'message': 'success'})
        else:
            return jsonify({'message': 'error', 'error': 'Failed to change username'})

@users.route('/change_username/<int:user_id>', methods=['PUT'])
@login_required
def changeUsernameRoute(user_id):
    if request.method == 'PUT':
        if not current_user.admin and user_id != current_user.id:
            if not current_user.is_manager or not isUserInManagerTeam(user_id, current_user.employee_id):
                return jsonify({'message': 'error', 'error': 'You can only change usernames for employees in your team.'})

        data = request.get_json()
        if not data or not data.get('username'):
            return jsonify({'message': 'error', 'error': 'Missing username'})

        username = data['username']

        username_err = _validate_username(username)
        if username_err:
            return jsonify({'message': 'error', 'error': username_err})

        target_users = getUsers(user_id)
        current_username = target_users[0]['username'] if target_users else None
        if usernameTaken(username) and username != current_username:
            return jsonify({'message': 'error', 'error': 'Username is already taken'})

        change = changeUsername(user_id, username)
        if change == 'success':
            return jsonify({'message': 'success'})
        else:
            return jsonify({'message': 'error', 'error': 'Failed to change username'})
