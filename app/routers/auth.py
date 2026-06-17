from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.schemas import Token
from app.auth.security import verify_password, create_access_token
from app.logging_utils import log_action

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        log_action(db, action="login", status="failure", user_id=user.id if user else None)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        log_action(db, action="login", status="failure", user_id=user.id)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    log_action(db, action="login", status="success", user_id=user.id)
    token = create_access_token({"sub": user.username, "user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}
