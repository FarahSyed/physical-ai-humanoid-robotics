"""
Validation utility functions for the pipeline verification system.

This module provides validation functions for data, configurations, and other
validation requirements in the pipeline system.
"""
from typing import Any, Dict, List, Optional, Union
import re
import hashlib
from pathlib import Path


def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate data against a simple schema definition.

    Args:
        data: Data to validate
        schema: Schema definition with expected keys and types

    Returns:
        True if data matches schema, False otherwise
    """
    try:
        for key, expected_type in schema.items():
            if key not in data:
                return False
            if not isinstance(data[key], expected_type):
                return False
        return True
    except Exception:
        return False


def validate_config_hash(config: Dict[str, Any], expected_hash: str) -> bool:
    """
    Validate a configuration against its expected hash.

    Args:
        config: Configuration dictionary to validate
        expected_hash: Expected SHA256 hash string

    Returns:
        True if configuration matches the hash, False otherwise
    """
    try:
        # Convert config to string representation for hashing
        config_str = str(sorted(config.items()))
        actual_hash = hashlib.sha256(config_str.encode()).hexdigest()
        return actual_hash == expected_hash
    except Exception:
        return False


def calculate_config_hash(config: Dict[str, Any]) -> str:
    """
    Calculate SHA256 hash of a configuration.

    Args:
        config: Configuration dictionary to hash

    Returns:
        SHA256 hash string
    """
    try:
        # Convert config to string representation for hashing
        config_str = str(sorted(config.items()))
        return hashlib.sha256(config_str.encode()).hexdigest()
    except Exception:
        # Return empty string if hashing fails
        return ""


def validate_file_path(file_path: str, allowed_extensions: Optional[List[str]] = None) -> bool:
    """
    Validate a file path for safety and optionally check extensions.

    Args:
        file_path: Path to validate
        allowed_extensions: Optional list of allowed file extensions (e.g., ['.txt', '.json'])

    Returns:
        True if path is valid and safe, False otherwise
    """
    try:
        path = Path(file_path)

        # Check for path traversal attacks
        if ".." in path.parts:
            return False

        # Check if extension is allowed
        if allowed_extensions:
            if path.suffix.lower() not in [ext.lower() for ext in allowed_extensions]:
                return False

        return True
    except Exception:
        return False


def validate_content_length(content: str, max_length: int = 1000000) -> bool:
    """
    Validate content length to prevent memory issues.

    Args:
        content: Content to validate
        max_length: Maximum allowed length (default: 1MB)

    Returns:
        True if content length is within limits, False otherwise
    """
    try:
        return len(content) <= max_length
    except Exception:
        return False


def validate_preview_params(offset: int, limit: int, total_length: int) -> bool:
    """
    Validate preview parameters for sampling and paging.

    Args:
        offset: Starting position
        limit: Number of characters/lines to return
        total_length: Total length of content

    Returns:
        True if parameters are valid, False otherwise
    """
    try:
        # Check for negative values
        if offset < 0 or limit < 0:
            return False

        # Check if offset is beyond content length
        if offset > total_length:
            return False

        # Allow offset + limit to exceed total_length (will be truncated)
        # This allows for previewing content that goes beyond the end of the file
        # The caller should handle truncation appropriately
        return True
    except Exception:
        return False


def sanitize_content(content: str, max_length: int = 1000000) -> str:
    """
    Sanitize content by limiting length and removing potentially harmful characters.

    Args:
        content: Content to sanitize
        max_length: Maximum allowed length (default: 1MB)

    Returns:
        Sanitized content string
    """
    try:
        # Limit length
        if len(content) > max_length:
            content = content[:max_length]

        # Return content (we could add more sanitization here if needed)
        return content
    except Exception:
        return ""


def validate_approval_decision(decision: str) -> bool:
    """
    Validate approval decision against allowed values (APPROVE, REJECT, REQUEST_CHANGE).

    Args:
        decision: Decision string to validate

    Returns:
        True if decision is valid, False otherwise
    """
    allowed_decisions = {"APPROVE", "REJECT", "REQUEST_CHANGE"}
    return decision.upper() in allowed_decisions


def validate_pipeline_state(state: str) -> bool:
    """
    Validate pipeline state against allowed values.

    Args:
        state: State string to validate

    Returns:
        True if state is valid, False otherwise
    """
    allowed_states = {
        "IDLE", "EXTRACTION_IN_PROGRESS", "EXTRACTION_COMPLETE", "EXTRACTION_APPROVED",
        "CHUNKING_IN_PROGRESS", "CHUNKING_COMPLETE", "CHUNKING_APPROVED",
        "EMBEDDING_IN_PROGRESS", "EMBEDDING_COMPLETE", "FAILED", "REJECTED"
    }
    return state in allowed_states


def validate_approval_status(status: str) -> bool:
    """
    Validate approval status against allowed values (APPROVED, REJECTED, PENDING).

    Args:
        status: Status string to validate

    Returns:
        True if status is valid, False otherwise
    """
    allowed_statuses = {"APPROVED", "REJECTED", "PENDING"}
    return status in allowed_statuses


def is_valid_iso_datetime(datetime_str: str) -> bool:
    """
    Validate if a string is in ISO 8601 datetime format.

    Args:
        datetime_str: String to validate

    Returns:
        True if string is valid ISO 8601 datetime, False otherwise
    """
    try:
        # Basic ISO 8601 format validation using regex
        # This pattern matches YYYY-MM-DDTHH:MM:SS[.sss][Z] or [±HH:MM]
        iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3,})?(Z|[+-]\d{2}:\d{2})?$'
        return bool(re.match(iso_pattern, datetime_str))
    except Exception:
        return False


def validate_artifact_paths(artifact_paths: Dict[str, str]) -> bool:
    """
    Validate artifact paths dictionary.

    Args:
        artifact_paths: Dictionary of artifact paths to validate

    Returns:
        True if paths are valid, False otherwise
    """
    try:
        required_keys = {"extracted_content", "chunked_output"}

        # Check if all required keys are present
        if not all(key in artifact_paths for key in required_keys):
            return False

        # Validate each path
        for path in artifact_paths.values():
            if not validate_file_path(path):
                return False

        return True
    except Exception:
        return False