from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_response_includes_generated_request_id():
    response = client.get("/docs")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"]


def test_response_reuses_provided_request_id():
    response = client.get(
        "/docs",
        headers={"X-Request-ID": "test-request-123"},
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-123"