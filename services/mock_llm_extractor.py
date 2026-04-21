from models.extraction import ExtractResponse


class MockLlmExtractor:
    async def extract(self, text: str) -> ExtractResponse:
        lowered = text.lower()

        return ExtractResponse(
            email="llm@example.com" if "email" in lowered else None,
            order_id="ORD-LLM-001" if "order" in lowered else None,
            urgency="high" if "urgent" in lowered else "low",
            has_refund_request="refund" in lowered,
        )