from fastapi.testclient import TestClient

from main import app, get_routing_service
from models.routing import RouteResponse
from services.exceptions import AppServiceError

client = TestClient(app)


class FakeRoutingService:
    async def route(self, user_input: str) -> RouteResponse:
        return RouteResponse(route="summarize")


class FailingRoutingService:
    async def route(self, user_input: str) -> RouteResponse:
        raise AppServiceError("Failed to route request.")


def fake_get_routing_service():
    return FakeRoutingService()


def failing_get_routing_service():
    return FailingRoutingService()


def test_route_endpoint_uses_service_override():
    app.dependency_overrides[get_routing_service] = fake_get_routing_service

    response = client.post(
        "/route",
        json={"user_input": "anything"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "route": "summarize"
    }

    app.dependency_overrides.clear()


def test_route_endpoint_returns_500_when_service_fails():
    app.dependency_overrides[get_routing_service] = failing_get_routing_service

    response = client.post(
        "/route",
        json={"user_input": "anything"}
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Failed to route request."
    }

    app.dependency_overrides.clear()