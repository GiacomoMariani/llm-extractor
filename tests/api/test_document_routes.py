from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

AUTH_HEADERS = {"X-API-Key": "test-secret-key"}


def test_upload_document_requires_api_key():
    response = client.post(
        "/documents/upload",
        files={
            "file": (
                "guide.txt",
                b"FastAPI is the backend framework.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing API key."
    }


def test_upload_document_returns_queued_ingestion_job():
    response = client.post(
        "/documents/upload",
        headers=AUTH_HEADERS,
        files={
            "file": (
                "guide.txt",
                b"FastAPI is the backend framework. Testing is important.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["job_id"].startswith("job-")
    assert payload["filename"] == "guide.txt"
    assert payload["status"] == "queued"
    assert payload["document_id"] is None
    assert payload["chunk_count"] is None
    assert payload["error_message"] is None
    assert payload["created_at"]
    assert payload["updated_at"]


def test_upload_document_job_can_be_fetched_after_background_completion():
    upload_response = client.post(
        "/documents/upload",
        headers=AUTH_HEADERS,
        files={
            "file": (
                "guide.txt",
                b"FastAPI is the backend framework. Testing is important.",
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 200

    upload_payload = upload_response.json()
    job_id = upload_payload["job_id"]

    job_response = client.get(
        f"/documents/jobs/{job_id}",
        headers=AUTH_HEADERS,
    )

    assert job_response.status_code == 200

    job_payload = job_response.json()
    assert job_payload["job_id"] == job_id
    assert job_payload["filename"] == "guide.txt"
    assert job_payload["status"] == "completed"
    assert job_payload["document_id"].startswith("doc-")
    assert job_payload["chunk_count"] >= 1
    assert job_payload["error_message"] is None


def test_upload_document_rejects_non_txt_files():
    response = client.post(
        "/documents/upload",
        headers=AUTH_HEADERS,
        files={
            "file": (
                "guide.pdf",
                b"not really a pdf",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Only .txt files are supported."
    }


def test_upload_document_rejects_empty_text_file():
    response = client.post(
        "/documents/upload",
        headers=AUTH_HEADERS,
        files={
            "file": (
                "empty.txt",
                b"   ",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Uploaded document is empty."
    }


def test_get_document_ingestion_job_requires_api_key():
    response = client.get("/documents/jobs/job-missing")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing API key."
    }


def test_get_document_ingestion_job_returns_job_status():
    import main

    job = main.sqlite_ingestion_job_store.create_job("guide.txt")
    main.sqlite_ingestion_job_store.mark_completed(
        job_id=job.job_id,
        document_id="doc-123",
        chunk_count=3,
    )

    response = client.get(
        f"/documents/jobs/{job.job_id}",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()
    assert payload["job_id"] == job.job_id
    assert payload["filename"] == "guide.txt"
    assert payload["status"] == "completed"
    assert payload["document_id"] == "doc-123"
    assert payload["chunk_count"] == 3
    assert payload["error_message"] is None
    assert payload["created_at"]
    assert payload["updated_at"]


def test_get_document_ingestion_job_returns_404_for_unknown_job():
    response = client.get(
        "/documents/jobs/job-missing",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Ingestion job not found."
    }


def test_ask_document_returns_grounded_answer_with_citations():
    upload_response = client.post(
        "/documents/upload",
        headers=AUTH_HEADERS,
        files={
            "file": (
                "guide.txt",
                (
                    b"FastAPI is the backend framework used in this project. "
                    b"Pytest is used for testing. "
                    b"Docker has not been added yet."
                ),
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

    document_id = job_response.json()["document_id"]
    assert document_id is not None

    response = client.post(
        "/documents/ask",
        headers=AUTH_HEADERS,
        json={
            "document_id": document_id,
            "question": "What is used for the backend?",
            "top_k": 2,
        },
    )

    assert response.status_code == 200

    payload = response.json()
    assert "FastAPI" in payload["answer"]
    assert len(payload["citations"]) >= 1

    first_citation = payload["citations"][0]

    assert first_citation["chunk_id"].startswith(f"{document_id}-chunk-")
    assert first_citation["snippet"]
    assert 0.0 <= first_citation["vector_score"] <= 1.0
    assert 0.0 <= first_citation["keyword_score"] <= 1.0
    assert 0.0 <= first_citation["hybrid_score"] <= 1.0


def test_ask_document_returns_404_for_unknown_document():
    response = client.post(
        "/documents/ask",
        headers=AUTH_HEADERS,
        json={
            "document_id": "doc-missing",
            "question": "What is used for the backend?",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Document not found."
    }