"""
Unit tests for the hash utilities
"""
import pytest
from src.utils.hash_utils import (
    generate_content_hash,
    generate_url_hash,
    generate_combined_hash,
    compare_content_hashes,
    is_likely_duplicate
)


class TestHashUtils:
    """Test cases for hash utilities"""

    def test_generate_content_hash_with_string(self):
        """Test generating hash for string content"""
        content = "test content"
        hash_value = generate_content_hash(content)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 produces 64-character hex string
        assert hash_value.islower()
        assert all(c in '0123456789abcdef' for c in hash_value)

    def test_generate_content_hash_with_bytes(self):
        """Test generating hash for bytes content"""
        content = b"test content"
        hash_value = generate_content_hash(content)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 produces 64-character hex string

    def test_generate_content_hash_different_content_produces_different_hashes(self):
        """Test that different content produces different hashes"""
        hash1 = generate_content_hash("content 1")
        hash2 = generate_content_hash("content 2")
        assert hash1 != hash2

    def test_generate_content_hash_same_content_produces_same_hash(self):
        """Test that the same content produces the same hash"""
        content = "test content"
        hash1 = generate_content_hash(content)
        hash2 = generate_content_hash(content)
        assert hash1 == hash2

    def test_generate_content_hash_with_different_algorithms(self):
        """Test that different algorithms produce different hashes"""
        content = "test content"
        sha256_hash = generate_content_hash(content, 'sha256')
        sha1_hash = generate_content_hash(content, 'sha1')
        md5_hash = generate_content_hash(content, 'md5')
        assert sha256_hash != sha1_hash
        assert sha256_hash != md5_hash
        assert sha1_hash != md5_hash

    def test_generate_url_hash(self):
        """Test generating hash for URL"""
        url = "https://example.com/page"
        hash_value = generate_url_hash(url)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 produces 64-character hex string

    def test_generate_url_hash_same_url_produces_same_hash(self):
        """Test that the same URL produces the same hash"""
        url = "https://example.com/page"
        hash1 = generate_url_hash(url)
        hash2 = generate_url_hash(url)
        assert hash1 == hash2

    def test_generate_url_hash_different_urls_produce_different_hashes(self):
        """Test that different URLs produce different hashes"""
        hash1 = generate_url_hash("https://example.com/page1")
        hash2 = generate_url_hash("https://example.com/page2")
        assert hash1 != hash2

    def test_generate_combined_hash(self):
        """Test generating combined hash of URL and content"""
        url = "https://example.com/page"
        content = "page content"
        hash_value = generate_combined_hash(url, content)
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 produces 64-character hex string

    def test_generate_combined_hash_different_inputs_produce_different_hashes(self):
        """Test that different URL/content combinations produce different hashes"""
        hash1 = generate_combined_hash("https://example.com/page1", "content1")
        hash2 = generate_combined_hash("https://example.com/page2", "content2")
        hash3 = generate_combined_hash("https://example.com/page1", "content2")
        assert hash1 != hash2
        assert hash1 != hash3
        assert hash2 != hash3

    def test_compare_content_hashes_same_hashes(self):
        """Test that comparing identical hashes returns True"""
        content = "test content"
        hash1 = generate_content_hash(content)
        hash2 = generate_content_hash(content)  # Same content, same hash
        assert compare_content_hashes(hash1, hash2) is True

    def test_compare_content_hashes_different_hashes(self):
        """Test that comparing different hashes returns False"""
        hash1 = generate_content_hash("content 1")
        hash2 = generate_content_hash("content 2")
        assert compare_content_hashes(hash1, hash2) is False

    def test_is_likely_duplicate_with_existing_url_hash(self):
        """Test that duplicate detection works with existing URL hash"""
        url = "https://example.com/page"
        content = "test content"
        url_hash = generate_url_hash(url)
        content_hash = generate_content_hash(content)

        existing_url_hashes = {url_hash, "other_url_hash"}
        existing_content_hashes = {"other_content_hash"}

        result = is_likely_duplicate(url_hash, content_hash, existing_url_hashes, existing_content_hashes)
        assert result is True

    def test_is_likely_duplicate_with_existing_content_hash(self):
        """Test that duplicate detection works with existing content hash"""
        url = "https://example.com/page"
        content = "test content"
        url_hash = generate_url_hash(url)
        content_hash = generate_content_hash(content)

        existing_url_hashes = {"other_url_hash"}
        existing_content_hashes = {content_hash, "other_content_hash"}

        result = is_likely_duplicate(url_hash, content_hash, existing_url_hashes, existing_content_hashes)
        assert result is True

    def test_is_likely_duplicate_with_no_existing_hashes(self):
        """Test that duplicate detection returns False when no existing hashes match"""
        url_hash = "unique_url_hash"
        content_hash = "unique_content_hash"

        existing_url_hashes = {"other_url_hash"}
        existing_content_hashes = {"other_content_hash"}

        result = is_likely_duplicate(url_hash, content_hash, existing_url_hashes, existing_content_hashes)
        assert result is False

    def test_is_likely_duplicate_with_both_matching(self):
        """Test that duplicate detection returns True when both hashes match"""
        url_hash = "common_url_hash"
        content_hash = "common_content_hash"

        existing_url_hashes = {"common_url_hash", "other_url_hash"}
        existing_content_hashes = {"common_content_hash", "other_content_hash"}

        result = is_likely_duplicate(url_hash, content_hash, existing_url_hashes, existing_content_hashes)
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__])