"""Request/response schemas (the API's public contract).

Kept separate from ORM models so the wire format can evolve independently
of the storage schema.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.batch import BatchStatus, ItemStatus


class BatchSubmitRequest(BaseModel):
    items: list[dict[str, Any]] = Field(
        min_length=1,
        max_length=10_000,  # generous static ceiling; the authoritative,
        # configurable limit (settings.max_batch_size) is enforced in
        # BatchService so it can be tuned per environment without a schema change.
        description="List of item payloads to process. Each item is an arbitrary JSON object.",
    )


class BatchSubmitResponse(BaseModel):
    id: UUID
    status: BatchStatus
    total_items: int


class BatchStatusCounts(BaseModel):
    pending: int
    processing: int
    completed: int
    failed: int


class BatchStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: BatchStatus
    total_items: int
    counts: BatchStatusCounts
    created_at: datetime
    updated_at: datetime


class BatchItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: ItemStatus
    payload: dict[str, Any]
    result: dict[str, Any] | None
    error_message: str | None
    attempts: int
    created_at: datetime
    updated_at: datetime


class PaginatedBatchItems(BaseModel):
    items: list[BatchItemResponse]
    total: int
    limit: int
    offset: int
