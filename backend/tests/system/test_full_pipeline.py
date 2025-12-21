"""
System tests for the full pipeline
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from src.main import RAGExtractionPipeline
from src.models.extracted_content import ExtractedContent


class TestFullPipeline:
    """System tests for the complete RAG pipeline"""

    @patch('src.crawler.sitemap_parser.requests.get')
    def test_full_pipeline_execution(self, mock_get):
        """Test the complete pipeline execution"""
        # Mock a simple sitemap response
        mock_sitemap_content = '''<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url>
                <loc>https://example.com/page1</loc>
                <lastmod>2023-01-01</lastmod>
            </url>
        </urlset>'''

        mock_get.return_value.status_code = 200
        mock_get.return_value.text = mock_sitemap_content

        # Create pipeline instance
        pipeline = RAGExtractionPipeline()

        # Test extraction pipeline (with mocked crawling)
        with patch.object(pipeline.website_crawler, 'crawl_urls') as mock_crawl:
            # Mock the crawl to return some content
            mock_content = ExtractedContent(
                url="https://example.com/page1",
                title="Test Page",
                content="This is test content for full pipeline testing.",
                module="Test Module",
                section="Test Section"
            )
            mock_crawl.return_value = [mock_content]

            # Run extraction pipeline with temporary output directory
            with tempfile.TemporaryDirectory() as temp_dir:
                extracted_contents = pipeline.run_extraction_pipeline(
                    sitemap_url="https://example.com/sitemap.xml",
                    output_dir=temp_dir
                )

                # Verify extraction worked
                assert len(extracted_contents) == 1
                assert extracted_contents[0].url == "https://example.com/page1"

    def test_pipeline_with_no_content(self):
        """Test pipeline behavior when no content is found"""
        pipeline = RAGExtractionPipeline()

        # Test with empty content list
        result = pipeline.run_embedding_pipeline([])
        assert result["status"] == "skipped"