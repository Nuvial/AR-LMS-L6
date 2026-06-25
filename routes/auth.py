from flask import Blueprint, request, redirect, url_for, flash, render_template, abort, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

from functools import wraps

from .models.auth import LoginForm, RegisterForm, ForceChangePasswordForm, User
from .models.auth import usernameTaken, isEmployeeIdRegistered, registerUser, forgotPassword, getUserData, getUserDataById, unForgotPassword
from .models.users import changePassword, validate_password, getUserPasswordHash
from .models.employees import get_employees

# Initialise blueprint and bcrypt
auth = Blueprint('auth', __name__)
bcrypt = Bcrypt()

# Custom decorator function to enforce admin permission on admin routes.
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.admin:
            flash('You need to be an admin to access this page.', 'danger')
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def admin_or_manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.admin and not current_user.is_manager:
            flash('You need to be an admin or team manager to access this page.', 'danger')
            return redirect(url_for('auth.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    login_form = LoginForm()
    if request.method == 'POST' and login_form.validate_on_submit():
        user_data = getUserData(login_form.username.data)
        if user_data and bcrypt.check_password_hash(user_data['password'], login_form.password.data):
            if user_data['pending_confirmation']:
                flash('Your account registration is awaiting admin confirmation. Please contact an administrator.', 'warning')
                return render_template('pages/login.html', login_form=login_form)
            if user_data['password_reset_required']:
                session['pending_password_reset_user_id'] = user_data['pk_user_id']
                return redirect(url_for('auth.force_change_password'))
            user = User(user_data['pk_user_id'], user_data['fk_employee_id'], user_data['username'], user_data['password'], user_data['role'])
            unForgotPassword(user.id)
            login_user(user)
            return redirect(url_for('auth.dashboard', active_page='dashboard'))

        flash('Either the username or password are incorrect. Please try again.', 'danger')
    return render_template('pages/login.html', login_form=login_form)


@auth.route('/force_change_password', methods=['GET', 'POST'])
def force_change_password():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))

    user_id = session.get('pending_password_reset_user_id')
    if not user_id:
        return redirect(url_for('auth.login'))

    user_data = getUserDataById(user_id)
    if not user_data or not user_data['password_reset_required']:
        session.pop('pending_password_reset_user_id', None)
        return redirect(url_for('auth.login'))

    form = ForceChangePasswordForm()
    if form.validate_on_submit():
        if form.password.data != form.confirm_password.data:
            flash('Passwords do not match.', 'danger')
            return render_template('pages/force-change-password.html', form=form)

        current_hash = getUserPasswordHash(user_id)
        password_errs = validate_password(form.password.data, current_hash=current_hash)
        if password_errs:
            flash(password_errs[0], 'danger')
            return render_template('pages/force-change-password.html', form=form)

        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        result = changePassword(user_id, hashed_password, reset_required=False)
        if result == 'success':
            session.pop('pending_password_reset_user_id', None)
            flash('Password changed successfully. Please log in with your new password.', 'success')
            return redirect(url_for('auth.login'))

        flash('An error occurred. Please try again.', 'danger')

    return render_template('pages/force-change-password.html', form=form)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        employee_id = form.employee_id.data
        username = form.username.data
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')

        #Check if username already exists
        username_invalid = usernameTaken(username)
        if username_invalid:
            flash('Username already exists. Please pick a different username and try again.', 'danger')
            return render_template('pages/register.html', register_form=form)
        
        #Check if employee_id is a valid id
        employee_id_valid = get_employees(employee_id)
        if not employee_id_valid:
            flash('Employee ID does not exist. Please ensure it is correct and try again. Otherwise, please ask an admin to add you to the system.', 'danger')
            return render_template('pages/register.html', register_form=form)
        
        #Check if employee_id is already registered
        user_id_invalid = isEmployeeIdRegistered(employee_id)
        if user_id_invalid:
            flash('Employee ID is already registered to a username. Please ensure it is correct and try again.', 'danger')
            return render_template('pages/register.html', register_form=form)


        # Register user (pending admin confirmation)
        data = {
            'employee_id': employee_id,
            'username': username,
            'hashed_password': hashed_password
        }
        status = registerUser(data, pending=True)

        if status['message'] == 'success':
            flash('Registration submitted. Your account is awaiting admin confirmation before you can log in.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('pages/register.html', register_form=form)


@auth.route('/forgot_password/<user_id>', methods=['POST'])
def forgot_password(user_id):
    if request.method == 'POST':
        status = forgotPassword(user_id)
        if status == 'success':
            flash('Request to reset password sent. Please inform an admin member to approve this request.', 'success')
            return {'status': 'success'}
        return {'status': 'error'}


@auth.route('/check_users/<username>', methods=['GET'])
def check_users(username):
    if request.method == 'GET':
        user = getUserData(username)
        if user:
            return {'user_id': user['pk_user_id']}
        return {'user_id': ''}


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))


@auth.route('/dashboard')
@login_required
def dashboard():
    return render_template('pages/dashboard.html', active_page='dashboard')