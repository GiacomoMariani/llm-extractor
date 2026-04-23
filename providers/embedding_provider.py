from sentence_transformers import SentenceTransformer


class LocalEmbeddingProvider:
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ):
        self.model_name = model_name
        self._model: SentenceTransformer | None = None

    def embed_document(self, text: str) -> list[float]:
        model = self._get_model()
        vector = model.encode_document(
            text,
            normalize_embeddings=True,
        )
        return vector.tolist()

    def embed_query(self, text: str) -> list[float]:
        model = self._get_model()
        vector = model.encode_query(
            text,
            normalize_embeddings=True,
        )
        return vector.tolist()

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model


embedding_provider = LocalEmbeddingProvider()