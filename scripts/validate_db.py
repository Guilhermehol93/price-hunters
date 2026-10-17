#!/usr/bin/env python3
"""
Price Hunter - Database Schema & Integrity Validator
Verifies tables, constraints, indexes, and RLS configurations on PostgreSQL / Supabase.
"""

import os
import sys
import argparse
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import psycopg
except ImportError:
    print("[ERROR] psycopg not found. Please install: pip install \"psycopg[binary]\"")
    sys.exit(1)


EXPECTED_TABLES = [
    "schema_migrations",
    "users",
    "user_preferences",
    "search_sites",
    "connector_configs",
    "stores",
    "sellers",
    "products",
    "product_variants",
    "commercial_listings",
    "price_history",
    "external_history_sources",
    "saved_searches",
    "monitored_products",
    "alert_rules",
    "notifications",
    "notification_deliveries",
    "collection_runs",
    "collection_logs",
    "audit_logs"
]

RLS_PROTECTED_TABLES = [
    "users",
    "user_preferences",
    "saved_searches",
    "monitored_products",
    "alert_rules",
    "notifications",
    "notification_deliveries",
    "audit_logs",
    "search_sites",
    "connector_configs",
    "stores",
    "sellers",
    "products",
    "product_variants",
    "commercial_listings",
    "price_history",
    "external_history_sources",
    "collection_runs",
    "collection_logs"
]


def validate_schema(db_url: str):
    print("=" * 70)
    print(" PRICE HUNTER - VALIDAÇÃO DE INTEGRIDADE DO BANCO DE DADOS")
    print("=" * 70)

    try:
        conn = psycopg.connect(db_url, prepare_threshold=None)
    except Exception as e:
        print(f"[FAIL] Falha ao conectar: {e}")
        return False

    all_passed = True

    with conn.cursor() as cur:
        # 1. Checar versão do PostgreSQL
        cur.execute("SELECT version();")
        pg_version = cur.fetchone()[0]
        print(f"[INFO] Servidor: {pg_version[:60]}...")

        # 2. Verificar Tabelas Existentes
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
        """)
        existing_tables = {row[0] for row in cur.fetchall()}

        print("\n[CHECK 1] Existência de Tabelas:")
        for t in EXPECTED_TABLES:
            if t in existing_tables:
                print(f"  [OK]   Tabela '{t}' encontrada")
            else:
                print(f"  [FAIL] Tabela obrigatória ausente: '{t}'")
                all_passed = False

        # 3. Verificar Status de Row Level Security (RLS)
        cur.execute("""
            SELECT relname, relrowsecurity
            FROM pg_class
            JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
            WHERE pg_namespace.nspname = 'public' AND relkind = 'r';
        """)
        rls_status = {row[0]: row[1] for row in cur.fetchall()}

        print("\n[CHECK 2] Row Level Security (RLS):")
        for t in RLS_PROTECTED_TABLES:
            if t in rls_status:
                is_enabled = rls_status[t]
                if is_enabled:
                    print(f"  [OK]   RLS ativo na tabela '{t}'")
                else:
                    print(f"  [WARN] RLS desativado na tabela '{t}'")
            else:
                print(f"  [SKIP] Tabela '{t}' não existe no banco")

        # 4. Verificar Índices Críticos
        cur.execute("""
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public';
        """)
        indexes = {row[0] for row in cur.fetchall()}

        critical_indexes = [
            "idx_price_history_listing_observed",
            "idx_price_history_listing_price",
            "idx_listings_radar",
            "idx_monitored_user_active",
            "idx_alert_rules_monitored"
        ]

        print("\n[CHECK 3] Índices de Alta Performance:")
        for idx in critical_indexes:
            if idx in indexes:
                print(f"  [OK]   Índice '{idx}' presente")
            else:
                print(f"  [WARN] Índice recomendado ausente: '{idx}'")

        # 5. Contagem de Registros
        print("\n[CHECK 4] Registros Iniciais / Sementes:")
        for t in ["search_sites", "connector_configs", "stores", "products", "commercial_listings"]:
            if t in existing_tables:
                cur.execute(f"SELECT count(*) FROM {t};")
                count = cur.fetchone()[0]
                print(f"  [DATA] {t}: {count} linhas")

    conn.close()
    print("=" * 70)
    if all_passed:
        print("[SUCESSO] Todas as validações obrigatórias foram aprovadas!")
    else:
        print("[AVISO] Algumas verificações apresentaram inconsistências.")
    print("=" * 70)
    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Validador de Esquema e Integridade")
    parser.add_argument("--db-url", type=str, help="URL de conexão PostgreSQL")
    args = parser.parse_args()

    db_url = args.db_url or os.getenv("DATABASE_URL")
    if not db_url:
        print("[ERROR] DATABASE_URL não definida em .env ou parâmetro --db-url")
        sys.exit(1)

    if db_url.startswith("postgresql+psycopg://"):
        db_url = db_url.replace("postgresql+psycopg://", "postgresql://", 1)

    ok = validate_schema(db_url)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
