import pytest

from clients.order_client import (
    HttpOrderClient,
    LocalOrderClient,
    OrderClientError,
    create_order_client,
)


def test_local_order_client_returns_existing_order():
    client = LocalOrderClient()

    order = client.get_order("ORD-123")

    assert order is not None
    assert order["status"] == "shipped"
    assert order["estimated_delivery"] == "2026-05-02"
    assert order["refund_eligible"] is True


def test_local_order_client_normalizes_order_id():
    client = LocalOrderClient()

    order = client.get_order("ord-123")

    assert order is not None
    assert order["status"] == "shipped"


def test_local_order_client_returns_none_for_missing_order():
    client = LocalOrderClient()

    order = client.get_order("ORD-999")

    assert order is None


def test_local_order_client_returns_copy_of_order_data():
    client = LocalOrderClient()

    order = client.get_order("ORD-123")
    assert order is not None

    order["status"] = "changed"

    fresh_order = client.get_order("ORD-123")

    assert fresh_order is not None
    assert fresh_order["status"] == "shipped"


def test_create_order_client_returns_local_client_by_default():
    client = create_order_client()

    assert isinstance(client, LocalOrderClient)


def test_create_order_client_returns_http_client():
    client = create_order_client(
        client_type="http",
        base_url="https://orders.example.com",
        api_key="secret-token",
    )

    assert isinstance(client, HttpOrderClient)
    assert client.base_url == "https://orders.example.com"
    assert client.api_key == "secret-token"


def test_create_order_client_requires_base_url_for_http_client():
    with pytest.raises(OrderClientError) as error:
        create_order_client(client_type="http")

    assert "ORDER_API_BASE_URL is required" in str(error.value)


def test_create_order_client_rejects_unknown_client_type():
    with pytest.raises(OrderClientError) as error:
        create_order_client(client_type="something-else")

    assert "Unsupported order client type" in str(error.value)