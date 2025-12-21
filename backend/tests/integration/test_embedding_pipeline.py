"""
Integration tests for embedding pipeline
"""
import pytest
from unittest.mock import Mock, patch
from src.embeddings.embedding_generator import EmbeddingGenerator, EmbeddingStorageManager
from src.models.extracted_content import ExtractedContent, EmbeddingVector


class TestEmbeddingPipeline:
    """Integration tests for the embedding generation pipeline"""

    @patch('cohere.Client')
    def test_embedding_generation_and_storage_integration(self, mock_cohere):
        """Test that embedding generation works with storage"""
        # Mock the Cohere client response
        mock_client = Mock()
        mock_client.embed.return_value = Mock(embeddings=[[0.1, 0.2, 0.3, 0.4]])
        mock_cohere.return_value = mock_client

        # Create test content
        content = ExtractedContent(
            url="https://example.com/test",
            title="Test Page",
            content="This is test content for embedding integration testing.",
            module="Test Module",
            section="Test Section"
        )

        # Test embedding generator
        generator = EmbeddingGenerator()
        embedding_vectors = generator.batch_generate_with_validation([content], batch_size=1)

        # Should have generated embeddings
        assert len(embedding_vectors) == 1
        assert isinstance(embedding_vectors[0], EmbeddingVector)

        # Test storage manager (mock Qdrant)
        storage_manager = EmbeddingStorageManager()
        # For now, just test that the method exists and can be called
        result = storage_manager.store_with_deduplication(embedding_vectors, batch_size=1)

        # Result should be a dict with status information
        assert isinstance(result, dict)