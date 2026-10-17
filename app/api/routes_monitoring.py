"""Monitoring and Alert Rules API Routes"""

from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import get_db
from app.repositories.monitoring_repo import MonitoringRepository
from app.repositories.listing_repo import ListingRepository
from app.repositories.product_repo import ProductRepository
from app.models.monitoring import MonitoredProduct, AlertRule
from app.models.listing import CommercialListing
from app.models.product import Product
from app.models.store import Store
from app.models.user import User
from app.schemas.monitoring import (
    MonitoredProductCreate, MonitoredProductResponse, AlertRuleResponse
)
from app.services.ssrf_guard import validate_target_url, SSRFSecurityException
from app.connectors import get_connector_for_url
from app.workers.task_worker import check_monitored_product

router = APIRouter(prefix="/monitoring", tags=["Monitoramento e Alertas"])


def get_current_user_id(db: Session) -> UUID:
    """Retorna o ID do usuário padrão (em modo standalone) ou extrai do token JWT."""
    stmt = select(User).where(User.role == "admin").limit(1)
    admin = db.scalars(stmt).first()
    if admin:
        return admin.id
    # Se ainda não houver usuário, cria temporariamente o admin
    default_admin = User(email="admin@pricehunter.local", full_name="Admin", role="admin")
    db.add(default_admin)
    db.commit()
    db.refresh(default_admin)
    return default_admin.id


@router.get("", response_model=list[MonitoredProductResponse])
def list_monitored(db: Session = Depends(get_db)):
    repo = MonitoringRepository(db)
    user_id = get_current_user_id(db)
    return repo.get_by_user(user_id=user_id, is_active_only=False)


@router.post("", response_model=MonitoredProductResponse, status_code=201)
async def create_monitored_product(
    payload: MonitoredProductCreate,
    db: Session = Depends(get_db)
):
    user_id = get_current_user_id(db)
    listing_id = payload.listing_id
    product_id = payload.product_id

    # Se uma URL direta foi informada (cadastro por URL)
    if payload.custom_url:
        try:
            safe_url = validate_target_url(payload.custom_url)
        except SSRFSecurityException as e:
            raise HTTPException(status_code=400, detail=f"URL bloqueada por segurança (SSRF): {e}")

        # Tenta raspar os dados imediatamente
        connector = get_connector_for_url(safe_url)
        scraped = await connector.fetch_product_details(safe_url)
        if not scraped:
            raise HTTPException(status_code=422, detail="Não foi possível extrair dados e preço da URL informada.")

        # Garantir ou criar a loja
        stmt = select(Store).where(Store.slug == scraped.store_slug)
        store = db.scalars(stmt).first()
        if not store:
            store = Store(
                slug=scraped.store_slug,
                name=scraped.store_slug.capitalize(),
                domain=scraped.store_slug + ".com"
            )
            db.add(store)
            db.commit()
            db.refresh(store)

        # Criar ou encontrar produto
        prod = Product(
            title=scraped.title,
            image_url=scraped.image_url,
            category="Geral"
        )
        db.add(prod)
        db.commit()
        db.refresh(prod)
        product_id = prod.id

        # Criar o anúncio comercial
        listing = CommercialListing(
            product_id=prod.id,
            store_id=store.id,
            url=safe_url,
            title=scraped.title,
            current_price=scraped.current_price,
            original_price=scraped.original_price,
            opportunity_score=50,
            historical_discount_pct=Decimal("0.0")
        )
        db.add(listing)
        db.commit()
        db.refresh(listing)
        listing_id = listing.id

    if not listing_id and not product_id:
        raise HTTPException(status_code=400, detail="É necessário informar listing_id, product_id ou custom_url.")

    monitored = MonitoredProduct(
        user_id=user_id,
        product_id=product_id,
        listing_id=listing_id,
        target_price=payload.target_price,
        target_discount_pct=payload.target_discount_pct,
        check_frequency_minutes=payload.check_frequency_minutes,
        notify_on_stock=payload.notify_on_stock,
        is_active=True
    )
    db.add(monitored)
    db.commit()
    db.refresh(monitored)

    # Regras de alerta associadas
    if payload.rules:
        for r in payload.rules:
            rule = AlertRule(
                monitored_product_id=monitored.id,
                rule_type=r.rule_type,
                threshold_value=r.threshold_value,
                is_active=r.is_active,
                cooldown_hours=r.cooldown_hours,
                channel=r.channel
            )
            db.add(rule)
    else:
        # Regra padrão: avisar se o preço cair até a meta ou score >= 75
        target_val = payload.target_price or Decimal("0.0")
        rule = AlertRule(
            monitored_product_id=monitored.id,
            rule_type="target_price" if payload.target_price else "opportunity_score",
            threshold_value=target_val if payload.target_price else Decimal("75"),
            channel="telegram"
        )
        db.add(rule)

    db.commit()
    db.refresh(monitored)
    return monitored


@router.post("/{monitored_id}/check-now")
async def trigger_immediate_check(monitored_id: UUID, db: Session = Depends(get_db)):
    repo = MonitoringRepository(db)
    item = repo.get_by_id(monitored_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item monitorado não encontrado")

    await check_monitored_product(monitored_id, db)
    return {"message": "Verificação concluída com sucesso"}


@router.delete("/{monitored_id}", status_code=204)
def delete_monitored(monitored_id: UUID, db: Session = Depends(get_db)):
    repo = MonitoringRepository(db)
    ok = repo.delete(monitored_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return None
