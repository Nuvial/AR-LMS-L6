import os
import sys
import tempfile

import pytest

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _PROJECT_ROOT)

os.environ.setdefault("FLASK_SECRET_KEY", "test-secret-key")
os.environ.setdefault("APP_ENVIRONMENT", "test")
os.environ.setdefault("APP_HOST", "local")
os.environ.setdefault("HIBP_ENABLED", "false")  # never call the live API in tests


@pytest.fixture(scope="session")
def _app_workdir():
    original_cwd = os.getcwd()
    tmp = tempfile.mkdtemp(prefix="ar-lms-l6-tests-")
    os.chdir(tmp)
    yield tmp
    os.chdir(original_cwd)

@pytest.fixture(scope="session")
def flask_app(_app_workdir):
    """Import and configure the Flask app exactly once for the test session."""
    import app as app_module

    app_module.app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    return app_module.app


@pytest.fixture()
def app(flask_app):
    """
    Rebuild a fresh, seeded database before each test.
    """
    import app as app_module
    from db import get_db

    db_file = os.path.join(os.getcwd(), "data", "database.db")
    if os.path.exists(db_file):
        os.remove(db_file)

    app_module.init_db()  # recreates seeded db

    # The seeded admin/user accounts are created with a forced password reset 
    # should be cleared so test logins take the normal authenticated path.
    with flask_app.app_context():
        db = get_db()
        db.execute("UPDATE Users SET password_reset_required = 0")
        db.commit()

    yield flask_app


@pytest.fixture()
def client(app):
    """An unauthenticated test client."""
    return app.test_client()




def login(client, username, password):
    """Authenticate a test client via the login form."""
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


@pytest.fixture()
def admin_client(app):
    """A client logged in as the seeded admin account (employee 1)."""
    c = app.test_client()
    login(c, "admin", "admin")
    return c


@pytest.fixture()
def user_client(app):
    """A client logged in as the seeded regular-employee account (employee 2)."""
    c = app.test_client()
    login(c, "user", "user")
    return c
