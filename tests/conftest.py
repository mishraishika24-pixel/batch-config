"""Shared pytest fixtures.

Tests run against an in-memory SQLite database (via StaticPool, so all
connections in a test share the same schema and data) instead of a real
Postgres instance. This keeps the suite fast and hermetic -- no Docker or
network dependency required to run `pytest`.

Note: SQLite has no real row-level locking, so `SELECT ... FOR UPDATE
SKIP LOCKED` is accepted but is effectively a no-op there. These tests
verify the *functional* contract of BatchRepository.claim_pending_items
(claimed items aren't returned twice); the actual cross-process
concurrency guarantee was verified manually against a real Postgres
container during development (see README's "Testing" section).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.database.session import get_db
from app.main import app
from app.models import Base


@pytest.fixture()
def test_settings() -> Settings:
    return Settings(
        database_url="sqlite+pysqlite:///:memory:",
        max_batch_size=5,
        default_page_size=10,
        max_page_size=20,
        worker_claim_batch_size=10,
        worker_max_item_attempts=2,
        worker_poll_interval_seconds=0.01,
    )


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def db_session(db_engine) -> Session:
    session_factory = sessionmaker(bind=db_engine, future=True)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def api_client(db_engine, test_settings) -> TestClient:
    session_factory = sessionmaker(bind=db_engine, future=True)

    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = lambda: test_settings
    try:
        # raise_server_exceptions=False mirrors production: an unhandled
        # exception should reach the client as our generic 500 JSON body,
        # not propagate and blow up the test process.
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
