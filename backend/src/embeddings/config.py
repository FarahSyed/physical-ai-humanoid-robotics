"""
Configuration management for embedding providers.

This module defines the configuration class for embedding providers,
including hash validation for determinism enforcement.
"""
import hashlib
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import os
from .security import APIKeyValidator


@dataclass
class EmbeddingConfig:
    """
    Configuration for embedding providers with determinism enforcement.

    This class manages embedding provider configuration and ensures
    execution determinism by storing and validating configuration hashes.
    """

    provider: str = "cohere"
    model: str = "embed-english-v3.0"
    api_key: Optional[str] = None
    input_type: str = "search_document"
    truncate: str = "END"
    batch_size: int = 100
    parallel_workers: int = 4
    # Qdrant configuration
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: Optional[str] = None
    qdrant_collection_name: str = "approved_chunks_embeddings"
    qdrant_https: bool = False
    qdrant_timeout: int = 30

    @classmethod
    def load_from_environment(cls) -> 'EmbeddingConfig':
        """
        Load embedding configuration from environment variables.

        Returns:
            EmbeddingConfig: Configuration loaded from environment
        """
        # Load provider from environment or use default
        provider = os.getenv("EMBEDDING_PROVIDER", "cohere")

        # Load model from environment or use default
        model = os.getenv("EMBEDDING_MODEL", "embed-english-v3.0")

        # Load API key from environment
        api_key = os.getenv("COHERE_API_KEY")
        if not api_key:
            api_key = os.getenv("EMBEDDING_API_KEY")

        # Load other parameters from environment
        input_type = os.getenv("EMBEDDING_INPUT_TYPE", "search_document")
        truncate = os.getenv("EMBEDDING_TRUNCATE", "END")
        batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))
        parallel_workers = int(os.getenv("EMBEDDING_PARALLEL_WORKERS", "4"))

        # Load Qdrant configuration from environment
        qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        qdrant_collection_name = os.getenv("QDRANT_COLLECTION_NAME", "approved_chunks_embeddings")
        qdrant_https = os.getenv("QDRANT_HTTPS", "false").lower() == "true"
        qdrant_timeout = int(os.getenv("QDRANT_TIMEOUT", "30"))

        # Create configuration instance
        config = cls(
            provider=provider,
            model=model,
            api_key=api_key,
            input_type=input_type,
            truncate=truncate,
            batch_size=batch_size,
            parallel_workers=parallel_workers,
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port,
            qdrant_api_key=qdrant_api_key,
            qdrant_collection_name=qdrant_collection_name,
            qdrant_https=qdrant_https,
            qdrant_timeout=qdrant_timeout
        )

        # Validate the configuration
        config._validate_config()

        return config

    def _validate_config(self):
        """Validate the configuration after initialization."""
        if not self.provider:
            raise ValueError("Provider must be specified")
        if not self.model:
            raise ValueError("Model must be specified")
        if not self.api_key:
            raise ValueError("API key must be provided via environment variables (COHERE_API_KEY or EMBEDDING_API_KEY)")

        # Validate the API key format
        if not APIKeyValidator.validate_api_key(self.api_key, self.provider):
            raise ValueError(f"Invalid API key format for provider: {self.provider}")

    def __post_init__(self):
        """Validate configuration after initialization."""
        # Load API key from environment if not provided during initialization
        if not self.api_key:
            self.api_key = os.getenv("COHERE_API_KEY")
            if not self.api_key:
                self.api_key = os.getenv("EMBEDDING_API_KEY")

        self._validate_config()

    def get_hash(self) -> str:
        """
        Generate a hash of the configuration for determinism enforcement.

        Returns:
            str: SHA256 hash of the configuration (excluding API key)
        """
        # Create a copy of the config without the API key for hashing
        config_dict = asdict(self)
        config_dict.pop('api_key', None)  # Remove API key from hash calculation

        # Convert to JSON string for consistent hashing
        config_json = json.dumps(config_dict, sort_keys=True, default=str)

        # Generate SHA256 hash
        return hashlib.sha256(config_json.encode('utf-8')).hexdigest()

    def validate_config_hash(self, stored_hash: str) -> bool:
        """
        Validate the current configuration against a stored hash.

        Args:
            stored_hash: The hash to validate against

        Returns:
            bool: True if the current configuration matches the stored hash
        """
        current_hash = self.get_hash()
        return current_hash == stored_hash

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the configuration to a dictionary (excluding API key).

        Returns:
            Dict[str, Any]: Configuration as dictionary
        """
        config_dict = asdict(self)
        # Remove API key from the dictionary to avoid exposing it
        config_dict.pop('api_key', None)
        return config_dict

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'EmbeddingConfig':
        """
        Create an EmbeddingConfig from a dictionary.

        Args:
            config_dict: Dictionary containing configuration values

        Returns:
            EmbeddingConfig: New instance from the dictionary
        """
        # Get API key from environment if not in config dict
        api_key = config_dict.get('api_key') or os.getenv("COHERE_API_KEY")
        if not api_key:
            raise ValueError("API key must be provided or set as COHERE_API_KEY environment variable")

        # Create the config object
        config = cls(
            provider=config_dict.get('provider', 'cohere'),
            model=config_dict.get('model', 'embed-english-v3.0'),
            api_key=api_key,
            input_type=config_dict.get('input_type', 'search_document'),
            truncate=config_dict.get('truncate', 'END'),
            batch_size=config_dict.get('batch_size', 100),
            parallel_workers=config_dict.get('parallel_workers', 4)
        )

        # Validate the API key format
        if not APIKeyValidator.validate_api_key(config.api_key, config.provider):
            raise ValueError(f"Invalid API key format for provider: {config.provider}")

        return config