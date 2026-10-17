"""Background Worker for Crawling and Monitoring Checks"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.repositories.monitoring_repo import MonitoringRepository
from app.repositories.listing_repo import ListingRepository
from app.repositories.notification_repo import NotificationRepository
from app.connectors import get_connector_for_url
from app.services.intelligence import PriceIntelligenceService
from app.services.telegram import TelegramService
from app.models.notification import Notification

logger = logging.getLogger(__name__)


async def check_monitored_product(monitored_id, db: Session):
    """Executa a verificação pontual de um produto monitorado."""
    monitoring_repo = MonitoringRepository(db)
    listing_repo = ListingRepository(db)
    notif_repo = NotificationRepository(db)
    telegram_service = TelegramService()

    monitored = monitoring_repo.get_by_id(monitored_id)
    if not monitored or not monitored.is_active or not monitored.listing:
        return

    listing = monitored.listing
    connector = get_connector_for_url(listing.url)

    logger.info(f"Verificando preço atualizado para: {listing.title} ({listing.url})")
    scraped = await connector.fetch_product_details(listing.url)
    if not scraped:
        logger.warning(f"Não foi possível obter dados para {listing.url}")
        monitored.last_checked_at = datetime.utcnow()
        db.commit()
        return

    # Atualizar preço na listagem
    old_price = listing.current_price
    new_price = scraped.current_price
    listing.current_price = new_price
    listing.last_checked_at = datetime.utcnow()

    # Adicionar snapshot ao histórico
    listing_repo.add_price_point(
        listing_id=listing.id,
        current_price=new_price,
        original_price=scraped.original_price,
        source="monitoring_worker"
    )

    # Recalcular métricas de inteligência
    history = listing_repo.get_history(listing.id, days=90)
    stats = PriceIntelligenceService.calculate_stats(history, new_price)

    store_rep = float(listing.store.reputation_score) if listing.store and listing.store.reputation_score else 8.0
    new_score = PriceIntelligenceService.calculate_opportunity_score(
        current_price=new_price,
        stats=stats,
        store_reputation=store_rep
    )
    listing.opportunity_score = new_score
    listing.historical_discount_pct = Decimal(str(stats["historical_discount_pct"]))
    monitored.last_checked_at = datetime.utcnow()
    db.commit()

    # Avaliar regras de alerta
    for rule in monitored.alert_rules:
        if not rule.is_active:
            continue

        triggered = PriceIntelligenceService.evaluate_alert(
            rule_type=rule.rule_type,
            threshold_value=rule.threshold_value,
            current_price=new_price,
            opportunity_score=new_score,
            historical_discount_pct=listing.historical_discount_pct,
            all_time_min=Decimal(str(stats["all_time_min"]))
        )

        if triggered:
            # Checar cooldown para não inundar o usuário
            already_notified = notif_repo.has_recent_alert(
                monitored_product_id=monitored.id,
                rule_type=rule.rule_type,
                cooldown_hours=rule.cooldown_hours
            )
            if already_notified:
                logger.info(f"Alerta omitido devido ao cooldown de {rule.cooldown_hours}h.")
                continue

            # Criar notificação
            title = f"Alerta de Preço: {listing.title[:50]}..."
            msg = (
                f"O item atingiu o critério {rule.rule_type}!\n"
                f"Novo preço: R$ {new_price:,.2f} (Score {new_score}/100)"
            )
            notif = Notification(
                user_id=monitored.user_id,
                monitored_product_id=monitored.id,
                listing_id=listing.id,
                title=title,
                message=msg,
                channel=rule.channel,
                status="pending",
                trigger_price=new_price,
                trigger_discount_pct=listing.historical_discount_pct,
                trigger_opportunity_score=new_score
            )
            db.add(notif)
            db.commit()
            db.refresh(notif)

            # Enviar Telegram se configurado
            user_pref = monitored.user.preferences if monitored.user else None
            chat_id = user_pref.telegram_chat_id if user_pref and user_pref.telegram_chat_id else None

            if rule.channel == "telegram" and telegram_service.is_configured:
                target_chat = chat_id or telegram_service.token
                res = await telegram_service.send_deal_alert(
                    chat_id=target_chat,
                    title=listing.title,
                    current_price=float(new_price),
                    original_price=float(scraped.original_price) if scraped.original_price else None,
                    historical_discount_pct=float(listing.historical_discount_pct),
                    opportunity_score=new_score,
                    store_name=listing.store.name if listing.store else "Loja Online",
                    deal_url=listing.url,
                    is_all_time_low=stats.get("is_all_time_low", False)
                )
                if res.get("ok"):
                    notif.status = "sent"
                    notif.sent_at = datetime.utcnow()
                    monitored.last_notified_at = datetime.utcnow()
                    notif_repo.record_delivery(notif.id, "telegram", "success", str(res))
                else:
                    notif.status = "failed"
                    notif_repo.record_delivery(notif.id, "telegram", "failed", error_message=res.get("error"))
                db.commit()


async def run_worker_cycle():
    """Ciclo executado periodicamente para todos os monitoramentos ativos pendentes."""
    db = SessionLocal()
    try:
        repo = MonitoringRepository(db)
        due_items = repo.get_due_for_check(limit=20)
        logger.info(f"Ciclo do worker iniciado. Itens elegíveis para verificação: {len(due_items)}")
        for item in due_items:
            try:
                await check_monitored_product(item.id, db)
            except Exception as e:
                logger.error(f"Erro ao processar item monitorado {item.id}: {e}")
    finally:
        db.close()


async def start_worker_loop(interval_seconds: int = 60):
    """Loop contínuo para o container de worker."""
    logger.info(f"Iniciando loop do worker de coleta com intervalo de {interval_seconds}s...")
    while True:
        try:
            await run_worker_cycle()
        except Exception as e:
            logger.error(f"Erro não tratado no worker loop: {e}")
        await asyncio.sleep(interval_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_worker_loop())
