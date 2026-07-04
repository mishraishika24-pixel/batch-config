"""Liveness and readiness endpoints.

Kept deliberately separate:
  - /health (liveness): the process can serve requests at all. Must never
    depend on external systems, or a DB blip would cause the orchestrator
    to kill and restart healthy processes.
  - /ready (readiness): the process can serve *real* traffic right now.
    Checks the database connection; a load balancer / orchestrator should
    stop routing traffic here (without restarting the process) if this fails.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import get_db

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("readiness_check_failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unavailable",
        ) from None
    return {"status": "ready"}
