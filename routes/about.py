from flask import Blueprint, render_template

# Initialise blueprint and bcrypt
about = Blueprint('about', __name__)

@about.route('/about', methods=['GET', 'POST'])
def aboutPage():
    return render_template('about.html')