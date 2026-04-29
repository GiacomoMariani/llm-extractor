from typing import Protocol

from models.document_qa import Citation, DocumentAskResponse
from services.document_store import StoredDocument
from services.exceptions import NotFoundError
from services.retrieval_service import RetrievalService
from services.rule_based_answerer import RuleBasedAnswerer


class DocumentStoreProtocol(Protocol):
    def get_document(self, document_id: str) -> StoredDocument | None:
        ...


class DocumentAnsweringService:
    def __init__(
        self,
        store: DocumentStoreProtocol,
        retrieval_service: RetrievalService,
        answerer: RuleBasedAnswerer,
    ):
        self.store = store
        self.retrieval_service = retrieval_service
        self.answerer = answerer

    async def answer(
        self,
        document_id: str,
        question: str,
        top_k: int = 3,
    ) -> DocumentAskResponse:
        stored_document = self.store.get_document(document_id)

        if stored_document is None:
            raise NotFoundError("Document not found.")

        scored_chunks = self.retrieval_service.retrieve_with_scores(
            question=question.strip(),
            chunks=stored_document.chunks,
            top_k=top_k,
        )

        combined_context = "\n".join(
            scored_chunk.chunk.text
            for scored_chunk in scored_chunks
        )

        answer_response = await self.answerer.answer(
            question.strip(),
            combined_context,
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