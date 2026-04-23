from models.document_qa import Citation, DocumentAskResponse
from services.document_store import InMemoryDocumentStore
from services.exceptions import NotFoundError
from services.retrieval_service import RetrievalService
from services.rule_based_answerer import RuleBasedAnswerer


class DocumentAnsweringService:
    def __init__(
        self,
        store: InMemoryDocumentStore,
        retrieval_service: RetrievalService,
        answerer: RuleBasedAnswerer,
    ):
        self.store = store
        self.retrieval_service = retrieval_service
        self.answerer = answerer

    async def answer(
        self,
        document_id: str,
        question: str,
        top_k: int = 3,
    ) -> DocumentAskResponse:
        stored_document = self.store.get_document(document_id)

        if stored_document is None:
            raise NotFoundError("Document not found.")

        selected_chunks = self.retrieval_service.retrieve(
            question=question.strip(),
            chunks=stored_document.chunks,
            top_k=top_k,
        )

        combined_context = "\n".join(chunk.text for chunk in selected_chunks)

        answer_response = await self.answerer.answer(
            question.strip(),
            combined_context,
        )

        citations = [
            Citation(
                chunk_id=chunk.chunk_id,
                snippet=self._snippet(chunk.text),
            )
            for chunk in selected_chunks
        ]

        return DocumentAskResponse(
            answer=answer_response.answer,
            citations=citations,
        )

    def _snippet(self, text: str, limit: int = 160) -> str:
        cleaned = " ".join(text.split())

        if len(cleaned) <= limit:
            return cleaned

        return cleaned[:limit].rstrip() + "..."