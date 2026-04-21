from typing import Protocol

from providers.fake_model_client import FakeModelClient
from services.llm_extractor import MockJsonLlmExtractor
from services.mock_llm_extractor import MockLlmExtractor
from services.rule_based_extractor import RuleBasedExtractor
from settings import get_settings


class TicketExtractor(Protocol):
    async def extract(self, text: str):
        ...


def get_extractor() -> TicketExtractor:
    settings = get_settings()

    if settings.extractor_type == "mock_llm":
        return MockLlmExtractor()

    if settings.extractor_type == "mock_llm_json":
        return MockJsonLlmExtractor(FakeModelClient())

    return RuleBasedExtractor()