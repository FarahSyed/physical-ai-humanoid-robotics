"""
Interface and implementations for embedding providers.

This module defines the interface for embedding providers and includes
a concrete implementation for Cohere.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import asyncio
from .config import EmbeddingConfig


class EmbeddingProvider(ABC):
    """
    Abstract interface for embedding providers.

    This interface defines the contract for embedding providers to generate
    vector embeddings for text content.
    """

    @abstractmethod
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to generate embeddings for

        Returns:
            List of embedding vectors (each vector is a list of floats)
        """
        pass

    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Validate the connection to the embedding provider.

        Returns:
            bool: True if the connection is valid, False otherwise
        """
        pass


class CohereEmbeddingProvider(EmbeddingProvider):
    """
    Cohere implementation of the EmbeddingProvider interface.
    """

    def __init__(self, config: EmbeddingConfig):
        """
        Initialize the Cohere embedding provider.

        Args:
            config: Configuration for the embedding provider
        """
        self.config = config
        self._client = None

    def _get_client(self):
        """Lazy load the Cohere client."""
        if self._client is None:
            try:
                import cohere
                self._client = cohere.AsyncClient(self.config.api_key)
            except ImportError:
                raise ImportError(
                    "Cohere package is required for Cohere embedding provider. "
                    "Install it with: pip install cohere"
                )
        return self._client

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings using the Cohere API.

        Args:
            texts: List of text strings to generate embeddings for

        Returns:
            List of embedding vectors (each vector is a list of floats)
        """
        client = self._get_client()

        # Split texts into batches to respect API limits
        all_embeddings = []
        for i in range(0, len(texts), self.config.batch_size):
            batch = texts[i:i + self.config.batch_size]

            try:
                response = await client.embed(
                    texts=batch,
                    model=self.config.model,
                    input_type=self.config.input_type,
                    truncate=self.config.truncate
                )

                # Extract embeddings from the response
                batch_embeddings = [embedding for embedding in response.embeddings]
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                raise RuntimeError(f"Failed to generate embeddings: {str(e)}")

        return all_embeddings

    async def validate_connection(self) -> bool:
        """
        Validate the connection to the Cohere API.

        Returns:
            bool: True if the connection is valid, False otherwise
        """
        try:
            client = self._get_client()
            # Test the connection with a simple embed call
            test_response = await client.embed(
                texts=["test"],
                model=self.config.model,
                input_type=self.config.input_type,
                truncate=self.config.truncate
            )
            return len(test_response.embeddings) > 0
        except Exception:
            return False