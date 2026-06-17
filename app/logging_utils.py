from typing import Optional
from sqlalchemy.orm import Session
from app import models


def log_action(db: Session, action: str, status: str, user_id: Optional[int] = None) -> None:
    entry = models.AccessLog(user_id=user_id, action=action, status=status)
    db.add(entry)
    db.commit()
