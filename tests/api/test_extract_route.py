from fastapi.testclient import TestClient

from main import app, get_extraction_service
from models.extraction import ExtractResponse
from services.exceptions import AppServiceError
from services.extraction_service import ExtractionService

client = TestClient(app)

AUTH_HEADERS = {"X-API-Key": "test-secret-key"}


class FakeExtractionService:
    async def extract(self, text: str) -> ExtractResponse:
        return ExtractResponse(
            email="ada@example.com",
            order_id="ORD-123",
            urgency="high",
            has_refund_request=True,
        )


class FailingExtractionService:
    async def extract(self, text: str) -> ExtractResponse:
        raise AppServiceError("Failed to extract structured data.")


def fake_get_extraction_service() -> ExtractionService:
    return FakeExtractionService()


def failing_get_extraction_service() -> ExtractionService:
    return FailingExtractionService()


def teardown_function():
    app.dependency_overrides.clear()


def test_extract_route_uses_service_override():
    app.dependency_overrides[get_extraction_service] = fake_get_extraction_service

    response = client.post(
        "/extract",
        headers=AUTH_HEADERS,
        json={"text": "anything"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "email": "ada@example.com",
        "order_id": "ORD-123",
        "urgency": "high",
        "has_refund_request": True,
    }


def test_extract_route_returns_500_when_service_fails():
    app.dependency_overrides[get_extraction_service] = failing_get_extraction_service

    response = client.post(
        "/extract",
        headers=AUTH_HEADERS,
        json={"text": "anything"},
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Failed to extract structured data."
    }