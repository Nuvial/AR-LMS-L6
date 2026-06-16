from flask import request, jsonify, Blueprint, render_template
from flask_login import login_required

from .auth import admin_required

teams = Blueprint('teams', __name__)

@teams.route('/')
@login_required
@admin_required
def index():
    return render_template('pages/team-overview.html', active_page='teams')
