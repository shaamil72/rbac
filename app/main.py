from fastapi import FastAPI
from app.database import engine
from app import models
from app.routers import auth, users, roles, permissions, logs

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RBAC User Management API",
    description="Role-Based Access Control system — users, roles, permissions, and audit logging.",
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(permissions.router)
app.include_router(logs.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "docs": "/docs"}
