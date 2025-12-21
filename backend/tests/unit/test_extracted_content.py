"""
Unit tests for the extracted content data models
"""
import pytest
from datetime import datetime
from src.models.extracted_content import ExtractedContent, EmbeddingVector, ContentMetadata


class TestExtractedContent:
    """Test cases for ExtractedContent class"""

    def test_extracted_content_creation(self):
        """Test creating an ExtractedContent object"""
        content = ExtractedContent(
            id="test-id",
            url="https://example.com",
            title="Test Page",
            content="This is test content"
        )

        assert content.id == "test-id"
        assert content.url == "https://example.com"
        assert content.title == "Test Page"
        assert content.content == "This is test content"
        assert content.word_count == 4  # "This is test content" has 4 words
        assert content.content_hash is not None
        assert content.created_at is not None
        assert content.updated_at is not None

    def test_extracted_content_post_init_defaults(self):
        """Test that post_init sets default values correctly"""
        content = ExtractedContent(
            id="test-id",
            url="https://example.com",
            title="Test Page",
            content="This is test content"
        )

        # Check defaults were set
        assert content.version == "1.0.0"
        assert content.content_type == "text"
        assert content.module is None
        assert content.section is None
        assert content.metadata == {}

    def test_extracted_content_word_count_calculation(self):
        """Test that word count is calculated correctly"""
        content = ExtractedContent(
            id="test-id",
            url="https://example.com",
            title="Test Page",
            content="This is a test with multiple words"
        )

        assert content.word_count == 7

    def test_extracted_content_hash_generation(self):
        """Test that content hash is generated"""
        content = ExtractedContent(
            id="test-id",
            url="https://example.com",
            title="Test Page",
            content="This is test content"
        )

        assert content.content_hash is not None
        assert isinstance(content.content_hash, str)
        assert len(content.content_hash) > 0

    def test_extracted_content_validation_valid(self):
        """Test validation of a valid ExtractedContent object"""
        content = ExtractedContent(
            id="test-id",
            url="https://example.com",
            title="Test Page",
            content="This is test content"
        )

        assert content.validate() is True

    def test_extracted_content_validation_invalid_url(self):
        """Test validation with invalid URL"""
        content = ExtractedContent(
            id="test-id",
            url="",  # Empty URL
            title="Test Page",
            content="This is test content"
        )

        assert content.validate() is False

    def test_extracted_content_validation_invalid_title(self):
        """Test validation with invalid title"""
        content = ExtractedContent(
            id="test-id",
            url="https://example.com",
            title="",  # Empty title
            content="This is test content"
        )

        assert content.validate() is False

    def test_extracted_content_validation_invalid_content_type(self):
        """Test validation with invalid content (not string)"""
        content = ExtractedContent(
            id="test-id",
            url="https://example.com",
            title="Test Page",
            content=123  # Not a string
        )

        # This should fail validation
        # Note: The current implementation will still create the object but validation will fail
        assert content.validate() is False

    def test_extracted_content_to_dict(self):
        """Test converting ExtractedContent to dictionary"""
        content = ExtractedContent(
            id="test-id",
            url="https://example.com",
            title="Test Page",
            content="This is test content",
            module="Module 1",
            section="Week 1"
        )

        result = content.to_dict()

        assert result["id"] == "test-id"
        assert result["url"] == "https://example.com"
        assert result["title"] == "Test Page"
        assert result["content"] == "This is test content"
        assert result["module"] == "Module 1"
        assert result["section"] == "Week 1"
        assert result["word_count"] == 4

    def test_extracted_content_from_dict(self):
        """Test creating ExtractedContent from dictionary"""
        data = {
            "id": "test-id",
            "url": "https://example.com",
            "title": "Test Page",
            "content": "This is test content",
            "module": "Module 1",
            "section": "Week 1",
            "version": "2.0.0",
            "content_type": "documentation",
            "word_count": 10,
            "content_hash": "test-hash",
            "metadata": {"custom": "value"}
        }

        content = ExtractedContent.from_dict(data)

        assert content.id == "test-id"
        assert content.url == "https://example.com"
        assert content.title == "Test Page"
        assert content.content == "This is test content"
        assert content.module == "Module 1"
        assert content.section == "Week 1"
        assert content.version == "2.0.0"
        assert content.content_type == "documentation"
        assert content.word_count == 10
        assert content.content_hash == "test-hash"
        assert content.metadata == {"custom": "value"}

    def test_extracted_content_update_content(self):
        """Test updating content and dependent fields"""
        content = ExtractedContent(
            id="test-id",
            url="https://example.com",
            title="Test Page",
            content="Original content"
        )

        original_hash = content.content_hash
        original_word_count = content.word_count
        original_updated_at = content.updated_at

        # Update content
        content.update_content("New updated content with more words")

        # Check that content was updated
        assert content.content == "New updated content with more words"
        assert content.word_count == 6  # New word count
        assert content.content_hash != original_hash  # Hash should change
        assert content.updated_at > original_updated_at  # Updated time should be later


