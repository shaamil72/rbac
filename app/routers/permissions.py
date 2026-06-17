from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.schemas import PermissionCreate, PermissionOut
from app.auth.security import get_current_user
from app.logging_utils import log_action

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.get("", response_model=list[PermissionOut])
def list_permissions(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    return db.query(models.Permission).all()


@router.post("", response_model=PermissionOut, status_code=status.HTTP_201_CREATED)
def create_permission(
    payload: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if db.query(models.Permission).filter(models.Permission.name == payload.name).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Permission already exists")
    perm = models.Permission(name=payload.name, resource=payload.resource)
    db.add(perm)
    db.commit()
    db.refresh(perm)
    log_action(db, action=f"create_permission:{perm.name}", status="success", user_id=current_user.id)
    return perm


@router.get("/{permission_id}", response_model=PermissionOut)
def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    perm = db.query(models.Permission).filter(models.Permission.id == permission_id).first()
    if not perm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    return perm


@router.delete("/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    perm = db.query(models.Permission).filter(models.Permission.id == permission_id).first()
    if not perm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")
    name = perm.name
    db.delete(perm)
    db.commit()
    log_action(db, action=f"delete_permission:{name}", status="success", user_id=current_user.id)
