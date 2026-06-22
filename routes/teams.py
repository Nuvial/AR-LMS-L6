from flask import request, jsonify, Blueprint, render_template
from flask_login import login_required

from .models.teams import getTeams, getEmployees, createTeam, getPossibleManagers, updateTeam, deleteTeam
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
            return jsonify({"error": "No teams found"})

@teams.route('/get_employees/', methods=['GET', 'POST'])
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
        
        if employees['message']:
            return jsonify(employees['employees']), 200
        else:
            return jsonify({'message': employees['message'], 'error': employees['error']})
    
    if request.method == 'POST':
        teamIdData = request.get_json()
        teamIds = teamIdData['teamIds']
        
        teams = {}
        for i in teamIds:
            team = getEmployees(i)
            if team['message'] == 'success':
                teams[i] = team
                continue
            return jsonify({'message': team['message'], 'error': team['error']})
        
        return jsonify(teams), 200


@teams.route('/get_potential_managers/', methods=['GET'])
@login_required
@admin_required
def getPotentialManagers(teamId=None):
    """
    Route to get all employees that are compatible to become a manager.
    """
    if request.method == 'GET':
        employees = getPossibleManagers()
        if employees['message'] == 'success':
            return jsonify(employees['employees']), 200
        
        return jsonify({'message': employees['message'], 'error': employees['error']})
        
@teams.route('/add_team', methods=['POST'])
@login_required
@admin_required
def addTeam():
    """
    Route to add a new team from the team management page
    """
    if request.method == 'POST':
        teamData = request.get_json()
        teamName = teamData['teamName']
        managerId = teamData['managerId']
        employees = teamData['employees']

        team = createTeam(
            teamName,
            managerId,
            employees
        )
        
        if team['message'] == 'success':
            return jsonify({'message': 'success'}), 200
        
        return jsonify({'message': team['message'], 'error': team['error']})
    
@teams.route('/update_team/<int:team_id>', methods=['POST'])
@login_required
@admin_required
def updateTeamRoute(team_id):
    """
    Route to update a team from the team management page
    """
    if request.method == 'POST':
        teamData = request.get_json()
        teamName = teamData['teamName']
        managerId = teamData['managerId']
        employees = teamData['employees']

        team = updateTeam(
            team_id,
            teamName,
            managerId,
            employees
        )
        
        if team['message'] == 'success':
            return jsonify({'message': 'success'}), 200
        
        return jsonify({'message': team['message'], 'error': team['error']})

@teams.route('/delete_team/<int:team_id>', methods=['DELETE'])
@login_required
@admin_required
def deleteTeamRoute(team_id):
    """
    Route to delete a team from the team management page
    """
    if request.method == 'DELETE':
        team = deleteTeam(team_id)
        
        if team['message'] == 'success':
            return jsonify({'message': 'success'}), 200
        
        return jsonify({'message': team['message'], 'error': team['error']})