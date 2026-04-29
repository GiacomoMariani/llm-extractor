import json
import time
import urllib.error
import urllib.request
from typing import Any


ORDER_FIXTURES: dict[str, dict[str, Any]] = {
    "ORD-123": {
        "status": "shipped",
        "estimated_delivery": "2026-05-02",
        "refund_eligible": True,
        "refund_reason": "The order has not been delivered yet.",
    },
    "ORD-456": {
        "status": "processing",
        "estimated_delivery": "2026-05-05",
        "refund_eligible": True,
        "refund_reason": "The order is still processing.",
    },
    "ORD-789": {
        "status": "delivered",
        "estimated_delivery": "2026-04-20",
        "refund_eligible": False,
        "refund_reason": "The order has already been delivered.",
    },
}


class LocalOrderClient:
    def __init__(self, orders: dict[str, dict[str, Any]] | None = None):
        self._orders = ORDER_FIXTURES if orders is None else orders

    def get_order(self, order_id: str) -> dict[str, Any] | None:
        normalized_order_id = order_id.upper()
        order = self._orders.get(normalized_order_id)

        if order is None:
            return None

        return dict(order)


import json
import urllib.error
import urllib.request
from typing import Any


class OrderClientError(Exception):
    pass


class HttpOrderClient:
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(
            self,
            base_url: str,
            api_key: str | None = None,
            timeout_seconds: float = 5.0,
            max_retries: int = 2,
            retry_delay_seconds: float = 0.25,
            max_retry_delay_seconds: float = 5.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.max_retry_delay_seconds = max_retry_delay_seconds

    def get_order(self, order_id: str) -> dict[str, Any] | None:
        normalized_order_id = order_id.upper()
        url = f"{self.base_url}/orders/{normalized_order_id}"

        headers = {
            "Accept": "application/json",
        }

        if self.api_key is not None:
            headers["Authorization"] = f"Bearer {self.api_key}"

        request = urllib.request.Request(
            url=url,
            headers=headers,
            method="GET",
        )

        total_attempts = self.max_retries + 1

        for attempt_number in range(1, total_attempts + 1):
            try:
                with urllib.request.urlopen(
                    request,
                    timeout=self.timeout_seconds,
                ) as response:
                    body = response.read().decode("utf-8")
                    data = json.loads(body)

                return dict(data)

            except urllib.error.HTTPError as ex:
                if ex.code == 404:
                    return None

                if self._should_retry_http_error(ex, attempt_number, total_attempts):
                    retry_delay_seconds = self._get_retry_delay_seconds(ex)
                    self._wait_before_retry(retry_delay_seconds)
                    continue

                raise OrderClientError(
                    f"Order API returned HTTP {ex.code}."
                ) from ex

            except urllib.error.URLError as ex:
                if self._should_retry_url_error(attempt_number, total_attempts):
                    self._wait_before_retry(self.retry_delay_seconds)
                    continue

                raise OrderClientError(
                    "Order API request failed."
                ) from ex

            except json.JSONDecodeError as ex:
                raise OrderClientError(
                    "Order API returned invalid JSON."
                ) from ex

        raise OrderClientError("Order API request failed after retries.")

    def _should_retry_http_error(
        self,
        error: urllib.error.HTTPError,
        attempt_number: int,
        total_attempts: int,
    ) -> bool:
        return (
            error.code in self.RETRYABLE_STATUS_CODES
            and attempt_number < total_attempts
        )

    def _should_retry_url_error(
        self,
        attempt_number: int,
        total_attempts: int,
    ) -> bool:
        return attempt_number < total_attempts

    def _get_retry_delay_seconds(
            self,
            error: urllib.error.HTTPError,
    ) -> float:
        if error.code != 429:
            return self.retry_delay_seconds

        retry_after = None

        if error.headers is not None:
            retry_after = error.headers.get("Retry-After")

        if retry_after is None:
            return self.retry_delay_seconds

        try:
            retry_after_seconds = float(retry_after)
        except ValueError:
            return self.retry_delay_seconds

        if retry_after_seconds < 0:
            return self.retry_delay_seconds

        return min(retry_after_seconds, self.max_retry_delay_seconds)

        return min(retry_after_seconds, self.max_retry_delay_seconds)

    def _wait_before_retry(self, delay_seconds: float) -> None:
        if delay_seconds > 0:
            time.sleep(delay_seconds)

class FallbackOrderClient:
    def __init__(
        self,
        primary_client: Any,
        fallback_client: Any,
    ):
        self.primary_client = primary_client
        self.fallback_client = fallback_client

    def get_order(self, order_id: str) -> dict[str, Any] | None:
        try:
            return self.primary_client.get_order(order_id)
        except OrderClientError:
            return self.fallback_client.get_order(order_id)

def create_order_client(
    client_type: str = "local",
    base_url: str | None = None,
    api_key: str | None = None,
) -> LocalOrderClient | HttpOrderClient | FallbackOrderClient:
    normalized_client_type = client_type.lower()

    if normalized_client_type == "local":
        return LocalOrderClient()

    if normalized_client_type == "http":
        if not base_url:
            raise OrderClientError(
                "ORDER_API_BASE_URL is required when ORDER_CLIENT_TYPE=http."
            )

        return HttpOrderClient(
            base_url=base_url,
            api_key=api_key,
        )

    if normalized_client_type == "http_with_fallback":
        if not base_url:
            raise OrderClientError(
                "ORDER_API_BASE_URL is required when ORDER_CLIENT_TYPE=http_with_fallback."
            )

        return FallbackOrderClient(
            primary_client=HttpOrderClient(
                base_url=base_url,
                api_key=api_key,
            ),
            fallback_client=LocalOrderClient(),
        )

    raise OrderClientError(
        f"Unsupported order client type: {client_type}"
    )