# RBAC — Role-Based Access Control System

A FastAPI application for managing users, roles, and permissions with a full audit log and a browser-based admin dashboard.

---

## Requirements

- Python 3.10 or higher
- pip

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/shaamil72/rbac.git
cd rbac
```

### 2. Create and activate a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Seed the database

Run this once to create the SQLite database and populate it with starter roles, permissions, and users.

```bash
python seed.py
```

This creates:

| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| admin | admin123 | Admin | All permissions |
| manager1 | manager123 | Manager | read/write users, read roles, read logs |
| jdoe | user123 | User | read:users only |

---

## Running the application

```bash
python -m uvicorn app.main:app --reload
```

The server starts on **http://localhost:8000**.

| URL | Description |
|-----|-------------|
| http://localhost:8000/ | Login page |
| http://localhost:8000/app | Admin dashboard |
| http://localhost:8000/docs | Interactive API docs (Swagger UI) |
| http://localhost:8000/redoc | Alternative API docs (ReDoc) |

---

## Using the dashboard

1. Open http://localhost:8000/ in your browser
2. Log in with one of the seeded accounts (e.g. `admin` / `admin123`)
3. Use the sidebar to navigate between **Users**, **Roles**, **Permissions**, and **Access Logs**

### What each role can do in the UI

| Section | Admin | Manager | User |
|---------|-------|---------|------|
| View users | ✅ | ✅ | ✅ |
| Create / edit users | ✅ | ✅ | ❌ |
| Delete users | ✅ | ❌ | ❌ |
| View roles | ✅ | ✅ | ❌ |
| Create / delete roles | ✅ | ❌ | ❌ |
| View permissions | ✅ | ❌ | ❌ |
| Create / delete permissions | ✅ | ❌ | ❌ |
| View access logs | ✅ | ✅ | ❌ |

---

## API overview

All endpoints (except login) require a Bearer token in the `Authorization` header.

### Authentication

```
POST /auth/token
```
Form fields: `username`, `password`  
Returns: `{ "access_token": "...", "token_type": "bearer" }`

### Users

| Method | Endpoint | Permission required |
|--------|----------|-------------------|
| GET | /users | read:users |
| POST | /users | write:users |
| GET | /users/{id} | read:users |
| PATCH | /users/{id} | write:users |
| DELETE | /users/{id} | delete:users |
| PATCH | /users/{id}/password | write:users |
| POST | /users/{id}/roles/{role_id} | write:users |
| DELETE | /users/{id}/roles/{role_id} | write:users |
| GET | /users/{id}/permissions | read:users |

### Roles

| Method | Endpoint | Permission required |
|--------|----------|-------------------|
| GET | /roles | read:roles |
| POST | /roles | write:roles |
| GET | /roles/{id} | read:roles |
| DELETE | /roles/{id} | write:roles |
| POST | /roles/{id}/permissions/{perm_id} | write:roles |
| DELETE | /roles/{id}/permissions/{perm_id} | write:roles |

### Permissions

| Method | Endpoint | Permission required |
|--------|----------|-------------------|
| GET | /permissions | read:permissions |
| POST | /permissions | write:permissions |
| GET | /permissions/{id} | read:permissions |
| DELETE | /permissions/{id} | write:permissions |

### Logs

| Method | Endpoint | Permission required |
|--------|----------|-------------------|
| GET | /logs | read:logs |
| GET | /logs?user_id={id} | read:logs |

---

## Running the tests

Install test dependencies:

```bash
pip install -r requirements-dev.txt
```

Run the suite:

```bash
python -m pytest -v
```

40 tests covering auth, permission enforcement, CRUD operations, and edge cases. Uses an in-memory SQLite database — the production `rbac.db` is not touched.

---

## Resetting the database

Delete `rbac.db` and re-run the seed script:

```bash
del rbac.db        # Windows
rm rbac.db         # macOS / Linux

python seed.py
```

---

## Project structure

```
app/
  main.py           # App entry point, router registration
  models.py         # SQLAlchemy ORM models
  schemas.py        # Pydantic request/response schemas
  database.py       # Database engine and session
  logging_utils.py  # Audit log helper
  auth/
    security.py     # JWT, password hashing, permission dependency
  routers/
    auth.py         # POST /auth/token
    users.py        # /users endpoints
    roles.py        # /roles endpoints
    permissions.py  # /permissions endpoints
    logs.py         # /logs endpoints
  static/           # Frontend HTML/CSS/JS
tests/
  conftest.py       # Fixtures and helpers
  test_auth.py
  test_users.py
  test_roles.py
  test_permissions.py
  test_logs.py
seed.py             # Database seeding script
requirements.txt
requirements-dev.txt
```
