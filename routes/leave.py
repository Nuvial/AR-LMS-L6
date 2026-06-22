from flask import request, jsonify, Blueprint, render_template
from flask_login import login_required, current_user

from .models.leave import getLeave, getRemainingLeave, getRequestedLeave, approveLeave, denyLeave, requestLeave, deleteRequest, isLeaveInManagerTeam, getLeaveOwnerRole
from .auth import admin_required, admin_or_manager_required

leave = Blueprint('leave', __name__)

@leave.route('/')
@login_required
def index():
    return render_template('pages/process-leave.html', active_page='process_leave')


@leave.route('/get_leave', methods=['GET'])
@leave.route('/get_leave/<int:employee_id>', methods=['GET'])
@login_required
def getLeaveRoute(employee_id=None):
    """
    Route to get all or specific employee/s leave.
    Args:
        employee_id (int, optional): Employee ID to get. If not provided, gets all employees.
    """
    if request.method == 'GET':
        leave = getLeave(employee_id)
        
        if leave['message'] == 'success':
            return jsonify({'message': 'success', 'leave': leave['leave']})
        else:
            return jsonify({'message': 'error', 'error': leave['error']})

@leave.route('/get_leave/remaining', methods=['GET'])
@leave.route('/get_leave/remaining/<int:employee_id>', methods=['GET'])
@login_required
def getRemainingLeaveRoute(employee_id=None):
    """
    Route to get the remaining sick and annual leave for a specific employee.
    Args:
        employee_id (int): Employee ID to get remaining leave for.
    """
    if request.method == 'GET':
        stats = getRemainingLeave(employee_id)
        
        if stats:
            return jsonify(stats), 200
        else:
            return jsonify({"error": "No leave found"}), 404

@leave.route('/get_leave/requested', methods=['GET'])
@login_required
def getRequestedLeaveRoute():
    """
    Route to get employees with requested leave
    """
    if request.method == 'GET':
        employees = getRequestedLeave()

        if employees:
            return jsonify(employees), 200
        else:
            return jsonify({"error": "No requested leave." })
        
@leave.route('/update_leave/approve/<int:leave_id>', methods=['PUT'])
@login_required
@admin_or_manager_required
def approveLeaveRoute(leave_id):
    """
    Approves a specific leave id.
    Args:
        leave_id (int): Specific ID of the leave to approve.
        comment (str): Any admin comments.
    """
    if request.method == 'PUT':
        if not current_user.admin and not isLeaveInManagerTeam(leave_id, current_user.employee_id):
            return jsonify({"error": "You can only approve leave for employees in your team."}), 403
        if getLeaveOwnerRole(leave_id) == 'admin' and not current_user.admin:
            return jsonify({"error": "Admin leave requests must be approved by another admin."}), 403
        comments = request.get_json()['comment']
        approve = approveLeave(leave_id, comments)
        if approve == 'success':
            return {'data': 'success'}
        else:
            return jsonify({"error": "Could not approve leave." })

@leave.route('/update_leave/deny/<int:leave_id>', methods=['PUT'])
@login_required
@admin_or_manager_required
def denyLeaveRoute(leave_id):
    """
    Denies a specific leave id.
    Args:
        leave_id (int): Specific ID of the leave to deny.
        comment (str): Any admin comments.
    """
    if request.method == 'PUT':
        if not current_user.admin and not isLeaveInManagerTeam(leave_id, current_user.employee_id):
            return jsonify({"error": "You can only deny leave for employees in your team."}), 403
        if getLeaveOwnerRole(leave_id) == 'admin' and not current_user.admin:
            return jsonify({"error": "Admin leave requests must be approved by another admin."}), 403
        comments = request.get_json()['comment']
        deny = denyLeave(leave_id, comments)
        if deny == 'success':
            return {'data': 'success'}
        else:
            return jsonify({"error": "Could not deny leave." })

@leave.route('/update_leave/delete/<int:leave_id>', methods=['DELETE'])
@login_required
def deleteLeaveRoute(leave_id):
    """
    Deletes a specific leave id. Note: The leave HAS to be pending, otherwise it cannot be deleted once it has been approved.
    Args:
        leave_id (int): Specific ID of the leave to delete.
    """
    if request.method == 'DELETE':
        delete = deleteRequest(leave_id, current_user.employee_id)
        if delete == 'success':
            return {'data': 'success'}
        else:
            return jsonify({"error": "Could not delete leave." })

@leave.route('/request_leave/', methods=['POST'])
@login_required
def requestLeaveRoute():
    """
    Route to request leave for the logged in user.
    """
    if request.method == 'POST':
        data = request.get_json()
        fk_employee_id = current_user.employee_id
        leave_type = data['leave_type']
        start_date = data['start_date']
        end_date = data['end_date']
        comment_employee = data['employee_comments']

        leave_request = requestLeave(fk_employee_id, leave_type, start_date, end_date, comment_employee)
        if leave_request == 'success':
            return {'data': 'success'}
        else:
            return jsonify({"error": "Could not deny leave." })