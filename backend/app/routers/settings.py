from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_seller
from app.models.settings import Settings
from app.models.user import User
from app.schemas.settings import SettingsOut, SettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db)):
    settings_row = db.query(Settings).filter(Settings.id == 1).first()
    if not settings_row:
        settings_row = Settings(id=1, delivery_fee=0)
        db.add(settings_row)
        db.commit()
        db.refresh(settings_row)
    return settings_row


@router.put("", response_model=SettingsOut)
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db), _: User = Depends(require_seller)):
    settings_row = db.query(Settings).filter(Settings.id == 1).first()
    if not settings_row:
        settings_row = Settings(id=1, delivery_fee=payload.delivery_fee)
        db.add(settings_row)
    else:
        settings_row.delivery_fee = payload.delivery_fee
    db.commit()
    db.refresh(settings_row)
    return settings_row
