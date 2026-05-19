from providers.model_client import ModelClient


class FakeDocumentQAModelClient(ModelClient):
    model_name = "fake-document-qa"

    async def complete(self, prompt: str) -> str:
        context = self._extract_context(prompt)

        if not context:
            return "I could not find this information in the uploaded documents."

        source_id = self._extract_first_source_id(context)
        answer_text = self._extract_first_context_text(context)

        if not answer_text:
            return "I could not find this information in the uploaded documents."

        return f"{answer_text} [{source_id}]"

    def _extract_context(self, prompt: str) -> str:
        start_marker = "Retrieved context:"
        end_marker = "Answer:"

        if start_marker not in prompt:
            return ""

        context = prompt.split(start_marker, 1)[1]

        if end_marker in context:
            context = context.split(end_marker, 1)[0]

        return context.strip()

    def _extract_first_source_id(self, context: str) -> str:
        for line in context.splitlines():
            stripped = line.strip()

            if stripped.startswith("[") and "]" in stripped:
                return stripped.split("]", 1)[0].lstrip("[")

        return "1"

    def _extract_first_context_text(self, context: str) -> str:
        for line in context.splitlines():
            stripped = line.strip()

            if not stripped:
                continue

            if stripped.startswith("[") and "]" in stripped:
                continue

            return stripped

        return ""