class TestEmbeddingVector:
    """Test cases for EmbeddingVector class"""

    def test_embedding_vector_creation(self):
        """Test creating an EmbeddingVector object"""
        vector = EmbeddingVector(
            id="test-id",
            vector=[0.1, 0.2, 0.3],
            payload={"url": "https://example.com", "title": "Test", "content_hash": "hash123"}
        )

        assert vector.id == "test-id"
        assert vector.vector == [0.1, 0.2, 0.3]
        assert vector.payload == {"url": "https://example.com", "title": "Test", "content_hash": "hash123"}

    def test_embedding_vector_validation_valid(self):
        """Test validation of a valid EmbeddingVector object"""
        vector = EmbeddingVector(
            id="test-id",
            vector=[0.1, 0.2, 0.3],
            payload={"url": "https://example.com", "title": "Test", "content_hash": "hash123"}
        )

        assert vector.validate() is True

    def test_embedding_vector_validation_invalid_id(self):
        """Test validation with invalid ID"""
        vector = EmbeddingVector(
            id="",  # Empty ID
            vector=[0.1, 0.2, 0.3],
            payload={"url": "https://example.com", "title": "Test", "content_hash": "hash123"}
        )

        assert vector.validate() is False

    def test_embedding_vector_validation_invalid_vector(self):
        """Test validation with invalid vector"""
        vector = EmbeddingVector(
            id="test-id",
            vector="not-a-list",  # Not a list
            payload={"url": "https://example.com", "title": "Test", "content_hash": "hash123"}
        )

        assert vector.validate() is False

    def test_embedding_vector_validation_invalid_payload(self):
        """Test validation with invalid payload"""
        vector = EmbeddingVector(
            id="test-id",
            vector=[0.1, 0.2, 0.3],
            payload="not-a-dict"  # Not a dict
        )

        assert vector.validate() is False

    def test_embedding_vector_validation_missing_payload_fields(self):
        """Test validation with missing required payload fields"""
        vector = EmbeddingVector(
            id="test-id",
            vector=[0.1, 0.2, 0.3],
            payload={"url": "https://example.com", "title": "Test"}  # Missing content_hash
        )

        assert vector.validate() is False

    def test_embedding_vector_validation_non_numeric_vector_elements(self):
        """Test validation with non-numeric vector elements"""
        vector = EmbeddingVector(
            id="test-id",
            vector=[0.1, "not-a-number", 0.3],  # Contains non-numeric element
            payload={"url": "https://example.com", "title": "Test", "content_hash": "hash123"}
        )

        assert vector.validate() is False

    def test_embedding_vector_to_dict(self):
        """Test converting EmbeddingVector to dictionary"""
        vector = EmbeddingVector(
            id="test-id",
            vector=[0.1, 0.2, 0.3],
            payload={"url": "https://example.com", "title": "Test", "content_hash": "hash123"}
        )

        result = vector.to_dict()

        assert result["id"] == "test-id"
        assert result["vector"] == [0.1, 0.2, 0.3]
        assert result["payload"] == {"url": "https://example.com", "title": "Test", "content_hash": "hash123"}

    def test_embedding_vector_from_dict(self):
        """Test creating EmbeddingVector from dictionary"""
        data = {
            "id": "test-id",
            "vector": [0.4, 0.5, 0.6],
            "payload": {"url": "https://example2.com", "title": "Test2", "content_hash": "hash456"}
        }

        vector = EmbeddingVector.from_dict(data)

        assert vector.id == "test-id"
        assert vector.vector == [0.4, 0.5, 0.6]
        assert vector.payload == {"url": "https://example2.com", "title": "Test2", "content_hash": "hash456"}


