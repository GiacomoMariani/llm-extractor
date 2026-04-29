import pytest
import urllib.error

from clients.order_client import (
    FallbackOrderClient,
    HttpOrderClient,
    LocalOrderClient,
    OrderClientError,
    create_order_client,
)

class FakeHttpResponse:
    def __init__(self, body: str):
        self.body = body.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return None

    def read(self) -> bytes:
        return self.body

class FakeSuccessfulOrderClient:
    def get_order(self, order_id: str):
        return {
            "status": "from-primary",
            "estimated_delivery": "2026-05-10",
            "refund_eligible": True,
            "refund_reason": "Primary client result.",
        }


class FakeFailingOrderClient:
    def get_order(self, order_id: str):
        raise OrderClientError("Primary client failed.")


class FakeMissingOrderClient:
    def get_order(self, order_id: str):
        return None

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

def test_http_order_client_retries_retryable_http_error_then_succeeds(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request)

        if len(calls) == 1:
            raise urllib.error.HTTPError(
                url=request.full_url,
                code=503,
                msg="Service Unavailable",
                hdrs=None,
                fp=None,
            )

        return FakeHttpResponse(
            """
            {
                "status": "shipped",
                "estimated_delivery": "2026-05-02",
                "refund_eligible": true,
                "refund_reason": "The order has not been delivered yet."
            }
            """
        )

    monkeypatch.setattr(
        "clients.order_client.urllib.request.urlopen",
        fake_urlopen,
    )

    client = HttpOrderClient(
        base_url="https://orders.example.com",
        max_retries=1,
        retry_delay_seconds=0,
    )

    order = client.get_order("ord-123")

    assert order is not None
    assert order["status"] == "shipped"
    assert order["estimated_delivery"] == "2026-05-02"
    assert len(calls) == 2

def test_http_order_client_uses_retry_after_header_for_429(monkeypatch):
    calls = []
    sleep_delays = []

    def fake_sleep(delay):
        sleep_delays.append(delay)

    def fake_urlopen(request, timeout):
        calls.append(request)

        if len(calls) == 1:
            raise urllib.error.HTTPError(
                url=request.full_url,
                code=429,
                msg="Too Many Requests",
                hdrs={"Retry-After": "2"},
                fp=None,
            )

        return FakeHttpResponse(
            """
            {
                "status": "shipped",
                "estimated_delivery": "2026-05-02",
                "refund_eligible": true,
                "refund_reason": "The order has not been delivered yet."
            }
            """
        )

    monkeypatch.setattr(
        "clients.order_client.urllib.request.urlopen",
        fake_urlopen,
    )
    monkeypatch.setattr(
        "clients.order_client.time.sleep",
        fake_sleep,
    )

    client = HttpOrderClient(
        base_url="https://orders.example.com",
        max_retries=1,
        retry_delay_seconds=0,
    )

    order = client.get_order("ORD-123")

    assert order is not None
    assert order["status"] == "shipped"
    assert len(calls) == 2
    assert sleep_delays == [2.0]

def test_http_order_client_caps_retry_after_delay_for_429(monkeypatch):
    calls = []
    sleep_delays = []

    def fake_sleep(delay):
        sleep_delays.append(delay)

    def fake_urlopen(request, timeout):
        calls.append(request)

        if len(calls) == 1:
            raise urllib.error.HTTPError(
                url=request.full_url,
                code=429,
                msg="Too Many Requests",
                hdrs={"Retry-After": "999"},
                fp=None,
            )

        return FakeHttpResponse(
            """
            {
                "status": "shipped",
                "estimated_delivery": "2026-05-02",
                "refund_eligible": true,
                "refund_reason": "The order has not been delivered yet."
            }
            """
        )

    monkeypatch.setattr(
        "clients.order_client.urllib.request.urlopen",
        fake_urlopen,
    )
    monkeypatch.setattr(
        "clients.order_client.time.sleep",
        fake_sleep,
    )

    client = HttpOrderClient(
        base_url="https://orders.example.com",
        max_retries=1,
        retry_delay_seconds=0,
        max_retry_delay_seconds=5,
    )

    order = client.get_order("ORD-123")

    assert order is not None
    assert order["status"] == "shipped"
    assert len(calls) == 2
    assert sleep_delays == [5.0]

