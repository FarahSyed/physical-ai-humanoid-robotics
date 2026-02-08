"""
Unit tests for embedding provider integration.

This module tests the embedding provider integration components
including configuration, provider interface, and batch processing.
"""
import unittest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
from src.embeddings import EmbeddingConfig, EmbeddingProvider, CohereEmbeddingProvider, EmbeddingTask, BatchEmbeddingProcessor
from src.embeddings.config import EmbeddingConfig


class TestEmbeddingConfig(unittest.TestCase):
    """Tests for EmbeddingConfig class."""

    def setUp(self):
        """Set up test fixtures."""
        # Set a mock API key in environment for testing
        import os
        os.environ["COHERE_API_KEY"] = "test-api-key-12345"

    def tearDown(self):
        """Clean up after tests."""
        import os
        if "COHERE_API_KEY" in os.environ:
            del os.environ["COHERE_API_KEY"]

    def test_config_creation_with_defaults(self):
        """Test creating config with default values."""
        config = EmbeddingConfig()
        self.assertEqual(config.provider, "cohere")
        self.assertEqual(config.model, "embed-english-v3.0")
        self.assertEqual(config.input_type, "search_document")
        self.assertEqual(config.batch_size, 100)
        self.assertEqual(config.parallel_workers, 4)

    def test_config_creation_with_custom_values(self):
        """Test creating config with custom values."""
        config = EmbeddingConfig(
            provider="test-provider",
            model="test-model",
            input_type="search_query",
            batch_size=50,
            parallel_workers=2
        )
        self.assertEqual(config.provider, "test-provider")
        self.assertEqual(config.model, "test-model")
        self.assertEqual(config.input_type, "search_query")
        self.assertEqual(config.batch_size, 50)
        self.assertEqual(config.parallel_workers, 2)

    def test_config_hash_generation(self):
        """Test that config hash is generated correctly."""
        config1 = EmbeddingConfig(model="model-a")
        config2 = EmbeddingConfig(model="model-a")
        config3 = EmbeddingConfig(model="model-b")

        hash1 = config1.get_hash()
        hash2 = config2.get_hash()
        hash3 = config3.get_hash()

        # Same configs should have same hash
        self.assertEqual(hash1, hash2)
        # Different configs should have different hashes
        self.assertNotEqual(hash1, hash3)

    def test_config_hash_excludes_api_key(self):
        """Test that config hash doesn't include API key."""
        config1 = EmbeddingConfig(model="test-model", api_key="valid-api-key-12345")
        config2 = EmbeddingConfig(model="test-model", api_key="another-valid-key-67890")

        hash1 = config1.get_hash()
        hash2 = config2.get_hash()

        # Hashes should be the same despite different API keys
        self.assertEqual(hash1, hash2)

    def test_config_hash_validation(self):
        """Test config hash validation."""
        config = EmbeddingConfig(model="test-model")
        original_hash = config.get_hash()

        # Valid hash should return True
        self.assertTrue(config.validate_config_hash(original_hash))

        # Invalid hash should return False
        self.assertFalse(config.validate_config_hash("invalid-hash"))

    def test_config_to_dict_excludes_api_key(self):
        """Test that to_dict excludes API key."""
        config = EmbeddingConfig(api_key="valid-api-key-12345")
        config_dict = config.to_dict()

        # API key should not be in the dict
        self.assertNotIn('api_key', config_dict)
        # Other values should be present
        self.assertIn('model', config_dict)

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            'provider': 'test-provider',
            'model': 'test-model',
            'input_type': 'search_query',
            'batch_size': 50
        }

        # This should raise an error because no API key is provided
        with patch('os.getenv', return_value='test-api-key'):
            config = EmbeddingConfig.from_dict(config_dict)
            self.assertEqual(config.provider, 'test-provider')
            self.assertEqual(config.model, 'test-model')


