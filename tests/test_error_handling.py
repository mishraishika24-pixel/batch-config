"""Tests for failure paths that are easy to skip: a down dependency, and a
genuinely unexpected exception. Both matter for an operational-readiness
story as much as the happy path does.
"""

import uuid

from app.api.deps import get_batch_service
from app.database.session import get_db
from app.main import app


class _BrokenSession:
    """Stands in for a DB session whose connection has failed."""

    def execute(self, *args, **kwargs):
        raise RuntimeError("connection refused")

    def close(self):
        pass


def test_ready_returns_503_when_database_is_unreachable(api_client):
    def broken_get_db():
        yield _BrokenSession()

    app.dependency_overrides[get_db] = broken_get_db

    response = api_client.get("/ready")

    assert response.status_code == 503


class _CrashingBatchService:
    """Simulates a genuine bug (not a modeled AppError) surfacing in a route."""

    def get_batch_status(self, batch_id):
        raise RuntimeError("boom: something we did not anticipate")


def test_unexpected_exception_returns_generic_500_without_leaking_details(api_client):
    app.dependency_overrides[get_batch_service] = lambda: _CrashingBatchService()

    response = api_client.get(f"/api/v1/batches/{uuid.uuid4()}")

    assert response.status_code == 500
    body = response.json()
    assert body["error"]["code"] == "internal_error"
    # The real exception message must never reach the client.
    assert "boom" not in body["error"]["message"]
