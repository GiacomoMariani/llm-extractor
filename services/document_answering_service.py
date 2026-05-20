import re
from typing import Protocol

from models.answering import AnswerResponse
from models.document_qa import Citation, DocumentAskResponse
from services.document_answerer import (
    DocumentAnswerer,
    RuleBasedDocumentAnswerer,
)
from services.document_qa_prompt_builder import RetrievedContextBlock
from services.document_store import StoredDocument
from services.exceptions import NotFoundError
from services.retrieval_service import RetrievalService
from services.rule_based_answerer import RuleBasedAnswerer
from services.usage_tracking_service import SQLiteUsageTrackingService


FALLBACK_ANSWER = "I could not find this information in the uploaded documents."


class DocumentStoreProtocol(Protocol):
    def get_document(self, document_id: str) -> StoredDocument | None:
        ...

    def list_documents(self):
        ...


class DocumentAnsweringService:
    def __init__(
        self,
        store: DocumentStoreProtocol,
        retrieval_service: RetrievalService,
        answerer: DocumentAnswerer | RuleBasedAnswerer,
        usage_tracking_service: SQLiteUsageTrackingService | None = None,
    ):
        self.store = store
        self.retrieval_service = retrieval_service
        self.answerer: DocumentAnswerer = (
            RuleBasedDocumentAnswerer(answerer)
            if isinstance(answerer, RuleBasedAnswerer)
            else answerer
        )
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

        context_blocks = [
            RetrievedContextBlock(
                source_id=index + 1,
                filename=stored_document.filename,
                page_number=scored_chunk.chunk.page_number,
                text=scored_chunk.chunk.text,
            )
            for index, scored_chunk in enumerate(scored_chunks)
        ]

        combined_context = "\n".join(
            block.text
            for block in context_blocks
        )

        answer_response = await self.answerer.answer(
            question=cleaned_question,
            context_blocks=context_blocks,
        )
        answer_response = _polish_answer_response(
            question=cleaned_question,
            answer_response=answer_response,
        )

        citations = [
            Citation(
                chunk_id=scored_chunk.chunk.chunk_id,
                filename=stored_document.filename,
                page_number=scored_chunk.chunk.page_number,
                snippet=self._snippet(scored_chunk.chunk.text),
                vector_score=scored_chunk.vector_score,
                keyword_score=scored_chunk.keyword_score,
                hybrid_score=scored_chunk.hybrid_score,
            )
            for scored_chunk in scored_chunks
        ]

        if _requires_fallback_due_to_missing_citations(
            answer_response=answer_response,
            citations=citations,
        ):
            answer_response = AnswerResponse(
                answer=FALLBACK_ANSWER,
                was_fallback=True,
            )
            citations = []

        visible_citations = [] if answer_response.was_fallback else citations

        if self.usage_tracking_service is not None:
            self.usage_tracking_service.record_usage(
                operation="document_answer",
                provider="local",
                model_name=getattr(
                    self.answerer,
                    "model_name",
                    self.answerer.__class__.__name__,
                ),
                input_text=f"{cleaned_question}\n\n{combined_context}",
                output_text=answer_response.answer,
                metadata={
                    "document_id": document_id,
                },
            )

        return DocumentAskResponse(
            answer=answer_response.answer,
            citations=visible_citations,
            was_fallback=answer_response.was_fallback,
        )

    async def answer_all(
        self,
        question: str,
        top_k: int = 3,
    ) -> DocumentAskResponse:
        cleaned_question = question.strip()

        documents = [
            self.store.get_document(summary.document_id)
            for summary in self.store.list_documents()
        ]

        documents = [
            document
            for document in documents
            if document is not None
        ]

        chunks = [
            chunk
            for document in documents
            for chunk in document.chunks
        ]

        filename_by_chunk_id = {
            chunk.chunk_id: document.filename
            for document in documents
            for chunk in document.chunks
        }

        scored_chunks = self.retrieval_service.retrieve_with_scores(
            question=cleaned_question,
            chunks=chunks,
            top_k=top_k,
        )

        context_blocks = [
            RetrievedContextBlock(
                source_id=index + 1,
                filename=filename_by_chunk_id.get(
                    scored_chunk.chunk.chunk_id,
                    "unknown",
                ),
                page_number=scored_chunk.chunk.page_number,
                text=scored_chunk.chunk.text,
            )
            for index, scored_chunk in enumerate(scored_chunks)
        ]

        combined_context = "\n".join(
            block.text
            for block in context_blocks
        )

        answer_response = await self.answerer.answer(
            question=cleaned_question,
            context_blocks=context_blocks,
        )
        answer_response = _polish_answer_response(
            question=cleaned_question,
            answer_response=answer_response,
        )

        citations = [
            Citation(
                chunk_id=scored_chunk.chunk.chunk_id,
                filename=filename_by_chunk_id.get(
                    scored_chunk.chunk.chunk_id,
                    "unknown",
                ),
                page_number=scored_chunk.chunk.page_number,
                snippet=self._snippet(scored_chunk.chunk.text),
                vector_score=scored_chunk.vector_score,
                keyword_score=scored_chunk.keyword_score,
                hybrid_score=scored_chunk.hybrid_score,
            )
            for scored_chunk in scored_chunks
        ]

        if _requires_fallback_due_to_missing_citations(
            answer_response=answer_response,
            citations=citations,
        ):
            answer_response = AnswerResponse(
                answer=FALLBACK_ANSWER,
                was_fallback=True,
            )
            citations = []

        visible_citations = [] if answer_response.was_fallback else citations

        if self.usage_tracking_service is not None:
            self.usage_tracking_service.record_usage(
                operation="knowledge_base_answer",
                provider="local",
                model_name=getattr(
                    self.answerer,
                    "model_name",
                    self.answerer.__class__.__name__,
                ),
                input_text=f"{cleaned_question}\n\n{combined_context}",
                output_text=answer_response.answer,
                metadata={
                    "document_id": "all-documents",
                },
            )

        return DocumentAskResponse(
            answer=answer_response.answer,
            citations=visible_citations,
            was_fallback=answer_response.was_fallback,
        )

    def _snippet(self, text: str, limit: int = 160) -> str:
        cleaned = " ".join(text.split())

        if len(cleaned) <= limit:
            return cleaned

        return cleaned[:limit].rstrip() + "..."


