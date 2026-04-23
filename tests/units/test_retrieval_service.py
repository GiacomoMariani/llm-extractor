from providers.embedding_provider import LocalEmbeddingProvider
from services.document_store import StoredChunk
from services.retrieval_service import RetrievalService


def test_retrieval_returns_top_k_chunks():
    provider = LocalEmbeddingProvider()
    retrieval_service = RetrievalService(provider)

    chunks = [
        StoredChunk(
            chunk_id="chunk-1",
            text="FastAPI is the backend framework used in this project.",
            embedding=provider.embed_document("FastAPI is the backend framework used in this project."),
        ),
        StoredChunk(
            chunk_id="chunk-2",
            text="Pytest is used for testing.",
            embedding=provider.embed_document("Pytest is used for testing."),
        ),
        StoredChunk(
            chunk_id="chunk-3",
            text="Docker has not been added yet.",
            embedding=provider.embed_document("Docker has not been added yet."),
        ),
    ]

    results = retrieval_service.retrieve(
        question="What backend framework is used?",
        chunks=chunks,
        top_k=2,
    )

    assert len(results) == 2
    assert results[0].chunk_id == "chunk-1"