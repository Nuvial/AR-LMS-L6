import os
from flask import Flask, redirect, url_for, g
from flask_login import LoginManager, current_user
from flask_bcrypt import Bcrypt

from routes.models.auth import User, registerUser, upgradeUser
from db import get_db

app = Flask(__name__)
bcrypt = Bcrypt()
secret_key = os.environ.get('FLASK_SECRET_KEY')
if not secret_key:
    raise RuntimeError('FLASK_SECRET_KEY environment variable is not set.')
app.secret_key = secret_key

# === Blueprint Registration ===
from routes.employees import employees
app.register_blueprint(employees, url_prefix='/employees')

from routes.auth import auth
app.register_blueprint(auth)

from routes.about import about
app.register_blueprint(about)

from routes.stats import stats
app.register_blueprint(stats, url_prefix='/stats')

from routes.leave import leave
app.register_blueprint(leave, url_prefix='/leave')

from routes.teams import teams
app.register_blueprint(teams, url_prefix='/teams')

from routes.users import users
app.register_blueprint(users, url_prefix='/users')

# === Flask-Login Setup ===
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('auth.dashboard'))
    return redirect(url_for('auth.login'))


@app.after_request
def prevent_caching(response):
    # Force the browser to revalidate all pages so history.back() can't serve a cached authenticated page after the user has logged out.
    if 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

@app.route('/ping')
def ping():
    return "ok", 200

@login_manager.user_loader
def load_user(user_id):
    """Load user from the database using user_id."""
    db = get_db()
    user = db.execute("""
        SELECT u.*, r.name AS role
        FROM Users u
        JOIN Employees e ON u.fk_employee_id = e.pk_employee_id
        JOIN Roles r ON e.fk_role_id = r.pk_role_id
        WHERE u.pk_user_id = ?
    """, (user_id,)).fetchone()
    if user:
        return User(user['pk_user_id'], user['fk_employee_id'], user['username'], user['password'], user['role'])
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
    with app.app_context():
        db = get_db()
        initialised = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Users'").fetchone() is not None
        has_roles = initialised and db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Roles'").fetchone() is not None

    if initialised:
        print("[INFO] Existing database found. Skipping init.")
        if has_roles:
            with app.app_context():
                db = get_db()
                db.execute("""
                    UPDATE Employees
                    SET fk_role_id = (SELECT pk_role_id FROM Roles WHERE name = 'manager')
                    WHERE pk_employee_id IN (SELECT fk_manager_id FROM Team WHERE fk_manager_id IS NOT NULL)
                    AND fk_role_id = (SELECT pk_role_id FROM Roles WHERE name = 'employee')
                """)
                db.commit()
    else:
        print("[INIT] No database found. Initialising...")
        init_db()

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

@app.context_processor
def inject_env_info():
    validEnvironments = ["dev", "test", "production"]
    validHosts = ["local", "primary", "secondary"]

    environment = os.environ.get("APP_ENVIRONMENT")
    appHost = os.environ.get("APP_HOST")

    if ((environment == None or environment not in validEnvironments) or (appHost == None or appHost not in validHosts)):
        raise Exception("APP_HOST or APP_ENVIRONMENT environment variables have not been defined")

    return {
        "env": environment,
        "env_host": appHost,
    }

ensure_db_exists()
if __name__ == '__main__':
    app.run(debug=True)
