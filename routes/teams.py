from flask import request, jsonify, Blueprint, render_template
from flask_login import login_required

import time

from .models.teams import getTeams, getEmployees
from .auth import admin_required

teams = Blueprint('teams', __name__)

@teams.route('/')
@login_required
@admin_required
def index():
    return render_template('pages/team-overview.html', active_page='teams')

@teams.route('/get_teams', methods=['GET'])
@teams.route('/get_teams/<int:team_id>', methods=['GET'])
@login_required
@admin_required
def getTeamsRoute(teamId=None):
    """
    Route to get all or specific team/s.
    Args:
        teamId (int, optional): Team ID to get. If not provided, gets all teams.
    """
    if request.method == 'GET':
        teams = getTeams(teamId)
        if teams or teams == []:
            return jsonify(teams), 200
        else:
            return jsonify({"error": "No teams found"}), 404

@teams.route('/get_employees/', methods=['GET'])
@teams.route('/get_employees/<int:team_id>', methods=['GET'])
@login_required
@admin_required
def getEmployeesRoute(teamId=None):
    """
    Route to get all employees either in a specific team if teamId is provided, or all employees
    NOT in a team if no teamId is provided.
    Args:
        teamId (int, optional): TeamID to get employees for, if not provided gets all employees NOT in a team.
    """
    if request.method == 'GET':
        employees = getEmployees(teamId)
        if employees:
            return jsonify(employees), 200
        else:
            return jsonify({"error": "No employees found"}), 400