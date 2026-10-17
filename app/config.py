"""Application Configuration Settings"""

import os
from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Ambiente de Execução
    ENVIRONMENT: Literal["development", "production", "testing"] = "development"
    APP_NAME: str = "Price Hunter"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Banco de Dados
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/pricehunter",
        description="URL de conexão PostgreSQL (local ou Supabase)"
    )
    DB_POOL_MODE: Literal["direct", "transaction", "session"] = "direct"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 5
    DB_POOL_TIMEOUT: int = 30

    # Supabase (Opcional, quando gerenciado)
    SUPABASE_URL: str | None = None
    SUPABASE_ANON_KEY: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None
    SUPABASE_JWT_SECRET: str | None = None
    USE_SUPABASE_AUTH: bool = False

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_DEFAULT_CHAT_ID: str | None = None
    TELEGRAM_ALERT_COOLDOWN_HOURS: int = 24
    TELEGRAM_ENABLED: bool = True

    # Redis (Filas e Cache)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = True

    # Segurança & Scraping
    ALLOW_PRIVATE_IPS: bool = False  # SSRF Guard
    REQUEST_TIMEOUT_SECONDS: int = 15
    MAX_CONCURRENT_SCRAPES: int = 5
    DEFAULT_USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    # Parâmetros de Inteligência de Preço
    OPPORTUNITY_SCORE_MIN_THRESHOLD: int = 70
    DEFAULT_DISCOUNT_THRESHOLD_PCT: float = 15.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
