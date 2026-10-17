"""Database Engine and Session Factory"""

import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


def get_engine_args():
    connect_args = {}
    engine_kwargs = {
        "echo": settings.DEBUG,
        "future": True,
    }

    url = settings.DATABASE_URL

    # Se for PostgreSQL via psycopg
    if "postgresql" in url:
        # Quando usando Supabase Pooler em modo transaction (porta 6543)
        if settings.DB_POOL_MODE == "transaction" or ":6543" in url:
            connect_args["prepare_threshold"] = None
            logger.info("Configurando SQLAlchemy com prepare_threshold=None para Transaction Pooler")

        engine_kwargs["connect_args"] = connect_args
        engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
        engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
        engine_kwargs["pool_timeout"] = settings.DB_POOL_TIMEOUT
        engine_kwargs["pool_pre_ping"] = True

    elif "sqlite" in url:
        connect_args["check_same_thread"] = False
        engine_kwargs["connect_args"] = connect_args

    return engine_kwargs


# Inicialização segura da engine
engine = create_engine(settings.DATABASE_URL, **get_engine_args())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency injection helper para endpoints FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
