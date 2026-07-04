"""API-level tests: HTTP contract, validation, and error responses.

Uses the `api_client` fixture (FastAPI TestClient wired to an in-memory
SQLite DB via dependency overrides) so these exercise the full stack --
routing, validation, exception handlers, middleware -- without a real
Postgres instance.
"""

import uuid


def test_health_returns_ok(api_client):
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_ready_when_db_is_reachable(api_client):
    response = api_client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_response_includes_a_request_id_header(api_client):
    response = api_client.get("/health")

    assert "X-Request-ID" in response.headers


class TestSubmitBatch:
    def test_returns_202_with_pending_status(self, api_client):
        response = api_client.post(
            "/api/v1/batches", json={"items": [{"value": "a"}, {"value": "b"}]}
        )

        assert response.status_code == 202
        body = response.json()
        assert body["status"] == "PENDING"
        assert body["total_items"] == 2
        uuid.UUID(body["id"])  # raises if not a valid UUID

    def test_rejects_an_empty_items_list(self, api_client):
        response = api_client.post("/api/v1/batches", json={"items": []})

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "validation_error"

    def test_rejects_a_missing_items_field(self, api_client):
        response = api_client.post("/api/v1/batches", json={})

        assert response.status_code == 422

    def test_rejects_a_batch_over_the_configured_max_size(self, api_client, test_settings):
        items = [{"value": i} for i in range(test_settings.max_batch_size + 1)]

        response = api_client.post("/api/v1/batches", json={"items": items})

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "batch_too_large"


class TestGetBatchStatus:
    def test_returns_404_for_an_unknown_batch(self, api_client):
        response = api_client.get(f"/api/v1/batches/{uuid.uuid4()}")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "batch_not_found"

    def test_malformed_uuid_returns_422_not_500(self, api_client):
        response = api_client.get("/api/v1/batches/not-a-valid-uuid")

        assert response.status_code == 422


class TestBatchLifecycle:
    def test_submit_then_status_then_items_end_to_end(self, api_client):
        submit_response = api_client.post("/api/v1/batches", json={"items": [{"value": "a"}]})
        batch_id = submit_response.json()["id"]

        status_response = api_client.get(f"/api/v1/batches/{batch_id}")
        assert status_response.status_code == 200
        status_body = status_response.json()
        assert status_body["status"] == "PENDING"
        assert status_body["counts"] == {
            "pending": 1,
            "processing": 0,
            "completed": 0,
            "failed": 0,
        }

        items_response = api_client.get(f"/api/v1/batches/{batch_id}/items")
        assert items_response.status_code == 200
        items_body = items_response.json()
        assert items_body["total"] == 1
        assert items_body["items"][0]["payload"] == {"value": "a"}
        assert items_body["items"][0]["status"] == "PENDING"

    def test_items_endpoint_supports_status_filtering_and_pagination(self, api_client):
        items = [{"value": i} for i in range(5)]
        batch_id = api_client.post("/api/v1/batches", json={"items": items}).json()["id"]

        page = api_client.get(
            f"/api/v1/batches/{batch_id}/items", params={"limit": 2, "offset": 0}
        ).json()
        assert len(page["items"]) == 2
        assert page["total"] == 5

        filtered = api_client.get(
            f"/api/v1/batches/{batch_id}/items", params={"status": "PENDING"}
        ).json()
        assert filtered["total"] == 5

        filtered_empty = api_client.get(
            f"/api/v1/batches/{batch_id}/items", params={"status": "COMPLETED"}
        ).json()
        assert filtered_empty["total"] == 0

    def test_items_endpoint_returns_404_for_unknown_batch(self, api_client):
        response = api_client.get(f"/api/v1/batches/{uuid.uuid4()}/items")

        assert response.status_code == 404
