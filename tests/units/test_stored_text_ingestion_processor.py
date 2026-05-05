from types import SimpleNamespace

import pytest

from models.ingestion_queue_model import StoredTextUploadIngestionPayload
from services.document_ingestion_worker import DocumentIngestionWorker
from services.ingestion_job_store import SQLiteIngestionJobStore
from services.stored_text_ingestion_processor import (
    process_stored_text_upload_payload_safely,
)
from services.uploaded_text_store import SQLiteUploadedTextStore


class SuccessfulIngestionService:
    async def ingest_text(self, filename: str, text: str):
        return SimpleNamespace(
            document_id="doc-123",
            filename=filename,
            chunk_count=2,
        )


@pytest.mark.asyncio
async def test_process_stored_text_upload_payload_loads_text_and_completes_job(
    tmp_path,
):
    job_store = SQLiteIngestionJobStore(tmp_path / "jobs.db")
    text_store = SQLiteUploadedTextStore(tmp_path / "uploaded_texts.db")

    worker = DocumentIngestionWorker(
        ingestion_service=SuccessfulIngestionService(),
        job_store=job_store,
    )

    queued_job = worker.create_text_upload_job("guide.txt")

    content_id = text_store.save_text(
        filename="guide.txt",
        text="FastAPI is the backend framework.",
    )

    await process_stored_text_upload_payload_safely(
        worker=worker,
        text_store=text_store,
        payload=StoredTextUploadIngestionPayload(
            job_id=queued_job.job_id,
            filename="guide.txt",
            content_id=content_id,
        ),
    )

    stored_job = job_store.get_job(queued_job.job_id)

    assert stored_job is not None
    assert stored_job.status == "completed"
    assert stored_job.document_id == "doc-123"
    assert stored_job.chunk_count == 2
    assert stored_job.error_message is None
    assert text_store.get_text(content_id) is None


@pytest.mark.asyncio
async def test_process_stored_text_upload_payload_marks_job_failed_when_content_missing(
    tmp_path,
):
    job_store = SQLiteIngestionJobStore(tmp_path / "jobs.db")
    text_store = SQLiteUploadedTextStore(tmp_path / "uploaded_texts.db")

    worker = DocumentIngestionWorker(
        ingestion_service=SuccessfulIngestionService(),
        job_store=job_store,
    )

    queued_job = worker.create_text_upload_job("guide.txt")

    await process_stored_text_upload_payload_safely(
        worker=worker,
        text_store=text_store,
        payload=StoredTextUploadIngestionPayload(
            job_id=queued_job.job_id,
            filename="guide.txt",
            content_id="missing-content-id",
        ),
    )

    stored_job = job_store.get_job(queued_job.job_id)

    assert stored_job is not None
    assert stored_job.status == "failed"
    assert stored_job.error_message == "Uploaded text content could not be found."


class FailingIngestionService:
    async def ingest_text(self, filename: str, text: str):
        raise RuntimeError("ingestion failed")

@pytest.mark.asyncio
async def test_process_stored_text_upload_payload_keeps_text_when_ingestion_fails(
    tmp_path,
):
    job_store = SQLiteIngestionJobStore(tmp_path / "jobs.db")
    text_store = SQLiteUploadedTextStore(tmp_path / "uploaded_texts.db")

    worker = DocumentIngestionWorker(
        ingestion_service=FailingIngestionService(),
        job_store=job_store,
    )

    queued_job = worker.create_text_upload_job("guide.txt")

    content_id = text_store.save_text(
        filename="guide.txt",
        text="FastAPI is the backend framework.",
    )

    await process_stored_text_upload_payload_safely(
        worker=worker,
        text_store=text_store,
        payload=StoredTextUploadIngestionPayload(
            job_id=queued_job.job_id,
            filename="guide.txt",
            content_id=content_id,
        ),
    )

    stored_job = job_store.get_job(queued_job.job_id)

    assert stored_job is not None
    assert stored_job.status == "failed"
    assert stored_job.error_message == "Unexpected document ingestion failure."
    assert text_store.get_text(content_id) == "FastAPI is the backend framework."