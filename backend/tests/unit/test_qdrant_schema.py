"""
Unit tests for the Qdrant schema definitions
"""
import pytest
from datetime import datetime
from src.models.qdrant_schema import QdrantSchema, ContentType


class TestQdrantSchema:
    """Test cases for QdrantSchema class"""

    def test_get_embedding_payload_schema(self):
        """Test that get_embedding_payload_schema returns the correct schema"""
        schema = QdrantSchema.get_embedding_payload_schema()

        # Check that it returns a dictionary
        assert isinstance(schema, dict)

        # Check that it contains expected keys
        expected_keys = [
            "url", "title", "module", "section", "version", "content_type",
            "word_count", "content_hash", "created_at", "updated_at",
            "quality_score", "chunk_index", "total_chunks", "language", "metadata"
        ]

        for key in expected_keys:
            assert key in schema

    def test_create_payload_with_required_fields(self):
        """Test creating a payload with required fields"""
        payload = QdrantSchema.create_payload(
            url="https://example.com",
            title="Test Page"
        )

        assert payload["url"] == "https://example.com"
        assert payload["title"] == "Test Page"
        assert payload["content_type"] == ContentType.TEXT.value
        assert payload["word_count"] == 0
        assert payload["content_hash"] == ""
        assert "created_at" in payload
        assert "updated_at" in payload

    def test_create_payload_with_content_calculates_word_count(self):
        """Test that word count is calculated from content if not provided"""
        content = "This is a test content with several words"
        payload = QdrantSchema.create_payload(
            url="https://example.com",
            title="Test Page",
            content=content
        )

        # The content has 8 words
        assert payload["word_count"] == 8

    def test_create_payload_with_explicit_word_count(self):
        """Test that explicit word count overrides content calculation"""
        content = "This content has different word count"
        explicit_count = 42
        payload = QdrantSchema.create_payload(
            url="https://example.com",
            title="Test Page",
            content=content,
            word_count=explicit_count
        )

        assert payload["word_count"] == 42

    def test_create_payload_with_different_content_types(self):
        """Test creating payloads with different content types"""
        for content_type in ContentType:
            payload = QdrantSchema.create_payload(
                url="https://example.com",
                title="Test Page",
                content_type=content_type
            )

            assert payload["content_type"] == content_type.value

    def test_create_payload_with_all_fields(self):
        """Test creating a payload with all possible fields"""
        now = datetime.utcnow()
        metadata = {"custom_field": "custom_value"}

        payload = QdrantSchema.create_payload(
            url="https://example.com/page",
            title="Test Title",
            content="Test content with some words",
            module="Module 1",
            section="Week 1-2",
            version="2.0.0",
            content_type=ContentType.DOCUMENTATION,
            word_count=100,
            content_hash="abc123",
            created_at=now,
            updated_at=now,
            quality_score=0.85,
            chunk_index=1,
            total_chunks=3,
            language="en",
            additional_metadata=metadata
        )

        assert payload["url"] == "https://example.com/page"
        assert payload["title"] == "Test Title"
        assert payload["module"] == "Module 1"
        assert payload["section"] == "Week 1-2"
        assert payload["version"] == "2.0.0"
        assert payload["content_type"] == ContentType.DOCUMENTATION.value
        assert payload["word_count"] == 100
        assert payload["content_hash"] == "abc123"
        assert payload["quality_score"] == 0.85
        assert payload["chunk_index"] == 1
        assert payload["total_chunks"] == 3
        assert payload["language"] == "en"
        assert payload["metadata"] == metadata

    def test_generate_embedding_id_returns_valid_uuid(self):
        """Test that generate_embedding_id returns a valid UUID string"""
        id1 = QdrantSchema.generate_embedding_id()
        id2 = QdrantSchema.generate_embedding_id()

        # Check that both are strings and different
        assert isinstance(id1, str)
        assert isinstance(id2, str)
        assert id1 != id2
        # Check that it looks like a UUID (contains hyphens in the right places)
        assert len(id1) == 36  # Standard UUID length
        assert id1.count("-") == 4  # Standard UUID format

    def test_validate_payload_with_valid_payload(self):
        """Test that validate_payload returns True for valid payload"""
        payload = {
            "url": "https://example.com",
            "title": "Test Page",
            "content_type": ContentType.TEXT.value,
            "content_hash": "abc123"
        }

        result = QdrantSchema.validate_payload(payload)
        assert result is True

    def test_validate_payload_with_missing_required_fields(self):
        """Test that validate_payload returns False for missing required fields"""
        # Test missing url
        payload = {
            "title": "Test Page",
            "content_type": ContentType.TEXT.value,
            "content_hash": "abc123"
        }
        result = QdrantSchema.validate_payload(payload)
        assert result is False

        # Test missing title
        payload = {
            "url": "https://example.com",
            "content_type": ContentType.TEXT.value,
            "content_hash": "abc123"
        }
        result = QdrantSchema.validate_payload(payload)
        assert result is False

        # Test missing content_type
        payload = {
            "url": "https://example.com",
            "title": "Test Page",
            "content_hash": "abc123"
        }
        result = QdrantSchema.validate_payload(payload)
        assert result is False

        # Test missing content_hash
        payload = {
            "url": "https://example.com",
            "title": "Test Page",
            "content_type": ContentType.TEXT.value
        }
        result = QdrantSchema.validate_payload(payload)
        assert result is False

    def test_validate_payload_with_none_values(self):
        """Test that validate_payload returns False for None values in required fields"""
        payload = {
            "url": None,
            "title": "Test Page",
            "content_type": ContentType.TEXT.value,
            "content_hash": "abc123"
        }

        result = QdrantSchema.validate_payload(payload)
        assert result is False

    def test_validate_payload_with_invalid_content_type(self):
        """Test that validate_payload returns False for invalid content type"""
        payload = {
            "url": "https://example.com",
            "title": "Test Page",
            "content_type": "invalid_type",
            "content_hash": "abc123"
        }

        result = QdrantSchema.validate_payload(payload)
        assert result is False

    def test_get_search_filters_with_all_parameters(self):
        """Test creating search filters with all parameters"""
        filters = QdrantSchema.get_search_filters(
            module="Module 1",
            section="Week 1-2",
            content_type=ContentType.DOCUMENTATION,
            min_quality_score=0.7,
            url_pattern="example.com"
        )

        assert filters["module"] == "Module 1"
        assert filters["section"] == "Week 1-2"
        assert filters["content_type"] == ContentType.DOCUMENTATION.value
        assert filters["quality_score"] == {"$gte": 0.7}
        assert filters["url"] == {"$regex": "example.com"}

    def test_get_search_filters_with_none_parameters(self):
        """Test creating search filters with no parameters (empty dict)"""
        filters = QdrantSchema.get_search_filters()
        assert filters == {}

    def test_get_search_filters_with_individual_parameters(self):
        """Test creating search filters with individual parameters"""
        # Test with just module
        filters = QdrantSchema.get_search_filters(module="Module 1")
        assert filters == {"module": "Module 1"}

        # Test with just content type
        filters = QdrantSchema.get_search_filters(content_type=ContentType.CODE)
        assert filters == {"content_type": ContentType.CODE.value}

        # Test with just min quality score
        filters = QdrantSchema.get_search_filters(min_quality_score=0.5)
        assert filters == {"quality_score": {"$gte": 0.5}}


if __name__ == "__main__":
    pytest.main([__file__])