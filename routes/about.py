from flask import Blueprint, render_template

# Initialise blueprint and bcrypt
about = Blueprint('about', __name__)

@about.route('/about', methods=['GET'])
def aboutPage():
    return render_template('pages/about.html')