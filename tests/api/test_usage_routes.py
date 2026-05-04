from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

AUTH_HEADERS = {"X-API-Key": "test-secret-key"}


def test_get_usage_summary_requires_api_key():
    response = client.get("/usage/summary")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing API key."
    }


def test_get_usage_summary_returns_totals():
    import main

    main.sqlite_usage_tracking_service.record_usage_tokens(
        operation="embedding",
        provider="local",
        model_name="local-embedding",
        input_tokens=10,
        output_tokens=0,
        estimated_cost_usd=0.01,
    )

    main.sqlite_usage_tracking_service.record_usage_tokens(
        operation="document_answer",
        provider="local",
        model_name="rule-based-answerer",
        input_tokens=20,
        output_tokens=5,
        estimated_cost_usd=0.02,
    )

    response = client.get(
        "/usage/summary",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["total_estimated_cost_usd"] == 0.03
    assert payload["recent_record_count"] == 2


def test_get_recent_usage_requires_api_key():
    response = client.get("/usage/recent")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing API key."
    }


def test_get_recent_usage_returns_recent_records():
    import main

    first_record = main.sqlite_usage_tracking_service.record_usage_tokens(
        operation="embedding",
        provider="local",
        model_name="local-embedding",
        input_tokens=10,
        output_tokens=0,
        estimated_cost_usd=0.01,
        metadata={"document_id": "doc-1"},
    )

    second_record = main.sqlite_usage_tracking_service.record_usage_tokens(
        operation="document_answer",
        provider="local",
        model_name="rule-based-answerer",
        input_tokens=20,
        output_tokens=5,
        estimated_cost_usd=0.02,
        metadata={"document_id": "doc-2"},
    )

    response = client.get(
        "/usage/recent?limit=10",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()
    assert len(payload["records"]) == 2

    assert payload["records"][0]["usage_id"] == second_record.usage_id
    assert payload["records"][0]["operation"] == "document_answer"
    assert payload["records"][0]["provider"] == "local"
    assert payload["records"][0]["model_name"] == "rule-based-answerer"
    assert payload["records"][0]["input_tokens"] == 20
    assert payload["records"][0]["output_tokens"] == 5
    assert payload["records"][0]["estimated_cost_usd"] == 0.02
    assert payload["records"][0]["metadata"] == {"document_id": "doc-2"}
    assert payload["records"][0]["created_at"]

    assert payload["records"][1]["usage_id"] == first_record.usage_id


def test_get_recent_usage_respects_limit():
    import main

    first_record = main.sqlite_usage_tracking_service.record_usage_tokens(
        operation="first",
        provider="local",
        model_name="test-model",
        input_tokens=1,
        output_tokens=0,
        estimated_cost_usd=0.01,
    )

    second_record = main.sqlite_usage_tracking_service.record_usage_tokens(
        operation="second",
        provider="local",
        model_name="test-model",
        input_tokens=1,
        output_tokens=0,
        estimated_cost_usd=0.02,
    )

    response = client.get(
        "/usage/recent?limit=1",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()
    assert len(payload["records"]) == 1
    assert payload["records"][0]["usage_id"] == second_record.usage_id
    assert payload["records"][0]["usage_id"] != first_record.usage_id


def test_get_recent_usage_rejects_invalid_limit():
    response = client.get(
        "/usage/recent?limit=0",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 422


def test_usage_records_are_created_by_document_upload_and_ask():
    upload_response = client.post(
        "/documents/upload",
        headers=AUTH_HEADERS,
        files={
            "file": (
                "guide.txt",
                b"FastAPI is the backend framework used in this project.",
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 200

    job_id = upload_response.json()["job_id"]

    job_response = client.get(
        f"/documents/jobs/{job_id}",
        headers=AUTH_HEADERS,
    )

    assert job_response.status_code == 200
    assert job_response.json()["status"] == "completed"

    document_id = job_response.json()["document_id"]
    assert document_id is not None

    ask_response = client.post(
        "/documents/ask",
        headers=AUTH_HEADERS,
        json={
            "document_id": document_id,
            "question": "What backend framework is used?",
        },
    )

    assert ask_response.status_code == 200

    usage_response = client.get(
        "/usage/recent?limit=10",
        headers=AUTH_HEADERS,
    )

    assert usage_response.status_code == 200

    operations = {
        record["operation"]
        for record in usage_response.json()["records"]
    }

    assert "document_embedding" in operations
    assert "document_answer" in operations