from flask import Blueprint, request, redirect, url_for, flash, render_template, abort
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt

from functools import wraps

from .models.auth import LoginForm, RegisterForm, User
from .models.auth import usernameTaken, isEmployeeIdRegistered, registerUser, forgotPassword, getUserData, unForgotPassword
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
    login_form = LoginForm()
    if request.method == 'POST' and login_form.validate_on_submit():
        user = User.get(login_form.username.data)
        if user and bcrypt.check_password_hash(user.password, login_form.password.data):
            unForgotPassword(user.id)
            login_user(user)
            return redirect(url_for('auth.dashboard', active_page='dashboard'))
        
        flash('Either the username or password are incorrect. Please try again.', 'danger')
    return render_template('pages/login.html', login_form=login_form)


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


        # Register user
        data = {
            'employee_id': employee_id,
            'username': username,
            'hashed_password': hashed_password
        }
        status = registerUser(data)

        if status['message'] == 'success':
            flash('Registration Successful! You may now log in.', 'success')
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