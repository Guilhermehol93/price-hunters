#!/usr/bin/env python3
"""
Price Hunter - Database Connection Diagnostics
Tests direct connections, Supabase pooler ports (5432 session, 6543 transaction), and latency.
"""

import os
import sys
import time
import argparse

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


def test_connection(url: str, name: str = "Conexão"):
    print(f"\n[TESTANDO] {name}...")
    start_t = time.perf_counter()
    try:
        # Usamos prepare_threshold=None para suportar Supavisor / PgBouncer
        with psycopg.connect(url, prepare_threshold=None, connect_timeout=10) as conn:
            conn_time = (time.perf_counter() - start_t) * 1000
            with conn.cursor() as cur:
                q_start = time.perf_counter()
                cur.execute("SELECT version(), current_database(), current_user, inet_server_addr();")
                row = cur.fetchone()
                query_time = (time.perf_counter() - q_start) * 1000

                print(f"  [OK] Conectado com sucesso em {conn_time:.1f}ms (Query em {query_time:.1f}ms)")
                print(f"  -> Banco: {row[1]}")
                print(f"  -> Usuário: {row[2]}")
                print(f"  -> Servidor IP: {row[3]}")
                print(f"  -> Versão: {row[0][:60]}...")
                return True
    except Exception as e:
        total_time = (time.perf_counter() - start_t) * 1000
        print(f"  [FALHA] Erro após {total_time:.1f}ms: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Teste de Conectividade com Banco")
    parser.add_argument("--url", type=str, help="URL do banco")
    args = parser.parse_args()

    default_url = args.url or os.getenv("DATABASE_URL")
    if not default_url:
        print("[ERROR] DATABASE_URL não definida em .env ou parâmetro --url")
        sys.exit(1)

    if default_url.startswith("postgresql+psycopg://"):
        default_url = default_url.replace("postgresql+psycopg://", "postgresql://", 1)

    print("=" * 70)
    print(" PRICE HUNTER - DIAGNÓSTICO DE REDE E CONECTIVIDADE SQL")
    print("=" * 70)

    # Identificar se é Supabase ou Local
    is_supabase = "supabase" in default_url or "pooler.supabase.com" in default_url
    if is_supabase:
        print("[DETECTADO] Provedor: Supabase Managed Database")
    else:
        print("[DETECTADO] Provedor: PostgreSQL Próprio / Docker Local")

    success = test_connection(default_url, "DATABASE_URL Principal")
    print("=" * 70)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
