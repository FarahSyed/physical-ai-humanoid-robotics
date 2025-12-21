"""
Integration tests for pre-embedding verification
"""
import pytest
from src.validation.pre_embedding_checker import PreEmbeddingChecker
from src.validation.verification_reporter import VerificationReporter
from src.models.extracted_content import ExtractedContent


class TestPreEmbeddingVerification:
    """Integration tests for the pre-embedding verification pipeline"""

    def test_pre_embedding_check_and_reporting_integration(self):
        """Test that pre-embedding checks work with verification reporting"""
        # Create test content
        content = ExtractedContent(
            url="https://example.com/test",
            title="Test Page",
            content="This is test content for pre-embedding verification integration testing.",
            module="Test Module",
            section="Test Section"
        )

        # Test pre-embedding checker
        checker = PreEmbeddingChecker()
        is_approved = checker.is_content_approved(content)

        # Should be approved for basic valid content
        assert is_approved

        # Test verification reporter
        reporter = VerificationReporter()
        report = reporter.generate_content_report([content])

        # Verify report structure
        assert 'total_content' in report
        assert 'approved_content' in report
        assert 'rejected_content' in report
        assert report['total_content'] == 1
        assert report['approved_content'] == 1