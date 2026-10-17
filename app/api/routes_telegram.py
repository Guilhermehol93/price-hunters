"""Telegram Bot Integration and Preferences API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.models.user import User, UserPreference
from app.schemas.config import (
    UserPreferenceUpdate, UserPreferenceResponse,
    TelegramTestRequest, TelegramTestResponse
)
from app.services.telegram import TelegramService
from app.config import settings

router = APIRouter(prefix="/telegram", tags=["Telegram e Notificações"])


@router.get("/status")
def get_telegram_status():
    service = TelegramService()
    return {
        "configured": service.is_configured,
        "bot_token_present": bool(settings.TELEGRAM_BOT_TOKEN),
        "default_chat_id": settings.TELEGRAM_DEFAULT_CHAT_ID,
        "cooldown_hours": settings.TELEGRAM_ALERT_COOLDOWN_HOURS,
    }


@router.post("/test", response_model=TelegramTestResponse)
async def send_test_telegram(payload: TelegramTestRequest, db: Session = Depends(get_db)):
    service = TelegramService()
    if not service.is_configured:
        raise HTTPException(
            status_code=400,
            detail="TELEGRAM_BOT_TOKEN não está configurado nas variáveis de ambiente."
        )

    target_chat = payload.chat_id or settings.TELEGRAM_DEFAULT_CHAT_ID
    if not target_chat:
        # Tenta buscar nas preferências do usuário
        stmt = select(UserPreference).limit(1)
        pref = db.scalars(stmt).first()
        if pref and pref.telegram_chat_id:
            target_chat = pref.telegram_chat_id

    if not target_chat:
        raise HTTPException(
            status_code=400,
            detail="Nenhum Chat ID fornecido ou cadastrado nas preferências."
        )

    res = await service.send_test_message(chat_id=target_chat)
    if res.get("ok"):
        return TelegramTestResponse(
            success=True,
            chat_id=target_chat,
            message_id=res.get("message_id")
        )
    else:
        return TelegramTestResponse(
            success=False,
            chat_id=target_chat,
            error=res.get("error")
        )
