import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    extractor_type: str = "rule"


def get_settings() -> Settings:
    return Settings(
        extractor_type=os.getenv("EXTRACTOR_TYPE", "rule").lower()
    )