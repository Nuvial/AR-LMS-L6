# AR LMS - AtkinsRéalis Leave Management System

A Flask web application for managing employee records, leave requests, team structures, and login accounts within a hierarchical organisation.

**Author:** Neri Malinauskas
**Module:** Software Engineering & DevOps — Level 6 Apprenticeship

---

## Tech Stack

### Application

| Layer    | Technology                                                                             |
| -------- | -------------------------------------------------------------------------------------- |
| Backend  | Python 3.12, Flask 3.x                                                                 |
| Auth     | Flask-Login, Flask-Bcrypt, Flask-WTF (CSRF)                                            |
| Database | SQLite (auto-initialised)                                                              |
| Frontend | Bootstrap 5, jQuery, FullCalendar, Mermaid                                             |
| CI/CD    | GitHub Actions > Test Suite > Docker (GHCR) > Personal Domain & Render.com as Failover |
| Failover | Cloudflare Worker (cron ping)                                                          |

### Custom Host

| Layer                | Technology            |
| -------------------- | --------------------- |
| Container            | Docker                |
| Container Management | containrrr/watchtower |
| DNS / Edge           | Cloudflare            |
| Reverse Proxy        | NGINX                 |


---

## Local Setup

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/Nuvial/AR-LMS-L6
cd AR-LMS-L6

python -m venv .venv # or "python3" for linux
./.venv/Scripts/activate # or source ./.venv/bin/activate for linux 
```

### 2. Install dependencies

For running the app:

```bash
pip install -r requirements.txt
```

For development (includes testing and security scanning tools):

```bash
pip install -r requirements-dev.txt
```

### 3. Configure environment variables

Copy the example below into a `.env` file in the project root, or export the variables directly in your shell.

```dotenv
# Required - used to sign Flask sessions. Use a long random string in production.
FLASK_SECRET_KEY = "your-secret-key-here"

# Application environment. Valid values: dev | test | production
APP_ENVIRONMENT = "dev"

# Deployment host. Valid values: local | primary | secondary
APP_HOST = "local"

# Whether to check passwords against the HaveIBeenPwned API.
# Set to false for local development to avoid external network calls.
HIBP_ENABLED = "false"
```

> **Note:** All four variables are required. The app will raise an exception at startup if `FLASK_SECRET_KEY`, `APP_ENVIRONMENT`, or `APP_HOST` are missing or invalid.

### 4. Run the application

```bash
flask --app app run
```

The app is served at `http://127.0.0.1:5000` by default.

On first run, the database is automatically created at `data/database.db` and seeded from `schema.sql` with sample employees and two default accounts (see below).

---

## Environment Variables Reference

| Variable | Required | Valid Values | Description |
|---|---|---|---|
| `FLASK_SECRET_KEY` | Yes | Any string | Signs session cookies. Use a long, random value in production. |
| `APP_ENVIRONMENT` | Yes | `dev`, `test`, `production` | Controls environment labelling in the UI and CI pipeline behaviour. |
| `APP_HOST` | Yes | `local`, `primary`, `secondary` | Displayed as a host tag in the UI. Set to `secondary` on the backup host. |
| `HIBP_ENABLED` | No | `true`, `false` | Enables k-anonymity breach-password checks via the HIBP API. Defaults to `true` if unset. Set to `false` locally to avoid network calls. |

---

## Database
The application uses **SQLite**. The database file is stored at `data/database.db` and is created automatically on first startup from `schema.sql`.

To reset the database, delete `data/database.db` and restart the app. This will re-initialise and re-seed.
### Default accounts
Two accounts are created automatically on first initialisation:

| Username | Password | Role     |
| -------- | -------- | -------- |
| `admin`  | `admin`  | Admin    |
| `user`   | `user`   | Employee |

> **Important:** Upon logging in a password change request is immediately displayed. This is to ensure a secure password is set for the account. If the user account is not immediately used, it is recommended to delete the login account from within the app as the admin. Details on this can be found in the about page of the application.

---
## Running Tests

The test suite uses **pytest** with coverage reporting.

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov

# Run with coverage and enforce a minimum threshold
pytest --cov --cov-fail-under=68
```

Test configuration is in `pyproject.toml`. Tests are located in the `tests/` directory.

---
## Security Scanning

```bash
# Static analysis (Bandit) checks for common security issues
bandit -c pyproject.toml -r . -ll

# Dependency vulnerability scan
pip-audit -r requirements.txt
```

Both scans are run automatically in the CI pipeline on every push to `main` or `test`.

---
## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/deploy.yml`) runs on pushes and pull requests to `main` and `test`:

1. **Test**: runs pytest with coverage and the Bandit and pip-audit security scans.
2. **Build**: builds a Docker image and pushes it to the GitHub Container Registry (`ghcr.io`).
3. **Deploy**: triggers a Render.com redploy via webhook. The custom server polls the container registry for any changes and restarts the containers accordingly.  
   - Pushes to `main` deploy to the **production** service.  
   - Pushes to `test` deploy to the **test** service.
1. **Cloudflare Worker**: deploys a cron worker (`.cloudflare/`) that pings the primary host every minute to trigger automatic failover detection.
---

## Project Structure

```
.
├── app.py                  # App factory, blueprint registration, DB init
├── db.py                   # SQLite connection helper
├── schema.sql              # Database schema and seed data
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development/testing dependencies
├── pyproject.toml          # pytest, coverage, and bandit configuration
├── routes/
│   ├── auth.py             # Login, logout, dashboard, RBAC decorators
│   ├── employees.py        # Employee record CRUD
│   ├── leave.py            # Leave request and approval
│   ├── teams.py            # Team management (admin only)
│   ├── users.py            # Login account management and profile settings
│   ├── about.py            # About route
│   └── models/             # Database query functions per domain
├── templates/
│   ├── layouts/            # Base Jinja2 templates
│   ├── pages/              # Page templates
│   └── partials/           # Reusable template components
├── static/
│   ├── css/                # Per-page stylesheets
│   └── js/                 # Per-page JavaScript modules
├── tests/                  # pytest test suite
├── .github/workflows/      # CI/CD pipeline
└── .cloudflare/            # Cloudflare Worker for failover cron
```
