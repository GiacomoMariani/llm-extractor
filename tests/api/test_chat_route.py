from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

AUTH_HEADERS = {"X-API-Key": "test-secret-key"}


def test_chat_route_returns_assistant_reply():
    response = client.post(
        "/chat",
        headers=AUTH_HEADERS,
        json={"message": "Hello"},
    )

    assert response.status_code == 200

    payload = response.json()

    assert "reply" in payload
    assert payload["reply"]

def test_chat_route_requires_api_key():
    response = client.post(
        "/chat",
        json={"message": "Hello"},
    )

    assert response.status_code == 401


def test_chat_route_rejects_empty_message():
    response = client.post(
        "/chat",
        headers=AUTH_HEADERS,
        json={"message": ""},
    )

    assert response.status_code == 422