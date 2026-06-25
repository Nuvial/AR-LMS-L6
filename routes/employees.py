import re

from flask import request, jsonify, Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from .models.employees import add_employee, get_employees, update_employee, delete_employee, is_last_admin
from .auth import admin_required

employees = Blueprint('employees', __name__)

_NAME_RE = re.compile(r"^[a-zA-Z\- ]+$")

def _validate_employee_fields(data, require_all=True):
    """
    Validates employee fields. Returns an error string or None.
    When require_all=False only validates fields that are present.
    """
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    leave_bal = data.get('default_leave_balance')
    sick_bal = data.get('default_sick_leave_balance')
    daily_hours = data.get('contracted_daily_hours')
    weekly_hours = data.get('contracted_weekly_hours')

    if require_all:
        if (not first_name or not last_name or leave_bal is None or sick_bal is None
                or daily_hours is None or weekly_hours is None):
            return 'Missing required fields'

    if first_name is not None:
        if not _NAME_RE.match(str(first_name).strip()) or not (1 <= len(str(first_name).strip()) <= 32):
            return 'First name must be 1-32 letters, spaces or hyphens only'

    if last_name is not None:
        if not _NAME_RE.match(str(last_name).strip()) or not (1 <= len(str(last_name).strip()) <= 32):
            return 'Last name must be 1-32 letters, spaces or hyphens only'

    if leave_bal is not None:
        try:
            val = float(leave_bal)
            if not (0 <= val <= 5000):
                return 'Default leave balance must be between 0 and 5000 hours'
        except (ValueError, TypeError):
            return 'Default leave balance must be a number'

    if sick_bal is not None:
        try:
            val = float(sick_bal)
            if not (0 <= val <= 5000):
                return 'Default sick leave balance must be between 0 and 5000 hours'
        except (ValueError, TypeError):
            return 'Default sick leave balance must be a number'

    if daily_hours is not None:
        try:
            val = float(daily_hours)
            if not (0 < val <= 24):
                return 'Contracted daily hours must be between 0 and 24'
        except (ValueError, TypeError):
            return 'Contracted daily hours must be a number'

    if weekly_hours is not None:
        try:
            val = float(weekly_hours)
            if not (0 < val <= 168):
                return 'Contracted weekly hours must be between 0 and 168'
        except (ValueError, TypeError):
            return 'Contracted weekly hours must be a number'

    return None


@employees.route('/')
@login_required
def index():
    return render_template('pages/employees-view.html', active_page='view_records')

@employees.route('/modify')
@login_required
@admin_required
def modify_index():
    return redirect(url_for('employees.index'))

@employees.route('/get_employees/self', methods=['GET'])
@login_required
def get_current_employee():
    if request.method == 'GET':
        employee = get_employees(current_user.employee_id)
        if employee:
            return jsonify(employee)
        else:
            return jsonify({'message': 'error', 'error': 'No employee found'})

@employees.route('/get_employees', methods=['GET'])
@employees.route('/get_employees/<int:employee_id>', methods=['GET'])
@login_required
def get_employees_route(employee_id=None):
    if request.method == 'GET':
        employees_data = get_employees(employee_id)
        if employees_data:
            return jsonify(employees_data)
        else:
            return jsonify({'message': 'error', 'error': 'No employees found'})

@employees.route('/add_employee', methods=['POST'])
@login_required
@admin_required
def add_employee_route():
    if request.method == 'POST':
        employee_data = request.get_json()
        if not employee_data:
            return jsonify({'message': 'error', 'error': 'Missing request body'})

        err = _validate_employee_fields(employee_data, require_all=True)
        if err:
            return jsonify({'message': 'error', 'error': err})

        try:
            status = add_employee(employee_data)
            if status['status'] == 'success':
                return jsonify({'message': 'success', 'employee_id': status['employee_id']})
            else:
                return jsonify({'message': 'error', 'error': 'Failed to add employee'})
        except Exception as e:
            return jsonify({'message': 'error', 'error': str(e)})

@employees.route('/update_employee/self', methods=['PUT'])
@login_required
def updateEmployeeSelf():
    if request.method == 'PUT':
        employee_data = request.get_json()
        if not employee_data:
            return jsonify({'message': 'error', 'error': 'Missing request body'})

        # Self-updates only allow first/last name — validate only those
        partial = {k: v for k, v in employee_data.items() if k in ('first_name', 'last_name')}
        err = _validate_employee_fields(partial, require_all=False)
        if err:
            return jsonify({'message': 'error', 'error': err})

        try:
            status = update_employee(current_user.id, employee_data)
            if status == 'success':
                return jsonify({'message': 'success'})
            else:
                return jsonify({'message': 'error', 'error': 'Failed to update employee'})
        except Exception as e:
            return jsonify({'message': 'error', 'error': str(e)})

@employees.route('/update_employee/<int:employee_id>', methods=['PUT'])
@login_required
@admin_required
def update_employee_route(employee_id):
    if request.method == 'PUT':
        employee_data = request.get_json()
        if not employee_data:
            return jsonify({'message': 'error', 'error': 'Missing request body'})

        err = _validate_employee_fields(employee_data, require_all=False)
        if err:
            return jsonify({'message': 'error', 'error': err})

        try:
            status = update_employee(employee_id, employee_data)
            if status == 'success':
                return jsonify({'message': 'success'})
            else:
                return jsonify({'message': 'error', 'error': 'Failed to update employee'})
        except Exception as e:
            return jsonify({'message': 'error', 'error': str(e)})

@employees.route('/delete_employee/<int:employee_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_employee_route(employee_id):
    if request.method == 'DELETE':
        try:
            if employee_id == current_user.employee_id and is_last_admin(employee_id):
                return jsonify({'message': 'error', 'error': 'Cannot delete your account as you are the only admin. Please assign another admin first.'})
            status = delete_employee(employee_id)
            if status == 'success':
                return jsonify({'message': 'success'})
            else:
                return jsonify({'message': 'error', 'error': 'Failed to delete employee'})
        except Exception as e:
            return jsonify({'message': 'error', 'error': str(e)})
