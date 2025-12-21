"""
End-to-end integration tests for the complete pipeline
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from src.main import RAGExtractionPipeline
from src.models.extracted_content import ExtractedContent


class TestE2EPipeline:
    """End-to-end integration tests for the complete pipeline"""

    @patch('src.crawler.sitemap_parser.requests.get')
    def test_complete_extraction_to_storage_pipeline(self, mock_get):
        """Test the complete pipeline from extraction to storage"""
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

        # Test complete pipeline with mocked components
        with patch.object(pipeline.website_crawler, 'crawl_urls') as mock_crawl, \
             patch.object(pipeline.embedding_generator, 'batch_generate_with_validation') as mock_embed, \
             patch.object(pipeline.qdrant_client, 'create_collection_if_not_exists') as mock_create_col, \
             patch.object(pipeline.embedding_storage, 'store_with_deduplication') as mock_store:

            # Mock the crawl to return some content
            mock_content = ExtractedContent(
                url="https://example.com/page1",
                title="Test Page",
                content="This is test content for end-to-end pipeline testing.",
                module="Test Module",
                section="Test Section"
            )
            mock_crawl.return_value = [mock_content]

            # Mock embedding generation
            from src.models.extracted_content import EmbeddingVector
            mock_embedding = EmbeddingVector(
                id=mock_content.id,
                vector=[0.1, 0.2, 0.3, 0.4],
                payload={
                    "url": mock_content.url,
                    "title": mock_content.title,
                    "module": mock_content.module,
                    "section": mock_content.section
                }
            )
            mock_embed.return_value = [mock_embedding]

            # Mock Qdrant operations
            mock_create_col.return_value = True
            mock_store.return_value = {"status": "success", "count": 1}

            # Run extraction pipeline with temporary output directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Run extraction
                extracted_contents = pipeline.run_extraction_pipeline(
                    sitemap_url="https://example.com/sitemap.xml",
                    output_dir=temp_dir
                )

                # Verify extraction worked
                assert len(extracted_contents) == 1

                # Run embedding pipeline
                embedding_result = pipeline.run_embedding_pipeline(extracted_contents)

                # Verify embedding pipeline worked
                assert embedding_result["status"] == "success"