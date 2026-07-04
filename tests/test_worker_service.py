"""Unit tests for WorkerService: the claim -> process -> finalize cycle.

Uses fake ItemProcessor implementations to deterministically exercise
success, expected failure, and unexpected-bug scenarios without touching
a real external system.
"""

import pytest

from app.models.batch import BatchStatus, ItemStatus
from app.repositories.batch_repository import BatchRepository
from app.services.batch_service import BatchService
from app.services.item_processor import ItemProcessingError, ItemProcessor, SimulatedItemProcessor
from app.services.worker_service import WorkerService


class AlwaysFailProcessor(ItemProcessor):
    """Simulates a well-behaved but permanently-failing downstream call."""

    def process(self, payload):
        raise ItemProcessingError("always fails")


class BuggyProcessor(ItemProcessor):
    """Simulates a bug in processing code (not a domain ItemProcessingError)."""

    def process(self, payload):
        raise RuntimeError("boom, unexpected bug")


@pytest.fixture()
def repository(db_session) -> BatchRepository:
    return BatchRepository(db_session)


@pytest.fixture()
def service(repository, test_settings) -> BatchService:
    return BatchService(repository, test_settings)


class TestProcessOnce:
    def test_returns_zero_when_the_queue_is_empty(self, repository, test_settings):
        worker = WorkerService(repository, SimulatedItemProcessor(), test_settings)

        assert worker.process_once() == 0

    def test_happy_path_marks_item_and_batch_completed(self, service, repository, test_settings):
        submitted = service.submit_batch([{"value": "a"}])
        worker = WorkerService(repository, SimulatedItemProcessor(), test_settings)

        claimed = worker.process_once()

        assert claimed == 1
        status = service.get_batch_status(submitted.id)
        assert status.status == BatchStatus.COMPLETED
        assert status.counts.completed == 1

    def test_partial_failure_finalizes_batch_as_completed_with_errors(
        self, service, repository, test_settings
    ):
        submitted = service.submit_batch(
            [{"value": "a"}, {"simulate_failure": True, "failure_reason": "boom"}]
        )
        worker = WorkerService(repository, SimulatedItemProcessor(), test_settings)

        # test_settings.worker_max_item_attempts == 2: two poll cycles are
        # enough for the failing item to exhaust its retries.
        worker.process_once()
        worker.process_once()

        status = service.get_batch_status(submitted.id)
        assert status.status == BatchStatus.COMPLETED_WITH_ERRORS
        assert status.counts.completed == 1
        assert status.counts.failed == 1

    def test_all_items_failing_finalizes_batch_as_failed(self, service, repository, test_settings):
        submitted = service.submit_batch([{"any": "thing"}])
        worker = WorkerService(repository, AlwaysFailProcessor(), test_settings)

        for _ in range(test_settings.worker_max_item_attempts):
            worker.process_once()

        status = service.get_batch_status(submitted.id)
        assert status.status == BatchStatus.FAILED

    def test_failing_item_is_requeued_before_exhausting_max_attempts(
        self, service, repository, test_settings
    ):
        submitted = service.submit_batch([{"any": "thing"}])
        worker = WorkerService(repository, AlwaysFailProcessor(), test_settings)

        worker.process_once()

        page = service.get_batch_items(submitted.id, status=None, limit=10, offset=0)
        item = page.items[0]
        # max_item_attempts == 2, so after 1 failed attempt it must be
        # requeued (PENDING), not yet terminally FAILED.
        assert item.status == ItemStatus.PENDING
        assert item.attempts == 1

    def test_item_is_terminally_failed_after_exhausting_max_attempts(
        self, service, repository, test_settings
    ):
        submitted = service.submit_batch([{"any": "thing"}])
        worker = WorkerService(repository, AlwaysFailProcessor(), test_settings)

        for _ in range(test_settings.worker_max_item_attempts):
            worker.process_once()

        page = service.get_batch_items(submitted.id, status=None, limit=10, offset=0)
        item = page.items[0]
        assert item.status == ItemStatus.FAILED
        assert item.error_message == "always fails"
        assert item.attempts == test_settings.worker_max_item_attempts

    def test_unexpected_processor_exception_is_isolated_and_does_not_propagate(
        self, service, repository, test_settings
    ):
        # A bug in the processor must not crash the poll loop or take down
        # the rest of the batch -- it's handled the same as any other
        # per-item failure (subject to the same retry/finalize rules).
        submitted = service.submit_batch([{"any": "thing"}])
        worker = WorkerService(repository, BuggyProcessor(), test_settings)

        claimed = worker.process_once()

        assert claimed == 1
        page = service.get_batch_items(submitted.id, status=None, limit=10, offset=0)
        assert page.items[0].status in (ItemStatus.PENDING, ItemStatus.FAILED)

    def test_process_once_only_claims_up_to_the_configured_batch_size(
        self, service, repository, test_settings
    ):
        service.submit_batch([{"value": i} for i in range(test_settings.max_batch_size)])
        worker = WorkerService(repository, SimulatedItemProcessor(), test_settings)
        # Force a small claim size to verify the limit is actually respected.
        test_settings.worker_claim_batch_size = 2

        claimed = worker.process_once()

        assert claimed == 2
