"""
Unit tests for the configuration loader module
"""
import os
import pytest
from unittest.mock import patch, mock_open
from src.utils.config_loader import ConfigLoader


class TestConfigLoader:
    """Test cases for ConfigLoader class"""

    def test_config_loader_initialization_without_env_file(self):
        """Test that ConfigLoader can be initialized without an env file"""
        config_loader = ConfigLoader()
        assert config_loader is not None

    def test_config_loader_initialization_with_env_file(self):
        """Test that ConfigLoader can be initialized with an env file"""
        config_loader = ConfigLoader(".env.example")
        assert config_loader is not None

    @patch.dict(os.environ, {"COHERE_API_KEY": "test_key"})
    def test_cohere_api_key_property(self):
        """Test that cohere_api_key returns the correct value"""
        config_loader = ConfigLoader()
        assert config_loader.cohere_api_key == "test_key"

    def test_cohere_api_key_missing_raises_error(self):
        """Test that missing COHERE_API_KEY raises an error"""
        config_loader = ConfigLoader()
        with pytest.raises(ValueError, match="COHERE_API_KEY environment variable is required"):
            _ = config_loader.cohere_api_key

    @patch.dict(os.environ, {"QDRANT_HOST": "https://test-qdrant.com"})
    def test_qdrant_host_property(self):
        """Test that qdrant_host returns the correct value"""
        config_loader = ConfigLoader()
        assert config_loader.qdrant_host == "https://test-qdrant.com"

    def test_qdrant_host_missing_raises_error(self):
        """Test that missing QDRANT_HOST raises an error"""
        config_loader = ConfigLoader()
        with pytest.raises(ValueError, match="QDRANT_HOST environment variable is required"):
            _ = config_loader.qdrant_host

    @patch.dict(os.environ, {"QDRANT_API_KEY": "test_qdrant_key"})
    def test_qdrant_api_key_property(self):
        """Test that qdrant_api_key returns the correct value"""
        config_loader = ConfigLoader()
        assert config_loader.qdrant_api_key == "test_qdrant_key"

    @patch.dict(os.environ, {})
    def test_qdrant_api_key_optional(self):
        """Test that qdrant_api_key returns None when not set"""
        config_loader = ConfigLoader()
        assert config_loader.qdrant_api_key is None

    @patch.dict(os.environ, {"QDRANT_COLLECTION_NAME": "test_collection"})
    def test_qdrant_collection_name_property(self):
        """Test that qdrant_collection_name returns the correct value"""
        config_loader = ConfigLoader()
        assert config_loader.qdrant_collection_name == "test_collection"

    @patch.dict(os.environ, {})
    def test_qdrant_collection_name_default(self):
        """Test that qdrant_collection_name returns default when not set"""
        config_loader = ConfigLoader()
        assert config_loader.qdrant_collection_name == "book_content_embeddings"

    @patch.dict(os.environ, {"WEBSITE_CRAWL_DELAY": "2"})
    def test_website_crawl_delay_property(self):
        """Test that website_crawl_delay returns the correct value"""
        config_loader = ConfigLoader()
        assert config_loader.website_crawl_delay == 2

    @patch.dict(os.environ, {})
    def test_website_crawl_delay_default(self):
        """Test that website_crawl_delay returns default when not set"""
        config_loader = ConfigLoader()
        assert config_loader.website_crawl_delay == 1

    @patch.dict(os.environ, {"WEBSITE_CRAWL_DELAY": "invalid"})
    def test_website_crawl_delay_invalid_raises_error(self):
        """Test that invalid website_crawl_delay raises an error"""
        config_loader = ConfigLoader()
        with pytest.raises(ValueError, match="WEBSITE_CRAWL_DELAY must be an integer"):
            _ = config_loader.website_crawl_delay

    @patch.dict(os.environ, {"EXTRACTION_TIMEOUT": "600"})
    def test_extraction_timeout_property(self):
        """Test that extraction_timeout returns the correct value"""
        config_loader = ConfigLoader()
        assert config_loader.extraction_timeout == 600

    @patch.dict(os.environ, {})
    def test_extraction_timeout_default(self):
        """Test that extraction_timeout returns default when not set"""
        config_loader = ConfigLoader()
        assert config_loader.extraction_timeout == 300

    @patch.dict(os.environ, {"EXTRACTION_TIMEOUT": "invalid"})
    def test_extraction_timeout_invalid_raises_error(self):
        """Test that invalid extraction_timeout raises an error"""
        config_loader = ConfigLoader()
        with pytest.raises(ValueError, match="EXTRACTION_TIMEOUT must be an integer"):
            _ = config_loader.extraction_timeout

    @patch.dict(os.environ, {"FRONTEND_SITEMAP_URL": "https://example.com"})
    def test_frontend_sitemap_url_property(self):
        """Test that frontend_sitemap_url returns the correct value"""
        config_loader = ConfigLoader()
        assert config_loader.frontend_sitemap_url == "https://example.com"

    def test_frontend_sitemap_url_missing_raises_error(self):
        """Test that missing FRONTEND_SITEMAP_URL raises an error"""
        config_loader = ConfigLoader()
        with pytest.raises(ValueError, match="FRONTEND_SITEMAP_URL environment variable is required"):
            _ = config_loader.frontend_sitemap_url

    @patch.dict(os.environ, {"EMBEDDING_BATCH_SIZE": "20"})
    def test_embedding_batch_size_property(self):
        """Test that embedding_batch_size returns the correct value"""
        config_loader = ConfigLoader()
        assert config_loader.embedding_batch_size == 20

    @patch.dict(os.environ, {})
    def test_embedding_batch_size_default(self):
        """Test that embedding_batch_size returns default when not set"""
        config_loader = ConfigLoader()
        assert config_loader.embedding_batch_size == 10

    @patch.dict(os.environ, {"EMBEDDING_BATCH_SIZE": "invalid"})
    def test_embedding_batch_size_invalid_raises_error(self):
        """Test that invalid embedding_batch_size raises an error"""
        config_loader = ConfigLoader()
        with pytest.raises(ValueError, match="EMBEDDING_BATCH_SIZE must be an integer"):
            _ = config_loader.embedding_batch_size


if __name__ == "__main__":
    pytest.main([__file__])