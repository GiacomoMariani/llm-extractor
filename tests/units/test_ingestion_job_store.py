from services.ingestion_job_store import SQLiteIngestionJobStore


def test_create_job_stores_queued_job(tmp_path):
    store = SQLiteIngestionJobStore(str(tmp_path / "test_jobs.db"))

    job = store.create_job("guide.txt")

    assert job.job_id.startswith("job-")
    assert job.filename == "guide.txt"
    assert job.status == "queued"
    assert job.document_id is None
    assert job.chunk_count is None
    assert job.error_message is None
    assert job.created_at
    assert job.updated_at

    stored_job = store.get_job(job.job_id)

    assert stored_job == job


def test_create_job_normalizes_empty_filename(tmp_path):
    store = SQLiteIngestionJobStore(str(tmp_path / "test_jobs.db"))

    job = store.create_job("   ")

    assert job.filename == "uploaded.txt"


def test_mark_processing_updates_job_status(tmp_path):
    store = SQLiteIngestionJobStore(str(tmp_path / "test_jobs.db"))

    job = store.create_job("guide.txt")
    updated_job = store.mark_processing(job.job_id)

    assert updated_job is not None
    assert updated_job.job_id == job.job_id
    assert updated_job.status == "processing"
    assert updated_job.document_id is None
    assert updated_job.chunk_count is None
    assert updated_job.error_message is None


def test_mark_completed_updates_job_with_document_metadata(tmp_path):
    store = SQLiteIngestionJobStore(str(tmp_path / "test_jobs.db"))

    job = store.create_job("guide.txt")
    updated_job = store.mark_completed(
        job_id=job.job_id,
        document_id="doc-123",
        chunk_count=4,
    )

    assert updated_job is not None
    assert updated_job.job_id == job.job_id
    assert updated_job.status == "completed"
    assert updated_job.document_id == "doc-123"
    assert updated_job.chunk_count == 4
    assert updated_job.error_message is None


def test_mark_failed_updates_job_with_error_message(tmp_path):
    store = SQLiteIngestionJobStore(str(tmp_path / "test_jobs.db"))

    job = store.create_job("guide.txt")
    updated_job = store.mark_failed(
        job_id=job.job_id,
        error_message="Embedding failed.",
    )

    assert updated_job is not None
    assert updated_job.job_id == job.job_id
    assert updated_job.status == "failed"
    assert updated_job.document_id is None
    assert updated_job.chunk_count is None
    assert updated_job.error_message == "Embedding failed."


def test_get_job_returns_none_for_unknown_job(tmp_path):
    store = SQLiteIngestionJobStore(str(tmp_path / "test_jobs.db"))

    job = store.get_job("job-missing")

    assert job is None


def test_status_update_returns_none_for_unknown_job(tmp_path):
    store = SQLiteIngestionJobStore(str(tmp_path / "test_jobs.db"))

    updated_job = store.mark_processing("job-missing")

    assert updated_job is None


def test_clear_removes_jobs(tmp_path):
    store = SQLiteIngestionJobStore(str(tmp_path / "test_jobs.db"))

    job = store.create_job("guide.txt")

    store.clear()

    assert store.get_job(job.job_id) is None