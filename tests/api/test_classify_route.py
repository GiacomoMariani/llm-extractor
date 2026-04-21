from fastapi.testclient import TestClient

from main import app, get_classification_service
from models.classification import ClassifyResponse
from services.exceptions import AppServiceError

client = TestClient(app)


class FakeClassificationService:
    async def classify(self, text: str) -> ClassifyResponse:
        return ClassifyResponse(category="technical")


class FailingClassificationService:
    async def classify(self, text: str) -> ClassifyResponse:
        raise AppServiceError("Failed to classify text.")


def fake_get_classification_service():
    return FakeClassificationService()


def failing_get_classification_service():
    return FailingClassificationService()


def test_classify_route_uses_service_override():
    app.dependency_overrides[get_classification_service] = fake_get_classification_service

    response = client.post(
        "/classify",
        json={"text": "anything"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "category": "technical"
    }

    app.dependency_overrides.clear()


def test_classify_route_returns_500_when_service_fails():
    app.dependency_overrides[get_classification_service] = failing_get_classification_service

    response = client.post(
        "/classify",
        json={"text": "anything"}
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Failed to classify text."
    }

    app.dependency_overrides.clear()