import os
import json
import sqlite3
from pathlib import Path
from uuid import uuid4

from services.document_store import StoredChunk, StoredDocument


class SQLiteDocumentStore:
    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path
        self._initialize()

    def _initialize(self) -> None:
        Path(self.db_path).touch(exist_ok=True)

        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    original_text TEXT NOT NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    FOREIGN KEY (document_id) REFERENCES documents(document_id)
                )
                """
            )

            connection.commit()

    def save_document(
        self,
        filename: str,
        text: str,
        chunk_payloads: list[dict[str, object]],
    ) -> StoredDocument:
        document_id = f"doc-{uuid4().hex[:12]}"

        chunks: list[StoredChunk] = []

        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO documents (document_id, filename, original_text)
                VALUES (?, ?, ?)
                """,
                (document_id, filename, text),
            )

            for index, chunk_payload in enumerate(chunk_payloads, start=1):
                chunk_id = f"{document_id}-chunk-{index}"
                chunk_text = chunk_payload["text"]
                chunk_embedding = chunk_payload["embedding"]

                cursor.execute(
                    """
                    INSERT INTO chunks (chunk_id, document_id, text, embedding)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        chunk_id,
                        document_id,
                        chunk_text,
                        json.dumps(chunk_embedding),
                    ),
                )

                chunks.append(
                    StoredChunk(
                        chunk_id=chunk_id,
                        text=chunk_text,
                        embedding=chunk_embedding,
                    )
                )

            connection.commit()

        return StoredDocument(
            document_id=document_id,
            filename=filename,
            original_text=text,
            chunks=chunks,
        )

    def get_document(self, document_id: str) -> StoredDocument | None:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT document_id, filename, original_text
                FROM documents
                WHERE document_id = ?
                """,
                (document_id,),
            )
            document_row = cursor.fetchone()

            if document_row is None:
                return None

            cursor.execute(
                """
                SELECT chunk_id, text, embedding
                FROM chunks
                WHERE document_id = ?
                ORDER BY rowid
                """,
                (document_id,),
            )
            chunk_rows = cursor.fetchall()

        chunks = [
            StoredChunk(
                chunk_id=chunk_id,
                text=text,
                embedding=json.loads(embedding),
            )
            for chunk_id, text, embedding in chunk_rows
        ]

        return StoredDocument(
            document_id=document_row[0],
            filename=document_row[1],
            original_text=document_row[2],
            chunks=chunks,
        )

    def clear(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM chunks")
            cursor.execute("DELETE FROM documents")
            connection.commit()

sqlite_document_store = SQLiteDocumentStore(
    db_path=os.getenv("APP_DB_PATH", "app.db")
)