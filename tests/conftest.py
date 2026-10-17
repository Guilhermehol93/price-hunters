"""Pytest Configuration and Test Fixtures"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

import app.models  # Importa todos os modelos para registrar no Base.metadata
from app.database import Base, get_db
from app.config import settings
from app.main import app

# Configura ambiente para teste
settings.ENVIRONMENT = "testing"
settings.ALLOW_PRIVATE_IPS = True

# Usar SQLite em memória com StaticPool para compartilhar a conexão entre sessões
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Cria tabelas no banco SQLite compartilhado para cada teste isolado."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Client de teste do FastAPI com override da sessão de banco."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
