"""Database engine/session setup.

A single engine is created per process (API or worker) with connection
pooling and pre-ping enabled so stale connections (e.g. after a DB restart)
are detected and replaced rather than surfacing as request failures.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped session.

    Always closed after the request, regardless of outcome, to return the
    connection to the pool.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
