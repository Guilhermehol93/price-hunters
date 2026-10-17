"""Telegram Bot Integration and Preferences API Routes"""

from fastapi import APIRouter, Depends, HTTPException
from app.schemas.config import TelegramTestResponse
from app.services.telegram import TelegramService
from app.config import settings
from app.api.security import require_api_access

router = APIRouter(prefix="/telegram", tags=["Telegram e Notificações"])


@router.get("/status")
def get_telegram_status():
    service = TelegramService()
    return {
        "configured": service.is_configured,
        "bot_token_present": bool(settings.TELEGRAM_BOT_TOKEN),
        "cooldown_hours": settings.TELEGRAM_ALERT_COOLDOWN_HOURS,
    }


@router.post("/test", response_model=TelegramTestResponse, dependencies=[Depends(require_api_access)])
async def send_test_telegram():
    service = TelegramService()
    if not service.is_configured:
        raise HTTPException(
            status_code=400,
            detail="TELEGRAM_BOT_TOKEN não está configurado nas variáveis de ambiente."
        )

    # Destino controlado pelo operador; o chamador não pode escolher outro chat.
    target_chat = settings.TELEGRAM_DEFAULT_CHAT_ID

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
