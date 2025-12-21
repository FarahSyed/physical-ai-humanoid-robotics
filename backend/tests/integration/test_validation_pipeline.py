"""
Integration tests for validation pipeline
"""
import pytest
import tempfile
import os
from src.storage.content_validator import ContentValidator
from src.storage.metadata_manager import MetadataManager
from src.storage.review_checker import ReviewChecker
from src.models.extracted_content import ExtractedContent


class TestValidationPipeline:
    """Integration tests for the content validation pipeline"""

    def test_content_validation_and_metadata_integration(self):
        """Test that content validation works with metadata management"""
        # Create test content
        content = ExtractedContent(
            url="https://example.com/test",
            title="Test Page",
            content="This is test content for validation integration testing.",
            module="Test Module",
            section="Test Section"
        )

        # Test validation
        validator = ContentValidator()
        is_valid, quality_score = validator.validate_content(content)

        # Should be valid (basic content)
        assert is_valid
        assert 0.0 <= quality_score <= 1.0

        # Test metadata management
        metadata_manager = MetadataManager()
        metadata = metadata_manager.create_metadata(content)

        # Verify metadata was created correctly
        assert metadata.content_id == content.id
        assert metadata.source_url == content.url
        assert metadata.quality_score == quality_score

    def test_review_mechanism_integration(self):
        """Test the review mechanism"""
        # Create test content
        content = ExtractedContent(
            url="https://example.com/test",
            title="Test Page",
            content="This is test content for review integration testing.",
            module="Test Module",
            section="Test Section"
        )

        # Test review checker
        checker = ReviewChecker()
        needs_review = checker.needs_review(content)

        # Should not need review for valid content
        assert not needs_review