import os
from dataclasses import dataclass


def _get_int_env(
    name: str,
    default: int,
    *,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError as ex:
        raise ValueError(f"{name} must be an integer.") from ex

    if min_value is not None and value < min_value:
        raise ValueError(f"{name} must be at least {min_value}.")

    if max_value is not None and value > max_value:
        raise ValueError(f"{name} must be at most {max_value}.")

    return value


@dataclass(frozen=True)
class Settings:
    extractor_type: str = "rule"
    order_client_type: str = "local"
    order_api_base_url: str | None = None
    order_api_key: str | None = None
    uploaded_text_db_path: str = "uploaded_texts.db"
    uploaded_text_cleanup_max_age_hours: int = 24


def get_settings() -> Settings:
    return Settings(
        extractor_type=os.getenv("EXTRACTOR_TYPE", "rule").lower(),
        order_client_type=os.getenv("ORDER_CLIENT_TYPE", "local").lower(),
        order_api_base_url=os.getenv("ORDER_API_BASE_URL"),
        order_api_key=os.getenv("ORDER_API_KEY"),
        uploaded_text_db_path=os.getenv(
            "APP_UPLOADED_TEXT_DB_PATH",
            "uploaded_texts.db",
        ),
        uploaded_text_cleanup_max_age_hours=_get_int_env(
            "APP_UPLOADED_TEXT_CLEANUP_MAX_AGE_HOURS",
            default=24,
            min_value=1,
            max_value=24 * 30,
        ),
    )