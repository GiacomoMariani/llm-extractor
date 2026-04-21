from models.classification import ClassifyResponse


class RuleBasedClassifier:
    async def classify(self, text: str) -> ClassifyResponse:
        lowered = text.lower()

        if "refund" in lowered:
            return ClassifyResponse(category="refund")

        if any(word in lowered for word in ["invoice", "charge", "payment", "billing"]):
            return ClassifyResponse(category="billing")

        if any(word in lowered for word in ["error", "bug", "issue", "login", "crash"]):
            return ClassifyResponse(category="technical")

        return ClassifyResponse(category="general")