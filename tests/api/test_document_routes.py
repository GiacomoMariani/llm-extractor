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


def test_upload_document_returns_document_metadata():
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
    assert payload["document_id"].startswith("doc-")
    assert payload["filename"] == "guide.txt"
    assert payload["chunk_count"] >= 1


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
    document_id = upload_response.json()["document_id"]

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
    assert payload["citations"][0]["chunk_id"].startswith(f"{document_id}-chunk-")


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