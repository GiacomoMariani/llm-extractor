from providers.embedding_provider import LocalEmbeddingProvider
from services.document_store import StoredChunk


class RetrievalService:
    def __init__(self, embedding_provider: LocalEmbeddingProvider):
        self.embedding_provider = embedding_provider

    def retrieve(
        self,
        question: str,
        chunks: list[StoredChunk],
        top_k: int = 3,
    ) -> list[StoredChunk]:
        if not chunks:
            return []

        query_embedding = self.embedding_provider.embed_query(question)

        scored_chunks: list[tuple[float, StoredChunk]] = []

        for chunk in chunks:
            score = self._dot_product(query_embedding, chunk.embedding)
            scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda item: item[0], reverse=True)

        return [chunk for _, chunk in scored_chunks[:top_k]]

    def _dot_product(
        self,
        left: list[float],
        right: list[float],
    ) -> float:
        return sum(left_value * right_value for left_value, right_value in zip(left, right))