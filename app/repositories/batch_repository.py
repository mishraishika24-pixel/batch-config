"""Data-access layer for batches and batch items.

Isolated from business logic so SQL details -- notably the
`FOR UPDATE SKIP LOCKED` claim query that lets multiple worker processes
poll the same table safely -- live in one place and can be exercised
directly in tests without going through the service or API layers.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.batch import Batch, BatchItem, BatchStatus, ItemStatus


class BatchRepository:
    def __init__(self, session: Session):
        self.session = session

    # --- writes: submission ---

    def create_batch(self, items: list[dict]) -> Batch:
        batch = Batch(status=BatchStatus.PENDING, total_items=len(items))
        batch.items = [BatchItem(payload=item, status=ItemStatus.PENDING) for item in items]
        self.session.add(batch)
        self.session.commit()
        self.session.refresh(batch)
        return batch

    # --- reads: status/listing ---

    def get_batch(self, batch_id: UUID) -> Batch | None:
        return self.session.get(Batch, batch_id)

    def get_item_counts(self, batch_id: UUID) -> dict[ItemStatus, int]:
        rows = self.session.execute(
            select(BatchItem.status, func.count(BatchItem.id))
            .where(BatchItem.batch_id == batch_id)
            .group_by(BatchItem.status)
        ).all()
        counts = {status: 0 for status in ItemStatus}
        for status, count in rows:
            counts[status] = count
        return counts

    def list_items(
        self,
        batch_id: UUID,
        status: ItemStatus | None,
        limit: int,
        offset: int,
    ) -> tuple[list[BatchItem], int]:
        query = select(BatchItem).where(BatchItem.batch_id == batch_id)
        count_query = select(func.count(BatchItem.id)).where(BatchItem.batch_id == batch_id)
        if status is not None:
            query = query.where(BatchItem.status == status)
            count_query = count_query.where(BatchItem.status == status)

        total = self.session.execute(count_query).scalar_one()
        items = (
            self.session.execute(query.order_by(BatchItem.id).limit(limit).offset(offset))
            .scalars()
            .all()
        )
        return list(items), total

    # --- worker-facing: claim, update, finalize ---

    def claim_pending_items(self, limit: int) -> list[BatchItem]:
        """Atomically claim up to `limit` PENDING items across all batches.

        `SKIP LOCKED` means concurrent worker processes each get a disjoint
        set of rows instead of blocking on one another, without needing an
        external broker. Marking them PROCESSING (and committing) here, in
        the same transaction that took the row lock, is what makes the
        claim durable even if this worker crashes immediately after.
        """
        items = (
            self.session.execute(
                select(BatchItem)
                .where(BatchItem.status == ItemStatus.PENDING)
                .order_by(BatchItem.id)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
            .scalars()
            .all()
        )
        for item in items:
            item.status = ItemStatus.PROCESSING
            item.attempts += 1
        self.session.commit()
        return list(items)

    def mark_batch_processing_if_pending(self, batch_id: UUID) -> None:
        batch = self.get_batch(batch_id)
        if batch is not None and batch.status == BatchStatus.PENDING:
            batch.status = BatchStatus.PROCESSING
            self.session.commit()

    def save_item_result(
        self,
        item: BatchItem,
        status: ItemStatus,
        result: dict | None = None,
        error_message: str | None = None,
    ) -> None:
        item.status = status
        item.result = result
        item.error_message = error_message
        self.session.commit()

    def requeue_item(self, item: BatchItem) -> None:
        """Send a failed item back to PENDING so a future poll retries it.

        `attempts` is left untouched here -- it was already incremented at
        claim time -- so the worker can compare it against
        `worker_max_item_attempts` to decide when to stop retrying.
        """
        item.status = ItemStatus.PENDING
        item.error_message = None
        self.session.commit()

    def finalize_batch_if_complete(self, batch_id: UUID) -> Batch | None:
        """Recompute the batch's terminal status once no items are left
        PENDING or PROCESSING. Returns the batch if this call finalized it,
        otherwise None (already finalized, or still in flight).
        """
        counts = self.get_item_counts(batch_id)
        outstanding = counts[ItemStatus.PENDING] + counts[ItemStatus.PROCESSING]
        if outstanding > 0:
            return None

        batch = self.get_batch(batch_id)
        terminal_statuses = (
            BatchStatus.COMPLETED,
            BatchStatus.COMPLETED_WITH_ERRORS,
            BatchStatus.FAILED,
        )
        if batch is None or batch.status in terminal_statuses:
            return None

        if counts[ItemStatus.FAILED] == 0:
            batch.status = BatchStatus.COMPLETED
        elif counts[ItemStatus.COMPLETED] == 0:
            batch.status = BatchStatus.FAILED
        else:
            batch.status = BatchStatus.COMPLETED_WITH_ERRORS

        self.session.commit()
        return batch