class TestContentMetadata:
    """Test cases for ContentMetadata class"""

    def test_content_metadata_creation(self):
        """Test creating a ContentMetadata object"""
        metadata = ContentMetadata(
            content_id="test-id",
            source_url="https://example.com",
            module="Module 1",
            section="Week 1-2",
            quality_score=0.85
        )

        assert metadata.content_id == "test-id"
        assert metadata.source_url == "https://example.com"
        assert metadata.module == "Module 1"
        assert metadata.section == "Week 1-2"
        assert metadata.quality_score == 0.85
        assert metadata.extraction_date is not None

    def test_content_metadata_post_init_defaults(self):
        """Test that post_init sets default values correctly"""
        metadata = ContentMetadata(
            content_id="test-id",
            source_url="https://example.com"
        )

        # Check defaults were set
        assert metadata.version == "1.0.0"
        assert metadata.quality_score == 0.0
        assert metadata.language == "en"
        assert metadata.content_structure == {}
        assert metadata.extraction_date is not None

    def test_content_metadata_validation_valid(self):
        """Test validation of a valid ContentMetadata object"""
        metadata = ContentMetadata(
            content_id="test-id",
            source_url="https://example.com"
        )

        assert metadata.validate() is True

    def test_content_metadata_validation_invalid_content_id(self):
        """Test validation with invalid content_id"""
        metadata = ContentMetadata(
            content_id="",  # Empty content_id
            source_url="https://example.com"
        )

        assert metadata.validate() is False

    def test_content_metadata_validation_invalid_source_url(self):
        """Test validation with invalid source_url"""
        metadata = ContentMetadata(
            content_id="test-id",
            source_url=""  # Empty source_url
        )

        assert metadata.validate() is False

    def test_content_metadata_validation_invalid_quality_score_low(self):
        """Test validation with quality score below 0.0"""
        metadata = ContentMetadata(
            content_id="test-id",
            source_url="https://example.com",
            quality_score=-0.1  # Below 0.0
        )

        assert metadata.validate() is False

    def test_content_metadata_validation_invalid_quality_score_high(self):
        """Test validation with quality score above 1.0"""
        metadata = ContentMetadata(
            content_id="test-id",
            source_url="https://example.com",
            quality_score=1.1  # Above 1.0
        )

        assert metadata.validate() is False

    def test_content_metadata_validation_negative_content_length(self):
        """Test validation with negative content_length"""
        metadata = ContentMetadata(
            content_id="test-id",
            source_url="https://example.com",
            content_length=-10  # Negative
        )

        assert metadata.validate() is False

    def test_content_metadata_validation_negative_word_count(self):
        """Test validation with negative word_count"""
        metadata = ContentMetadata(
            content_id="test-id",
            source_url="https://example.com",
            word_count=-5  # Negative
        )

        assert metadata.validate() is False

    def test_content_metadata_to_dict(self):
        """Test converting ContentMetadata to dictionary"""
        metadata = ContentMetadata(
            content_id="test-id",
            source_url="https://example.com",
            module="Module 1",
            quality_score=0.75,
            content_length=1000,
            word_count=200
        )

        result = metadata.to_dict()

        assert result["content_id"] == "test-id"
        assert result["source_url"] == "https://example.com"
        assert result["module"] == "Module 1"
        assert result["quality_score"] == 0.75
        assert result["content_length"] == 1000
        assert result["word_count"] == 200

    def test_content_metadata_from_dict(self):
        """Test creating ContentMetadata from dictionary"""
        data = {
            "content_id": "test-id",
            "source_url": "https://example.com",
            "module": "Module 1",
            "section": "Week 1-2",
            "version": "2.0.0",
            "quality_score": 0.85,
            "content_length": 1500,
            "word_count": 300,
            "language": "es",
            "content_structure": {"headings": ["Intro", "Details"]},
            "content_hash": "hash789"
        }

        metadata = ContentMetadata.from_dict(data)

        assert metadata.content_id == "test-id"
        assert metadata.source_url == "https://example.com"
        assert metadata.module == "Module 1"
        assert metadata.section == "Week 1-2"
        assert metadata.version == "2.0.0"
        assert metadata.quality_score == 0.85
        assert metadata.content_length == 1500
        assert metadata.word_count == 300
        assert metadata.language == "es"
        assert metadata.content_structure == {"headings": ["Intro", "Details"]}
        assert metadata.content_hash == "hash789"


if __name__ == "__main__":
    pytest.main([__file__])