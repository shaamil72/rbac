from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.schemas import UserCreate, UserOut, UserUpdate, UserPermissionsOut, PermissionCheckOut, PasswordChange
from app.auth.security import hash_password, get_current_user
from app.logging_utils import log_action

router = APIRouter(prefix="/users", tags=["Users"])



@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    return db.query(models.User).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    conflict = db.query(models.User).filter(
        (models.User.username == payload.username) | (models.User.email == payload.email)
    ).first()
    if conflict:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already exists")
    user = models.User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, action=f"create_user:{user.username}", status="success", user_id=current_user.id)
    return user


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if payload.email is not None:
        user.email = payload.email
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    log_action(db, action=f"update_user:{user.username}", status="success", user_id=current_user.id)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    username = user.username
    db.delete(user)
    db.commit()
    log_action(db, action=f"delete_user:{username}", status="success", user_id=current_user.id)


@router.patch("/{user_id}/password", response_model=UserOut)
def change_password(
    user_id: int,
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Password must be at least 6 characters")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    db.refresh(user)
    log_action(db, action=f"change_password:{user.username}", status="success", user_id=current_user.id)
    return user


@router.get("/{user_id}/permissions", response_model=UserPermissionsOut)
def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    seen = set()
    unique_perms = []
    for role in user.roles:
        for perm in role.permissions:
            if perm.id not in seen:
                seen.add(perm.id)
                unique_perms.append(perm)
    return UserPermissionsOut(user_id=user.id, username=user.username, permissions=unique_perms)


@router.get("/{user_id}/permissions/check", response_model=PermissionCheckOut)
def check_user_permission(
    user_id: int,
    permission: str,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    has_permission = any(
        perm.name == permission
        for role in user.roles
        for perm in role.permissions
    )
    return PermissionCheckOut(
        user_id=user.id,
        username=user.username,
        permission=permission,
        has_permission=has_permission,
    )


@router.post("/{user_id}/roles/{role_id}", response_model=UserOut)
def assign_role(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not user or not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User or role not found")
    if role not in user.roles:
        user.roles.append(role)
        db.commit()
        db.refresh(user)
        log_action(db, action=f"assign_role:{role.name}->{user.username}", status="success", user_id=current_user.id)
    return user


@router.delete("/{user_id}/roles/{role_id}", response_model=UserOut)
def remove_role(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    role = db.query(models.Role).filter(models.Role.id == role_id).first()
    if not user or not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User or role not found")
    if role in user.roles:
        user.roles.remove(role)
        db.commit()
        db.refresh(user)
        log_action(db, action=f"remove_role:{role.name}->{user.username}", status="success", user_id=current_user.id)
    return user
