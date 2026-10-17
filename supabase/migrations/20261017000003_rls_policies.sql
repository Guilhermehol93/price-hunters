-- ============================================================================
-- Price Hunter - Migração 00003: Row Level Security (RLS) e Políticas de Acesso
-- Compatível com: Supabase Auth e PostgreSQL Standalone
-- ============================================================================

-- Função auxiliar segura para obter o ID do usuário (compatível com Supabase e Standalone)
CREATE OR REPLACE FUNCTION current_app_user_id()
RETURNS UUID AS $$
BEGIN
    -- Se estiver rodando dentro do Supabase com auth.uid()
    IF NULLIF(current_setting('request.jwt.claim.sub', true), '') IS NOT NULL THEN
        RETURN (current_setting('request.jwt.claim.sub', true))::uuid;
    END IF;
    -- Se uma variável de sessão de aplicação estiver configurada (ex: standalone multi-user)
    IF NULLIF(current_setting('app.current_user_id', true), '') IS NOT NULL THEN
        RETURN (current_setting('app.current_user_id', true))::uuid;
    END IF;
    RETURN NULL;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- ----------------------------------------------------------------------------
-- 1. Habilitar RLS nas tabelas de dados privados de usuários
-- ----------------------------------------------------------------------------
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE monitored_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_deliveries ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- ----------------------------------------------------------------------------
-- 2. Habilitar RLS nas tabelas públicas de catálogo
-- ----------------------------------------------------------------------------
ALTER TABLE search_sites ENABLE ROW LEVEL SECURITY;
ALTER TABLE connector_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE stores ENABLE ROW LEVEL SECURITY;
ALTER TABLE sellers ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE product_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE commercial_listings ENABLE ROW LEVEL SECURITY;
ALTER TABLE price_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE external_history_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE collection_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE collection_logs ENABLE ROW LEVEL SECURITY;

-- ----------------------------------------------------------------------------
-- 3. Políticas para Catálogo Público (Leitura Livre / Escrita Restrita)
-- ----------------------------------------------------------------------------
-- Leitura pública para busca, anúncios, histórico e lojas
CREATE POLICY "Public read search_sites" ON search_sites FOR SELECT USING (true);
CREATE POLICY "Public read stores" ON stores FOR SELECT USING (true);
CREATE POLICY "Public read sellers" ON sellers FOR SELECT USING (true);
CREATE POLICY "Public read products" ON products FOR SELECT USING (true);
CREATE POLICY "Public read product_variants" ON product_variants FOR SELECT USING (true);
CREATE POLICY "Public read commercial_listings" ON commercial_listings FOR SELECT USING (true);
CREATE POLICY "Public read price_history" ON price_history FOR SELECT USING (true);
CREATE POLICY "Public read external_history_sources" ON external_history_sources FOR SELECT USING (true);

-- ----------------------------------------------------------------------------
-- 4. Políticas para Tabelas Privadas (Isolamento por Usuário)
-- ----------------------------------------------------------------------------

-- Usuários: apenas o próprio usuário pode ver e editar seu registro
CREATE POLICY "Users can view own profile"
    ON users FOR SELECT
    USING (id = current_app_user_id());

CREATE POLICY "Users can update own profile"
    ON users FOR UPDATE
    USING (id = current_app_user_id());

-- Preferências: apenas o próprio usuário
CREATE POLICY "Users can view own preferences"
    ON user_preferences FOR SELECT
    USING (user_id = current_app_user_id());

CREATE POLICY "Users can update own preferences"
    ON user_preferences FOR UPDATE
    USING (user_id = current_app_user_id())
    WITH CHECK (user_id = current_app_user_id());

CREATE POLICY "Users can insert own preferences"
    ON user_preferences FOR INSERT
    WITH CHECK (user_id = current_app_user_id());

-- Pesquisas Salvas
CREATE POLICY "Users can view own saved_searches"
    ON saved_searches FOR SELECT
    USING (user_id = current_app_user_id());

CREATE POLICY "Users can insert own saved_searches"
    ON saved_searches FOR INSERT
    WITH CHECK (user_id = current_app_user_id());

CREATE POLICY "Users can update own saved_searches"
    ON saved_searches FOR UPDATE
    USING (user_id = current_app_user_id())
    WITH CHECK (user_id = current_app_user_id());

CREATE POLICY "Users can delete own saved_searches"
    ON saved_searches FOR DELETE
    USING (user_id = current_app_user_id());

-- Produtos Monitorados
CREATE POLICY "Users can view own monitored_products"
    ON monitored_products FOR SELECT
    USING (user_id = current_app_user_id());

CREATE POLICY "Users can insert own monitored_products"
    ON monitored_products FOR INSERT
    WITH CHECK (user_id = current_app_user_id());

