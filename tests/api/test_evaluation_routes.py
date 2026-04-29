from fastapi.testclient import TestClient

from main import app
from models.evaluation import DocumentQAEvalCaseResult, DocumentQAEvalSummary

client = TestClient(app)

AUTH_HEADERS = {"X-API-Key": "test-secret-key"}


def test_get_latest_document_qa_eval_requires_api_key():
    response = client.get("/evals/document-qa/latest")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing API key."
    }


def test_get_latest_document_qa_eval_returns_404_when_no_runs_exist():
    response = client.get(
        "/evals/document-qa/latest",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "No document QA evaluation runs found."
    }


def test_get_latest_document_qa_eval_returns_latest_saved_run():
    import main

    first_summary = DocumentQAEvalSummary(
        total_cases=1,
        passed=1,
        failed=0,
        average_latency_ms=10.0,
        results=[
            DocumentQAEvalCaseResult(
                name="first_case",
                passed=True,
                answer="FastAPI is the backend framework.",
                citation_count=1,
                checks=["Answer contains 'FastAPI'."],
                failures=[],
                latency_ms=10.0,
                document_id="doc-111",
            )
        ],
    )

    second_summary = DocumentQAEvalSummary(
        total_cases=2,
        passed=1,
        failed=1,
        average_latency_ms=15.5,
        results=[
            DocumentQAEvalCaseResult(
                name="passing_case",
                passed=True,
                answer="Hybrid retrieval combines vector similarity with keyword search.",
                citation_count=1,
                checks=["Answer contains 'Hybrid retrieval'."],
                failures=[],
                latency_ms=12.0,
                document_id="doc-222",
            ),
            DocumentQAEvalCaseResult(
                name="failing_case",
                passed=False,
                answer="I could not find the answer.",
                citation_count=0,
                checks=[],
                failures=["Answer does not contain 'Docker'."],
                latency_ms=19.0,
                document_id=None,
            ),
        ],
    )

    main.sqlite_evaluation_result_store.save_summary(first_summary)
    latest_saved_run = main.sqlite_evaluation_result_store.save_summary(second_summary)

    response = client.get(
        "/evals/document-qa/latest",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["run_id"] == latest_saved_run.run_id
    assert payload["total_cases"] == 2
    assert payload["passed"] == 1
    assert payload["failed"] == 1
    assert payload["average_latency_ms"] == 15.5
    assert payload["created_at"]
    assert len(payload["results"]) == 2

    passing_case = payload["results"][0]
    assert passing_case["name"] == "passing_case"
    assert passing_case["passed"] is True
    assert passing_case["answer"] == (
        "Hybrid retrieval combines vector similarity with keyword search."
    )
    assert passing_case["citation_count"] == 1
    assert passing_case["checks"] == ["Answer contains 'Hybrid retrieval'."]
    assert passing_case["failures"] == []
    assert passing_case["latency_ms"] == 12.0
    assert passing_case["document_id"] == "doc-222"

    failing_case = payload["results"][1]
    assert failing_case["name"] == "failing_case"
    assert failing_case["passed"] is False
    assert failing_case["answer"] == "I could not find the answer."
    assert failing_case["citation_count"] == 0
    assert failing_case["checks"] == []
    assert failing_case["failures"] == ["Answer does not contain 'Docker'."]
    assert failing_case["latency_ms"] == 19.0
    assert failing_case["document_id"] is None