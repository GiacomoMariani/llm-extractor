from fastapi.testclient import TestClient

from main import app, get_extraction_service
from models.extraction import ExtractResponse
from services.exceptions import AppServiceError

client = TestClient(app)


class FakeExtractionService:
    async def extract(self, text: str) -> ExtractResponse:
        return ExtractResponse(
            email="fake@example.com",
            order_id="ORD-TEST-999",
            urgency="high",
            has_refund_request=True,
        )


class FailingExtractionService:
    async def extract(self, text: str) -> ExtractResponse:
        raise AppServiceError("Failed to extract fields.")


def fake_get_extraction_service():
    return FakeExtractionService()


def failing_get_extraction_service():
    return FailingExtractionService()


def test_extract_route_uses_service_override():
    app.dependency_overrides[get_extraction_service] = fake_get_extraction_service

    response = client.post(
        "/extract",
        json={"text": "anything"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "email": "fake@example.com",
        "order_id": "ORD-TEST-999",
        "urgency": "high",
        "has_refund_request": True,
    }

    app.dependency_overrides.clear()


def test_extract_route_returns_500_when_service_fails():
    app.dependency_overrides[get_extraction_service] = failing_get_extraction_service

    response = client.post(
        "/extract",
        json={"text": "anything"}
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Failed to extract fields."
    }

    app.dependency_overrides.clear()