class TestCohereEmbeddingProvider(unittest.TestCase):
    """Tests for CohereEmbeddingProvider class."""

    def setUp(self):
        """Set up test fixtures."""
        import os
        os.environ["COHERE_API_KEY"] = "test-api-key-12345"
        self.config = EmbeddingConfig()
        self.provider = CohereEmbeddingProvider(self.config)

    def tearDown(self):
        """Clean up after tests."""
        import os
        if "COHERE_API_KEY" in os.environ:
            del os.environ["COHERE_API_KEY"]

    @patch('cohere.AsyncClient')
    def test_get_client(self, mock_client_class):
        """Test that the client is created properly."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        client = self.provider._get_client()
        self.assertIsNotNone(client)

    @patch('cohere.AsyncClient')
    def test_validate_connection_success(self, mock_client_class):
        """Test successful connection validation."""
        mock_client = AsyncMock()
        mock_client.embed = AsyncMock()
        mock_response = Mock()
        mock_response.embeddings = [[0.1, 0.2, 0.3]]
        mock_client.embed.return_value = mock_response
        mock_client_class.return_value = mock_client

        self.provider._client = mock_client

        result = asyncio.run(self.provider.validate_connection())
        self.assertTrue(result)

    @patch('cohere.AsyncClient')
    def test_validate_connection_failure(self, mock_client_class):
        """Test failed connection validation."""
        mock_client = AsyncMock()
        mock_client.embed = AsyncMock(side_effect=Exception("Connection failed"))
        mock_client_class.return_value = mock_client

        self.provider._client = mock_client

        result = asyncio.run(self.provider.validate_connection())
        self.assertFalse(result)

    @patch('cohere.AsyncClient')
    def test_generate_embeddings_success(self, mock_client_class):
        """Test successful embedding generation."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.embeddings = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_client.embed.return_value = mock_response
        mock_client_class.return_value = mock_client

        self.provider._client = mock_client

        texts = ["text1", "text2"]
        embeddings = asyncio.run(self.provider.generate_embeddings(texts))

        self.assertEqual(len(embeddings), 2)
        self.assertEqual(len(embeddings[0]), 3)
        self.assertEqual(len(embeddings[1]), 3)

    @patch('cohere.AsyncClient')
    def test_generate_embeddings_failure(self, mock_client_class):
        """Test failed embedding generation."""
        mock_client = AsyncMock()
        mock_client.embed = AsyncMock(side_effect=Exception("API Error"))
        mock_client_class.return_value = mock_client

        self.provider._client = mock_client

        texts = ["text1"]
        with self.assertRaises(RuntimeError):
            asyncio.run(self.provider.generate_embeddings(texts))


class TestBatchEmbeddingProcessor(unittest.TestCase):
    """Tests for BatchEmbeddingProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        import os
        os.environ["COHERE_API_KEY"] = "test-api-key-12345"
        self.config = EmbeddingConfig(parallel_workers=2)
        self.mock_provider = Mock(spec=EmbeddingProvider)
        self.processor = BatchEmbeddingProcessor(self.config, self.mock_provider)

    def tearDown(self):
        """Clean up after tests."""
        import os
        if "COHERE_API_KEY" in os.environ:
            del os.environ["COHERE_API_KEY"]

    def test_embedding_task_creation(self):
        """Test creating an embedding task."""
        task = EmbeddingTask(
            chunk_id="chunk-1",
            content="test content",
            pipeline_id="pipeline-1",
            metadata={"source": "test"}
        )

        self.assertEqual(task.chunk_id, "chunk-1")
        self.assertEqual(task.content, "test content")
        self.assertEqual(task.pipeline_id, "pipeline-1")
        self.assertEqual(task.metadata, {"source": "test"})

    @patch('src.embeddings.batch_processor.EmbeddingQueue')
    def test_process_batch_empty(self, mock_queue_class):
        """Test processing an empty batch."""
        mock_queue = Mock()
        mock_queue.running = True
        mock_queue_class.return_value = mock_queue
        self.processor.queue = mock_queue

        results = asyncio.run(self.processor.process_batch([]))
        self.assertEqual(len(results), 0)

    def test_process_batch_with_tasks(self):
        """Test processing a batch of tasks."""
        # Create test tasks
        task1 = EmbeddingTask(
            chunk_id="chunk-1",
            content="content 1",
            pipeline_id="pipeline-1",
            metadata={}
        )
        task2 = EmbeddingTask(
            chunk_id="chunk-2",
            content="content 2",
            pipeline_id="pipeline-1",
            metadata={}
        )
        tasks = [task1, task2]

        # Mock the queue behavior
        original_start = self.processor.queue.start
        original_process_pipeline = self.processor.queue.process_pipeline

        # Replace with mock that returns empty results
        async def mock_process_pipeline(pipeline_id, pipeline_tasks):
            from src.embeddings.batch_processor import EmbeddingResult
            return [
                EmbeddingResult(chunk_id=task.chunk_id, embedding=[0.1, 0.2], success=True)
                for task in pipeline_tasks
            ]

        self.processor.queue.start = AsyncMock()
        self.processor.queue.process_pipeline = mock_process_pipeline
        self.processor.queue.running = True

        results = asyncio.run(self.processor.process_batch(tasks))

        self.assertEqual(len(results), 2)
        self.assertTrue(results[0].success)
        self.assertTrue(results[1].success)


if __name__ == '__main__':
    unittest.main()