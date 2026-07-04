"""Repository-level tests for the claim/finalize contract.

These exercise BatchRepository directly (no service, no HTTP) since the
claim/finalize behavior is the trickiest part of the system to get right.
"""

from app.models.batch import BatchStatus, ItemStatus
from app.repositories.batch_repository import BatchRepository


def test_claim_pending_items_marks_them_processing_and_increments_attempts(db_session):
    repo = BatchRepository(db_session)
    batch = repo.create_batch([{"value": "a"}, {"value": "b"}, {"value": "c"}])

    claimed = repo.claim_pending_items(limit=2)

    assert len(claimed) == 2
    assert all(item.status == ItemStatus.PROCESSING for item in claimed)
    assert all(item.attempts == 1 for item in claimed)

    _, pending_total = repo.list_items(batch.id, status=ItemStatus.PENDING, limit=10, offset=0)
    assert pending_total == 1


def test_claim_pending_items_does_not_reclaim_already_claimed_items(db_session):
    # SQLite has no real row-level locking, so this verifies the
    # *functional* contract (claimed items aren't handed out twice) rather
    # than true cross-process concurrency safety, which was verified
    # manually against a real Postgres container during development.
    repo = BatchRepository(db_session)
    repo.create_batch([{"value": "a"}, {"value": "b"}])

    first_claim = repo.claim_pending_items(limit=10)
    second_claim = repo.claim_pending_items(limit=10)

    assert len(first_claim) == 2
    assert second_claim == []


def test_claim_pending_items_returns_empty_list_when_queue_is_empty(db_session):
    repo = BatchRepository(db_session)

    assert repo.claim_pending_items(limit=10) == []


def test_finalize_batch_if_complete_is_a_noop_while_items_are_outstanding(db_session):
    repo = BatchRepository(db_session)
    batch = repo.create_batch([{"value": "a"}, {"value": "b"}])
    repo.claim_pending_items(limit=1)  # one item still PENDING

    result = repo.finalize_batch_if_complete(batch.id)

    assert result is None
    assert repo.get_batch(batch.id).status == BatchStatus.PENDING


def test_finalize_batch_if_complete_is_idempotent(db_session):
    repo = BatchRepository(db_session)
    batch = repo.create_batch([{"value": "a"}])
    items = repo.claim_pending_items(limit=10)
    repo.save_item_result(items[0], ItemStatus.COMPLETED, result={"ok": True})

    first_call = repo.finalize_batch_if_complete(batch.id)
    second_call = repo.finalize_batch_if_complete(batch.id)

    assert first_call is not None
    assert first_call.status == BatchStatus.COMPLETED
    assert second_call is None  # already terminal -- must not re-finalize


def test_requeue_item_resets_status_to_pending_and_clears_error(db_session):
    repo = BatchRepository(db_session)
    repo.create_batch([{"value": "a"}])
    item = repo.claim_pending_items(limit=10)[0]
    repo.save_item_result(item, ItemStatus.FAILED, error_message="transient error")

    repo.requeue_item(item)

    assert item.status == ItemStatus.PENDING
    assert item.error_message is None
