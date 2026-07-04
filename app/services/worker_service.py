"""Worker-side orchestration: claim items, process them, finalize batches.

Deliberately separated from the polling loop in ``app.worker`` so this
class -- the part with actual logic -- is directly unit-testable without
threads, signals, or real time delays.
"""

import logging

from app.core.config import Settings
from app.models.batch import BatchItem, ItemStatus
from app.repositories.batch_repository import BatchRepository
from app.services.item_processor import ItemProcessingError, ItemProcessor

logger = logging.getLogger(__name__)


class WorkerService:
    def __init__(self, repository: BatchRepository, processor: ItemProcessor, settings: Settings):
        self.repository = repository
        self.processor = processor
        self.settings = settings

    def process_once(self) -> int:
        """Claim a small batch of PENDING items and process each one.

        Returns the number of items claimed. Zero means the queue was
        empty; the caller (the poll loop) should back off before retrying.
        """
        items = self.repository.claim_pending_items(self.settings.worker_claim_batch_size)
        if not items:
            return 0

        batch_ids = {item.batch_id for item in items}
        for batch_id in batch_ids:
            self.repository.mark_batch_processing_if_pending(batch_id)

        for item in items:
            self._process_item(item)

        for batch_id in batch_ids:
            self.repository.finalize_batch_if_complete(batch_id)

        return len(items)

    def _process_item(self, item: BatchItem) -> None:
        try:
            result = self.processor.process(item.payload)
        except Exception as exc:
            self._handle_item_failure(item, exc)
        else:
            self.repository.save_item_result(item, ItemStatus.COMPLETED, result=result)

    def _handle_item_failure(self, item: BatchItem, exc: Exception) -> None:
        is_expected = isinstance(exc, ItemProcessingError)
        message = str(exc) if is_expected else "Unexpected processing error."

        log = logger.warning if is_expected else logger.exception
        log(
            "item_processing_failed",
            extra={
                "item_id": item.id,
                "batch_id": str(item.batch_id),
                "attempts": item.attempts,
                "expected": is_expected,
            },
        )

        # A single bad item must never abort the rest of the batch. Retry a
        # bounded number of times (attempts is incremented at claim time)
        # before giving up and marking it terminally FAILED.
        if item.attempts < self.settings.worker_max_item_attempts:
            self.repository.requeue_item(item)
        else:
            self.repository.save_item_result(item, ItemStatus.FAILED, error_message=message)
