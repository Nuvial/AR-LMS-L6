from flask import request, jsonify, Blueprint, render_template
from flask_login import login_required

from .models.stats import getStats, updateStats, addStats, Averages
from .auth import admin_required

stats = Blueprint('stats', __name__)

def _validate_stats_fields(data, require_all=True):
    """Returns an error string or None if valid."""
    attendance = data.get('attendance')
    productivity = data.get('productivity')
    performance = data.get('performance')

    if require_all:
        if attendance is None or productivity is None or performance is None:
            return 'Missing required fields: attendance, productivity, performance'

    if attendance is not None:
        try:
            val = float(attendance)
            if not (0 <= val <= 100):
                return 'Attendance must be between 0 and 100'
        except (ValueError, TypeError):
            return 'Attendance must be a number'

    if productivity is not None:
        try:
            val = float(productivity)
            if not (0 <= val <= 100):
                return 'Productivity must be between 0 and 100'
        except (ValueError, TypeError):
            return 'Productivity must be a number'

    if performance is not None:
        try:
            val = float(performance)
            if not (0 <= val <= 10):
                return 'Performance must be between 0 and 10'
        except (ValueError, TypeError):
            return 'Performance must be a number'

    return None


@stats.route('/create/<int:employee_id>', methods=['POST'])
@login_required
@admin_required
def createStatsRoute(employee_id):
    if request.method == 'POST':
        employee_data = request.get_json()
        if not employee_data:
            return jsonify({'message': 'error', 'error': 'Missing request body'})

        err = _validate_stats_fields(employee_data, require_all=True)
        if err:
            return jsonify({'message': 'error', 'error': err})

        try:
            status = addStats(employee_id, employee_data)
            if status['status'] == 'success':
                return jsonify({'message': 'success'})
            else:
                return jsonify({'message': 'error', 'error': 'Failed to add employee stats'})
        except Exception as e:
            return jsonify({'message': 'error', 'error': str(e)})


@stats.route('/get_stats', methods=['GET'])
@stats.route('/get_stats/<int:employee_id>', methods=['GET'])
@login_required
def getStatsRoute(employee_id=None):
    if request.method == 'GET':
        stats_data = getStats(employee_id)
        if stats_data:
            return jsonify(stats_data)
        else:
            return jsonify({'message': 'error', 'error': 'No stats found'})

@stats.route('/update/<int:employee_id>', methods=['PUT'])
@login_required
@admin_required
def updateStatsRoute(employee_id):
    if request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({'message': 'error', 'error': 'Missing request body'})

        err = _validate_stats_fields(data, require_all=False)
        if err:
            return jsonify({'message': 'error', 'error': err})

        try:
            status = updateStats(employee_id, data)
            if status == 'success':
                return jsonify({'message': 'success'})
            else:
                return jsonify({'message': 'error', 'error': 'Failed to update employee stats'})
        except Exception as e:
            return jsonify({'message': 'error', 'error': str(e)})



# --------------- Averages Routes ----------------

@stats.route('/attendance/top5', methods=['GET'])
@login_required
@admin_required
def getAttendanceTop5():
    if request.method == 'GET':
        attendance = Averages('attendance')
        stats_data = attendance.top5()
        if stats_data:
            return jsonify(stats_data)
        else:
            return jsonify({'message': 'error', 'error': 'No stats found'})

@stats.route('/attendance/bottom5', methods=['GET'])
@login_required
@admin_required
def getAttendanceBottom5():
    if request.method == 'GET':
        attendance = Averages('attendance')
        stats_data = attendance.bottom5()
        if stats_data:
            return jsonify(stats_data)
        else:
            return jsonify({'message': 'error', 'error': 'No stats found'})

@stats.route('/attendance/mean', methods=['GET'])
@login_required
@admin_required
def getAttendanceMean():
    if request.method == 'GET':
        attendance = Averages('attendance')
        stats_data = attendance.mean()
        if stats_data:
            return jsonify(stats_data)
        else:
            return jsonify({'message': 'error', 'error': 'No stats found'})

@stats.route('/attendance/median', methods=['GET'])
@login_required
@admin_required
def getAttendanceMedian():
    if request.method == 'GET':
        attendance = Averages('attendance')
        stats_data = attendance.median()
        if stats_data:
            return jsonify(stats_data)
        else:
            return jsonify({'message': 'error', 'error': 'No stats found'})

@stats.route('/attendance/range', methods=['GET'])
@login_required
@admin_required
def getAttendanceRange():
    if request.method == 'GET':
        attendance = Averages('attendance')
        stats_data = attendance.range()
        if stats_data:
            return jsonify(stats_data)
        else:
            return jsonify({'message': 'error', 'error': 'No stats found'})

@stats.route('/attendance/modal', methods=['GET'])
@login_required
@admin_required
def getAttendanceModal():
    if request.method == 'GET':
        attendance = Averages('attendance')
        stats_data = attendance.modal()
        if stats_data:
            return jsonify(stats_data)
        else:
            return jsonify({'message': 'error', 'error': 'No stats found'})

@stats.route('/performance/top5', methods=['GET'])
@login_required
@admin_required
def getPerformanceTop5():
    if request.method == 'GET':
        performance = Averages('performance')
        stats_data = performance.top5()
        if stats_data:
            return jsonify(stats_data)
        else:
            return jsonify({'message': 'error', 'error': 'No stats found'})

@stats.route('/performance/bottom5', methods=['GET'])
@login_required
@admin_required
def getPerformanceBottom5():
    if request.method == 'GET':
        performance = Averages('performance')
        stats_data = performance.bottom5()
        if stats_data:
            return jsonify(stats_data)
        else:
            return jsonify({'message': 'error', 'error': 'No stats found'})

@stats.route('/performance/mean', methods=['GET'])
@login_required
@admin_required
def getPerformanceMean():
    if request.method == 'GET':
        performance = Averages('performance')
        stats_data = performance.mean()
        if stats_data:
            return jsonify(stats_data)
        else:
            return jsonify({'message': 'error', 'error': 'No stats found'})

@stats.route('/performance/median', methods=['GET'])
@login_required
@admin_required
def getPerformanceMedian():
    if request.method == 'GET':
        performance = Averages('performance')
        stats_data = performance.median()
        if stats_data:
            return jsonify(stats_data)
        else:
            return jsonify({'message': 'error', 'error': 'No stats found'})

@stats.route('/performance/range', methods=['GET'])
@login_required
@admin_required
def getPerformanceRange():
    if request.method == 'GET':
        performance = Averages('performance')
        stats_data = performance.range()
        if stats_data:
            return jsonify(stats_data)
        else:
            return jsonify({'message': 'error', 'error': 'No stats found'})

@stats.route('/performance/modal', methods=['GET'])
@login_required
@admin_required
def getPerformanceModal():
    if request.method == 'GET':
        performance = Averages('performance')
        stats_data = performance.modal()
        if stats_data:
            return jsonify(stats_data)
        else:
            return jsonify({'message': 'error', 'error': 'No stats found'})
