import pytest

from providers.embedding_provider import LocalEmbeddingProvider
from services.document_ingestion_service import DocumentIngestionService
from services.document_store import InMemoryDocumentStore
from services.exceptions import AppServiceError
from services.usage_tracking_service import SQLiteUsageTrackingService


@pytest.mark.asyncio
async def test_document_ingestion_creates_document_and_chunks():
    store = InMemoryDocumentStore()
    embedding_provider = LocalEmbeddingProvider()

    service = DocumentIngestionService(
        store=store,
        embedding_provider=embedding_provider,
    )

    result = await service.ingest_text(
        filename="guide.txt",
        text="FastAPI is the backend framework used in this project.",
    )

    stored_document = store.get_document(result.document_id)

    assert result.document_id.startswith("doc-")
    assert result.filename == "guide.txt"
    assert result.chunk_count >= 1

    assert stored_document is not None
    assert stored_document.document_id == result.document_id
    assert stored_document.filename == "guide.txt"
    assert len(stored_document.chunks) == result.chunk_count
    assert "FastAPI" in stored_document.chunks[0].text
    assert len(stored_document.chunks[0].embedding) > 0


@pytest.mark.asyncio
async def test_document_ingestion_rejects_empty_text():
    store = InMemoryDocumentStore()
    embedding_provider = LocalEmbeddingProvider()

    service = DocumentIngestionService(
        store=store,
        embedding_provider=embedding_provider,
    )

    with pytest.raises(AppServiceError, match="Uploaded document is empty."):
        await service.ingest_text(
            filename="empty.txt",
            text="   ",
        )


@pytest.mark.asyncio
async def test_document_ingestion_records_embedding_usage(tmp_path):
    db_path = str(tmp_path / "test_usage.db")
    store = InMemoryDocumentStore()
    embedding_provider = LocalEmbeddingProvider()
    usage_tracking_service = SQLiteUsageTrackingService(db_path)

    service = DocumentIngestionService(
        store=store,
        embedding_provider=embedding_provider,
        usage_tracking_service=usage_tracking_service,
    )

    result = await service.ingest_text(
        filename="guide.txt",
        text="FastAPI is the backend framework used in this project.",
    )

    records = usage_tracking_service.list_recent_usage()

    assert len(records) == result.chunk_count
    assert records[0].operation == "document_embedding"
    assert records[0].provider == "local"
    assert records[0].model_name == "LocalEmbeddingProvider"
    assert records[0].input_tokens > 0
    assert records[0].output_tokens == 0
    assert records[0].estimated_cost_usd == 0.0
    assert records[0].metadata == {
        "document_id": result.document_id,
        "filename": "guide.txt",
    }