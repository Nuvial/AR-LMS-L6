from datetime import datetime

from flask import request, jsonify, Blueprint, render_template
from flask_login import login_required, current_user

from .models.leave import getLeave, getRemainingLeave, getRequestedLeave, approveLeave, denyLeave, requestLeave, deleteRequest, isLeaveInManagerTeam, getLeaveOwnerRole
from .auth import admin_required, admin_or_manager_required

leave = Blueprint('leave', __name__)

_VALID_LEAVE_TYPES = {'Annual Leave', 'Sick Leave'}

def _validate_leave_request(data):
    """Returns an error string or None if valid."""
    leave_type = data.get('leave_type')
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if not leave_type or not start_date or not end_date:
        return 'Missing required fields: leave_type, start_date, end_date'

    if leave_type not in _VALID_LEAVE_TYPES:
        return f"Invalid leave type. Must be one of: {', '.join(sorted(_VALID_LEAVE_TYPES))}"

    try:
        start = datetime.strptime(str(start_date), '%Y-%m-%d')
    except ValueError:
        return 'start_date must be in YYYY-MM-DD format'

    try:
        end = datetime.strptime(str(end_date), '%Y-%m-%d')
    except ValueError:
        return 'end_date must be in YYYY-MM-DD format'

    if start > end:
        return 'start_date must not be after end_date'

    return None


@leave.route('/')
@login_required
def index():
    return render_template('pages/process-leave.html', active_page='process_leave')


@leave.route('/get_leave', methods=['GET'])
@leave.route('/get_leave/<int:employee_id>', methods=['GET'])
@login_required
def getLeaveRoute(employee_id=None):
    if request.method == 'GET':
        result = getLeave(employee_id)
        if result['message'] == 'success':
            return jsonify({'message': 'success', 'leave': result['leave']})
        else:
            return jsonify({'message': 'error', 'error': result['error']})

@leave.route('/get_leave/remaining', methods=['GET'])
@leave.route('/get_leave/remaining/<int:employee_id>', methods=['GET'])
@login_required
def getRemainingLeaveRoute(employee_id=None):
    if request.method == 'GET':
        result = getRemainingLeave(employee_id)
        if result:
            return jsonify(result)
        else:
            return jsonify({'message': 'error', 'error': 'No leave found'})

@leave.route('/get_leave/requested', methods=['GET'])
@login_required
def getRequestedLeaveRoute():
    if request.method == 'GET':
        employees = getRequestedLeave()
        if employees:
            return jsonify(employees)
        else:
            return jsonify({'message': 'error', 'error': 'No requested leave'})

@leave.route('/update_leave/approve/<int:leave_id>', methods=['PUT'])
@login_required
@admin_or_manager_required
def approveLeaveRoute(leave_id):
    if request.method == 'PUT':
        if not current_user.admin and not isLeaveInManagerTeam(leave_id, current_user.employee_id):
            return jsonify({'message': 'error', 'error': 'You can only approve leave for employees in your team.'})
        if getLeaveOwnerRole(leave_id) == 'admin' and not current_user.admin:
            return jsonify({'message': 'error', 'error': 'Admin leave requests must be approved by another admin.'})

        comments = request.get_json().get('comment', '')
        approve = approveLeave(leave_id, comments)
        if approve == 'success':
            return jsonify({'message': 'success'})
        else:
            return jsonify({'message': 'error', 'error': 'Could not approve leave'})

@leave.route('/update_leave/deny/<int:leave_id>', methods=['PUT'])
@login_required
@admin_or_manager_required
def denyLeaveRoute(leave_id):
    if request.method == 'PUT':
        if not current_user.admin and not isLeaveInManagerTeam(leave_id, current_user.employee_id):
            return jsonify({'message': 'error', 'error': 'You can only deny leave for employees in your team.'})
        if getLeaveOwnerRole(leave_id) == 'admin' and not current_user.admin:
            return jsonify({'message': 'error', 'error': 'Admin leave requests must be approved by another admin.'})

        comments = request.get_json().get('comment', '')
        deny = denyLeave(leave_id, comments)
        if deny == 'success':
            return jsonify({'message': 'success'})
        else:
            return jsonify({'message': 'error', 'error': 'Could not deny leave'})

@leave.route('/update_leave/delete/<int:leave_id>', methods=['DELETE'])
@login_required
def deleteLeaveRoute(leave_id):
    if request.method == 'DELETE':
        delete = deleteRequest(leave_id, current_user.employee_id)
        if delete == 'success':
            return jsonify({'message': 'success'})
        else:
            return jsonify({'message': 'error', 'error': 'Could not delete leave'})

@leave.route('/request_leave/', methods=['POST'])
@login_required
def requestLeaveRoute():
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'message': 'error', 'error': 'Missing request body'})

        err = _validate_leave_request(data)
        if err:
            return jsonify({'message': 'error', 'error': err})

        leave_request = requestLeave(
            current_user.employee_id,
            data['leave_type'],
            data['start_date'],
            data['end_date'],
            data.get('employee_comments', '')
        )
        if leave_request == 'success':
            return jsonify({'message': 'success'})
        else:
            return jsonify({'message': 'error', 'error': 'Could not submit leave request'})