CREATE POLICY "Users can update own monitored_products"
    ON monitored_products FOR UPDATE
    USING (user_id = current_app_user_id())
    WITH CHECK (user_id = current_app_user_id());

CREATE POLICY "Users can delete own monitored_products"
    ON monitored_products FOR DELETE
    USING (user_id = current_app_user_id());

-- Regras de Alerta
CREATE POLICY "Users can view own alert_rules"
    ON alert_rules FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM monitored_products mp
        WHERE mp.id = alert_rules.monitored_product_id
          AND mp.user_id = current_app_user_id()
    ));

CREATE POLICY "Users can insert own alert_rules"
    ON alert_rules FOR INSERT
    WITH CHECK (EXISTS (
        SELECT 1 FROM monitored_products mp
        WHERE mp.id = alert_rules.monitored_product_id
          AND mp.user_id = current_app_user_id()
    ));

CREATE POLICY "Users can update own alert_rules"
    ON alert_rules FOR UPDATE
    USING (EXISTS (
        SELECT 1 FROM monitored_products mp
        WHERE mp.id = alert_rules.monitored_product_id
          AND mp.user_id = current_app_user_id()
    ));

CREATE POLICY "Users can delete own alert_rules"
    ON alert_rules FOR DELETE
    USING (EXISTS (
        SELECT 1 FROM monitored_products mp
        WHERE mp.id = alert_rules.monitored_product_id
          AND mp.user_id = current_app_user_id()
    ));

-- Notificações
CREATE POLICY "Users can view own notifications"
    ON notifications FOR SELECT
    USING (user_id = current_app_user_id());

CREATE POLICY "Users can update own notifications"
    ON notifications FOR UPDATE
    USING (user_id = current_app_user_id());

-- Entregas de Notificação
CREATE POLICY "Users can view own notification deliveries"
    ON notification_deliveries FOR SELECT
    USING (EXISTS (
        SELECT 1 FROM notifications n
        WHERE n.id = notification_deliveries.notification_id
          AND n.user_id = current_app_user_id()
    ));

-- Logs de Auditoria
CREATE POLICY "Users can view own audit_logs"
    ON audit_logs FOR SELECT
    USING (user_id = current_app_user_id());

-- ----------------------------------------------------------------------------
-- 5. Bypass RLS para Roles Administrativas e Service Role
-- ----------------------------------------------------------------------------
-- No Supabase, o papel 'service_role' é utilizado pelo Backend/Worker.
-- Se o papel 'service_role' existir no PostgreSQL, conceder políticas explícitas:
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
        EXECUTE 'CREATE POLICY "Service role full access users" ON users TO service_role USING (true) WITH CHECK (true);';
        EXECUTE 'CREATE POLICY "Service role full access preferences" ON user_preferences TO service_role USING (true) WITH CHECK (true);';
        EXECUTE 'CREATE POLICY "Service role full access searches" ON saved_searches TO service_role USING (true) WITH CHECK (true);';
        EXECUTE 'CREATE POLICY "Service role full access monitored" ON monitored_products TO service_role USING (true) WITH CHECK (true);';
        EXECUTE 'CREATE POLICY "Service role full access alerts" ON alert_rules TO service_role USING (true) WITH CHECK (true);';
        EXECUTE 'CREATE POLICY "Service role full access notifications" ON notifications TO service_role USING (true) WITH CHECK (true);';
        EXECUTE 'CREATE POLICY "Service role full access deliveries" ON notification_deliveries TO service_role USING (true) WITH CHECK (true);';
        EXECUTE 'CREATE POLICY "Service role full access connector_configs" ON connector_configs TO service_role USING (true) WITH CHECK (true);';
        EXECUTE 'CREATE POLICY "Service role full access collection_runs" ON collection_runs TO service_role USING (true) WITH CHECK (true);';
        EXECUTE 'CREATE POLICY "Service role full access collection_logs" ON collection_logs TO service_role USING (true) WITH CHECK (true);';
        EXECUTE 'CREATE POLICY "Service role full access audit_logs" ON audit_logs TO service_role USING (true) WITH CHECK (true);';
        EXECUTE 'CREATE POLICY "Service role full access listings" ON commercial_listings TO service_role USING (true) WITH CHECK (true);';
        EXECUTE 'CREATE POLICY "Service role full access history" ON price_history TO service_role USING (true) WITH CHECK (true);';
        EXECUTE 'CREATE POLICY "Service role full access products" ON products TO service_role USING (true) WITH CHECK (true);';
        EXECUTE 'CREATE POLICY "Service role full access variants" ON product_variants TO service_role USING (true) WITH CHECK (true);';
        EXECUTE 'CREATE POLICY "Service role full access stores" ON stores TO service_role USING (true) WITH CHECK (true);';
        EXECUTE 'CREATE POLICY "Service role full access sellers" ON sellers TO service_role USING (true) WITH CHECK (true);';
    END IF;
END
$$;
