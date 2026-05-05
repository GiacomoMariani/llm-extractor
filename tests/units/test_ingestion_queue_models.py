from pydantic import ValidationError

from models.ingestion_queue_model import StoredTextUploadIngestionPayload


def test_stored_text_upload_ingestion_payload_is_serializable() -> None:
    payload = StoredTextUploadIngestionPayload(
        job_id="job-123",
        filename="guide.txt",
        content_id="content-456",
    )

    assert payload.model_dump() == {
        "job_id": "job-123",
        "filename": "guide.txt",
        "content_id": "content-456",
    }


def test_stored_text_upload_ingestion_payload_rejects_empty_content_id() -> None:
    try:
        StoredTextUploadIngestionPayload(
            job_id="job-123",
            filename="guide.txt",
            content_id="",
        )
    except ValidationError:
        return

    raise AssertionError("Expected empty content_id to fail validation")