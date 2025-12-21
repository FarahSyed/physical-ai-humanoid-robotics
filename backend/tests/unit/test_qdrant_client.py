"""
Unit tests for the Qdrant client module
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.embeddings.qdrant_client import QdrantEmbeddingClient


class TestQdrantClient:
    """Test cases for QdrantEmbeddingClient class"""

    @patch('src.embeddings.qdrant_client.QdrantClient')
    @patch('src.embeddings.qdrant_client.config')
    def test_qdrant_client_initialization(self, mock_config, mock_qdrant_client):
        """Test that QdrantEmbeddingClient initializes correctly"""
        # Set up mock config
        mock_config.qdrant_host = "https://test-qdrant.com"
        mock_config.qdrant_api_key = "test-key"
        mock_config.qdrant_collection_name = "test_collection"

        # Create client
        client = QdrantEmbeddingClient()

        # Verify QdrantClient was initialized with correct parameters
        mock_qdrant_client.assert_called_once_with(
            url="https://test-qdrant.com",
            api_key="test-key",
        )
        assert client.collection_name == "test_collection"

    @patch('src.embeddings.qdrant_client.QdrantClient')
    @patch('src.embeddings.qdrant_client.config')
    @patch('src.embeddings.qdrant_client.logger')
    def test_create_collection_if_not_exists_new_collection(self, mock_logger, mock_config, mock_qdrant_client):
        """Test creating a new collection"""
        # Set up mocks
        mock_config.qdrant_host = "https://test-qdrant.com"
        mock_config.qdrant_api_key = "test-key"
        mock_config.qdrant_collection_name = "test_collection"

        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client

        # Mock the get_collections method to return no existing collections
        mock_collections = Mock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections

        # Create client and call method
        client = QdrantEmbeddingClient()
        result = client.create_collection_if_not_exists(vector_size=1536, distance="Cosine")

        # Verify the collection was created
        assert result is True
        mock_client.create_collection.assert_called_once()
        mock_logger.info.assert_called()

    @patch('src.embeddings.qdrant_client.QdrantClient')
    @patch('src.embeddings.qdrant_client.config')
    @patch('src.embeddings.qdrant_client.logger')
    def test_create_collection_if_not_exists_existing_collection(self, mock_logger, mock_config, mock_qdrant_client):
        """Test that method handles existing collection correctly"""
        # Set up mocks
        mock_config.qdrant_host = "https://test-qdrant.com"
        mock_config.qdrant_api_key = "test-key"
        mock_config.qdrant_collection_name = "test_collection"

        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client

        # Mock the get_collections method to return an existing collection
        mock_collection = Mock()
        mock_collection.name = "test_collection"
        mock_collections = Mock()
        mock_collections.collections = [mock_collection]
        mock_client.get_collections.return_value = mock_collections

        # Create client and call method
        client = QdrantEmbeddingClient()
        result = client.create_collection_if_not_exists()

        # Verify the collection was not created again
        mock_client.create_collection.assert_not_called()
        mock_logger.info.assert_called()

    @patch('src.embeddings.qdrant_client.QdrantClient')
    @patch('src.embeddings.qdrant_client.config')
    @patch('src.embeddings.qdrant_client.logger')
    def test_upsert_embeddings_success(self, mock_logger, mock_config, mock_qdrant_client):
        """Test successful upsert of embeddings"""
        # Set up mocks
        mock_config.qdrant_host = "https://test-qdrant.com"
        mock_config.qdrant_api_key = "test-key"
        mock_config.qdrant_collection_name = "test_collection"

        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.upsert.return_value = Mock()

        # Create client and test data
        client = QdrantEmbeddingClient()
        embeddings = [
            {
                "id": "test_id_1",
                "vector": [0.1, 0.2, 0.3],
                "payload": {"url": "https://example.com", "title": "Test Page"}
            },
            {
                "id": "test_id_2",
                "vector": [0.4, 0.5, 0.6],
                "payload": {"url": "https://example2.com", "title": "Test Page 2"}
            }
        ]

        result = client.upsert_embeddings(embeddings, batch_size=2)

        # Verify the upsert was called
        assert result["status"] == "success"
        assert result["upserted_count"] == 2
        mock_client.upsert.assert_called()
        mock_logger.info.assert_called()

    @patch('src.embeddings.qdrant_client.QdrantClient')
    @patch('src.embeddings.qdrant_client.config')
    @patch('src.embeddings.qdrant_client.logger')
    def test_upsert_embeddings_error(self, mock_logger, mock_config, mock_qdrant_client):
        """Test upsert embeddings handles errors correctly"""
        # Set up mocks
        mock_config.qdrant_host = "https://test-qdrant.com"
        mock_config.qdrant_api_key = "test-key"
        mock_config.qdrant_collection_name = "test_collection"

        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.upsert.side_effect = Exception("Connection error")

        # Create client and test data
        client = QdrantEmbeddingClient()
        embeddings = [
            {
                "id": "test_id_1",
                "vector": [0.1, 0.2, 0.3],
                "payload": {"url": "https://example.com", "title": "Test Page"}
            }
        ]

        result = client.upsert_embeddings(embeddings)

        # Verify error handling
        assert result["status"] == "error"
        mock_logger.error.assert_called()

    @patch('src.embeddings.qdrant_client.QdrantClient')
    @patch('src.embeddings.qdrant_client.config')
    @patch('src.embeddings.qdrant_client.logger')
    def test_search_similar_success(self, mock_logger, mock_config, mock_qdrant_client):
        """Test successful search for similar embeddings"""
        # Set up mocks
        mock_config.qdrant_host = "https://test-qdrant.com"
        mock_config.qdrant_api_key = "test-key"
        mock_config.qdrant_collection_name = "test_collection"

        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client

        # Mock search results
        mock_result = Mock()
        mock_result.id = "result_id"
        mock_result.score = 0.95
        mock_result.payload = {"url": "https://example.com", "title": "Result Page"}
        mock_client.search.return_value = [mock_result]

        # Create client and call search
        client = QdrantEmbeddingClient()
        results = client.search_similar([0.1, 0.2, 0.3], top_k=5)

        # Verify the search was called and results formatted correctly
        mock_client.search.assert_called()
        assert len(results) == 1
        assert results[0]["id"] == "result_id"
        assert results[0]["score"] == 0.95
        assert results[0]["payload"]["url"] == "https://example.com"

    @patch('src.embeddings.qdrant_client.QdrantClient')
    @patch('src.embeddings.qdrant_client.config')
    @patch('src.embeddings.qdrant_client.logger')
    def test_search_similar_with_filters(self, mock_logger, mock_config, mock_qdrant_client):
        """Test search for similar embeddings with filters"""
        # Set up mocks
        mock_config.qdrant_host = "https://test-qdrant.com"
        mock_config.qdrant_api_key = "test-key"
        mock_config.qdrant_collection_name = "test_collection"

        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client

        # Mock search results
        mock_result = Mock()
        mock_result.id = "result_id"
        mock_result.score = 0.95
        mock_result.payload = {"url": "https://example.com", "title": "Result Page"}
        mock_client.search.return_value = [mock_result]

        # Create client and call search with filters
        client = QdrantEmbeddingClient()
        results = client.search_similar([0.1, 0.2, 0.3], top_k=5, filters={"module": "Module 1"})

        # Verify the search was called with proper filter
        mock_client.search.assert_called()
        assert len(results) == 1

    @patch('src.embeddings.qdrant_client.QdrantClient')
    @patch('src.embeddings.qdrant_client.config')
    @patch('src.embeddings.qdrant_client.logger')
    def test_search_similar_error(self, mock_logger, mock_config, mock_qdrant_client):
        """Test search for similar embeddings handles errors correctly"""
        # Set up mocks
        mock_config.qdrant_host = "https://test-qdrant.com"
        mock_config.qdrant_api_key = "test-key"
        mock_config.qdrant_collection_name = "test_collection"

        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.search.side_effect = Exception("Search error")

        # Create client and call search
        client = QdrantEmbeddingClient()
        results = client.search_similar([0.1, 0.2, 0.3])

        # Verify error handling
        assert results == []
        mock_logger.error.assert_called()

    @patch('src.embeddings.qdrant_client.QdrantClient')
    @patch('src.embeddings.qdrant_client.config')
    @patch('src.embeddings.qdrant_client.logger')
    def test_delete_by_payload_success(self, mock_logger, mock_config, mock_qdrant_client):
        """Test successful deletion by payload"""
        # Set up mocks
        mock_config.qdrant_host = "https://test-qdrant.com"
        mock_config.qdrant_api_key = "test-key"
        mock_config.qdrant_collection_name = "test_collection"

        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client

        # Create client and call delete
        client = QdrantEmbeddingClient()
        result = client.delete_by_payload({"url": "https://example.com"})

        # Verify the delete was called
        mock_client.delete.assert_called()
        assert result is True
        mock_logger.info.assert_called()

    @patch('src.embeddings.qdrant_client.QdrantClient')
    @patch('src.embeddings.qdrant_client.config')
    @patch('src.embeddings.qdrant_client.logger')
    def test_delete_by_payload_error(self, mock_logger, mock_config, mock_qdrant_client):
        """Test deletion by payload handles errors correctly"""
        # Set up mocks
        mock_config.qdrant_host = "https://test-qdrant.com"
        mock_config.qdrant_api_key = "test-key"
        mock_config.qdrant_collection_name = "test_collection"

        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.delete.side_effect = Exception("Delete error")

        # Create client and call delete
        client = QdrantEmbeddingClient()
        result = client.delete_by_payload({"url": "https://example.com"})

        # Verify error handling
        assert result is False
        mock_logger.error.assert_called()

    @patch('src.embeddings.qdrant_client.QdrantClient')
    @patch('src.embeddings.qdrant_client.config')
    @patch('src.embeddings.qdrant_client.logger')
    def test_get_collection_info_success(self, mock_logger, mock_config, mock_qdrant_client):
        """Test successful retrieval of collection info"""
        # Set up mocks
        mock_config.qdrant_host = "https://test-qdrant.com"
        mock_config.qdrant_api_key = "test-key"
        mock_config.qdrant_collection_name = "test_collection"

        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client

        # Mock collection info
        mock_collection_info = Mock()
        mock_collection_info.config.params.vectors.size = 1536
        mock_collection_info.config.params.vectors.distance = "Cosine"
        mock_collection_info.points_count = 100
        mock_collection_info.config.dict.return_value = {"param": "value"}
        mock_client.get_collection.return_value = mock_collection_info

        # Create client and get info
        client = QdrantEmbeddingClient()
        info = client.get_collection_info()

        # Verify the info was retrieved and formatted correctly
        mock_client.get_collection.assert_called()
        assert info["vector_size"] == 1536
        assert info["distance"] == "Cosine"
        assert info["point_count"] == 100

    @patch('src.embeddings.qdrant_client.QdrantClient')
    @patch('src.embeddings.qdrant_client.config')
    @patch('src.embeddings.qdrant_client.logger')
    def test_get_collection_info_error(self, mock_logger, mock_config, mock_qdrant_client):
        """Test collection info retrieval handles errors correctly"""
        # Set up mocks
        mock_config.qdrant_host = "https://test-qdrant.com"
        mock_config.qdrant_api_key = "test-key"
        mock_config.qdrant_collection_name = "test_collection"

        mock_client = Mock()
        mock_qdrant_client.return_value = mock_client
        mock_client.get_collection.side_effect = Exception("Info error")

        # Create client and get info
        client = QdrantEmbeddingClient()
        info = client.get_collection_info()

        # Verify error handling
        assert "error" in info
        mock_logger.error.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])