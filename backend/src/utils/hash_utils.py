"""
Content hash utility for deduplication purposes
"""
import hashlib
from typing import Union


def generate_content_hash(content: Union[str, bytes], algorithm: str = 'sha256') -> str:
    """
    Generate a hash for the given content to be used for deduplication.

    Args:
        content: The content to hash (string or bytes)
        algorithm: The hashing algorithm to use (default: 'sha256')

    Returns:
        The hexadecimal representation of the hash
    """
    if isinstance(content, str):
        content = content.encode('utf-8')

    hasher = hashlib.new(algorithm)
    hasher.update(content)
    return hasher.hexdigest()


def generate_url_hash(url: str) -> str:
    """
    Generate a hash for the given URL.

    Args:
        url: The URL to hash

    Returns:
        The hexadecimal representation of the hash
    """
    return generate_content_hash(url, 'sha256')


def generate_combined_hash(url: str, content: Union[str, bytes]) -> str:
    """
    Generate a combined hash of URL and content for more robust deduplication.

    Args:
        url: The URL of the content
        content: The content itself

    Returns:
        The hexadecimal representation of the combined hash
    """
    combined = f"{url}||{content}" if isinstance(content, str) else f"{url}||{content.decode('utf-8', errors='ignore')}"
    return generate_content_hash(combined, 'sha256')


def compare_content_hashes(hash1: str, hash2: str) -> bool:
    """
    Compare two content hashes for equality.

    Args:
        hash1: First hash to compare
        hash2: Second hash to compare

    Returns:
        True if the hashes are identical, False otherwise
    """
    return hash1 == hash2


def is_likely_duplicate(url_hash: str, content_hash: str, existing_url_hashes: set,
                       existing_content_hashes: set) -> bool:
    """
    Determine if content is likely a duplicate based on URL and content hashes.

    Args:
        url_hash: Hash of the URL
        content_hash: Hash of the content
        existing_url_hashes: Set of existing URL hashes
        existing_content_hashes: Set of existing content hashes

    Returns:
        True if the content is likely a duplicate, False otherwise
    """
    # Check if either the URL or content hash already exists
    return url_hash in existing_url_hashes or content_hash in existing_content_hashes