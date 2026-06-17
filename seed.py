"""
Run once to populate the database with starter roles, permissions, and users.

    python seed.py
"""
import sys
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal
from app import models
from app.auth.security import hash_password

models.Base.metadata.create_all(bind=engine)


def seed(db: Session) -> None:
    # --- Roles ---
    role_defs = [
        ("Admin",   "Full system access"),
        ("Manager", "Can manage users and view reports"),
        ("User",    "Standard read-only access"),
    ]
    roles: dict[str, models.Role] = {}
    for name, desc in role_defs:
        role = db.query(models.Role).filter(models.Role.name == name).first()
        if not role:
            role = models.Role(name=name, description=desc)
            db.add(role)
        roles[name] = role
    db.flush()

    # --- Permissions ---
    perm_defs = [
        ("read:users",        "users"),
        ("write:users",       "users"),
        ("delete:users",      "users"),
        ("read:roles",        "roles"),
        ("write:roles",       "roles"),
        ("read:permissions",  "permissions"),
        ("write:permissions", "permissions"),
        ("read:logs",         "logs"),
    ]
    perms: dict[str, models.Permission] = {}
    for name, resource in perm_defs:
        perm = db.query(models.Permission).filter(models.Permission.name == name).first()
        if not perm:
            perm = models.Permission(name=name, resource=resource)
            db.add(perm)
        perms[name] = perm
    db.flush()

    # --- Assign permissions to roles ---
    role_permission_map = {
        "Admin":   list(perms.values()),
        "Manager": [perms[k] for k in ("read:users", "write:users", "read:roles", "read:logs")],
        "User":    [perms["read:users"]],
    }
    for role_name, assigned_perms in role_permission_map.items():
        for perm in assigned_perms:
            if perm not in roles[role_name].permissions:
                roles[role_name].permissions.append(perm)

    # --- Users ---
    user_defs = [
        ("admin",    "admin@example.com",   "admin123",   ["Admin"]),
        ("manager1", "manager@example.com", "manager123", ["Manager"]),
        ("jdoe",     "jdoe@example.com",    "user123",    ["User"]),
    ]
    for username, email, password, role_names in user_defs:
        user = db.query(models.User).filter(models.User.username == username).first()
        if not user:
            user = models.User(
                username=username,
                email=email,
                hashed_password=hash_password(password),
            )
            db.add(user)
            db.flush()
        for rname in role_names:
            if roles[rname] not in user.roles:
                user.roles.append(roles[rname])

    db.commit()
    print("Seed complete.")
    print()
    print("  Users created:")
    print("    admin    / admin123   -> Role: Admin   (all permissions)")
    print("    manager1 / manager123 -> Role: Manager (read/write users, read roles+logs)")
    print("    jdoe     / user123    -> Role: User    (read:users only)")
    print()
    print("  Permissions created:", ", ".join(perms.keys()))


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed(db)
    except Exception as exc:
        db.rollback()
        print(f"Seed failed: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()
