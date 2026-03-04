"""
Cohere embedding client — multilingual-v3.0
Handles both single query embedding and batch document embedding.
"""

import cohere

from app.core.config import settings
from app.core.exceptions import ExternalServiceError

COHERE_EMBED_MODEL = "embed-multilingual-v3.0"
EMBED_DIMENSION = 1024  # fixed for multilingual-v3.0


class CohereEmbeddingClient:
    def __init__(self, api_key: str | None = None):
        self._client = cohere.AsyncClient(api_key or settings.COHERE_API_KEY)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of documents (for seeding). Uses search_document input type."""
        try:
            response = await self._client.embed(
                texts=texts,
                model=COHERE_EMBED_MODEL,
                input_type="search_document",
            )
            return response.embeddings
        except Exception as e:
            raise ExternalServiceError(detail=f"Cohere embedding failed: {str(e)}")

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single search query. Uses search_query input type."""
        try:
            response = await self._client.embed(
                texts=[text],
                model=COHERE_EMBED_MODEL,
                input_type="search_query",
            )
            return response.embeddings[0]
        except Exception as e:
            raise ExternalServiceError(detail=f"Cohere embedding failed: {str(e)}")