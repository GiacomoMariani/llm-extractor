from typing import Protocol

from models.answering import AnswerResponse
from services.document_qa_prompt_builder import RetrievedContextBlock
from services.rule_based_answerer import RuleBasedAnswerer


class DocumentAnswerer(Protocol):
    async def answer(
        self,
        question: str,
        context_blocks: list[RetrievedContextBlock],
    ) -> AnswerResponse:
        ...


class RuleBasedDocumentAnswerer:
    def __init__(self, answerer: RuleBasedAnswerer):
        self.answerer = answerer
        self.model_name = answerer.__class__.__name__

    async def answer(
        self,
        question: str,
        context_blocks: list[RetrievedContextBlock],
    ) -> AnswerResponse:
        combined_context = "\n".join(
            block.text
            for block in context_blocks
        )

        return await self.answerer.answer(
            question=question,
            context=combined_context,
        )

class FallbackDocumentAnswerer:
    def __init__(
        self,
        primary_answerer: DocumentAnswerer,
        fallback_answerer: DocumentAnswerer,
    ):
        self.primary_answerer = primary_answerer
        self.fallback_answerer = fallback_answerer
        self.model_name = (
            f"{getattr(primary_answerer, 'model_name', primary_answerer.__class__.__name__)}"
            "+fallback-rule"
        )

    async def answer(
        self,
        question: str,
        context_blocks: list[RetrievedContextBlock],
    ) -> AnswerResponse:
        try:
            return await self.primary_answerer.answer(
                question=question,
                context_blocks=context_blocks,
            )
        except Exception:
            return await self.fallback_answerer.answer(
                question=question,
                context_blocks=context_blocks,
            )