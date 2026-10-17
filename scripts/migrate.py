#!/usr/bin/env python3
"""
Price Hunter - Database Migration Tool
Supports PostgreSQL standalone, Docker, and Supabase (Direct or Pooler).
"""

import os
import sys
import argparse
import hashlib
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import psycopg
    from psycopg import sql
except ImportError:
    print("[ERROR] psycopg not found. Please install: pip install \"psycopg[binary]\"")
    sys.exit(1)


def get_connection_url(args_url: str | None = None) -> str:
    url = args_url or os.getenv("DATABASE_URL")
    if not url:
        print("[ERROR] No database URL provided. Set DATABASE_URL in .env or pass --db-url")
        sys.exit(1)
    # Convert sqlalchemy async format to psycopg standard if needed
    if url.startswith("postgresql+psycopg://"):
        url = url.replace("postgresql+psycopg://", "postgresql://", 1)
    elif url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return url


def calculate_checksum(file_path: Path) -> str:
    content = file_path.read_bytes()
    return hashlib.sha256(content).hexdigest()[:16]


def init_migrations_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(100) PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                checksum VARCHAR(64)
            );
        """)
    conn.commit()


def get_applied_migrations(conn) -> dict[str, str]:
    init_migrations_table(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT version, checksum FROM schema_migrations ORDER BY version;")
        rows = cur.fetchall()
        return {row[0]: row[1] for row in rows}


def get_available_migrations(migrations_dir: Path) -> list[Path]:
    if not migrations_dir.exists():
        print(f"[ERROR] Migrations directory does not exist: {migrations_dir}")
        sys.exit(1)
    sql_files = sorted([f for f in migrations_dir.glob("*.sql") if not f.name.endswith(".seed.sql")])
    return sql_files


def run_status(conn, migrations_dir: Path):
    applied = get_applied_migrations(conn)
    available = get_available_migrations(migrations_dir)

    print("\n" + "=" * 70)
    print(" PRICE HUNTER - STATUS DAS MIGRAÇÕES")
    print("=" * 70)
    print(f"{'Versão':<45} | {'Status':<12} | {'Checksum'}")
    print("-" * 70)

    for m in available:
        v = m.stem
        c = calculate_checksum(m)
        if v in applied:
            status = "APLICADA"
            check_match = "[OK]" if applied[v] == c else "[MODIFICADA]"
            print(f"{v:<45} | {status:<12} | {c} {check_match}")
        else:
            print(f"{v:<45} | {'PENDENTE':<12} | {c}")
    print("=" * 70 + "\n")


def run_migrate(conn, migrations_dir: Path, target_version: str | None = None):
    applied = get_applied_migrations(conn)
    available = get_available_migrations(migrations_dir)

    pending = [m for m in available if m.stem not in applied]
    if not pending:
        print("[INFO] Nenhuma migração pendente. O banco de dados está atualizado!")
        return

    print(f"[INFO] Encontradas {len(pending)} migrações pendentes para aplicar.")

    for m in pending:
        v = m.stem
        c = calculate_checksum(m)
        print(f" -> Aplicando migração: {v} ...", end=" ", flush=True)

        sql_content = m.read_text(encoding="utf-8")
        try:
            with conn.cursor() as cur:
                cur.execute(sql_content)
                cur.execute(
                    "INSERT INTO schema_migrations (version, checksum) VALUES (%s, %s);",
                    (v, c)
                )
            conn.commit()
            print("[SUCESSO]")
        except Exception as e:
            conn.rollback()
            print(f"\n[FALHA] Erro ao aplicar {v}: {e}")
            sys.exit(1)

        if target_version and v == target_version:
            print(f"[INFO] Versão alvo alcançada: {target_version}")
            break

    print("[INFO] Todas as migrações foram aplicadas com êxito!")


def run_seed(conn, seed_file: Path):
    if not seed_file.exists():
        print(f"[WARN] Arquivo de seed não encontrado: {seed_file}")
        return
    print(f"[INFO] Executando seed a partir de {seed_file} ...", end=" ", flush=True)
    sql_content = seed_file.read_text(encoding="utf-8")
    try:
        with conn.cursor() as cur:
            cur.execute(sql_content)
        conn.commit()
        print("[SUCESSO]")
    except Exception as e:
        conn.rollback()
        print(f"\n[FALHA] Erro ao executar seed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Price Hunter Migrator (PostgreSQL / Supabase)")
    parser.add_argument("--db-url", type=str, help="URL de conexão com o banco de dados")
    parser.add_argument("--dir", type=str, default="database/migrations", help="Diretório das migrações SQL")
    parser.add_argument("--status", action="store_true", help="Exibe status das migrações")
    parser.add_argument("--up", action="store_true", help="Executa as migrações pendentes")
    parser.add_argument("--seed", action="store_true", help="Executa o script de dados iniciais/demonstração")
    parser.add_argument("--seed-file", type=str, default="supabase/seed.sql", help="Caminho do arquivo seed")
    parser.add_argument("--target", type=str, help="Migrar até uma versão específica")

    args = parser.parse_args()
    db_url = get_connection_url(args.db_url)
    migrations_dir = Path(args.dir)

    # Conectar ao banco com suporte a poolers e transações seguras
    try:
        # prepare_threshold=None is required for Supabase transaction pooler (PgBouncer/Supavisor)
        conn = psycopg.connect(db_url, autocommit=False, prepare_threshold=None)
    except Exception as e:
        print(f"[ERROR] Não foi possível conectar ao PostgreSQL/Supabase: {e}")
        sys.exit(1)

    try:
        if args.status:
            run_status(conn, migrations_dir)
        elif args.up:
            run_migrate(conn, migrations_dir, args.target)
            if args.seed:
                run_seed(conn, Path(args.seed_file))
        elif args.seed:
            run_seed(conn, Path(args.seed_file))
        else:
            # Default action: run_status
            run_status(conn, migrations_dir)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
