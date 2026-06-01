import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

from routes.models.auth import User, registerUser, upgradeUser
from db import get_db

app = Flask(__name__)
bcrypt = Bcrypt()
app.secret_key = 'secret_key'  # Replace with a secure key

# === Blueprint Registration ===
from routes.employees import employees
app.register_blueprint(employees, url_prefix='/employees')

from routes.auth import auth
app.register_blueprint(auth)

from routes.stats import stats
app.register_blueprint(stats, url_prefix='/stats')

from routes.leave import leave
app.register_blueprint(leave, url_prefix='/leave')

from routes.users import users
app.register_blueprint(users, url_prefix='/users')

# === Flask-Login Setup ===
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'

@app.route('/')
def index():
    return redirect(url_for('auth.dashboard', active_page='dashboard'))

@app.route('/ping')
def ping():
    return "ok", 200

@login_manager.user_loader
def load_user(user_id):
    """Load user from the database using user_id."""
    db = get_db()
    user = db.execute("SELECT * FROM Users WHERE pk_user_id = ?", (user_id,)).fetchone()
    if user:
        return User(user['pk_user_id'], user['fk_employee_id'], user['username'], user['password'], user['admin'])
    return None

# === Database Initialisation ===
def init_db():
    """Initialise the SQLite database from schema.sql."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.executescript(f.read())
        db.commit()

        # Create default admin user
        registerUser({
            'employee_id': 1,
            'username': 'admin',
            'hashed_password': bcrypt.generate_password_hash('admin').decode('utf-8')
        })
        registerUser({
            'employee_id': 2,
            'username': 'user',
            'hashed_password': bcrypt.generate_password_hash('user').decode('utf-8')
        })
        upgradeUser(1)
        print("[INIT] Database initialised. Admin & User account created.")

def ensure_db_exists():
    if not os.path.exists('database.db'):
        print("[INIT] No database found. Creating new database...")
        init_db()
    else:
        print("[INFO] Existing database found. Skipping init.")

#  Ensure this is called when app is imported
ensure_db_exists()

if __name__ == '__main__':
    app.run(debug=True)
