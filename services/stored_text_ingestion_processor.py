from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from models.ingestion_queue_model import StoredTextUploadIngestionPayload

if TYPE_CHECKING:
    from services.document_ingestion_worker import DocumentIngestionWorker
    from services.uploaded_text_store import UploadedTextStore


logger = logging.getLogger(__name__)


async def process_stored_text_upload_payload_safely(
    worker: DocumentIngestionWorker,
    text_store: UploadedTextStore,
    payload: StoredTextUploadIngestionPayload,
) -> None:
    text = text_store.get_text(payload.content_id)

    if text is None:
        worker.job_store.mark_failed(
            job_id=payload.job_id,
            error_message="Uploaded text content could not be found.",
        )

        logger.warning(
            "Stored document ingestion content missing job_id=%s content_id=%s",
            payload.job_id,
            payload.content_id,
        )

        return

    await worker.process_existing_text_upload_job_safely(
        job_id=payload.job_id,
        filename=payload.filename,
        text=text,
    )

    stored_job = worker.job_store.get_job(payload.job_id)

    if stored_job is not None and stored_job.status == "completed":
        deleted = text_store.delete_text(payload.content_id)

        if not deleted:
            logger.warning(
                "Stored document ingestion cleanup missed job_id=%s content_id=%s",
                payload.job_id,
                payload.content_id,
            )