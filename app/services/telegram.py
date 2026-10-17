"""Telegram Bot Service for Instant Deal Alerts"""

import logging
from typing import Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class TelegramService:
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.TELEGRAM_BOT_TOKEN
        self.base_url = f"https://api.telegram.org/bot{self.token}" if self.token else None

    @property
    def is_configured(self) -> bool:
        return bool(settings.TELEGRAM_ENABLED and self.token and len(self.token) > 10)

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = False
    ) -> dict:
        """Envia mensagem de texto via Telegram Bot API"""
        if not self.is_configured:
            return {"ok": False, "error": "TELEGRAM_BOT_TOKEN não está configurado."}

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(url, json=payload)
                data = resp.json()
                if resp.status_code == 200 and data.get("ok"):
                    return {"ok": True, "message_id": data["result"]["message_id"]}
                else:
                    err_msg = data.get("description", resp.text)
                    logger.error(f"Erro Telegram API: {err_msg}")
                    return {"ok": False, "error": err_msg}
            except Exception as e:
                logger.error(f"Exceção ao contactar Telegram: {e}")
                return {"ok": False, "error": str(e)}

    async def send_deal_alert(
        self,
        chat_id: str,
        title: str,
        current_price: float,
        original_price: Optional[float],
        historical_discount_pct: float,
        opportunity_score: int,
        store_name: str,
        deal_url: str,
        is_all_time_low: bool = False
    ) -> dict:
        """Formata e envia alerta rico de oportunidade detectada"""
        badge = "🔥 <b>SUPER OFERTA DETECTADA</b> 🔥"
        if is_all_time_low:
            badge = "🚨 <b>MENOR PREÇO HISTÓRICO REGISTRADO</b> 🚨"

        orig_str = f"<s>R$ {original_price:,.2f}</s> ➔ " if original_price and original_price > current_price else ""

        text = (
            f"{badge}\n\n"
            f"📦 <b>{title}</b>\n"
            f"🏪 Loja: <b>{store_name}</b>\n\n"
            f"💰 Preço Atual: {orig_str}<b>R$ {current_price:,.2f}</b>\n"
            f"📉 Desconto Histórico: <b>{historical_discount_pct:.1f}%</b>\n"
            f"🎯 Score de Oportunidade: <b>{opportunity_score}/100</b>\n\n"
            f"🔗 <a href=\"{deal_url}\"><b>Acessar Oferta Agora</b></a>\n\n"
            f"<i>Monitorado pelo Price Hunter</i>"
        )

        return await self.send_message(chat_id, text, parse_mode="HTML")

    async def send_test_message(self, chat_id: Optional[str] = None) -> dict:
        """Envia mensagem de verificação de conectividade"""
        target_chat = chat_id or settings.TELEGRAM_DEFAULT_CHAT_ID
        if not target_chat:
            return {"ok": False, "error": "Nenhum Chat ID informado ou configurado em TELEGRAM_DEFAULT_CHAT_ID."}

        text = (
            "🎯 <b>Price Hunter — Teste de Notificação</b>\n\n"
            "✅ Seu bot do Telegram está configurado e pronto para disparar alertas de oportunidades!\n\n"
            "Quando um preço monitorado atingir sua meta, você receberá o alerta instantaneamente aqui."
        )
        return await self.send_message(target_chat, text, parse_mode="HTML")
