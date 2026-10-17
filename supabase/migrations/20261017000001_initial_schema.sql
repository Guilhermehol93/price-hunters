-- ============================================================================
-- Price Hunter - Migração 00001: Esquema Relacional Inicial
-- Compatível com: PostgreSQL 14+, PostgreSQL 15+, PostgreSQL 16+ e Supabase
-- ============================================================================

-- Habilita extensão para geração de UUIDs nativos
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tabela de Migrações (controle interno de versão)
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(100) PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    checksum VARCHAR(64)
);

-- 1. Usuários
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'user', -- 'admin', 'user', 'viewer'
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Preferências do Usuário
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    default_discount_threshold NUMERIC(5,2) NOT NULL DEFAULT 15.00,
    default_opportunity_score_threshold INTEGER NOT NULL DEFAULT 70,
    telegram_chat_id VARCHAR(100),
    notify_by_telegram BOOLEAN NOT NULL DEFAULT TRUE,
    notify_by_email BOOLEAN NOT NULL DEFAULT FALSE,
    preferred_currency VARCHAR(10) NOT NULL DEFAULT 'BRL',
    theme VARCHAR(20) NOT NULL DEFAULT 'dark',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Sites de Busca
CREATE TABLE IF NOT EXISTS search_sites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    base_url VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER NOT NULL DEFAULT 10,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Configurações dos Conectores
CREATE TABLE IF NOT EXISTS connector_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID NOT NULL REFERENCES search_sites(id) ON DELETE CASCADE,
    connector_type VARCHAR(50) NOT NULL, -- 'api', 'scraper', 'rss', 'headless'
    api_endpoint VARCHAR(500),
    rate_limit_per_minute INTEGER NOT NULL DEFAULT 30,
    timeout_seconds INTEGER NOT NULL DEFAULT 15,
    headers JSONB DEFAULT '{}'::jsonb,
    auth_config JSONB DEFAULT '{}'::jsonb,
    custom_settings JSONB DEFAULT '{}'::jsonb,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_tested_at TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'idle', -- 'idle', 'ok', 'error', 'degraded'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Lojas
CREATE TABLE IF NOT EXISTS stores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    logo_url VARCHAR(500),
    reputation_score NUMERIC(4,2) DEFAULT 8.00, -- 0.00 a 10.00
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. Vendedores (Marketplace Sellers)
CREATE TABLE IF NOT EXISTS sellers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    external_seller_id VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    rating NUMERIC(3,2), -- 0.00 a 5.00
    sales_count INTEGER DEFAULT 0,
    is_official BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_sellers_store_external UNIQUE (store_id, external_seller_id)
);

-- 7. Produtos (Catálogo Geral Normalizado)
CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    brand VARCHAR(100),
    model VARCHAR(100),
    category VARCHAR(150),
    ean_gtin VARCHAR(50),
    image_url VARCHAR(1000),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8. Variantes de Produtos
CREATE TABLE IF NOT EXISTS product_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    sku VARCHAR(100),
    title VARCHAR(500) NOT NULL,
    attributes JSONB DEFAULT '{}'::jsonb, -- e.g. {"cor": "Preto", "voltagem": "220V", "capacidade": "256GB"}
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9. Anúncios Comerciais (Listings)
CREATE TABLE IF NOT EXISTS commercial_listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    variant_id UUID REFERENCES product_variants(id) ON DELETE SET NULL,
    store_id UUID NOT NULL REFERENCES stores(id) ON DELETE CASCADE,
    seller_id UUID REFERENCES sellers(id) ON DELETE SET NULL,
    external_id VARCHAR(255),
    url VARCHAR(1500) NOT NULL,
    title VARCHAR(500) NOT NULL,
    current_price NUMERIC(12,2) NOT NULL,
    original_price NUMERIC(12,2),
    currency VARCHAR(10) NOT NULL DEFAULT 'BRL',
    in_stock BOOLEAN NOT NULL DEFAULT TRUE,
    condition VARCHAR(50) NOT NULL DEFAULT 'new', -- 'new', 'used', 'refurbished'
    rating NUMERIC(3,2),
    reviews_count INTEGER DEFAULT 0,
    opportunity_score INTEGER NOT NULL DEFAULT 0, -- 0 a 100
    historical_discount_pct NUMERIC(5,2) NOT NULL DEFAULT 0.00,
    last_checked_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_listings_store_external UNIQUE (store_id, external_id)
);