def test_http_order_client_falls_back_when_retry_after_is_invalid(monkeypatch):
    calls = []
    sleep_delays = []

    def fake_sleep(delay):
        sleep_delays.append(delay)

    def fake_urlopen(request, timeout):
        calls.append(request)

        if len(calls) == 1:
            raise urllib.error.HTTPError(
                url=request.full_url,
                code=429,
                msg="Too Many Requests",
                hdrs={"Retry-After": "not-a-number"},
                fp=None,
            )

        return FakeHttpResponse(
            """
            {
                "status": "shipped",
                "estimated_delivery": "2026-05-02",
                "refund_eligible": true,
                "refund_reason": "The order has not been delivered yet."
            }
            """
        )

    monkeypatch.setattr(
        "clients.order_client.urllib.request.urlopen",
        fake_urlopen,
    )
    monkeypatch.setattr(
        "clients.order_client.time.sleep",
        fake_sleep,
    )

    client = HttpOrderClient(
        base_url="https://orders.example.com",
        max_retries=1,
        retry_delay_seconds=0.5,
        max_retry_delay_seconds=5,
    )

    order = client.get_order("ORD-123")

    assert order is not None
    assert order["status"] == "shipped"
    assert len(calls) == 2
    assert sleep_delays == [0.5]

def test_http_order_client_falls_back_when_retry_after_is_negative(monkeypatch):
    calls = []
    sleep_delays = []

    def fake_sleep(delay):
        sleep_delays.append(delay)

    def fake_urlopen(request, timeout):
        calls.append(request)

        if len(calls) == 1:
            raise urllib.error.HTTPError(
                url=request.full_url,
                code=429,
                msg="Too Many Requests",
                hdrs={"Retry-After": "-10"},
                fp=None,
            )

        return FakeHttpResponse(
            """
            {
                "status": "shipped",
                "estimated_delivery": "2026-05-02",
                "refund_eligible": true,
                "refund_reason": "The order has not been delivered yet."
            }
            """
        )

    monkeypatch.setattr(
        "clients.order_client.urllib.request.urlopen",
        fake_urlopen,
    )
    monkeypatch.setattr(
        "clients.order_client.time.sleep",
        fake_sleep,
    )

    client = HttpOrderClient(
        base_url="https://orders.example.com",
        max_retries=1,
        retry_delay_seconds=0.5,
        max_retry_delay_seconds=5,
    )

    order = client.get_order("ORD-123")

    assert order is not None
    assert order["status"] == "shipped"
    assert len(calls) == 2
    assert sleep_delays == [0.5]

def test_http_order_client_returns_none_for_404_without_retrying(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request)

        raise urllib.error.HTTPError(
            url=request.full_url,
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(
        "clients.order_client.urllib.request.urlopen",
        fake_urlopen,
    )

    client = HttpOrderClient(
        base_url="https://orders.example.com",
        max_retries=2,
        retry_delay_seconds=0,
    )

    order = client.get_order("ORD-999")

    assert order is None
    assert len(calls) == 1


def test_http_order_client_raises_after_retryable_errors_are_exhausted(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request)

        raise urllib.error.HTTPError(
            url=request.full_url,
            code=503,
            msg="Service Unavailable",
            hdrs=None,
            fp=None,
        )

    monkeypatch.setattr(
        "clients.order_client.urllib.request.urlopen",
        fake_urlopen,
    )

    client = HttpOrderClient(
        base_url="https://orders.example.com",
        max_retries=2,
        retry_delay_seconds=0,
    )

    with pytest.raises(OrderClientError) as error:
        client.get_order("ORD-123")

    assert "Order API returned HTTP 503" in str(error.value)
    assert len(calls) == 3

def test_fallback_order_client_uses_primary_when_primary_succeeds():
    client = FallbackOrderClient(
        primary_client=FakeSuccessfulOrderClient(),
        fallback_client=LocalOrderClient(),
    )

    order = client.get_order("ORD-123")

    assert order is not None
    assert order["status"] == "from-primary"


def test_fallback_order_client_uses_fallback_when_primary_fails():
    client = FallbackOrderClient(
        primary_client=FakeFailingOrderClient(),
        fallback_client=LocalOrderClient(),
    )

    order = client.get_order("ORD-123")

    assert order is not None
    assert order["status"] == "shipped"


def test_fallback_order_client_does_not_fallback_when_primary_returns_none():
    client = FallbackOrderClient(
        primary_client=FakeMissingOrderClient(),
        fallback_client=LocalOrderClient(),
    )

    order = client.get_order("ORD-123")

    assert order is None


def test_create_order_client_returns_http_with_fallback_client():
    client = create_order_client(
        client_type="http_with_fallback",
        base_url="https://orders.example.com",
        api_key="secret-token",
    )

    assert isinstance(client, FallbackOrderClient)
    assert isinstance(client.primary_client, HttpOrderClient)
    assert isinstance(client.fallback_client, LocalOrderClient)