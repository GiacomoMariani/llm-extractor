from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

AUTH_HEADERS = {"X-API-Key": "test-secret-key"}


def test_tool_assistant_returns_order_status():
    response = client.post(
        "/tool-assistant",
        headers=AUTH_HEADERS,
        json={"message": "Where is ORD-123?"},
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["tool_called"] == "get_order_status"
    assert payload["tool_result"]["found"] is True
    assert payload["tool_result"]["order_id"] == "ORD-123"
    assert payload["tool_result"]["status"] == "shipped"
    assert "currently shipped" in payload["answer"]


def test_tool_assistant_checks_refund_eligibility():
    response = client.post(
        "/tool-assistant",
        headers=AUTH_HEADERS,
        json={"message": "Can I get a refund for ORD-789?"},
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["tool_called"] == "check_refund_eligibility"
    assert payload["tool_result"]["found"] is True
    assert payload["tool_result"]["order_id"] == "ORD-789"
    assert payload["tool_result"]["eligible"] is False
    assert "does not appear to be eligible" in payload["answer"]


def test_tool_assistant_asks_for_order_id_when_missing():
    response = client.post(
        "/tool-assistant",
        headers=AUTH_HEADERS,
        json={"message": "Where is my order?"},
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["tool_called"] is None
    assert payload["tool_result"] is None
    assert payload["answer"] == "Please provide an order ID so I can help with your request."


def test_tool_assistant_requires_api_key():
    response = client.post(
        "/tool-assistant",
        json={"message": "Where is ORD-123?"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing API key."
    }

def test_tool_assistant_creates_pending_refund_request_when_eligible():
    response = client.post(
        "/tool-assistant",
        headers=AUTH_HEADERS,
        json={"message": "I want to request a refund for ORD-123."},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["tool_called"] == "create_pending_refund_request"
    assert payload["tool_result"]["created"] is True
    assert payload["tool_result"]["order_id"] == "ORD-123"
    assert payload["tool_result"]["status"] == "pending_confirmation"
    assert payload["tool_result"]["pending_action_id"].startswith("PEND-")

    assert len(payload["tool_calls"]) == 1
    assert payload["tool_calls"][0]["tool_name"] == "create_pending_refund_request"
    assert payload["tool_calls"][0]["result"]["created"] is True

    assert "Please confirm" in payload["answer"]
    assert "if you want me to submit the refund request" in payload["answer"]


def test_tool_assistant_confirms_pending_refund_request():
    setup_response = client.post(
        "/tool-assistant",
        headers=AUTH_HEADERS,
        json={"message": "I want to request a refund for ORD-456."},
    )

    assert setup_response.status_code == 200

    setup_payload = setup_response.json()
    pending_action_id = setup_payload["tool_result"]["pending_action_id"]

    confirm_response = client.post(
        "/tool-assistant",
        headers=AUTH_HEADERS,
        json={"message": f"Confirm {pending_action_id}."},
    )

    assert confirm_response.status_code == 200

    payload = confirm_response.json()

    assert payload["tool_called"] == "confirm_pending_refund_request"
    assert payload["tool_result"]["confirmed"] is True
    assert payload["tool_result"]["pending_action_id"] == pending_action_id
    assert payload["tool_result"]["order_id"] == "ORD-456"
    assert payload["tool_result"]["refund_request_id"].startswith("REF-")

    assert len(payload["tool_calls"]) == 1
    assert payload["tool_calls"][0]["tool_name"] == "confirm_pending_refund_request"

    assert "Refund request" in payload["answer"]
    assert "has been submitted" in payload["answer"]


def test_tool_assistant_does_not_create_pending_refund_request_when_ineligible():
    response = client.post(
        "/tool-assistant",
        headers=AUTH_HEADERS,
        json={"message": "I want to request a refund for ORD-789."},
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["tool_called"] == "create_pending_refund_request"
    assert payload["tool_result"]["created"] is False
    assert payload["tool_result"]["order_id"] == "ORD-789"

    assert len(payload["tool_calls"]) == 1
    assert payload["tool_calls"][0]["tool_name"] == "create_pending_refund_request"
    assert payload["tool_calls"][0]["result"]["created"] is False

    assert "could not be created" in payload["answer"]