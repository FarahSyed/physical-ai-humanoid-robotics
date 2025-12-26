"""
Unit tests for the preview service module.
"""
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from src.pipeline.preview_service import PreviewService
from src.utils.validation_utils import validate_preview_params


class TestPreviewService(unittest.TestCase):
    """
    Test cases for PreviewService functionality.
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        self.preview_service = PreviewService(max_preview_length=1000, default_sample_size=200)

    def test_preview_extracted_content_success(self):
        """
        Test previewing extracted content successfully.
        """
        # Create a temporary content file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("This is test content for preview functionality. " * 10)  # Create content longer than default sample
            content_file_path = content_file.name

        try:
            # Test previewing extracted content
            result = self.preview_service.preview_extracted_content(content_file_path, offset=0, limit=50)

            # Verify the result
            self.assertIsNotNone(result)
            self.assertEqual(result["preview_type"], "extracted_content")
            self.assertEqual(result["source_path"], content_file_path)
            self.assertIn("This is test content for preview functionality.", result["preview_content"])
            self.assertLessEqual(len(result["preview_content"]), 50)  # Should respect limit
        finally:
            # Clean up temporary file
            os.remove(content_file_path)

    def test_preview_extracted_content_with_offset(self):
        """
        Test previewing extracted content with offset.
        """
        # Create a temporary content file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("0123456789" * 10)  # "01234567890123456789..."
            content_file_path = content_file.name

        try:
            # Test previewing with offset
            result = self.preview_service.preview_extracted_content(content_file_path, offset=5, limit=10)

            # Verify the result
            self.assertIsNotNone(result)
            self.assertEqual(result["preview_content"], "5678901234")  # Content starting at offset 5, length 10
        finally:
            # Clean up temporary file
            os.remove(content_file_path)

    def test_preview_extracted_content_file_not_exists(self):
        """
        Test previewing extracted content when file doesn't exist.
        """
        # Test with non-existent file
        result = self.preview_service.preview_extracted_content("/nonexistent/file.txt")

        # Verify the result is None
        self.assertIsNone(result)

    def test_preview_extracted_content_invalid_params(self):
        """
        Test previewing extracted content with invalid parameters.
        """
        # Create a temporary content file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("Test content")
            content_file_path = content_file.name

        try:
            # Test with invalid offset (beyond content length)
            result = self.preview_service.preview_extracted_content(content_file_path, offset=50, limit=10)

            # Verify the result is None
            self.assertIsNone(result)
        finally:
            # Clean up temporary file
            os.remove(content_file_path)

    def test_preview_chunked_output_success(self):
        """
        Test previewing chunked output successfully.
        """
        # Create a temporary chunked file - using simple content that will be split into chunks
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as chunk_file:
            chunk_file.write("First chunk content. Second chunk content. Third chunk content.")
            chunk_file_path = chunk_file.name

        try:
            # Test previewing chunked output (preview the first 10 characters of the content)
            result = self.preview_service.preview_chunked_output(chunk_file_path, chunk_index=0, offset=0, limit=10)

            # Verify the result
            self.assertIsNotNone(result)
            self.assertEqual(result["preview_type"], "chunked_output")
            self.assertEqual(result["source_path"], chunk_file_path)
            self.assertLessEqual(len(result["preview_content"]), 10)  # Should respect limit
        finally:
            # Clean up temporary file
            os.remove(chunk_file_path)

    def test_preview_chunked_output_specific_chunk(self):
        """
        Test previewing a specific chunk from chunked output.
        """
        # Create a temporary chunked file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as chunk_file:
            chunk_file.write("First chunk content. Second chunk content. Third chunk content.")
            chunk_file_path = chunk_file.name

        try:
            # Test previewing specific chunk
            result = self.preview_service.preview_chunked_output(chunk_file_path, chunk_index=0, offset=0, limit=15)

            # Verify the result
            self.assertIsNotNone(result)
            self.assertLessEqual(len(result["preview_content"]), 15)  # Should respect limit
        finally:
            # Clean up temporary file
            os.remove(chunk_file_path)

    def test_preview_chunked_output_invalid_chunk_index(self):
        """
        Test previewing chunked output with invalid chunk index.
        """
        # Create a temporary chunked file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as chunk_file:
            chunk_file.write("Test content")
            chunk_file_path = chunk_file.name

        try:
            # Test with invalid chunk index
            result = self.preview_service.preview_chunked_output(chunk_file_path, chunk_index=10, offset=0, limit=10)

            # Verify the result is None
            self.assertIsNone(result)
        finally:
            # Clean up temporary file
            os.remove(chunk_file_path)

    def test_preview_chunked_output_file_not_exists(self):
        """
        Test previewing chunked output when file doesn't exist.
        """
        # Test with non-existent file
        result = self.preview_service.preview_chunked_output("/nonexistent/file.txt")

        # Verify the result is None
        self.assertIsNone(result)

    def test_generate_content_sample_success(self):
        """
        Test generating content sample successfully.
        """
        # Create a temporary content file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("This is test content for sample generation. " * 5)
            content_file_path = content_file.name

        try:
            # Test generating content sample
            result = self.preview_service.generate_content_sample(content_file_path, sample_size=30)

            # Verify the result
            self.assertIsNotNone(result)
            self.assertIn("This is test content", result)
            self.assertLessEqual(len(result), 30)  # Should respect sample size
        finally:
            # Clean up temporary file
            os.remove(content_file_path)

    def test_generate_content_sample_file_not_exists(self):
        """
        Test generating content sample when file doesn't exist.
        """
        # Test with non-existent file
        result = self.preview_service.generate_content_sample("/nonexistent/file.txt")

        # Verify the result is None
        self.assertIsNone(result)

    def test_preview_large_content_with_pagination(self):
        """
        Test previewing large content with pagination.
        """
        # Create a temporary content file with more content
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7\nLine 8\nLine 9\nLine 10\n")
            content_file_path = content_file.name

        try:
            # Test previewing with pagination (page 1)
            result = self.preview_service.preview_large_content_with_pagination(content_file_path, page=1, page_size=20)

            # Verify the result
            self.assertIsNotNone(result)
            self.assertEqual(result["preview_type"], "paginated_content")
            self.assertEqual(result["page"], 1)
            self.assertGreater(result["total_pages"], 0)  # Should have at least one page
        finally:
            # Clean up temporary file
            os.remove(content_file_path)

    def test_preview_large_content_with_pagination_second_page(self):
        """
        Test previewing large content with pagination on second page.
        """
        # Create a temporary content file with more content
        large_content = "Line " + "\nLine ".join(str(i) for i in range(2, 21))  # Lines 1 through 20
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write(large_content)
            content_file_path = content_file.name

        try:
            # Test previewing with pagination (page 2)
            result = self.preview_service.preview_large_content_with_pagination(content_file_path, page=2, page_size=10)

            # Verify the result
            self.assertIsNotNone(result)
            self.assertEqual(result["page"], 2)
            self.assertGreaterEqual(result["total_pages"], 2)  # Should have at least 2 pages
        finally:
            # Clean up temporary file
            os.remove(content_file_path)

    def test_validate_preview_safety_safe_content(self):
        """
        Test validating preview safety with safe content.
        """
        safe_content = "This is safe content without harmful elements."

        # Test validation
        result = self.preview_service.validate_preview_safety(safe_content)

        # Verify the result
        self.assertTrue(result)

    def test_validate_preview_safety_unsafe_content(self):
        """
        Test validating preview safety with unsafe content.
        """
        unsafe_content = 'This content has <script>alert("xss")</script> harmful elements.'

        # Test validation
        result = self.preview_service.validate_preview_safety(unsafe_content)

        # Verify the result
        self.assertFalse(result)

    def test_sanitize_preview_content(self):
        """
        Test sanitizing preview content.
        """
        unsafe_content = '<script>alert("test");</script>Hello World'

        # Test sanitization
        result = self.preview_service.sanitize_preview_content(unsafe_content)

        # Verify the result
        self.assertIn("Hello World", result)  # Safe content should remain
        self.assertNotIn("<script>", result)  # Harmful content should be removed/replaced
        self.assertIn("&lt;script", result)  # Opening script tag should be escaped

    def test_preview_extracted_content_exceeds_max_length(self):
        """
        Test previewing content that exceeds maximum length.
        """
        # Create a temporary content file with very long content
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("A" * 2000)  # Content longer than default max length (1000)
            content_file_path = content_file.name

        try:
            # Test previewing content that exceeds max length
            result = self.preview_service.preview_extracted_content(content_file_path)

            # Verify the result is None (content too long)
            self.assertIsNone(result)
        finally:
            # Clean up temporary file
            os.remove(content_file_path)

    def test_preview_extracted_content_empty_file(self):
        """
        Test previewing content from an empty file.
        """
        # Create a temporary empty content file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("")  # Empty file
            content_file_path = content_file.name

        try:
            # Test previewing empty content
            result = self.preview_service.preview_extracted_content(content_file_path)

            # Verify the result
            self.assertIsNotNone(result)
            self.assertEqual(result["preview_content"], "")
            self.assertEqual(result["total_length"], 0)
        finally:
            # Clean up temporary file
            os.remove(content_file_path)


if __name__ == '__main__':
    unittest.main()