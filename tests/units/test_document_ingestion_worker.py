import sqlite3
from types import SimpleNamespace

import pytest

from services.document_ingestion_worker import DocumentIngestionWorker
from services.exceptions import AppServiceError
from services.ingestion_job_store import SQLiteIngestionJobStore


class SuccessfulIngestionService:
    async def ingest_text(self, filename: str, text: str):
        return SimpleNamespace(
            document_id="doc-123",
            filename=filename,
            chunk_count=2,
        )


class FailingIngestionService:
    async def ingest_text(self, filename: str, text: str):
        raise AppServiceError("Uploaded document is empty.")


class UnexpectedFailingIngestionService:
    async def ingest_text(self, filename: str, text: str):
        raise RuntimeError("Embedding provider crashed.")


@pytest.mark.asyncio
async def test_worker_creates_queued_job(tmp_path):
    db_path = str(tmp_path / "test_jobs.db")
    job_store = SQLiteIngestionJobStore(db_path)
    worker = DocumentIngestionWorker(
        ingestion_service=SuccessfulIngestionService(),
        job_store=job_store,
    )

    job = worker.create_text_upload_job("guide.txt")

    assert job.job_id.startswith("job-")
    assert job.filename == "guide.txt"
    assert job.status == "queued"
    assert job.document_id is None
    assert job.chunk_count is None
    assert job.error_message is None


@pytest.mark.asyncio
async def test_worker_creates_completed_job(tmp_path):
    db_path = str(tmp_path / "test_jobs.db")
    job_store = SQLiteIngestionJobStore(db_path)
    worker = DocumentIngestionWorker(
        ingestion_service=SuccessfulIngestionService(),
        job_store=job_store,
    )

    job = await worker.process_text_upload(
        filename="guide.txt",
        text="FastAPI is the backend framework.",
    )

    assert job.job_id.startswith("job-")
    assert job.filename == "guide.txt"
    assert job.status == "completed"
    assert job.document_id == "doc-123"
    assert job.chunk_count == 2
    assert job.error_message is None

    stored_job = job_store.get_job(job.job_id)

    assert stored_job == job


@pytest.mark.asyncio
async def test_worker_processes_existing_queued_job(tmp_path):
    db_path = str(tmp_path / "test_jobs.db")
    job_store = SQLiteIngestionJobStore(db_path)
    worker = DocumentIngestionWorker(
        ingestion_service=SuccessfulIngestionService(),
        job_store=job_store,
    )

    queued_job = worker.create_text_upload_job("guide.txt")

    completed_job = await worker.process_existing_text_upload_job(
        job_id=queued_job.job_id,
        filename="guide.txt",
        text="FastAPI is the backend framework.",
    )

    assert completed_job.job_id == queued_job.job_id
    assert completed_job.status == "completed"
    assert completed_job.document_id == "doc-123"
    assert completed_job.chunk_count == 2
    assert completed_job.error_message is None


@pytest.mark.asyncio
async def test_worker_marks_job_failed_when_ingestion_service_fails(tmp_path):
    db_path = str(tmp_path / "test_jobs.db")
    job_store = SQLiteIngestionJobStore(db_path)
    worker = DocumentIngestionWorker(
        ingestion_service=FailingIngestionService(),
        job_store=job_store,
    )

    with pytest.raises(AppServiceError, match="Uploaded document is empty."):
        await worker.process_text_upload(
            filename="empty.txt",
            text="   ",
        )

    stored_jobs = _get_all_jobs(db_path, job_store)

    assert len(stored_jobs) == 1
    assert stored_jobs[0].status == "failed"
    assert stored_jobs[0].error_message == "Uploaded document is empty."


@pytest.mark.asyncio
async def test_worker_safely_processes_failed_background_job(tmp_path):
    db_path = str(tmp_path / "test_jobs.db")
    job_store = SQLiteIngestionJobStore(db_path)
    worker = DocumentIngestionWorker(
        ingestion_service=FailingIngestionService(),
        job_store=job_store,
    )

    queued_job = worker.create_text_upload_job("empty.txt")

    await worker.process_existing_text_upload_job_safely(
        job_id=queued_job.job_id,
        filename="empty.txt",
        text="   ",
    )

    stored_job = job_store.get_job(queued_job.job_id)

    assert stored_job is not None
    assert stored_job.status == "failed"
    assert stored_job.error_message == "Uploaded document is empty."


@pytest.mark.asyncio
async def test_worker_converts_unexpected_exception_to_service_error(tmp_path):
    db_path = str(tmp_path / "test_jobs.db")
    job_store = SQLiteIngestionJobStore(db_path)
    worker = DocumentIngestionWorker(
        ingestion_service=UnexpectedFailingIngestionService(),
        job_store=job_store,
    )

    with pytest.raises(AppServiceError, match="Unexpected document ingestion failure."):
        await worker.process_text_upload(
            filename="guide.txt",
            text="FastAPI is the backend framework.",
        )

    stored_jobs = _get_all_jobs(db_path, job_store)

    assert len(stored_jobs) == 1
    assert stored_jobs[0].status == "failed"
    assert stored_jobs[0].error_message == "Unexpected document ingestion failure."


def _get_all_jobs(db_path: str, job_store: SQLiteIngestionJobStore):
    with sqlite3.connect(db_path) as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                job_id,
                filename,
                status,
                document_id,
                chunk_count,
                error_message,
                created_at,
                updated_at
            FROM ingestion_jobs
            ORDER BY created_at
            """
        )

        rows = cursor.fetchall()

    return [job_store._row_to_job(row) for row in rows]