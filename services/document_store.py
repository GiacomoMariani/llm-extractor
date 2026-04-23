from dataclasses import dataclass, field
from uuid import uuid4


@dataclass(frozen=True)
class StoredChunk:
    chunk_id: str
    text: str
    embedding: list[float]


@dataclass(frozen=True)
class StoredDocument:
    document_id: str
    filename: str
    original_text: str
    chunks: list[StoredChunk] = field(default_factory=list)


class InMemoryDocumentStore:
    def __init__(self):
        self._documents: dict[str, StoredDocument] = {}

    def save_document(
            self,
            filename: str,
            text: str,
            chunk_payloads: list[dict[str, object]],
    ) -> StoredDocument:
        document_id = f"doc-{uuid4().hex[:12]}"

        chunks = [
            StoredChunk(
                chunk_id=f"{document_id}-chunk-{index + 1}",
                text=chunk_payload["text"],
                embedding=chunk_payload["embedding"],
            )
            for index, chunk_payload in enumerate(chunk_payloads)
        ]

        stored_document = StoredDocument(
            document_id=document_id,
            filename=filename,
            original_text=text,
            chunks=chunks,
        )

        self._documents[document_id] = stored_document
        return stored_document

    def get_document(self, document_id: str) -> StoredDocument | None:
        return self._documents.get(document_id)

    def clear(self) -> None:
        self._documents.clear()


document_store = InMemoryDocumentStore()