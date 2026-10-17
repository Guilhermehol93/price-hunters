-- ==============================================================================
-- Supabase Seed Data - Price Hunter
-- ==============================================================================

-- 1. Sites de Busca Padrão
INSERT INTO search_sites (id, slug, name, base_url, is_active, priority)
VALUES
    ('11111111-1111-1111-1111-111111111001', 'mercadolivre', 'Mercado Livre Brasil', 'https://www.mercadolivre.com.br', true, 10),
    ('11111111-1111-1111-1111-111111111002', 'amazon_br', 'Amazon Brasil', 'https://www.amazon.com.br', true, 20),
    ('11111111-1111-1111-1111-111111111003', 'zoom', 'Zoom Preços', 'https://www.zoom.com.br', true, 30),
    ('11111111-1111-1111-1111-111111111004', 'buscape', 'Buscapé Comparador', 'https://www.buscape.com.br', true, 40)
ON CONFLICT (slug) DO NOTHING;

-- 2. Configurações dos Conectores Nativos
INSERT INTO connector_configs (id, site_id, connector_type, api_endpoint, rate_limit_per_minute, timeout_seconds, headers, custom_settings, is_enabled, status)
VALUES
    (
        '22222222-2222-2222-2222-222222222001',
        '11111111-1111-1111-1111-111111111001',
        'scraper',
        'https://api.mercadolibre.com/sites/MLB/search',
        40,
        15,
        '{"User-Agent": "PriceHunter/1.0"}'::jsonb,
        '{"extract_installments": true}'::jsonb,
        true,
        'ok'
    ),
    (
        '22222222-2222-2222-2222-222222222002',
        '11111111-1111-1111-1111-111111111002',
        'scraper',
        'https://www.amazon.com.br/s',
        25,
        20,
        '{"User-Agent": "Mozilla/5.0"}'::jsonb,
        '{"parse_prime_badge": true}'::jsonb,
        true,
        'ok'
    )
ON CONFLICT DO NOTHING;

-- 3. Lojas Comerciais de Referência
INSERT INTO stores (id, slug, name, domain, logo_url, reputation_score, is_active)
VALUES
    ('33333333-3333-3333-3333-333333333001', 'mercadolivre', 'Mercado Livre', 'mercadolivre.com.br', '/assets/stores/ml.svg', 9.20, true),
    ('33333333-3333-3333-3333-333333333002', 'amazon', 'Amazon Brasil', 'amazon.com.br', '/assets/stores/amazon.svg', 9.50, true),
    ('33333333-3333-3333-3333-333333333003', 'magalu', 'Magazine Luiza', 'magazineluiza.com.br', '/assets/stores/magalu.svg', 8.90, true),
    ('33333333-3333-3333-3333-333333333004', 'kabum', 'KaBuM!', 'kabum.com.br', '/assets/stores/kabum.svg', 9.10, true)
ON CONFLICT (slug) DO NOTHING;

-- 4. Usuário Padrão Inicial
INSERT INTO users (id, email, full_name, role, is_active)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'admin@pricehunter.local', 'Administrador Price Hunter', 'admin', true)
ON CONFLICT (email) DO NOTHING;

-- 5. Preferências do Usuário Padrão
INSERT INTO user_preferences (id, user_id, default_discount_threshold, default_opportunity_score_threshold, telegram_chat_id, notify_by_telegram, notify_by_email, preferred_currency, theme)
VALUES
    ('00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 15.00, 75, NULL, true, false, 'BRL', 'dark')
ON CONFLICT (user_id) DO NOTHING;

-- 6. Produtos de Demonstração
INSERT INTO products (id, title, description, brand, model, category, ean_gtin, image_url)
VALUES
    (
        '44444444-4444-4444-4444-444444444001',
        'Console PlayStation 5 Slim Edição Digital com 1 Controle sem Fio DualSense',
        'Console de última geração Sony com carregamento ultrarrápido em SSD de 1TB e gráficos 4K.',
        'Sony',
        'CFI-2000',
        'Consoles e Games',
        '0711719574446',
        'https://m.media-amazon.com/images/I/51wXpMvF1mL._AC_SL1000_.jpg'
    ),
    (
        '44444444-4444-4444-4444-444444444002',
        'Monitor Gamer LG UltraGear 27" IPS Full HD 144Hz 1ms HDR10 FreeSync',
        'Monitor de alto desempenho para jogos competitivos com taxa de atualização de 144Hz e painel IPS.',
        'LG',
        '27GN65R',
        'Monitores e Informática',
        '7893299920141',
        'https://m.media-amazon.com/images/I/71u+m6rMtkL._AC_SL1500_.jpg'
    )
ON CONFLICT DO NOTHING;

-- 7. Anúncios Comerciais dos Produtos de Demonstração
INSERT INTO commercial_listings (
    id, product_id, store_id, external_id, url, title,
    current_price, original_price, currency, in_stock,
    condition, rating, reviews_count, opportunity_score, historical_discount_pct,
    last_checked_at, is_active
) VALUES
    (
        '55555555-5555-5555-5555-555555555001',
        '44444444-4444-4444-4444-444444444001',
        '33333333-3333-3333-3333-333333333002',
        'AMZ-PS5-SLIM-DIG',
        'https://www.amazon.com.br/dp/B0DF1M7R6L',
        'PlayStation 5 Slim Edição Digital Sony 1TB',
        3199.00,
        3799.00,
        'BRL',
        true,
        'new',
        4.85,
        1420,
        88,
        15.79,
        NOW() - INTERVAL '30 minutes',
        true
    ),
    (
        '55555555-5555-5555-5555-555555555002',
        '44444444-4444-4444-4444-444444444002',
        '33333333-3333-3333-3333-333333333004',
        'KABUM-MONITOR-LG27',
        'https://www.kabum.com.br/produto/384654/monitor-gamer-lg-ultragear-27',
        'Monitor Gamer LG UltraGear 27 IPS 144Hz 1ms',
        899.90,
        1199.90,
        'BRL',
        true,
        'new',
        4.90,
        870,
        92,
        25.00,
        NOW() - INTERVAL '15 minutes',
        true
    )
ON CONFLICT DO NOTHING;
