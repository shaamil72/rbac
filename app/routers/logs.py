from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.schemas import AccessLogOut
from app.auth.security import get_current_user, require_permission

router = APIRouter(prefix="/logs", tags=["Access Logs"])


@router.get("", response_model=list[AccessLogOut])
def list_logs(
    user_id: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: models.User = Depends(require_permission("read:logs")),
):
    query = db.query(models.AccessLog)
    if user_id is not None:
        query = query.filter(models.AccessLog.user_id == user_id)
    return query.order_by(models.AccessLog.timestamp.desc()).limit(limit).all()
