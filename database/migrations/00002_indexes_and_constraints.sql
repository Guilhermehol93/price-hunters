-- ============================================================================
-- Price Hunter - Migração 00002: Índices e Restrições de Integridade
-- Compatível com: PostgreSQL 14+ e Supabase
-- ============================================================================

-- Restrições de Validação de Valores
ALTER TABLE commercial_listings
    ADD CONSTRAINT chk_listings_positive_price CHECK (current_price >= 0),
    ADD CONSTRAINT chk_listings_opportunity_score CHECK (opportunity_score >= 0 AND opportunity_score <= 100);

ALTER TABLE price_history
    ADD CONSTRAINT chk_price_history_positive_price CHECK (current_price >= 0);

ALTER TABLE alert_rules
    ADD CONSTRAINT chk_alert_rules_cooldown CHECK (cooldown_hours >= 0);

ALTER TABLE monitored_products
    ADD CONSTRAINT chk_monitored_frequency CHECK (check_frequency_minutes >= 5);

ALTER TABLE users
    ADD CONSTRAINT chk_users_role CHECK (role IN ('admin', 'user', 'viewer'));

-- ----------------------------------------------------------------------------
-- Índices para Histórico de Preços (Volume Elevado)
-- ----------------------------------------------------------------------------
-- Consulta rápida de histórico temporal por anúncio
CREATE INDEX IF NOT EXISTS idx_price_history_listing_observed
    ON price_history (listing_id, observed_at DESC);

-- Consulta de mínima/máxima por anúncio
CREATE INDEX IF NOT EXISTS idx_price_history_listing_price
    ON price_history (listing_id, current_price ASC);

-- ----------------------------------------------------------------------------
-- Índices para Anúncios Comerciais (Listings)
-- ----------------------------------------------------------------------------
-- Radar de Ofertas: ordenar por pontuação de oportunidade e desconto
CREATE INDEX IF NOT EXISTS idx_listings_radar
    ON commercial_listings (is_active, opportunity_score DESC, current_price ASC)
    WHERE is_active = TRUE;

-- Busca de anúncios por produto
CREATE INDEX IF NOT EXISTS idx_listings_product_id
    ON commercial_listings (product_id);

-- Busca de anúncios por loja
CREATE INDEX IF NOT EXISTS idx_listings_store_id
    ON commercial_listings (store_id);

-- Busca de anúncios atualizados recentemente
CREATE INDEX IF NOT EXISTS idx_listings_last_checked
    ON commercial_listings (last_checked_at);

-- ----------------------------------------------------------------------------
-- Índices para Produtos
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_products_category
    ON products (category);

CREATE INDEX IF NOT EXISTS idx_products_brand
    ON products (brand);

CREATE INDEX IF NOT EXISTS idx_products_ean
    ON products (ean_gtin)
    WHERE ean_gtin IS NOT NULL;

-- ----------------------------------------------------------------------------
-- Índices para Monitoramento e Alertas
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_monitored_user_active
    ON monitored_products (user_id, is_active);

CREATE INDEX IF NOT EXISTS idx_monitored_schedule
    ON monitored_products (is_active, last_checked_at NULLS FIRST)
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_alert_rules_monitored
    ON alert_rules (monitored_product_id, is_active);

CREATE INDEX IF NOT EXISTS idx_notifications_user_status
    ON notifications (user_id, status, created_at DESC);

-- ----------------------------------------------------------------------------
-- Índices para Coletas e Logs
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_collection_runs_site_status
    ON collection_runs (site_id, status, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_collection_logs_run_level
    ON collection_logs (run_id, level);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_date
    ON audit_logs (user_id, created_at DESC);
