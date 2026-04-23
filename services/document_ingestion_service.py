from models.document_qa import DocumentUploadResponse
from services.chunking import chunk_text
from services.document_store import InMemoryDocumentStore
from services.exceptions import AppServiceError
from providers.embedding_provider import LocalEmbeddingProvider

class DocumentIngestionService:
    def __init__(
        self,
        store: InMemoryDocumentStore,
        embedding_provider: LocalEmbeddingProvider,
    ):
        self.store = store
        self.embedding_provider = embedding_provider

    async def ingest_text(self, filename: str, text: str) -> DocumentUploadResponse:
        normalized_filename = filename.strip() or "uploaded.txt"
        normalized_text = text.strip()

        if not normalized_text:
            raise AppServiceError("Uploaded document is empty.")

        chunk_texts = chunk_text(normalized_text)

        chunk_payloads = [
            {
                "text": chunk_text_value,
                "embedding": self.embedding_provider.embed_document(chunk_text_value),
            }
            for chunk_text_value in chunk_texts
        ]

        stored_document = self.store.save_document(
            filename=normalized_filename,
            text=normalized_text,
            chunk_payloads=chunk_payloads,
        )

        return DocumentUploadResponse(
            document_id=stored_document.document_id,
            filename=stored_document.filename,
            chunk_count=len(stored_document.chunks),
        )