from services.document_store import InMemoryDocumentStore
from services.sqlite_document_store import SQLiteDocumentStore


def _chunk_payloads_with_pages() -> list[dict[str, object]]:
    return [
        {
            "text": "Page one content.",
            "embedding": [0.1, 0.2, 0.3],
            "page_number": 1,
        },
        {
            "text": "Page three content.",
            "embedding": [0.4, 0.5, 0.6],
            "page_number": 3,
        },
    ]


def _chunk_payloads_without_pages() -> list[dict[str, object]]:
    return [
        {
            "text": "Plain text content.",
            "embedding": [0.1, 0.2, 0.3],
        }
    ]


def test_in_memory_store_records_document_metadata_for_pdf():
    store = InMemoryDocumentStore()

    document = store.save_document(
        filename="handbook.pdf",
        text="Document text",
        chunk_payloads=_chunk_payloads_with_pages(),
    )

    assert document.file_type == "pdf"
    assert document.upload_date
    assert document.status == "indexed"
    assert document.page_count == 3

    summaries = store.list_documents()

    assert len(summaries) == 1

    summary = summaries[0]

    assert summary.document_id == document.document_id
    assert summary.filename == "handbook.pdf"
    assert summary.file_type == "pdf"
    assert summary.upload_date == document.upload_date
    assert summary.status == "indexed"
    assert summary.page_count == 3
    assert summary.chunk_count == 2


def test_in_memory_store_records_null_page_count_for_text_document():
    store = InMemoryDocumentStore()

    document = store.save_document(
        filename="guide.txt",
        text="Document text",
        chunk_payloads=_chunk_payloads_without_pages(),
    )

    assert document.file_type == "txt"
    assert document.page_count is None

    summary = store.list_documents()[0]

    assert summary.file_type == "txt"
    assert summary.page_count is None


def test_sqlite_store_records_document_metadata_for_pdf(tmp_path):
    store = SQLiteDocumentStore(
        db_path=str(tmp_path / "test.db"),
    )

    document = store.save_document(
        filename="handbook.pdf",
        text="Document text",
        chunk_payloads=_chunk_payloads_with_pages(),
    )

    loaded_document = store.get_document(document.document_id)

    assert loaded_document is not None
    assert loaded_document.file_type == "pdf"
    assert loaded_document.upload_date == document.upload_date
    assert loaded_document.status == "indexed"
    assert loaded_document.page_count == 3

    summaries = store.list_documents()

    assert len(summaries) == 1

    summary = summaries[0]

    assert summary.document_id == document.document_id
    assert summary.filename == "handbook.pdf"
    assert summary.file_type == "pdf"
    assert summary.upload_date == document.upload_date
    assert summary.status == "indexed"
    assert summary.page_count == 3
    assert summary.chunk_count == 2


def test_sqlite_store_preserves_metadata_after_reindex(tmp_path):
    store = SQLiteDocumentStore(
        db_path=str(tmp_path / "test.db"),
    )

    document = store.save_document(
        filename="handbook.pdf",
        text="Document text",
        chunk_payloads=_chunk_payloads_with_pages(),
    )

    updated_document = store.replace_document_chunks(
        document_id=document.document_id,
        chunk_payloads=[
            {
                "text": "Updated page two content.",
                "embedding": [0.7, 0.8, 0.9],
                "page_number": 2,
            }
        ],
    )

    assert updated_document is not None
    assert updated_document.document_id == document.document_id
    assert updated_document.filename == "handbook.pdf"
    assert updated_document.file_type == "pdf"
    assert updated_document.upload_date == document.upload_date
    assert updated_document.status == "indexed"
    assert updated_document.page_count == 2
    assert len(updated_document.chunks) == 1

    summary = store.list_documents()[0]

    assert summary.page_count == 2
    assert summary.chunk_count == 1