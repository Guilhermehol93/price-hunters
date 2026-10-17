"""Integration Tests for FastAPI Endpoints"""

from decimal import Decimal
from app.models.store import Store
from app.models.product import Product
from app.models.listing import CommercialListing


def test_health_check(client):
    res = client.get("/api/system/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database"]["status"] == "connected"


def test_system_stats(client, db_session):
    res = client.get("/api/system/stats")
    assert res.status_code == 200
    data = res.json()
    assert "products_count" in data
    assert "listings_count" in data


def test_create_and_list_product(client):
    payload = {
        "title": "Monitor Gamer Teste 24 polegadas",
        "brand": "AOC",
        "category": "Monitores",
        "description": "Monitor para testes unitários"
    }
    res = client.post("/api/products", json=payload)
    assert res.status_code == 201
    created = res.json()
    assert created["title"] == payload["title"]

    # Listar produtos
    list_res = client.get("/api/products")
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 1
    assert any(i["title"] == payload["title"] for i in items)


def test_radar_endpoint(client, db_session):
    # Criar loja e anúncio com alto score
    store = Store(slug="kabum_test", name="KaBuM! Teste", domain="kabum.com.br")
    db_session.add(store)
    db_session.commit()
    db_session.refresh(store)

    listing = CommercialListing(
        store_id=store.id,
        url="https://www.kabum.com.br/produto/123",
        title="Placa de Vídeo RTX 4070 em Promoção",
        current_price=Decimal("3500.00"),
        original_price=Decimal("4500.00"),
        opportunity_score=88,
        historical_discount_pct=Decimal("22.2"),
        is_active=True,
        in_stock=True
    )
    db_session.add(listing)
    db_session.commit()

    # Buscar no radar com filtro de score >= 80
    res = client.get("/api/radar?min_score=80")
    assert res.status_code == 200
    deals = res.json()
    assert len(deals) >= 1
    assert deals[0]["opportunity_score"] >= 80


def test_telegram_status(client):
    res = client.get("/api/telegram/status")
    assert res.status_code == 200
    data = res.json()
    assert "configured" in data


def test_list_products_empty(client):
    res = client.get("/api/products")
    assert res.status_code == 200
    assert res.json() == []


def test_search_products(client):
    payload1 = {"title": "Mouse Gamer Logitech G502", "brand": "Logitech", "category": "Periféricos"}
    payload2 = {"title": "Teclado Mecânico Redragon", "brand": "Redragon", "category": "Teclados"}
    client.post("/api/products", json=payload1)
    client.post("/api/products", json=payload2)

    res = client.get("/api/products?q=Logitech")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 1
    assert items[0]["brand"] == "Logitech"


def test_monitoring_endpoints(client):
    # Lista monitoramentos inicialmente vazia
    res = client.get("/api/monitoring")
    assert res.status_code == 200
    assert res.json() == []

    # Criar um produto primeiro
    prod_res = client.post("/api/products", json={"title": "Fone Bluetooth JBL", "brand": "JBL"})
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["id"]

    # Adicionar monitoramento para o produto criado
    mon_payload = {
        "product_id": prod_id,
        "target_price": 199.90,
        "check_frequency_minutes": 30
    }
    create_res = client.post("/api/monitoring", json=mon_payload)
    assert create_res.status_code == 201
    mon_data = create_res.json()
    assert mon_data["product_id"] == prod_id
    assert float(mon_data["target_price"]) == 199.90

    # Consultar lista
    list_res = client.get("/api/monitoring")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1
