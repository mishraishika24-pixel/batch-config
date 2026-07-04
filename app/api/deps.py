"""FastAPI dependency wiring.

Routes stay thin by depending on these factories rather than constructing
services/repositories themselves; tests override `get_db` (and can swap
`get_settings`) to run the same routes against a SQLite session.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database.session import get_db
from app.repositories.batch_repository import BatchRepository
from app.services.batch_service import BatchService


def get_batch_repository(db: Session = Depends(get_db)) -> BatchRepository:
    return BatchRepository(db)


def get_batch_service(
    repository: BatchRepository = Depends(get_batch_repository),
    settings: Settings = Depends(get_settings),
) -> BatchService:
    return BatchService(repository, settings)
