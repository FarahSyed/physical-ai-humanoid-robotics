"""
Configuration loader module for handling environment variables and settings
"""
import os
from typing import Optional
from dotenv import load_dotenv


class ConfigLoader:
    """
    Handles loading and accessing configuration values from environment variables
    """

    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize the configuration loader

        Args:
            env_file: Path to the .env file to load (optional)
        """
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to load .env from the current directory
            load_dotenv()

    @property
    def cohere_api_key(self) -> str:
        """Get the Cohere API key from environment variables"""
        key = os.getenv("COHERE_API_KEY")
        if not key:
            raise ValueError("COHERE_API_KEY environment variable is required")
        return key

    @property
    def qdrant_host(self) -> str:
        """Get the Qdrant host from environment variables"""
        host = os.getenv("QDRANT_HOST")
        if not host:
            raise ValueError("QDRANT_HOST environment variable is required")
        return host

    @property
    def qdrant_api_key(self) -> Optional[str]:
        """Get the Qdrant API key from environment variables (optional)"""
        return os.getenv("QDRANT_API_KEY")

    @property
    def qdrant_collection_name(self) -> str:
        """Get the Qdrant collection name from environment variables"""
        collection_name = os.getenv("QDRANT_COLLECTION_NAME", "book_content_embeddings")
        return collection_name

    @property
    def website_crawl_delay(self) -> int:
        """Get the website crawl delay from environment variables"""
        delay_str = os.getenv("WEBSITE_CRAWL_DELAY", "1")
        try:
            return int(delay_str)
        except ValueError:
            raise ValueError("WEBSITE_CRAWL_DELAY must be an integer")

    @property
    def extraction_timeout(self) -> int:
        """Get the extraction timeout from environment variables"""
        timeout_str = os.getenv("EXTRACTION_TIMEOUT", "300")
        try:
            return int(timeout_str)
        except ValueError:
            raise ValueError("EXTRACTION_TIMEOUT must be an integer")

    @property
    def frontend_sitemap_url(self) -> str:
        """Get the frontend sitemap URL from environment variables"""
        url = os.getenv("FRONTEND_SITEMAP_URL")
        if not url:
            raise ValueError("FRONTEND_SITEMAP_URL environment variable is required")
        return url

    @property
    def embedding_batch_size(self) -> int:
        """Get the embedding batch size from environment variables"""
        batch_size_str = os.getenv("EMBEDDING_BATCH_SIZE", "10")
        try:
            return int(batch_size_str)
        except ValueError:
            raise ValueError("EMBEDDING_BATCH_SIZE must be an integer")


# Global instance for easy access
config = ConfigLoader()