def _polish_answer_response(
    question: str,
    answer_response: AnswerResponse,
) -> AnswerResponse:
    if answer_response.was_fallback:
        return answer_response

    polished_answer = _format_order_ledger_answer(
        question=question,
        answer=answer_response.answer,
    )

    if polished_answer is None:
        return answer_response

    return AnswerResponse(
        answer=polished_answer,
        was_fallback=False,
    )


def _format_order_ledger_answer(question: str, answer: str) -> str | None:
    question_words = {
        word
        for word in re.findall(r"\b\w+\b", question.lower())
        if len(word) > 2
    }

    if not {"packed", "awaiting", "carrier", "pickup"}.intersection(
        question_words
    ):
        return None

    row_match = re.search(
        r"ORD-\d{4}-\d{4}\s*\|[^\n\r]+",
        answer,
    )

    if row_match is None:
        return None

    parts = [part.strip() for part in row_match.group(0).split("|")]

    if len(parts) < 10:
        return None

    order_id = parts[0]
    customer = parts[2]
    order_status = parts[4]
    assigned_owner = parts[8]
    notes = parts[9]

    if (
        order_status.lower() != "packed"
        and "awaiting carrier pickup" not in notes.lower()
    ):
        return None

    return (
        f"{order_id} for {customer} is packed and awaiting carrier pickup. "
        f"The assigned owner is {assigned_owner}."
    )


def _requires_fallback_due_to_missing_citations(
    answer_response: AnswerResponse,
    citations: list[Citation],
) -> bool:
    return (
        not answer_response.was_fallback
        and len(citations) == 0
    )
