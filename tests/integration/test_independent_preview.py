"""
Independent test for preview functionality.
This test verifies that the preview service works correctly in isolation,
without dependencies on the state management or approval systems.
"""
import os
import tempfile
import unittest

from src.pipeline.preview_service import PreviewService


class TestIndependentPreview(unittest.TestCase):
    """
    Independent test for preview functionality.
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        self.preview_service = PreviewService(max_preview_length=5000, default_sample_size=500)

    def test_preview_extracted_content_success(self):
        """
        Independent test: Preview extracted content successfully.
        """
        # Create a temporary content file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("This is test content for preview functionality. " * 5)  # Create content
            content_file_path = content_file.name

        try:
            # Test previewing extracted content
            result = self.preview_service.preview_extracted_content(content_file_path, offset=0, limit=30)

            # Verify the result
            self.assertIsNotNone(result)
            self.assertEqual(result["preview_type"], "extracted_content")
            self.assertEqual(result["source_path"], content_file_path)
            self.assertIn("This is test content", result["preview_content"])
            self.assertLessEqual(len(result["preview_content"]), 30)  # Should respect limit
            self.assertEqual(result["total_length"], len("This is test content for preview functionality. " * 5))
        finally:
            # Clean up temporary file
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_preview_extracted_content_with_offset(self):
        """
        Independent test: Preview extracted content with offset.
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
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_preview_extracted_content_file_not_exists(self):
        """
        Independent test: Preview extracted content when file doesn't exist.
        """
        # Test with non-existent file
        result = self.preview_service.preview_extracted_content("/nonexistent/file.txt")

        # Verify the result is None
        self.assertIsNone(result)

    def test_preview_extracted_content_with_various_offsets_and_limits(self):
        """
        Independent test: Preview extracted content with various offset and limit combinations.
        """
        # Create a temporary content file
        content = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write(content)
            content_file_path = content_file.name

        try:
            # Test different combinations
            test_cases = [
                (0, 5, "ABCDE"),      # Start of content
                (5, 5, "FGHIJ"),      # Middle of content
                (20, 5, "UVWXY"),     # End of content (offset 20, limit 5 gives 5 chars: U,V,W,X,Y)
                (0, 10, "ABCDEFGHIJ"), # More than available at end
                (25, 10, "Z"),        # Beyond content start (offset 25, limit 10 gives 1 char: Z)
            ]

            for offset, limit, expected in test_cases:
                result = self.preview_service.preview_extracted_content(content_file_path, offset=offset, limit=limit)
                if offset < len(content):
                    self.assertIsNotNone(result)
                    self.assertEqual(result["preview_content"], expected)
                else:
                    # If offset is beyond content length, result should be empty string or None depending on validation
                    self.assertIsNotNone(result)  # Should still return a result object
                    self.assertEqual(result["preview_content"], "")  # Should be empty
        finally:
            # Clean up temporary file
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_preview_chunked_output_success(self):
        """
        Independent test: Preview chunked output successfully.
        """
        # Create a temporary chunked file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as chunk_file:
            chunk_file.write("First chunk. Second chunk. Third chunk.")
            chunk_file_path = chunk_file.name

        try:
            # Test previewing chunked output
            result = self.preview_service.preview_chunked_output(chunk_file_path, offset=0, limit=15)

            # Verify the result
            self.assertIsNotNone(result)
            self.assertEqual(result["preview_type"], "chunked_output")
            self.assertEqual(result["source_path"], chunk_file_path)
            self.assertIn("First chunk", result["preview_content"])
            self.assertLessEqual(len(result["preview_content"]), 15)  # Should respect limit
        finally:
            # Clean up temporary file
            if os.path.exists(chunk_file_path):
                os.remove(chunk_file_path)

    def test_preview_chunked_output_with_specific_chunk(self):
        """
        Independent test: Preview a specific chunk from chunked output.
        """
        # Create a temporary chunked file with JSON array format to be parsed as chunks
        chunked_data = ["First chunk content", "Second chunk content", "Third chunk content"]
        import json
        chunked_json = json.dumps(chunked_data)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as chunk_file:
            chunk_file.write(chunked_json)
            chunk_file_path = chunk_file.name

        try:
            # Test previewing the second chunk (index 1)
            result = self.preview_service.preview_chunked_output(chunk_file_path, chunk_index=1, offset=0, limit=10)

            # Verify the result
            self.assertIsNotNone(result)
            self.assertEqual(result["chunk_index"], 1)
            self.assertEqual(result["chunk_total"], 3)
            self.assertLessEqual(len(result["preview_content"]), 10)  # Should respect limit
            # Should contain part of "Second chunk content"
            self.assertIn("Second", result["preview_content"])
        finally:
            # Clean up temporary file
            if os.path.exists(chunk_file_path):
                os.remove(chunk_file_path)

    def test_preview_chunked_output_invalid_chunk_index(self):
        """
        Independent test: Preview chunked output with invalid chunk index.
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
            if os.path.exists(chunk_file_path):
                os.remove(chunk_file_path)

    def test_generate_content_sample_success(self):
        """
        Independent test: Generate content sample successfully.
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
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_generate_content_sample_file_not_exists(self):
        """
        Independent test: Generate content sample when file doesn't exist.
        """
        # Test with non-existent file
        result = self.preview_service.generate_content_sample("/nonexistent/file.txt")

        # Verify the result is None
        self.assertIsNone(result)

    def test_preview_large_content_with_pagination(self):
        """
        Independent test: Preview large content with pagination.
        """
        # Create a temporary content file with more content
        large_content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7\nLine 8\nLine 9\nLine 10\n"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write(large_content)
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
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_preview_large_content_with_pagination_multiple_pages(self):
        """
        Independent test: Preview large content with pagination on multiple pages.
        """
        # Create content that will span multiple pages
        content = "A" * 100  # 100 characters
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write(content)
            content_file_path = content_file.name

        try:
            # Test previewing with small page size to create multiple pages
            result_page1 = self.preview_service.preview_large_content_with_pagination(content_file_path, page=1, page_size=30)
            result_page2 = self.preview_service.preview_large_content_with_pagination(content_file_path, page=2, page_size=30)
            result_page4 = self.preview_service.preview_large_content_with_pagination(content_file_path, page=4, page_size=30)

            # Verify the results
            self.assertIsNotNone(result_page1)
            self.assertIsNotNone(result_page2)
            # Page 4 might be empty or contain remaining content
            self.assertIsNotNone(result_page4)

            # Check that different pages have different content (or at least different offsets)
            self.assertEqual(result_page1["page"], 1)
            self.assertEqual(result_page2["page"], 2)
            self.assertEqual(result_page4["page"], 4)

            # Check total pages calculation
            self.assertGreaterEqual(result_page1["total_pages"], 3)  # Should need at least 4 pages for 100 chars with page_size 30
        finally:
            # Clean up temporary file
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_validate_preview_safety_safe_content(self):
        """
        Independent test: Validate preview safety with safe content.
        """
        safe_content = "This is safe content without harmful elements."

        # Test validation
        result = self.preview_service.validate_preview_safety(safe_content)

        # Verify the result
        self.assertTrue(result)

    def test_validate_preview_safety_unsafe_content(self):
        """
        Independent test: Validate preview safety with unsafe content.
        """
        unsafe_content = 'This content has <script>alert("xss")</script> harmful elements.'

        # Test validation
        result = self.preview_service.validate_preview_safety(unsafe_content)

        # Verify the result
        self.assertFalse(result)

    def test_sanitize_preview_content(self):
        """
        Independent test: Sanitize preview content.
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
        Independent test: Preview content that exceeds maximum length.
        """
        # Create a temporary content file with very long content
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("A" * 6000)  # Content longer than max length (5000)
            content_file_path = content_file.name

        try:
            # Test previewing content that exceeds max length
            result = self.preview_service.preview_extracted_content(content_file_path)

            # Verify the result is None (content too long)
            self.assertIsNone(result)
        finally:
            # Clean up temporary file
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_preview_extracted_content_empty_file(self):
        """
        Independent test: Preview content from an empty file.
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
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_preview_service_configuration(self):
        """
        Independent test: Preview service with different configurations.
        """
        # Create service with different settings
        custom_preview_service = PreviewService(max_preview_length=1000, default_sample_size=100)

        # Create content file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("Test content for configuration testing." * 3)
            content_file_path = content_file.name

        try:
            # Test with default limit (should use default_sample_size of 100)
            result = custom_preview_service.preview_extracted_content(content_file_path)

            # Verify the result uses the custom default
            self.assertIsNotNone(result)
            self.assertLessEqual(len(result["preview_content"]), 100)  # Should respect custom default
        finally:
            # Clean up temporary file
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_preview_chunk_parsing(self):
        """
        Independent test: Preview service chunk parsing functionality.
        """
        # Test the internal chunk parsing with JSON array
        import json
        chunks_data = ["Chunk 1 content", "Chunk 2 content", "Chunk 3 content"]
        json_content = json.dumps(chunks_data)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as chunk_file:
            chunk_file.write(json_content)
            chunk_file_path = chunk_file.name

        try:
            # Test previewing specific chunks
            result1 = self.preview_service.preview_chunked_output(chunk_file_path, chunk_index=0)
            result2 = self.preview_service.preview_chunked_output(chunk_file_path, chunk_index=2)

            # Verify the results
            self.assertIsNotNone(result1)
            self.assertIsNotNone(result2)
            self.assertEqual(result1["chunk_total"], 3)
            self.assertIn("Chunk 1", result1["preview_content"])
            self.assertIn("Chunk 3", result2["preview_content"])
        finally:
            # Clean up temporary file
            if os.path.exists(chunk_file_path):
                os.remove(chunk_file_path)


if __name__ == '__main__':
    unittest.main()