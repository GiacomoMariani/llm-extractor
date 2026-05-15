import re

from models.document_qa import DocumentUploadResponse
from providers.embedding_provider import LocalEmbeddingProvider
from services.chunking import chunk_text
from services.document_store import InMemoryDocumentStore, StoredDocument
from services.exceptions import AppServiceError
from services.usage_tracking_service import SQLiteUsageTrackingService


class DocumentIngestionService:
    def __init__(
        self,
        store: InMemoryDocumentStore,
        embedding_provider: LocalEmbeddingProvider,
        usage_tracking_service: SQLiteUsageTrackingService | None = None,
    ):
        self.store = store
        self.embedding_provider = embedding_provider
        self.usage_tracking_service = usage_tracking_service

    async def ingest_text(
        self,
        filename: str,
        text: str,
        is_demo: bool = False,
    ) -> DocumentUploadResponse:
        normalized_filename = filename.strip() or "uploaded.txt"
        normalized_text = text.strip()

        if not normalized_text:
            raise AppServiceError("Uploaded document is empty.")

        chunk_inputs = self._chunk_text_with_page_numbers(normalized_text)

        chunk_payloads = [
            {
                "text": chunk_input["text"],
                "embedding": self.embedding_provider.embed_document(
                    chunk_input["text"]
                ),
                "page_number": chunk_input["page_number"],
            }
            for chunk_input in chunk_inputs
        ]

        stored_document = self.store.save_document(
            filename=normalized_filename,
            text=normalized_text,
            chunk_payloads=chunk_payloads,
            is_demo=is_demo,
        )

        if self.usage_tracking_service is not None:
            for stored_chunk in stored_document.chunks:
                self.usage_tracking_service.record_usage(
                    operation="document_embedding",
                    provider="local",
                    model_name=self.embedding_provider.__class__.__name__,
                    input_text=stored_chunk.text,
                    output_text="",
                    metadata={
                        "document_id": stored_document.document_id,
                        "filename": stored_document.filename,
                    },
                )

        return DocumentUploadResponse(
            document_id=stored_document.document_id,
            filename=stored_document.filename,
            chunk_count=len(stored_document.chunks),
        )

    async def reindex_document(self, document_id: str) -> StoredDocument | None:
        stored_document = self.store.get_document(document_id)

        if stored_document is None:
            return None

        chunk_inputs = self._chunk_text_with_page_numbers(
            stored_document.original_text
        )

        chunk_payloads = [
            {
                "text": chunk_input["text"],
                "embedding": self.embedding_provider.embed_document(
                    chunk_input["text"]
                ),
                "page_number": chunk_input["page_number"],
            }
            for chunk_input in chunk_inputs
        ]

        return self.store.replace_document_chunks(
            document_id=document_id,
            chunk_payloads=chunk_payloads,
        )

    def _chunk_text_with_page_numbers(self, text: str) -> list[dict[str, object]]:
        page_markers = list(re.finditer(r"\[Page\s+(\d+)\]\s*", text))

        if not page_markers:
            return [
                {
                    "text": chunk,
                    "page_number": None,
                }
                for chunk in chunk_text(text)
            ]

        chunk_inputs: list[dict[str, object]] = []

        for index, marker in enumerate(page_markers):
            page_number = int(marker.group(1))
            page_start = marker.end()
            page_end = (
                page_markers[index + 1].start()
                if index + 1 < len(page_markers)
                else len(text)
            )

            page_text = text[page_start:page_end].strip()

            for chunk in chunk_text(page_text):
                chunk_inputs.append(
                    {
                        "text": chunk,
                        "page_number": page_number,
                    }
                )

        return chunk_inputs