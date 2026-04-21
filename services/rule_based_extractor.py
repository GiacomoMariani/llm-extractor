import re

from models.extraction import ExtractResponse


class RuleBasedExtractor:
    async def extract(self, text: str) -> ExtractResponse:
        normalized_text = text.strip()

        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", normalized_text)
        order_match = re.search(r"\b(?:ORD|ORDER)[-_ ]?\d+\b", normalized_text, re.IGNORECASE)

        lowered = normalized_text.lower()

        if any(word in lowered for word in ["urgent", "asap", "immediately", "critical"]):
            urgency = "high"
        elif any(word in lowered for word in ["soon", "please respond", "when possible"]):
            urgency = "medium"
        else:
            urgency = "low"

        has_refund_request = "refund" in lowered

        return ExtractResponse(
            email=email_match.group(0) if email_match else None,
            order_id=order_match.group(0) if order_match else None,
            urgency=urgency,
            has_refund_request=has_refund_request,
        )