-- 10. Histórico de Preços (Snapshots/Observações)
CREATE TABLE IF NOT EXISTS price_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID NOT NULL REFERENCES commercial_listings(id) ON DELETE CASCADE,
    current_price NUMERIC(12,2) NOT NULL,
    original_price NUMERIC(12,2),
    observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source VARCHAR(50) NOT NULL DEFAULT 'crawler', -- 'crawler', 'api', 'manual', 'external'
    raw_payload JSONB DEFAULT '{}'::jsonb
);

-- 11. Fontes Externas de Histórico
CREATE TABLE IF NOT EXISTS external_history_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID NOT NULL REFERENCES commercial_listings(id) ON DELETE CASCADE,
    source_name VARCHAR(100) NOT NULL, -- e.g. 'zoom_history', 'buscape_history', 'keepa'
    external_product_id VARCHAR(255),
    min_price_observed NUMERIC(12,2),
    max_price_observed NUMERIC(12,2),
    avg_price_observed NUMERIC(12,2),
    last_synced_at TIMESTAMPTZ,
    data_points_count INTEGER DEFAULT 0,
    raw_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 12. Pesquisas Salvas
CREATE TABLE IF NOT EXISTS saved_searches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    query_term VARCHAR(255) NOT NULL,
    filters JSONB DEFAULT '{}'::jsonb, -- e.g. {"max_price": 2500, "min_score": 75, "stores": ["amazon"]}
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    execution_frequency_hours INTEGER NOT NULL DEFAULT 6,
    last_executed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 13. Produtos Monitorados
CREATE TABLE IF NOT EXISTS monitored_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    listing_id UUID REFERENCES commercial_listings(id) ON DELETE SET NULL,
    target_price NUMERIC(12,2),
    target_discount_pct NUMERIC(5,2),
    check_frequency_minutes INTEGER NOT NULL DEFAULT 60,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    notify_on_stock BOOLEAN NOT NULL DEFAULT TRUE,
    last_checked_at TIMESTAMPTZ,
    last_notified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 14. Regras de Alerta
CREATE TABLE IF NOT EXISTS alert_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    monitored_product_id UUID NOT NULL REFERENCES monitored_products(id) ON DELETE CASCADE,
    rule_type VARCHAR(50) NOT NULL, -- 'target_price', 'percentage_drop', 'opportunity_score', 'all_time_low'
    threshold_value NUMERIC(12,2) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    cooldown_hours INTEGER NOT NULL DEFAULT 24,
    channel VARCHAR(50) NOT NULL DEFAULT 'telegram', -- 'telegram', 'email', 'webhook'
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 15. Notificações
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    monitored_product_id UUID REFERENCES monitored_products(id) ON DELETE SET NULL,
    listing_id UUID REFERENCES commercial_listings(id) ON DELETE SET NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    channel VARCHAR(50) NOT NULL DEFAULT 'telegram',
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'sent', 'failed'
    trigger_price NUMERIC(12,2),
    trigger_discount_pct NUMERIC(5,2),
    trigger_opportunity_score INTEGER,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 16. Tentativas de Entrega de Notificação
CREATE TABLE IF NOT EXISTS notification_deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    notification_id UUID NOT NULL REFERENCES notifications(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(50) NOT NULL, -- 'success', 'failed', 'retry'
    external_response TEXT,
    error_message TEXT,
    delivered_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 17. Execuções de Pesquisas e Coletas
CREATE TABLE IF NOT EXISTS collection_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID REFERENCES search_sites(id) ON DELETE SET NULL,
    trigger_type VARCHAR(50) NOT NULL, -- 'scheduled', 'manual', 'monitoring'
    status VARCHAR(50) NOT NULL DEFAULT 'running', -- 'running', 'completed', 'failed', 'cancelled'
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    items_scraped INTEGER NOT NULL DEFAULT 0,
    items_updated INTEGER NOT NULL DEFAULT 0,
    errors_count INTEGER NOT NULL DEFAULT 0,
    log_summary TEXT
);

-- 18. Logs Detalhados de Coleta
CREATE TABLE IF NOT EXISTS collection_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES collection_runs(id) ON DELETE CASCADE,
    level VARCHAR(20) NOT NULL, -- 'info', 'warning', 'error', 'debug'
    message TEXT NOT NULL,
    context JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 19. Logs de Auditoria
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL, -- 'create_alert', 'update_config', 'trigger_crawl', etc.
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID,
    changes JSONB DEFAULT '{}'::jsonb,
    ip_address VARCHAR(50),
    user_agent VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
