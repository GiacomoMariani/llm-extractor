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

@dataclass(frozen=True)
class DocumentQueryRetrievedSourceLog:
    source_id: str
    query_id: str
    chunk_id: str
    filename: str
    snippet: str
    page_number: int | None
    vector_score: float
    keyword_score: float
    hybrid_score: float


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
                    query_id
                    TEXT
                    PRIMARY
                    KEY,
                    document_id
                    TEXT
                    NOT
                    NULL,
                    question
                    TEXT
                    NOT
                    NULL,
                    answer
                    TEXT
                    NOT
                    NULL,
                    citation_count
                    INTEGER
                    NOT
                    NULL,
                    latency_ms
                    REAL
                    NOT
                    NULL,
                    was_fallback
                    INTEGER
                    NOT
                    NULL,
                    created_at
                    TEXT
                    NOT
                    NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS document_query_retrieved_sources
                (
                    source_id
                    TEXT
                    PRIMARY
                    KEY,
                    query_id
                    TEXT
                    NOT
                    NULL,
                    chunk_id
                    TEXT
                    NOT
                    NULL,
                    filename
                    TEXT
                    NOT
                    NULL,
                    snippet
                    TEXT
                    NOT
                    NULL,
                    page_number
                    INTEGER,
                    vector_score
                    REAL
                    NOT
                    NULL,
                    keyword_score
                    REAL
                    NOT
                    NULL,
                    hybrid_score
                    REAL
                    NOT
                    NULL,
                    FOREIGN
                    KEY
                (
                    query_id
                ) REFERENCES document_query_logs
                (
                    query_id
                )
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

    def record_retrieved_sources(
            self,
            *,
            query_id: str,
            sources: list[dict[str, object]],
    ) -> list[DocumentQueryRetrievedSourceLog]:
        logged_sources: list[DocumentQueryRetrievedSourceLog] = []

        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()

            for source in sources:
                source_id = f"source-{uuid4().hex[:12]}"

                logged_source = DocumentQueryRetrievedSourceLog(
                    source_id=source_id,
                    query_id=query_id,
                    chunk_id=str(source["chunk_id"]),
                    filename=str(source["filename"]),
                    snippet=str(source["snippet"]),
                    page_number=source.get("page_number"),
                    vector_score=float(source["vector_score"]),
                    keyword_score=float(source["keyword_score"]),
                    hybrid_score=float(source["hybrid_score"]),
                )

                cursor.execute(
                    """
                    INSERT INTO document_query_retrieved_sources (source_id,
                                                                  query_id,
                                                                  chunk_id,
                                                                  filename,
                                                                  snippet,
                                                                  page_number,
                                                                  vector_score,
                                                                  keyword_score,
                                                                  hybrid_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        logged_source.source_id,
                        logged_source.query_id,
                        logged_source.chunk_id,
                        logged_source.filename,
                        logged_source.snippet,
                        logged_source.page_number,
                        logged_source.vector_score,
                        logged_source.keyword_score,
                        logged_source.hybrid_score,
                    ),
                )

                logged_sources.append(logged_source)

            connection.commit()

        return logged_sources

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

    def list_retrieved_sources_for_query(
            self,
            query_id: str,
    ) -> list[DocumentQueryRetrievedSourceLog]:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT source_id,
                       query_id,
                       chunk_id,
                       filename,
                       snippet,
                       page_number,
                       vector_score,
                       keyword_score,
                       hybrid_score
                FROM document_query_retrieved_sources
                WHERE query_id = ?
                ORDER BY rowid
                """,
                (query_id,),
            )

            rows = cursor.fetchall()

        return [
            DocumentQueryRetrievedSourceLog(
                source_id=source_id,
                query_id=query_id,
                chunk_id=chunk_id,
                filename=filename,
                snippet=snippet,
                page_number=page_number,
                vector_score=vector_score,
                keyword_score=keyword_score,
                hybrid_score=hybrid_score,
            )
            for (
                source_id,
                query_id,
                chunk_id,
                filename,
                snippet,
                page_number,
                vector_score,
                keyword_score,
                hybrid_score,
            ) in rows
        ]

    def clear(self) -> None:
        self._initialize()

        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM document_query_retrieved_sources")
            cursor.execute("DELETE FROM document_query_logs")
            connection.commit()

sqlite_document_query_log_store = SQLiteDocumentQueryLogStore(
    db_path=os.getenv("APP_DB_PATH", "app.db")
)