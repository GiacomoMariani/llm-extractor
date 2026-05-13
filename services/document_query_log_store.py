import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, UTC
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class DocumentQueryLog:
    query_id: str
    document_id: str
    question: str
    answer: str
    citation_count: int
    latency_ms: float
    was_fallback: bool
    created_at: str


class SQLiteDocumentQueryLogStore:
    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path
        self._initialize()

    def _initialize(self) -> None:
        Path(self.db_path).touch(exist_ok=True)

        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS document_query_logs
                (
                    query_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    citation_count INTEGER NOT NULL,
                    latency_ms REAL NOT NULL,
                    was_fallback INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            connection.commit()

    def record_query(
        self,
        *,
        document_id: str,
        question: str,
        answer: str,
        citation_count: int,
        latency_ms: float,
        was_fallback: bool,
    ) -> DocumentQueryLog:
        query_id = f"query-{uuid4().hex[:12]}"
        created_at = datetime.now(UTC).isoformat()

        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO document_query_logs (
                    query_id,
                    document_id,
                    question,
                    answer,
                    citation_count,
                    latency_ms,
                    was_fallback,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    query_id,
                    document_id,
                    question,
                    answer,
                    citation_count,
                    latency_ms,
                    int(was_fallback),
                    created_at,
                ),
            )

            connection.commit()

        return DocumentQueryLog(
            query_id=query_id,
            document_id=document_id,
            question=question,
            answer=answer,
            citation_count=citation_count,
            latency_ms=latency_ms,
            was_fallback=was_fallback,
            created_at=created_at,
        )

    def list_recent(self, limit: int = 50) -> list[DocumentQueryLog]:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT query_id,
                       document_id,
                       question,
                       answer,
                       citation_count,
                       latency_ms,
                       was_fallback,
                       created_at
                FROM document_query_logs
                ORDER BY rowid DESC
                LIMIT ?
                """,
                (limit,),
            )

            rows = cursor.fetchall()

        return [
            DocumentQueryLog(
                query_id=query_id,
                document_id=document_id,
                question=question,
                answer=answer,
                citation_count=citation_count,
                latency_ms=latency_ms,
                was_fallback=bool(was_fallback),
                created_at=created_at,
            )
            for (
                query_id,
                document_id,
                question,
                answer,
                citation_count,
                latency_ms,
                was_fallback,
                created_at,
            ) in rows
        ]

    def clear(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM document_query_logs")
            connection.commit()


sqlite_document_query_log_store = SQLiteDocumentQueryLogStore(
    db_path=os.getenv("APP_DB_PATH", "app.db")
)