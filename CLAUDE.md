# CLAUDE.md — RBAC Project

## What this is

A FastAPI-based Role-Based Access Control (RBAC) system with a vanilla JS SPA frontend. Manages users, roles, and permissions with a full audit log. Built as a working scaffold — functional but not production-hardened.

## How to run

```bash
# Install dependencies
pip install -r requirements.txt

# Seed initial data (first time only)
python seed.py

# Start the dev server
python -m uvicorn app.main:app --reload
```

- App: http://localhost:8000/
- Dashboard: http://localhost:8000/app
- Swagger docs: http://localhost:8000/docs

**Seed credentials:**
| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin (all permissions) |
| manager1 | manager123 | Manager (read/write users, read roles+logs) |
| jdoe | user123 | User (read:users only) |

## Project structure

```
app/
  main.py           # FastAPI app init, router registration, static file mount
  models.py         # SQLAlchemy ORM: User, Role, Permission, AccessLog + junctions
  schemas.py        # Pydantic request/response models
  database.py       # SQLite engine, SessionLocal, get_db() dependency
  logging_utils.py  # log_action() — writes to access_logs table
  auth/
    security.py     # JWT encode/decode, password hashing, get_current_user()
  routers/
    auth.py         # POST /auth/token (login)
    users.py        # CRUD + role assignment + password change
    roles.py        # CRUD + permission assignment
    permissions.py  # CRUD
    logs.py         # GET /logs (with optional user_id filter)
  static/
    login.html      # Login page
    app.html        # Admin SPA (Bootstrap 5)
    js/
      api.js        # Fetch wrapper — injects Bearer token, handles 401 redirect
      app.js        # UI logic, modals, table rendering, all CRUD calls
    css/
      style.css
seed.py             # Creates roles, permissions, users
rbac.db             # SQLite database (auto-created on first run, gitignored)
```

## Architecture

**Request flow:**
```
HTTP request
  → FastAPI router (app/routers/*.py)
    → Pydantic schema validation (app/schemas.py)
      → SQLAlchemy ORM (app/models.py)
        → SQLite (rbac.db)
```

**Auth flow:**
- Login POSTs username/password to `/auth/token`
- Returns JWT (HS256, 60-min expiry)
- All protected endpoints use `Depends(get_current_user)` from `app/auth/security.py`
- Frontend stores token in `sessionStorage`, injects it via `api.js`

**Database:** SQLite, no migrations. Schema is auto-created at startup via `models.Base.metadata.create_all()`. To reset: delete `rbac.db` and re-run `seed.py`.

## Domain model

```
User ──< user_roles >── Role ──< role_permissions >── Permission
 │
 └──< AccessLog
```

- **User**: username, email, bcrypt hashed_password, is_active, created_at
- **Role**: name (unique), description — many-to-many with User and Permission
- **Permission**: name (unique, e.g. `read:users`), resource (e.g. `users`)
- **AccessLog**: user_id (nullable FK, SET NULL on delete), action string, timestamp, status (`success`/`failure`)

Relationships are eager-loaded (`lazy="selectin"`) — `user.roles` and `role.permissions` are always populated without extra queries.

Permission resolution: user's effective permissions = union of all permissions across all their roles. See `GET /users/{id}/permissions`.

No role hierarchy (roles don't nest or inherit from each other).

## Key known gaps (before production use)

1. **JWT secret is hardcoded** in `app/auth/security.py` — must move to `.env`
2. **No backend permission enforcement** — endpoints only check that a valid JWT exists; specific permissions (e.g. only admins can delete users) are not enforced server-side. Frontend controls this via UI only
3. **No test suite** — no pytest files or test directory exist
4. **No migrations** — schema changes require manual DB deletion and re-seed
5. **No .env file** — secrets live directly in source code

## Conventions

- All DB writes should call `log_action()` from `logging_utils.py` for audit trail
- Use `Depends(get_db)` for all SQLAlchemy sessions — never create sessions manually
- Use `Depends(get_current_user)` on every endpoint that requires authentication
- Pydantic schemas live in `schemas.py` — request models (input) and response models (output) are separate classes
- Junction tables (`user_roles`, `role_permissions`) are defined in `models.py` as `Table` objects, not as ORM classes
