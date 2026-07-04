"""Unit tests for BatchService: business rules only, no HTTP involved.

BatchService is framework-agnostic by design, so these tests exercise it
directly against a SQLite-backed repository.
"""

import uuid

import pytest

from app.core.exceptions import BatchNotFoundError, BatchTooLargeError
from app.models.batch import BatchStatus, ItemStatus
from app.repositories.batch_repository import BatchRepository
from app.services.batch_service import BatchService


@pytest.fixture()
def service(db_session, test_settings) -> BatchService:
    return BatchService(BatchRepository(db_session), test_settings)


class TestSubmitBatch:
    def test_creates_a_pending_batch_with_the_correct_item_count(self, service):
        response = service.submit_batch([{"value": "a"}, {"value": "b"}])

        assert response.status == BatchStatus.PENDING
        assert response.total_items == 2
        assert response.id is not None

    def test_rejects_batches_over_the_configured_max_size(self, service, test_settings):
        # test_settings.max_batch_size == 5; this is the authoritative,
        # environment-configurable limit (as opposed to the schema's
        # generous static ceiling), so it must be enforced here.
        items = [{"value": i} for i in range(test_settings.max_batch_size + 1)]

        with pytest.raises(BatchTooLargeError):
            service.submit_batch(items)

    def test_accepts_a_batch_exactly_at_the_max_size(self, service, test_settings):
        items = [{"value": i} for i in range(test_settings.max_batch_size)]

        response = service.submit_batch(items)

        assert response.total_items == test_settings.max_batch_size


class TestGetBatchStatus:
    def test_returns_zeroed_counts_for_a_freshly_submitted_batch(self, service):
        submitted = service.submit_batch([{"value": "a"}, {"value": "b"}, {"value": "c"}])

        status = service.get_batch_status(submitted.id)

        assert status.status == BatchStatus.PENDING
        assert status.total_items == 3
        assert status.counts.pending == 3
        assert status.counts.completed == 0
        assert status.counts.failed == 0

    def test_raises_not_found_for_an_unknown_batch_id(self, service):
        with pytest.raises(BatchNotFoundError):
            service.get_batch_status(uuid.uuid4())


class TestGetBatchItems:
    def test_raises_not_found_for_an_unknown_batch_id(self, service):
        with pytest.raises(BatchNotFoundError):
            service.get_batch_items(uuid.uuid4(), status=None, limit=10, offset=0)

    def test_filters_by_status(self, service, db_session):
        submitted = service.submit_batch([{"value": i} for i in range(3)])
        repo = BatchRepository(db_session)
        items, _ = repo.list_items(submitted.id, status=None, limit=3, offset=0)
        repo.save_item_result(items[0], ItemStatus.COMPLETED, result={"ok": True})

        completed_page = service.get_batch_items(
            submitted.id, status=ItemStatus.COMPLETED, limit=10, offset=0
        )
        pending_page = service.get_batch_items(
            submitted.id, status=ItemStatus.PENDING, limit=10, offset=0
        )

        assert completed_page.total == 1
        assert pending_page.total == 2

    def test_paginates_results(self, service):
        submitted = service.submit_batch([{"value": i} for i in range(5)])

        first_page = service.get_batch_items(submitted.id, status=None, limit=2, offset=0)
        second_page = service.get_batch_items(submitted.id, status=None, limit=2, offset=2)

        assert first_page.total == 5
        assert len(first_page.items) == 2
        assert len(second_page.items) == 2
        assert {item.id for item in first_page.items}.isdisjoint(
            {item.id for item in second_page.items}
        )
