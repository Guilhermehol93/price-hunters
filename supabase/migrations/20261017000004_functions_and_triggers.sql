-- ============================================================================
-- Price Hunter - Migração 00004: Funções e Gatilhos (Triggers)
-- Compatível com: PostgreSQL 14+ e Supabase
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Função Genérica para Atualização Automática de updated_at
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar gatilho updated_at nas tabelas relevantes
DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS trg_user_preferences_updated_at ON user_preferences;
CREATE TRIGGER trg_user_preferences_updated_at
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS trg_search_sites_updated_at ON search_sites;
CREATE TRIGGER trg_search_sites_updated_at
    BEFORE UPDATE ON search_sites
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS trg_connector_configs_updated_at ON connector_configs;
CREATE TRIGGER trg_connector_configs_updated_at
    BEFORE UPDATE ON connector_configs
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS trg_stores_updated_at ON stores;
CREATE TRIGGER trg_stores_updated_at
    BEFORE UPDATE ON stores
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS trg_sellers_updated_at ON sellers;
CREATE TRIGGER trg_sellers_updated_at
    BEFORE UPDATE ON sellers
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS trg_products_updated_at ON products;
CREATE TRIGGER trg_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS trg_product_variants_updated_at ON product_variants;
CREATE TRIGGER trg_product_variants_updated_at
    BEFORE UPDATE ON product_variants
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS trg_commercial_listings_updated_at ON commercial_listings;
CREATE TRIGGER trg_commercial_listings_updated_at
    BEFORE UPDATE ON commercial_listings
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS trg_monitored_products_updated_at ON monitored_products;
CREATE TRIGGER trg_monitored_products_updated_at
    BEFORE UPDATE ON monitored_products
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS trg_alert_rules_updated_at ON alert_rules;
CREATE TRIGGER trg_alert_rules_updated_at
    BEFORE UPDATE ON alert_rules
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS trg_saved_searches_updated_at ON saved_searches;
CREATE TRIGGER trg_saved_searches_updated_at
    BEFORE UPDATE ON saved_searches
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS trg_notifications_updated_at ON notifications;
CREATE TRIGGER trg_notifications_updated_at
    BEFORE UPDATE ON notifications
    FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ----------------------------------------------------------------------------
-- 2. Gatilho de Snapshot Automático de Histórico de Preço
-- Disparado quando um anúncio é inserido ou seu preço atual se altera
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trigger_capture_price_history()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'INSERT') OR (TG_OP = 'UPDATE' AND NEW.current_price IS DISTINCT FROM OLD.current_price) THEN
        INSERT INTO price_history (
            listing_id,
            current_price,
            original_price,
            observed_at,
            source,
            raw_payload
        ) VALUES (
            NEW.id,
            NEW.current_price,
            NEW.original_price,
            NOW(),
            'trigger_auto',
            json_build_object(
                'trigger_op', TG_OP,
                'in_stock', NEW.in_stock,
                'is_active', NEW.is_active
            )::jsonb
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_listings_capture_price ON commercial_listings;
CREATE TRIGGER trg_listings_capture_price
    AFTER INSERT OR UPDATE ON commercial_listings
    FOR EACH ROW EXECUTE FUNCTION trigger_capture_price_history();
