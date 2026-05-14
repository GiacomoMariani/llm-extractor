from types import SimpleNamespace

from services.document_query_log_store import SQLiteDocumentQueryLogStore


def test_record_query_stores_explicit_fallback_even_when_citations_exist(tmp_path):
    store = SQLiteDocumentQueryLogStore(
        db_path=str(tmp_path / "test.db"),
    )

    store.record_query(
        document_id="doc-123",
        question="What is the refund policy?",
        answer="I could not find the answer in the provided context.",
        citation_count=1,
        was_fallback=True,
        latency_ms=7.25,
        retrieved_sources=[],
    )

    logs = store.get_recent_logs(limit=10)

    assert len(logs) == 1

    log = logs[0]

    assert log.was_fallback is True
    assert log.citation_count == 1
    assert log.answer == "I could not find the answer in the provided context."


def test_record_query_stores_retrieved_source_debug_data(tmp_path):
    store = SQLiteDocumentQueryLogStore(
        db_path=str(tmp_path / "test.db"),
    )

    source = SimpleNamespace(
        chunk_id="chunk-1",
        filename="handbook.pdf",
        page_number=4,
        snippet="Employees may request support from HR.",
        vector_score=0.7,
        keyword_score=0.6,
        hybrid_score=0.65,
        rank=1,
    )

    store.record_query(
        document_id="doc-456",
        question="Who should employees contact?",
        answer="Employees may request support from HR.",
        citation_count=1,
        was_fallback=False,
        latency_ms=20.0,
        retrieved_sources=[source],
    )

    logs = store.get_recent_logs(limit=10)

    assert len(logs) == 1
    assert logs[0].was_fallback is False
    assert len(logs[0].retrieved_sources) == 1

    retrieved_source = logs[0].retrieved_sources[0]

    assert retrieved_source.chunk_id == "chunk-1"
    assert retrieved_source.filename == "handbook.pdf"
    assert retrieved_source.page_number == 4
    assert retrieved_source.snippet == "Employees may request support from HR."
    assert retrieved_source.vector_score == 0.7
    assert retrieved_source.keyword_score == 0.6
    assert retrieved_source.hybrid_score == 0.65
    assert retrieved_source.rank == 1