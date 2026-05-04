import pytest

from providers.embedding_provider import LocalEmbeddingProvider
from services.document_answering_service import DocumentAnsweringService
from services.document_ingestion_service import DocumentIngestionService
from services.document_store import InMemoryDocumentStore
from services.retrieval_service import RetrievalService
from services.rule_based_answerer import RuleBasedAnswerer
from services.usage_tracking_service import SQLiteUsageTrackingService


@pytest.mark.asyncio
async def test_document_answering_records_usage(tmp_path):
    db_path = str(tmp_path / "test_usage.db")
    store = InMemoryDocumentStore()
    embedding_provider = LocalEmbeddingProvider()
    retrieval_service = RetrievalService(embedding_provider)
    answerer = RuleBasedAnswerer()
    usage_tracking_service = SQLiteUsageTrackingService(db_path)

    ingestion_service = DocumentIngestionService(
        store=store,
        embedding_provider=embedding_provider,
    )

    ingestion_result = await ingestion_service.ingest_text(
        filename="guide.txt",
        text="FastAPI is the backend framework used in this project.",
    )

    service = DocumentAnsweringService(
        store=store,
        retrieval_service=retrieval_service,
        answerer=answerer,
        usage_tracking_service=usage_tracking_service,
    )

    response = await service.answer(
        document_id=ingestion_result.document_id,
        question="What backend framework is used?",
    )

    records = usage_tracking_service.list_recent_usage()

    assert "FastAPI" in response.answer
    assert len(records) == 1
    assert records[0].operation == "document_answer"
    assert records[0].provider == "local"
    assert records[0].model_name == "RuleBasedAnswerer"
    assert records[0].input_tokens > 0
    assert records[0].output_tokens > 0
    assert records[0].estimated_cost_usd == 0.0
    assert records[0].metadata == {
        "document_id": ingestion_result.document_id,
    }

    