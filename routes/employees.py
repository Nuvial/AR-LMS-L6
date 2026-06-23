from flask import request, jsonify, Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required, current_user

from .models.employees import add_employee, get_employees, update_employee, delete_employee
from .auth import admin_required

employees = Blueprint('employees', __name__)

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
            return jsonify(employee), 200
        else:
            return jsonify({"error": "No employees found"})

@employees.route('/get_employees', methods=['GET'])
@employees.route('/get_employees/<int:employee_id>', methods=['GET'])
@login_required
def get_employees_route(employee_id=None):
    """
    Route to get all or specific employee/s. <br>
    If route is requested by a non-admin account, only the requesting users details are ever returned.
    Args:
        employee_id (int, optional): Employee ID to get. If not provided, gets all employees.
    """
    if request.method == 'GET':
        employees_data = get_employees(employee_id)
        
        if employees_data:
            return jsonify(employees_data), 200
        else:
            return jsonify({"error": "No employees found"})


@employees.route('/add_employee', methods=['POST'])
@login_required
@admin_required
def add_employee_route():
    """
    Route to add a new employee.
    Args:
        None (expects JSON payload in request body):
            - first_name (str): The employee's first name.
            - last_name (str): The employee's last name.
            - employee_position (str): The employee's position.
            - default_leave_balance (float/int): The base leave balance for the employee.
            - default_sick_leave_balance (float/int): The base sick leave balance for the employee.
    """
    if request.method == 'POST':
        employee_data = request.get_json()
        first_name = employee_data.get('first_name')
        last_name = employee_data.get('last_name')
        position = employee_data.get('employee_position')
        default_leave_balance = employee_data.get('default_leave_balance')
        default_sick_leave_balance = employee_data.get('default_sick_leave_balance')


        if not first_name or not last_name or not position or not default_leave_balance or not default_sick_leave_balance:
            return jsonify({"error": "Missing required fields"}), 400
        
        try: 
            status = add_employee(employee_data)
            if status['status'] == 'success':
                return jsonify({"message": "Employee added successfully", 'employee_id': status['employee_id']}), 201
            else:
                return jsonify({"error": "Failed to add employee"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@employees.route('/update_employee/self', methods=['PUT'])
@login_required
def updateEmployeeSelf():
    """
    Route to update self employee record.
    Args:
        employee_id (int): Employee ID to update.
    """
    if request.method == 'PUT':
        employee_data = request.get_json()
        try:
            status = update_employee(current_user.id, employee_data)
            if status == 'success':
                return jsonify({"message": "Employee updated successfully"}), 200
            else:
                return jsonify({"error": "Failed to update employee"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@employees.route('/update_employee/<int:employee_id>', methods=['PUT'])
@login_required
@admin_required
def update_employee_route(employee_id):
    """
    Route to update an existing employee.
    Args:
        employee_id (int): Employee ID to update.
    """
    if request.method == 'PUT':
        employee_data = request.get_json()
        try:
            status = update_employee(employee_id, employee_data)
            if status == 'success':
                return jsonify({"message": "Employee updated successfully"}), 200
            else:
                return jsonify({"error": "Failed to update employee"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@employees.route('/delete_employee/<int:employee_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_employee_route(employee_id):
    """
    Route to delete an employee.
    Args:
        employee_id (int): Employee ID to delete.
    """
    if request.method == 'DELETE':
        try:
            status = delete_employee(employee_id)
            if status == 'success':
                return jsonify({"message": "Employee deleted successfully"}), 200
            else:
                return jsonify({"error": "Failed to delete employee"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500