"""
Security utilities for embedding operations.

This module provides utilities for secure handling of API keys and
other sensitive information in the embedding process.
"""
import os
import re
from typing import Optional
import logging


class APIKeyValidator:
    """
    Utility class for validating and securing API keys.
    """

    @staticmethod
    def validate_api_key(api_key: str, provider: str = "cohere") -> bool:
        """
        Validate an API key based on provider-specific rules.

        Args:
            api_key: The API key to validate
            provider: The provider type (default: "cohere")

        Returns:
            bool: True if the API key is valid, False otherwise
        """
        if not api_key or not isinstance(api_key, str):
            return False

        # For Cohere, API keys are typically long alphanumeric strings
        if provider.lower() == "cohere":
            # Cohere API keys are usually 32+ characters with alphanumeric and possibly special chars
            if len(api_key) < 16:
                return False
            # Check for common patterns that are clearly invalid
            if re.search(r'[<>"\']', api_key):
                return False
            return True

        # Add validation for other providers as needed
        return len(api_key) > 0

    @staticmethod
    def mask_api_key(api_key: str) -> str:
        """
        Mask an API key for safe logging.

        Args:
            api_key: The API key to mask

        Returns:
            str: Masked version of the API key
        """
        if not api_key:
            return ""

        # Show only first 4 and last 4 characters
        if len(api_key) <= 8:
            return "*" * len(api_key)
        return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]

    @staticmethod
    def get_api_key(provider: str = "cohere", env_var_name: Optional[str] = None) -> Optional[str]:
        """
        Get an API key from environment variables with provider-specific defaults.

        Args:
            provider: The provider type (default: "cohere")
            env_var_name: Specific environment variable name (optional)

        Returns:
            str: The API key or None if not found
        """
        if env_var_name:
            return os.getenv(env_var_name)

        # Provider-specific default environment variable names
        provider_env_vars = {
            "cohere": "COHERE_API_KEY",
            "openai": "OPENAI_API_KEY",
            "azure": "AZURE_OPENAI_API_KEY"
        }

        env_var = provider_env_vars.get(provider.lower())
        if env_var:
            return os.getenv(env_var)

        # Fallback to a generic API key variable
        return os.getenv("EMBEDDING_API_KEY")


def validate_and_secure_config(config) -> bool:
    """
    Validate and secure the embedding configuration.

    Args:
        config: The embedding configuration object

    Returns:
        bool: True if configuration is valid and secure, False otherwise
    """
    logger = logging.getLogger(__name__)

    # Validate API key
    if not config.api_key:
        logger.error("No API key provided in configuration")
        return False

    if not APIKeyValidator.validate_api_key(config.api_key, config.provider):
        logger.error(f"Invalid API key format for provider: {config.provider}")
        return False

    # Log a masked version for debugging
    logger.debug(f"Valid API key provided for provider: {config.provider}, key: {APIKeyValidator.mask_api_key(config.api_key)}")

    return True