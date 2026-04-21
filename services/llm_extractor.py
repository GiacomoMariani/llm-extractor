import json

from models.extraction import ExtractResponse
from providers.model_client import ModelClient


class MockJsonLlmExtractor:
    def __init__(self, model_client: ModelClient):
        self.model_client = model_client

    async def extract(self, text: str) -> ExtractResponse:
        prompt = self._build_prompt(text)
        raw_response = await self.model_client.complete(prompt)
        return self._parse_response(raw_response)

    def _build_prompt(self, text: str) -> str:
        return f"""
Extract these fields from the support message and return JSON only:
- email
- order_id
- urgency
- has_refund_request

Message:
{text}
""".strip()

    def _parse_response(self, raw_response: str) -> ExtractResponse:
        data = json.loads(raw_response)
        return ExtractResponse.model_validate(data)