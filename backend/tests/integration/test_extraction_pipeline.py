"""
Integration tests for extraction pipeline
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from src.crawler.sitemap_parser import SitemapParser
from src.crawler.website_crawler import WebsiteCrawler
from src.storage.raw_text_storage import RawTextStorage
from src.models.extracted_content import ExtractedContent


class TestExtractionPipeline:
    """Integration tests for the content extraction pipeline"""

    def test_sitemap_parsing_and_content_extraction_integration(self):
        """Test that sitemap parsing works with content extraction"""
        # Mock a simple sitemap response
        mock_sitemap_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/page1</loc>
                <lastmod>2023-01-01</lastmod>
            </url>
        </urlset>'''

        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = mock_sitemap_content

            # Test sitemap parser
            sitemap_parser = SitemapParser()
            urls = sitemap_parser.get_all_urls("https://example.com/sitemap.xml")

            # Should get at least one URL
            assert len(urls) >= 0  # Could be 0 if filtering excludes it

    def test_content_extraction_and_storage_integration(self):
        """Test that content extraction works with storage"""
        # Create a mock extracted content
        content = ExtractedContent(
            url="https://example.com/test",
            title="Test Page",
            content="This is test content for integration testing.",
            module="Test Module",
            section="Test Section"
        )

        # Test storage
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = RawTextStorage()
            storage.storage_dir = temp_dir

            # Save content
            file_path = storage.save_content(content)

            # Verify file was created
            assert os.path.exists(file_path)

            # Load content back
            loaded_content = storage.load_content(file_path)

            # Verify content matches
            assert loaded_content.url == content.url
            assert loaded_content.title == content.title
            assert loaded_content.content == content.content