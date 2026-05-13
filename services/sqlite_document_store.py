import os
import json
import sqlite3
from pathlib import Path
from uuid import uuid4

from services.document_store import StoredChunk, StoredDocument, StoredDocumentSummary

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
                CREATE TABLE IF NOT EXISTS documents
                (
                    document_id
                    TEXT
                    PRIMARY
                    KEY,
                    filename
                    TEXT
                    NOT
                    NULL,
                    original_text
                    TEXT
                    NOT
                    NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks
                (
                    chunk_id
                    TEXT
                    PRIMARY
                    KEY,
                    document_id
                    TEXT
                    NOT
                    NULL,
                    text
                    TEXT
                    NOT
                    NULL,
                    embedding
                    TEXT
                    NOT
                    NULL,
                    page_number
                    INTEGER,
                    FOREIGN
                    KEY
                (
                    document_id
                ) REFERENCES documents
                (
                    document_id
                )
                    )
                """
            )

            cursor.execute("PRAGMA table_info(chunks)")
            chunk_columns = {row[1] for row in cursor.fetchall()}

            if "page_number" not in chunk_columns:
                cursor.execute("ALTER TABLE chunks ADD COLUMN page_number INTEGER")

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
                    INSERT INTO chunks (chunk_id, document_id, text, embedding, page_number)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        chunk_id,
                        document_id,
                        chunk_text,
                        json.dumps(chunk_embedding),
                        chunk_payload.get("page_number"),
                    ),
                )

                chunks.append(
                    StoredChunk(
                        chunk_id=chunk_id,
                        text=chunk_text,
                        embedding=chunk_embedding,
                        page_number=chunk_payload.get("page_number"),
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
                SELECT chunk_id, text, embedding, page_number
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
                page_number=page_number,
            )
            for chunk_id, text, embedding, page_number in chunk_rows
        ]

        return StoredDocument(
            document_id=document_row[0],
            filename=document_row[1],
            original_text=document_row[2],
            chunks=chunks,
        )

    def list_documents(self) -> list[StoredDocumentSummary]:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT documents.document_id,
                       documents.filename,
                       COUNT(chunks.chunk_id) AS chunk_count
                FROM documents
                         LEFT JOIN chunks
                                   ON chunks.document_id = documents.document_id
                GROUP BY documents.document_id, documents.filename
                ORDER BY documents.rowid
                """
            )

            rows = cursor.fetchall()

        return [
            StoredDocumentSummary(
                document_id=document_id,
                filename=filename,
                chunk_count=chunk_count,
            )
            for document_id, filename, chunk_count in rows
        ]

    def delete_document(self, document_id: str) -> bool:
        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()

            cursor.execute(
                "SELECT 1 FROM documents WHERE document_id = ?",
                (document_id,),
            )

            if cursor.fetchone() is None:
                return False

            cursor.execute(
                "DELETE FROM chunks WHERE document_id = ?",
                (document_id,),
            )
            cursor.execute(
                "DELETE FROM documents WHERE document_id = ?",
                (document_id,),
            )

            connection.commit()

        return True

    def replace_document_chunks(
            self,
            document_id: str,
            chunk_payloads: list[dict[str, object]],
    ) -> StoredDocument | None:
        chunks: list[StoredChunk] = []

        with sqlite3.connect(self.db_path) as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT filename, original_text
                FROM documents
                WHERE document_id = ?
                """,
                (document_id,),
            )

            document_row = cursor.fetchone()

            if document_row is None:
                return None

            filename = document_row[0]
            original_text = document_row[1]

            cursor.execute(
                """
                DELETE
                FROM chunks
                WHERE document_id = ?
                """,
                (document_id,),
            )

            for index, chunk_payload in enumerate(chunk_payloads, start=1):
                chunk_id = f"{document_id}-chunk-{index}"
                chunk_text = chunk_payload["text"]
                chunk_embedding = chunk_payload["embedding"]
                page_number = chunk_payload.get("page_number")

                cursor.execute(
                    """
                    INSERT INTO chunks (chunk_id,
                                        document_id,
                                        text,
                                        embedding,
                                        page_number)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        chunk_id,
                        document_id,
                        chunk_text,
                        json.dumps(chunk_embedding),
                        page_number,
                    ),
                )

                chunks.append(
                    StoredChunk(
                        chunk_id=chunk_id,
                        text=chunk_text,
                        embedding=chunk_embedding,
                        page_number=page_number,
                    )
                )

            connection.commit()

        return StoredDocument(
            document_id=document_id,
            filename=filename,
            original_text=original_text,
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