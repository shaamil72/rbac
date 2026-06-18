import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app import models
from app.auth.security import hash_password, create_access_token

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db):
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


# ── helpers (plain functions, not fixtures) ─────────────────────────────────

def make_perm(db, name, resource):
    p = models.Permission(name=name, resource=resource)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def make_role(db, name, perms=None):
    r = models.Role(name=name)
    db.add(r)
    db.flush()
    if perms:
        r.permissions.extend(perms)
    db.commit()
    db.refresh(r)
    return r


def make_user(db, username, email=None, password="pass1234", roles=None, is_active=True):
    u = models.User(
        username=username,
        email=email or f"{username}@test.com",
        hashed_password=hash_password(password),
        is_active=is_active,
    )
    db.add(u)
    db.flush()
    if roles:
        u.roles.extend(roles)
    db.commit()
    db.refresh(u)
    return u


def auth_headers(user):
    token = create_access_token({"sub": user.username, "user_id": user.id})
    return {"Authorization": f"Bearer {token}"}


# ── shared permission set ───────────────────────────────────────────────────

PERM_DEFS = [
    ("read:users",        "users"),
    ("write:users",       "users"),
    ("delete:users",      "users"),
    ("read:roles",        "roles"),
    ("write:roles",       "roles"),
    ("read:permissions",  "permissions"),
    ("write:permissions", "permissions"),
    ("read:logs",         "logs"),
]


@pytest.fixture()
def perms(db):
    return {name: make_perm(db, name, res) for name, res in PERM_DEFS}


@pytest.fixture()
def admin(db, perms):
    role = make_role(db, "Admin", list(perms.values()))
    return make_user(db, "admin", roles=[role])


@pytest.fixture()
def admin_h(admin):
    return auth_headers(admin)


@pytest.fixture()
def readonly(db, perms):
    role = make_role(db, "ReadOnly", [perms["read:users"]])
    return make_user(db, "readonly", roles=[role])


@pytest.fixture()
def readonly_h(readonly):
    return auth_headers(readonly)


@pytest.fixture()
def noperm(db):
    return make_user(db, "noperm")


@pytest.fixture()
def noperm_h(noperm):
    return auth_headers(noperm)
