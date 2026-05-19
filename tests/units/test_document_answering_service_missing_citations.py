import pytest

from models.answering import AnswerResponse
from services.document_answering_service import DocumentAnsweringService
from services.document_store import InMemoryDocumentStore


class EmptyRetrievalService:
    def retrieve_with_scores(self, question, chunks, top_k):
        return []


class FactualAnswerWithoutRetrievedSources:
    model_name = "unsafe-test-answerer"

    async def answer(self, question, context_blocks):
        return AnswerResponse(
            answer="Refunds are available within 30 days.",
            was_fallback=False,
        )


@pytest.mark.asyncio
async def test_document_answering_service_falls_back_when_answer_has_no_citations():
    store = InMemoryDocumentStore()

    stored_document = store.save_document(
        filename="policy.pdf",
        text="Refunds are available within 30 days.",
        chunk_payloads=[
            {
                "text": "Refunds are available within 30 days.",
                "embedding": [1.0, 0.0],
                "page_number": 4,
            }
        ],
    )

    service = DocumentAnsweringService(
        store=store,
        retrieval_service=EmptyRetrievalService(),
        answerer=FactualAnswerWithoutRetrievedSources(),
    )

    result = await service.answer(
        document_id=stored_document.document_id,
        question="What is the refund policy?",
        top_k=1,
    )

    assert result.answer == (
        "I could not find this information in the uploaded documents."
    )
    assert result.was_fallback is True
    assert result.citations == []


@pytest.mark.asyncio
async def test_document_answering_service_answer_all_falls_back_when_answer_has_no_citations():
    store = InMemoryDocumentStore()

    store.save_document(
        filename="policy.pdf",
        text="Refunds are available within 30 days.",
        chunk_payloads=[
            {
                "text": "Refunds are available within 30 days.",
                "embedding": [1.0, 0.0],
                "page_number": 4,
            }
        ],
    )

    service = DocumentAnsweringService(
        store=store,
        retrieval_service=EmptyRetrievalService(),
        answerer=FactualAnswerWithoutRetrievedSources(),
    )

    result = await service.answer_all(
        question="What is the refund policy?",
        top_k=1,
    )

    assert result.answer == (
        "I could not find this information in the uploaded documents."
    )
    assert result.was_fallback is True
    assert result.citations == []
