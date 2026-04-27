from fastapi.testclient import TestClient

from main import app, get_answering_service
from models.answering import AnswerResponse
from services.answering_service import AnsweringService
from services.exceptions import AppServiceError

client = TestClient(app)

AUTH_HEADERS = {"X-API-Key": "test-secret-key"}


class FakeAnsweringService:
    async def answer(self, question: str, context: str) -> AnswerResponse:
        return AnswerResponse(answer="Fake answer")


class FailingAnsweringService:
    async def answer(self, question: str, context: str) -> AnswerResponse:
        raise AppServiceError("Failed to answer question.")


def fake_get_answering_service() -> AnsweringService:
    return FakeAnsweringService()


def failing_get_answering_service() -> AnsweringService:
    return FailingAnsweringService()


def teardown_function():
    app.dependency_overrides.clear()


def test_answer_route_uses_service_override():
    app.dependency_overrides[get_answering_service] = fake_get_answering_service

    response = client.post(
        "/answer",
        headers=AUTH_HEADERS,
        json={
            "question": "Anything?",
            "context": "Anything at all.",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Fake answer",
    }


def test_answer_route_returns_500_when_service_fails():
    app.dependency_overrides[get_answering_service] = failing_get_answering_service

    response = client.post(
        "/answer",
        headers=AUTH_HEADERS,
        json={
            "question": "Anything?",
            "context": "Anything at all.",
        },
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Failed to answer question."
    }