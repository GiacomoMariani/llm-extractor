from fastapi.testclient import TestClient

from main import app, get_summarization_service
from models.summarization import SummarizeResponse
from services.exceptions import AppServiceError

client = TestClient(app)


class FakeSummarizationService:
    async def summarize(self, text: str, max_sentences: int) -> SummarizeResponse:
        return SummarizeResponse(summary="Fake summary.")


class FailingSummarizationService:
    async def summarize(self, text: str, max_sentences: int) -> SummarizeResponse:
        raise AppServiceError("Failed to summarize text.")


def fake_get_summarization_service():
    return FakeSummarizationService()


def failing_get_summarization_service():
    return FailingSummarizationService()


def test_summarize_route_uses_service_override():
    app.dependency_overrides[get_summarization_service] = fake_get_summarization_service

    response = client.post(
        "/summarize",
        json={
            "text": "Anything at all.",
            "max_sentences": 2,
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "summary": "Fake summary."
    }

    app.dependency_overrides.clear()


def test_summarize_route_returns_500_when_service_fails():
    app.dependency_overrides[get_summarization_service] = failing_get_summarization_service

    response = client.post(
        "/summarize",
        json={
            "text": "Anything at all.",
            "max_sentences": 2,
        },
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Failed to summarize text."
    }

    app.dependency_overrides.clear()