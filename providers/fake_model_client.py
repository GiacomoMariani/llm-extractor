import json

from providers.model_client import ModelClient


class FakeModelClient(ModelClient):
    async def complete(self, prompt: str) -> str:
        message = self._extract_message(prompt)
        lowered = message.lower()

        response = {
            "email": "llm@example.com" if "email" in lowered else None,
            "order_id": "ORD-LLM-001" if "order" in lowered else None,
            "urgency": "high" if "urgent" in lowered else "low",
            "has_refund_request": "refund" in lowered,
        }

        return json.dumps(response)

    def _extract_message(self, prompt: str) -> str:
        marker = "Message:"

        if marker not in prompt:
            return prompt

        return prompt.split(marker, 1)[1].strip()