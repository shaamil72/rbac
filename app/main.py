from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", include_in_schema=False)
def serve_login():
    return FileResponse("app/static/login.html")


@app.get("/app", include_in_schema=False)
def serve_app():
    return FileResponse("app/static/app.html")
