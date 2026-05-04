from typing import Protocol

from models.document_qa import Citation, DocumentAskResponse
from services.document_store import StoredDocument
from services.exceptions import NotFoundError
from services.retrieval_service import RetrievalService
from services.rule_based_answerer import RuleBasedAnswerer
from services.usage_tracking_service import SQLiteUsageTrackingService


class DocumentStoreProtocol(Protocol):
    def get_document(self, document_id: str) -> StoredDocument | None:
        ...


class DocumentAnsweringService:
    def __init__(
        self,
        store: DocumentStoreProtocol,
        retrieval_service: RetrievalService,
        answerer: RuleBasedAnswerer,
        usage_tracking_service: SQLiteUsageTrackingService | None = None,
    ):
        self.store = store
        self.retrieval_service = retrieval_service
        self.answerer = answerer
        self.usage_tracking_service = usage_tracking_service

    async def answer(
        self,
        document_id: str,
        question: str,
        top_k: int = 3,
    ) -> DocumentAskResponse:
        stored_document = self.store.get_document(document_id)

        if stored_document is None:
            raise NotFoundError("Document not found.")

        cleaned_question = question.strip()

        scored_chunks = self.retrieval_service.retrieve_with_scores(
            question=cleaned_question,
            chunks=stored_document.chunks,
            top_k=top_k,
        )

        combined_context = "\n".join(
            scored_chunk.chunk.text
            for scored_chunk in scored_chunks
        )

        answer_response = await self.answerer.answer(
            cleaned_question,
            combined_context,
        )

        if self.usage_tracking_service is not None:
            self.usage_tracking_service.record_usage(
                operation="document_answer",
                provider="local",
                model_name=self.answerer.__class__.__name__,
                input_text=f"{cleaned_question}\n\n{combined_context}",
                output_text=answer_response.answer,
                metadata={
                    "document_id": document_id,
                },
            )

        citations = [
            Citation(
                chunk_id=scored_chunk.chunk.chunk_id,
                snippet=self._snippet(scored_chunk.chunk.text),
                vector_score=scored_chunk.vector_score,
                keyword_score=scored_chunk.keyword_score,
                hybrid_score=scored_chunk.hybrid_score,
            )
            for scored_chunk in scored_chunks
        ]

        return DocumentAskResponse(
            answer=answer_response.answer,
            citations=citations,
        )

    def _snippet(self, text: str, limit: int = 160) -> str:
        cleaned = " ".join(text.split())

        if len(cleaned) <= limit:
            return cleaned

        return cleaned[:limit].rstrip() + "..."