import asyncio

from sentence_transformers import SentenceTransformer

from orion.memory.interfaces.embeddings import EmbeddingProvider


class SentenceTransformerEmbeddingProvider(EmbeddingProvider):
    """
    Local embedding provider using Sentence Transformers.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-small-en-v1.5",
    ) -> None:
        self._model_name = model_name
        self.model: SentenceTransformer | None = None

    async def startup(self) -> None:
        self.model = await asyncio.to_thread(
            SentenceTransformer,
            self._model_name,
        )

    async def shutdown(self) -> None:
        self.model = None

    async def embed(self, text: str) -> list[float]:
        if self.model is None:
            raise RuntimeError("Embedding provider has not been started.")

        embedding = await asyncio.to_thread(
            self.model.encode, text, normalize_embeddings=True
        )

        return embedding.tolist()

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        if self.model is None:
            raise RuntimeError("Embedding provider has not been started.")

        embeddings = await asyncio.to_thread(
            self.model.encode, texts, normalize_embeddings=True
        )

        return embeddings.tolist()

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        if self.model is None:
            raise RuntimeError("Embedding provider has not been started.")

        dimension = self.model.get_embedding_dimension()

        if dimension is None:
            raise RuntimeError("Embedding dimension is unavailable.")

        return dimension
