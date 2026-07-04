"""Batch submission and query endpoints.

Routes are intentionally thin: validate input shape (via Pydantic),
delegate to BatchService, return its result. All business logic
(size limits, status computation, 404 semantics) lives in the service.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_batch_service
from app.core.config import Settings, get_settings
from app.models.batch import ItemStatus
from app.schemas.batch import (
    BatchStatusResponse,
    BatchSubmitRequest,
    BatchSubmitResponse,
    PaginatedBatchItems,
)
from app.services.batch_service import BatchService

router = APIRouter(prefix="/api/v1/batches", tags=["batches"])


@router.post("", response_model=BatchSubmitResponse, status_code=status.HTTP_202_ACCEPTED)
def submit_batch(
    payload: BatchSubmitRequest,
    service: BatchService = Depends(get_batch_service),
) -> BatchSubmitResponse:
    """Accept a batch of items for asynchronous processing.

    Returns immediately (202) with the batch id and PENDING status; actual
    processing happens out-of-band in the worker process. Poll
    GET /api/v1/batches/{id} to track progress.
    """
    return service.submit_batch(payload.items)


@router.get("/{batch_id}", response_model=BatchStatusResponse)
def get_batch_status(
    batch_id: UUID,
    service: BatchService = Depends(get_batch_service),
) -> BatchStatusResponse:
    return service.get_batch_status(batch_id)


@router.get("/{batch_id}/items", response_model=PaginatedBatchItems)
def get_batch_items(
    batch_id: UUID,
    item_status: ItemStatus | None = Query(default=None, alias="status"),
    limit: int | None = Query(default=None, ge=1),
    offset: int = Query(default=0, ge=0),
    service: BatchService = Depends(get_batch_service),
    settings: Settings = Depends(get_settings),
) -> PaginatedBatchItems:
    effective_limit = min(limit or settings.default_page_size, settings.max_page_size)
    return service.get_batch_items(batch_id, item_status, effective_limit, offset)
