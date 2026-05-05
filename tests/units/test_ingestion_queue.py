from fastapi import BackgroundTasks

from models.ingestion_queue_model import (
    StoredTextUploadIngestionPayload,
    TextUploadIngestionPayload,
)
from services.ingestion_queue import FastAPIBackgroundTasksIngestionQueue
from services.stored_text_ingestion_processor import (
    process_stored_text_upload_payload_safely,
)


class DummyWorker:
    def process_existing_text_upload_job_safely(
        self,
        job_id: str,
        filename: str,
        text: str,
    ) -> None:
        pass


class DummyTextStore:
    pass


def test_fastapi_background_tasks_ingestion_queue_schedules_text_upload() -> None:
    background_tasks = BackgroundTasks()
    worker = DummyWorker()

    queue = FastAPIBackgroundTasksIngestionQueue(background_tasks)

    queue.enqueue_text_upload(
        worker=worker,
        payload=TextUploadIngestionPayload(
            job_id="job-123",
            filename="guide.txt",
            text="hello world",
        ),
    )

    assert len(background_tasks.tasks) == 1

    task = background_tasks.tasks[0]
    assert task.func == worker.process_existing_text_upload_job_safely
    assert task.args == ("job-123", "guide.txt", "hello world")


def test_fastapi_background_tasks_ingestion_queue_schedules_stored_text_upload() -> None:
    background_tasks = BackgroundTasks()
    worker = DummyWorker()
    text_store = DummyTextStore()

    payload = StoredTextUploadIngestionPayload(
        job_id="job-123",
        filename="guide.txt",
        content_id="content-456",
    )

    queue = FastAPIBackgroundTasksIngestionQueue(background_tasks)

    queue.enqueue_stored_text_upload(
        worker=worker,
        text_store=text_store,
        payload=payload,
    )

    assert len(background_tasks.tasks) == 1

    task = background_tasks.tasks[0]
    assert task.func == process_stored_text_upload_payload_safely
    assert task.args == (worker, text_store, payload)