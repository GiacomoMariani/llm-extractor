import re

from models.summarization import SummarizeResponse


class RuleBasedSummarizer:
    async def summarize(self, text: str, max_sentences: int) -> SummarizeResponse:
        normalized_text = text.strip()

        sentences = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", normalized_text)
            if sentence.strip()
        ]

        selected = sentences[:max_sentences]

        if not selected:
            return SummarizeResponse(summary="")

        return SummarizeResponse(summary=" ".join(selected))