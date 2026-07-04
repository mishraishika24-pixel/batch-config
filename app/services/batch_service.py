"""Batch submission and query business logic.

Framework-agnostic: depends only on the repository and settings (both
injected), so it is unit-testable without FastAPI or a real Postgres
instance -- see tests/test_batch_service.py.
"""

from uuid import UUID

from app.core.config import Settings
from app.core.exceptions import BatchNotFoundError, BatchTooLargeError
from app.models.batch import ItemStatus
from app.repositories.batch_repository import BatchRepository
from app.schemas.batch import (
    BatchItemResponse,
    BatchStatusCounts,
    BatchStatusResponse,
    BatchSubmitResponse,
    PaginatedBatchItems,
)


class BatchService:
    def __init__(self, repository: BatchRepository, settings: Settings):
        self.repository = repository
        self.settings = settings

    def submit_batch(self, items: list[dict]) -> BatchSubmitResponse:
        if len(items) > self.settings.max_batch_size:
            raise BatchTooLargeError(
                f"Batch has {len(items)} items; the maximum allowed is "
                f"{self.settings.max_batch_size}."
            )

        batch = self.repository.create_batch(items)
        return BatchSubmitResponse(id=batch.id, status=batch.status, total_items=batch.total_items)

    def get_batch_status(self, batch_id: UUID) -> BatchStatusResponse:
        batch = self.repository.get_batch(batch_id)
        if batch is None:
            raise BatchNotFoundError(f"Batch {batch_id} was not found.")

        counts = self.repository.get_item_counts(batch_id)
        return BatchStatusResponse(
            id=batch.id,
            status=batch.status,
            total_items=batch.total_items,
            counts=BatchStatusCounts(
                pending=counts[ItemStatus.PENDING],
                processing=counts[ItemStatus.PROCESSING],
                completed=counts[ItemStatus.COMPLETED],
                failed=counts[ItemStatus.FAILED],
            ),
            created_at=batch.created_at,
            updated_at=batch.updated_at,
        )

    def get_batch_items(
        self,
        batch_id: UUID,
        status: ItemStatus | None,
        limit: int,
        offset: int,
    ) -> PaginatedBatchItems:
        batch = self.repository.get_batch(batch_id)
        if batch is None:
            raise BatchNotFoundError(f"Batch {batch_id} was not found.")

        items, total = self.repository.list_items(batch_id, status, limit, offset)
        return PaginatedBatchItems(
            items=[BatchItemResponse.model_validate(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )
