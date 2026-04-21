import json

import pytest
from pydantic import ValidationError

from providers.fake_model_client import FakeModelClient
from services.llm_extractor import MockJsonLlmExtractor


@pytest.mark.asyncio
async def test_mock_json_llm_extractor_returns_valid_response():
    extractor = MockJsonLlmExtractor(FakeModelClient())

    result = await extractor.extract(
        "My email is marco@example.com. I want a refund. This is urgent."
    )

    assert result.email == "llm@example.com"
    assert result.order_id is None
    assert result.urgency == "high"
    assert result.has_refund_request is True


@pytest.mark.asyncio
async def test_mock_json_llm_extractor_raises_on_invalid_json(monkeypatch):
    extractor = MockJsonLlmExtractor(FakeModelClient())

    async def fake_complete(prompt: str) -> str:
        return "{not valid json}"

    monkeypatch.setattr(extractor.model_client, "complete", fake_complete)

    with pytest.raises(json.JSONDecodeError):
        await extractor.extract("anything")


@pytest.mark.asyncio
async def test_mock_json_llm_extractor_raises_on_invalid_schema(monkeypatch):
    extractor = MockJsonLlmExtractor(FakeModelClient())

    async def fake_complete(prompt: str) -> str:
        return """
        {
            "email": 123,
            "order_id": null,
            "urgency": "high"
        }
        """

    monkeypatch.setattr(extractor.model_client, "complete", fake_complete)

    with pytest.raises(ValidationError):
        await extractor.extract("anything")