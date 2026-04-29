from types import SimpleNamespace

import pytest

from models.document_qa import Citation, DocumentAskResponse
from models.evaluation import DocumentQAEvalCase
from services.document_qa_evaluation_service import DocumentQAEvaluationService


class SuccessfulIngestionService:
    async def ingest_text(self, filename: str, text: str):
        return SimpleNamespace(
            document_id="doc-123",
            filename=filename,
            chunk_count=1,
        )


class SuccessfulAnsweringService:
    async def answer(self, document_id: str, question: str, top_k: int = 3):
        return DocumentAskResponse(
            answer="FastAPI is the backend framework used in this project.",
            citations=[
                Citation(
                    chunk_id="doc-123-chunk-1",
                    snippet="FastAPI is the backend framework used in this project.",
                    vector_score=1.0,
                    keyword_score=1.0,
                    hybrid_score=1.0,
                )
            ],
        )


class BadAnsweringService:
    async def answer(self, document_id: str, question: str, top_k: int = 3):
        return DocumentAskResponse(
            answer="I could not find the answer in the provided context.",
            citations=[],
        )


@pytest.mark.asyncio
async def test_document_qa_eval_case_passes_when_answer_and_citation_match():
    service = DocumentQAEvaluationService(
        ingestion_service=SuccessfulIngestionService(),
        answering_service=SuccessfulAnsweringService(),
    )

    case = DocumentQAEvalCase(
        name="backend_framework_question",
        document_text="FastAPI is the backend framework used in this project.",
        question="What backend framework is used?",
        expected_answer_contains=["FastAPI"],
        expected_citation_contains=["FastAPI"],
        min_citations=1,
    )

    result = await service.evaluate_case(case)

    assert result.passed is True
    assert result.name == "backend_framework_question"
    assert result.document_id == "doc-123"
    assert result.citation_count == 1
    assert result.failures == []
    assert result.latency_ms >= 0


@pytest.mark.asyncio
async def test_document_qa_eval_case_fails_when_answer_and_citation_do_not_match():
    service = DocumentQAEvaluationService(
        ingestion_service=SuccessfulIngestionService(),
        answering_service=BadAnsweringService(),
    )

    case = DocumentQAEvalCase(
        name="backend_framework_question",
        document_text="FastAPI is the backend framework used in this project.",
        question="What backend framework is used?",
        expected_answer_contains=["FastAPI"],
        expected_citation_contains=["FastAPI"],
        min_citations=1,
    )

    result = await service.evaluate_case(case)

    assert result.passed is False
    assert "Answer does not contain 'FastAPI'." in result.failures
    assert "Expected at least 1 citation(s), got 0." in result.failures
    assert "No citation contains 'FastAPI'." in result.failures


@pytest.mark.asyncio
async def test_document_qa_eval_summary_counts_passed_and_failed_cases():
    service = DocumentQAEvaluationService(
        ingestion_service=SuccessfulIngestionService(),
        answering_service=SuccessfulAnsweringService(),
    )

    cases = [
        DocumentQAEvalCase(
            name="passing_case",
            document_text="FastAPI is the backend framework.",
            question="What backend framework is used?",
            expected_answer_contains=["FastAPI"],
            expected_citation_contains=["FastAPI"],
            min_citations=1,
        ),
        DocumentQAEvalCase(
            name="failing_case",
            document_text="FastAPI is the backend framework.",
            question="What backend framework is used?",
            expected_answer_contains=["Django"],
            expected_citation_contains=["Django"],
            min_citations=1,
        ),
    ]

    summary = await service.evaluate_cases(cases)

    assert summary.total_cases == 2
    assert summary.passed == 1
    assert summary.failed == 1
    assert summary.average_latency_ms >= 0
    assert len(summary.results) == 2