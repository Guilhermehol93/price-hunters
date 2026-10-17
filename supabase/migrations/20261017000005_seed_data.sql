-- ============================================================================
-- Price Hunter - Migração 00005: Dados Iniciais e Conectores Padrão
-- ============================================================================

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
        '{"User-Agent": "PriceHunter/1.0 (+https://github.com/pricehunter)"}'::jsonb,
        '{"extract_installments": true, "filter_official_stores": false}'::jsonb,
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
        '{"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}'::jsonb,
        '{"parse_prime_badge": true, "currency": "BRL"}'::jsonb,
        true,
        'ok'
    ),
    (
        '22222222-2222-2222-2222-222222222003',
        '11111111-1111-1111-1111-111111111003',
        'scraper',
        'https://www.zoom.com.br/search',
        30,
        15,
        '{"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}'::jsonb,
        '{"fetch_historical_chart": true}'::jsonb,
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

-- 4. Usuário Padrão Inicial (Demonstração / Standalone)
INSERT INTO users (id, email, full_name, role, is_active)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'admin@pricehunter.local', 'Administrador Price Hunter', 'admin', true)
ON CONFLICT (email) DO NOTHING;

-- 5. Preferências do Usuário Padrão
INSERT INTO user_preferences (id, user_id, default_discount_threshold, default_opportunity_score_threshold, telegram_chat_id, notify_by_telegram, notify_by_email, preferred_currency, theme)
VALUES
    ('00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', 15.00, 75, NULL, true, false, 'BRL', 'dark')
ON CONFLICT (user_id) DO NOTHING;

-- 6. Produtos de Demonstração para Radar de Ofertas Inicial
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
    ),
    (
        '44444444-4444-4444-4444-444444444003',
        'Smartphone Samsung Galaxy S24 256GB 8GB RAM Tela 6.2" Galaxy AI',
        'Linha flagship com recursos de inteligência artificial generativa integrados e câmera de 50MP.',
        'Samsung',
        'SM-S921B',
        'Smartphones e Celulares',
        '7892509133487',
        'https://m.media-amazon.com/images/I/61jC7S1bQKL._AC_SL1000_.jpg'
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
    ),
    (
        '55555555-5555-5555-5555-555555555003',
        '44444444-4444-4444-4444-444444444003',
        '33333333-3333-3333-3333-333333333001',
        'MLB-GALAXY-S24-256',
        'https://www.mercadolivre.com.br/samsung-galaxy-s24-256gb/p/MLB289410',
        'Samsung Galaxy S24 5G 256GB Cinza Titânio',
        4149.00,
        4999.00,
        'BRL',
        true,
        'new',
        4.78,
        530,
        84,
        17.00,
        NOW() - INTERVAL '45 minutes',
        true
    )
ON CONFLICT DO NOTHING;

-- 8. Histórico Sintético de Preços (30 dias para demonstração dos gráficos de tendência)
INSERT INTO price_history (listing_id, current_price, original_price, observed_at, source)
VALUES
    ('55555555-5555-5555-5555-555555555001', 3799.00, 3799.00, NOW() - INTERVAL '30 days', 'demo_seed'),
    ('55555555-5555-5555-5555-555555555001', 3699.00, 3799.00, NOW() - INTERVAL '20 days', 'demo_seed'),
    ('55555555-5555-5555-5555-555555555001', 3599.00, 3799.00, NOW() - INTERVAL '10 days', 'demo_seed'),
    ('55555555-5555-5555-5555-555555555001', 3399.00, 3799.00, NOW() - INTERVAL '3 days', 'demo_seed'),
    ('55555555-5555-5555-5555-555555555001', 3199.00, 3799.00, NOW() - INTERVAL '30 minutes', 'demo_seed'),

    ('55555555-5555-5555-5555-555555555002', 1299.90, 1299.90, NOW() - INTERVAL '30 days', 'demo_seed'),
    ('55555555-5555-5555-5555-555555555002', 1199.90, 1299.90, NOW() - INTERVAL '15 days', 'demo_seed'),
    ('55555555-5555-5555-5555-555555555002', 1049.90, 1199.90, NOW() - INTERVAL '5 days', 'demo_seed'),
    ('55555555-5555-5555-5555-555555555002', 899.90, 1199.90, NOW() - INTERVAL '15 minutes', 'demo_seed'),

    ('55555555-5555-5555-5555-555555555003', 4999.00, 4999.00, NOW() - INTERVAL '30 days', 'demo_seed'),
    ('55555555-5555-5555-5555-555555555003', 4799.00, 4999.00, NOW() - INTERVAL '14 days', 'demo_seed'),
    ('55555555-5555-5555-5555-555555555003', 4499.00, 4999.00, NOW() - INTERVAL '7 days', 'demo_seed'),
    ('55555555-5555-5555-5555-555555555003', 4149.00, 4999.00, NOW() - INTERVAL '45 minutes', 'demo_seed');

-- 9. Exemplo de Monitoramento Ativo com Alerta Configurado
INSERT INTO monitored_products (
    id, user_id, product_id, listing_id, target_price,
    target_discount_pct, check_frequency_minutes, is_active, notify_on_stock
) VALUES (
    '66666666-6666-6666-6666-666666666001',
    '00000000-0000-0000-0000-000000000001',
    '44444444-4444-4444-4444-444444444001',
    '55555555-5555-5555-5555-555555555001',
    3250.00,
    15.00,
    30,
    true,
    true
) ON CONFLICT DO NOTHING;

INSERT INTO alert_rules (
    id, monitored_product_id, rule_type, threshold_value,
    is_active, cooldown_hours, channel
) VALUES (
    '77777777-7777-7777-7777-777777777001',
    '66666666-6666-6666-6666-666666666001',
    'target_price',
    3250.00,
    true,
    12,
    'telegram'
) ON CONFLICT DO NOTHING;
