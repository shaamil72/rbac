from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.schemas import RoleCreate, RoleOut
from app.auth.security import get_current_user, require_permission
from app.logging_utils import log_action

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("", response_model=list[RoleOut])
def list_roles(db: Session = Depends(get_db), _: models.User = Depends(require_permission("read:roles"))):
    return db.query(models.Role).all()


@router.post("", response_model=RoleOut, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("write:roles")),
):
    if db.query(models.Role).filter(models.Role.name == payload.name).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role already exists")
    role = models.Role(name=payload.name, description=payload.description)
    db.add(role)
    db.commit()
    db.refresh(role)
    log_action(db, action=f"create_role:{role.name}", status="success", user_id=current_user.id)
    return role


@router.get("/{role_id}", response_model=RoleOut)
def get_role(role_id: int, db: Session = Depends(get_db), _: models.User = Depends(require_permission("read:roles"))):
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("write:roles")),
):
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    name = role.name
    db.delete(role)
    db.commit()
    log_action(db, action=f"delete_role:{name}", status="success", user_id=current_user.id)


@router.post("/{role_id}/permissions/{permission_id}", response_model=RoleOut)
def assign_permission(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("write:roles")),
):
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    perm = db.query(models.Permission).filter(models.Permission.id == permission_id).first()
    if not role or not perm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role or permission not found")
    if perm not in role.permissions:
        role.permissions.append(perm)
        db.commit()
        db.refresh(role)
        log_action(db, action=f"assign_permission:{perm.name}->{role.name}", status="success", user_id=current_user.id)
    return role


@router.delete("/{role_id}/permissions/{permission_id}", response_model=RoleOut)
def remove_permission(
    role_id: int,
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_permission("write:roles")),
):
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    perm = db.query(models.Permission).filter(models.Permission.id == permission_id).first()
    if not role or not perm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role or permission not found")
    if perm in role.permissions:
        role.permissions.remove(perm)
        db.commit()
        db.refresh(role)
        log_action(db, action=f"remove_permission:{perm.name}->{role.name}", status="success", user_id=current_user.id)
    return role
