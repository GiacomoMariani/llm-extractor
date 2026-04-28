import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    extractor_type: str = "rule"
    order_client_type: str = "local"
    order_api_base_url: str | None = None
    order_api_key: str | None = None


def get_settings() -> Settings:
    return Settings(
        extractor_type=os.getenv("EXTRACTOR_TYPE", "rule").lower(),
        order_client_type=os.getenv("ORDER_CLIENT_TYPE", "local").lower(),
        order_api_base_url=os.getenv("ORDER_API_BASE_URL"),
        order_api_key=os.getenv("ORDER_API_KEY"),
    )