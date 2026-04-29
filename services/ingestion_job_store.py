import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class IngestionJob:
    job_id: str
    filename: str
    status: str
    document_id: str | None
    chunk_count: int | None
    error_message: str | None
    created_at: str
    updated_at: str


class SQLiteIngestionJobStore:
    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path
        self._initialize()

    def _initialize(self) -> None:
        Path(self.db_path).touch(exist_ok=True)

        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS ingestion_jobs (
                    job_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    status TEXT NOT NULL,
                    document_id TEXT,
                    chunk_count INTEGER,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

            connection.commit()

    def create_job(self, filename: str) -> IngestionJob:
        now = self._now()
        job_id = f"job-{uuid4().hex[:12]}"
        normalized_filename = filename.strip() or "uploaded.txt"

        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO ingestion_jobs (
                    job_id,
                    filename,
                    status,
                    document_id,
                    chunk_count,
                    error_message,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    normalized_filename,
                    "queued",
                    None,
                    None,
                    None,
                    now,
                    now,
                ),
            )

            connection.commit()

        return IngestionJob(
            job_id=job_id,
            filename=normalized_filename,
            status="queued",
            document_id=None,
            chunk_count=None,
            error_message=None,
            created_at=now,
            updated_at=now,
        )

    def get_job(self, job_id: str) -> IngestionJob | None:
        with sqlite3.connect(self.db_path) as connection:
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
                WHERE job_id = ?
                """,
                (job_id,),
            )

            row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_job(row)

    def mark_processing(self, job_id: str) -> IngestionJob | None:
        return self._update_job(
            job_id=job_id,
            status="processing",
        )

    def mark_completed(
        self,
        job_id: str,
        document_id: str,
        chunk_count: int,
    ) -> IngestionJob | None:
        return self._update_job(
            job_id=job_id,
            status="completed",
            document_id=document_id,
            chunk_count=chunk_count,
            error_message=None,
        )

    def mark_failed(
        self,
        job_id: str,
        error_message: str,
    ) -> IngestionJob | None:
        return self._update_job(
            job_id=job_id,
            status="failed",
            error_message=error_message,
        )

    def clear(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM ingestion_jobs")
            connection.commit()

    def _update_job(
        self,
        job_id: str,
        status: str,
        document_id: str | None = None,
        chunk_count: int | None = None,
        error_message: str | None = None,
    ) -> IngestionJob | None:
        now = self._now()

        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE ingestion_jobs
                SET
                    status = ?,
                    document_id = COALESCE(?, document_id),
                    chunk_count = COALESCE(?, chunk_count),
                    error_message = ?,
                    updated_at = ?
                WHERE job_id = ?
                """,
                (
                    status,
                    document_id,
                    chunk_count,
                    error_message,
                    now,
                    job_id,
                ),
            )

            connection.commit()

        return self.get_job(job_id)

    def _row_to_job(self, row: tuple[object, ...]) -> IngestionJob:
        return IngestionJob(
            job_id=str(row[0]),
            filename=str(row[1]),
            status=str(row[2]),
            document_id=None if row[3] is None else str(row[3]),
            chunk_count=None if row[4] is None else int(row[4]),
            error_message=None if row[5] is None else str(row[5]),
            created_at=str(row[6]),
            updated_at=str(row[7]),
        )

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


sqlite_ingestion_job_store = SQLiteIngestionJobStore(
    db_path=os.getenv("APP_DB_PATH", "app.db")
)