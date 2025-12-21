"""
Main pipeline script for RAG Chatbot - Website Content Extraction and Embedding
"""
import argparse
import asyncio
import os
from datetime import datetime
from typing import List, Dict, Any

from src.crawler.sitemap_parser import SitemapParser
from src.crawler.website_crawler import WebsiteCrawler, ContentExtractor
from src.storage.raw_text_storage import RawTextStorage
from src.storage.metadata_manager import MetadataManager
from src.embeddings.embedding_generator import EmbeddingGenerator, EmbeddingStorageManager
from src.models.extracted_content import ExtractedContent
from src.utils.config_loader import config
from src.utils.logger import logger
from src.utils.hash_utils import generate_content_hash
from src.embeddings.qdrant_client import qdrant_client


class RAGExtractionPipeline:
    """
    Main pipeline class that orchestrates the RAG website content extraction and embedding process
    """

    def __init__(self):
        self.sitemap_parser = SitemapParser(timeout=config.extraction_timeout)
        self.website_crawler = WebsiteCrawler()
        self.content_extractor = ContentExtractor()
        self.raw_text_storage = RawTextStorage()
        self.metadata_manager = MetadataManager()
        self.embedding_generator = EmbeddingGenerator()
        self.embedding_storage = EmbeddingStorageManager()
        self.qdrant_client = qdrant_client

    def extract_content_from_urls(self, urls: List[str]) -> List[ExtractedContent]:
        """
        Extract content from the provided URLs

        Args:
            urls: List of URLs to extract content from

        Returns:
            List of ExtractedContent objects
        """
        logger.info(f"Starting content extraction from {len(urls)} URLs")

        # Use the website crawler to extract content
        extracted_contents = self.website_crawler.crawl_urls(urls)

        logger.info(f"Completed content extraction. Extracted {len(extracted_contents)} items.")
        return extracted_contents

    def save_raw_content(self, extracted_contents: List[ExtractedContent], output_dir: str = "data/raw_text"):
        """
        Save extracted content to temporary storage for review

        Args:
            extracted_contents: List of extracted content objects
            output_dir: Directory to save the content
        """
        # Update the storage directory if needed
        self.raw_text_storage.storage_dir = output_dir

        # Use the RawTextStorage to save content
        saved_paths = self.raw_text_storage.save_multiple_content(extracted_contents)

        logger.info(f"Saved {len(saved_paths)} raw content files to {output_dir}")

    def generate_embeddings(self, extracted_contents: List[ExtractedContent], batch_size: int = 10):
        """
        Generate embeddings for extracted content using Cohere

        Args:
            extracted_contents: List of extracted content objects
            batch_size: Size of batches for embedding generation

        Returns:
            List of embedding dictionaries ready for Qdrant storage
        """
        # Use the EmbeddingGenerator to create embeddings
        embedding_vectors = self.embedding_generator.batch_generate_with_validation(
            extracted_contents, batch_size
        )

        # Convert EmbeddingVector objects to dictionaries for Qdrant
        embeddings_data = []
        for embedding_vector in embedding_vectors:
            embedding_data = {
                'id': embedding_vector.id,
                'vector': embedding_vector.vector,
                'payload': embedding_vector.payload
            }
            embeddings_data.append(embedding_data)

        logger.info(f"Generated {len(embeddings_data)} validated embeddings")
        return embeddings_data

    def run_extraction_pipeline(self, sitemap_url: str = None, output_dir: str = "data/raw_text"):
        """
        Run the full extraction pipeline: sitemap parsing -> content extraction -> save for review

        Args:
            sitemap_url: URL of the sitemap to parse (uses config if not provided)
            output_dir: Directory to save extracted content

        Returns:
            List of ExtractedContent objects
        """
        sitemap_url = sitemap_url or config.frontend_sitemap_url

        logger.info(f"Starting extraction pipeline for sitemap: {sitemap_url}")

        # 1. Parse sitemap to get URLs
        urls = self.sitemap_parser.get_all_urls(
            sitemap_url=sitemap_url,
            include_patterns=["/docs/", "/modules/", "/book/", "/chapter/"],  # Focus on content pages
            exclude_patterns=["/tag/", "/category/", "/search/", "/api/"]     # Exclude non-content pages
        )

        if not urls:
            logger.error("No URLs found in sitemap")
            return []

        logger.info(f"Found {len(urls)} URLs to process")

        # 2. Extract content from URLs
        extracted_contents = self.extract_content_from_urls(urls)

        # 3. Save raw content for review
        self.save_raw_content(extracted_contents, output_dir)

        logger.info(f"Extraction pipeline completed. Processed {len(extracted_contents)} pages.")
        return extracted_contents

    def run_embedding_pipeline(self, extracted_contents: List[ExtractedContent] = None,
                              batch_size: int = None):
        """
        Run the embedding pipeline: generate embeddings -> store in Qdrant

        Args:
            extracted_contents: List of extracted content objects (loads from raw_text if not provided)
            batch_size: Batch size for embedding generation (uses config if not provided)

        Returns:
            Results of the embedding storage operation
        """
        batch_size = batch_size or config.embedding_batch_size

        # If no extracted contents provided, we could load from raw text files
        # For now, we expect them to be passed in
        if not extracted_contents:
            logger.warning("No extracted contents provided. Skipping embedding generation.")
            return {"status": "skipped", "message": "No content provided for embedding"}

        logger.info(f"Starting embedding pipeline with {len(extracted_contents)} items")

        # 1. Create Qdrant collection if it doesn't exist
        success = self.qdrant_client.create_collection_if_not_exists()
        if not success:
            logger.error("Failed to create Qdrant collection")
            return {"status": "error", "message": "Failed to create Qdrant collection"}

        # 2. Generate embeddings
        embeddings_data = self.generate_embeddings(extracted_contents, batch_size)

        # 3. Store embeddings in Qdrant using the storage manager for deduplication
        result = self.embedding_storage.store_with_deduplication(
            [self._create_embedding_vector_from_data(ed) for ed in embeddings_data],
            batch_size
        )

        logger.info(f"Embedding pipeline completed. {result}")
        return result

    def _create_embedding_vector_from_data(self, embedding_data: Dict[str, Any]):
        """
        Helper method to create an EmbeddingVector from embedding data dictionary
        """
        from src.models.extracted_content import EmbeddingVector
        return EmbeddingVector(
            id=embedding_data['id'],
            vector=embedding_data['vector'],
            payload=embedding_data['payload']
        )

    def run_full_pipeline(self, sitemap_url: str = None, output_dir: str = "data/raw_text",
                         batch_size: int = None):
        """
        Run the complete RAG pipeline: extraction -> review -> embedding -> storage

        Args:
            sitemap_url: URL of the sitemap to parse (uses config if not provided)
            output_dir: Directory to save extracted content
            batch_size: Batch size for embedding generation (uses config if not provided)

        Returns:
            Dictionary with results of the full pipeline
        """
        logger.info("Starting full RAG pipeline")

        # 1. Run extraction pipeline
        extracted_contents = self.run_extraction_pipeline(sitemap_url, output_dir)

        if not extracted_contents:
            logger.error("Extraction pipeline returned no content. Aborting.")
            return {"status": "error", "message": "No content extracted"}

        # 2. Allow for content review (user should review content in output_dir before proceeding)
        logger.info(f"Content extracted and saved to {output_dir}. Please review before proceeding with embedding.")

        # 3. Run embedding pipeline
        embedding_result = self.run_embedding_pipeline(extracted_contents, batch_size)

        logger.info("Full RAG pipeline completed")
        return {
            "extraction": {
                "status": "completed",
                "count": len(extracted_contents)
            },
            "embedding": embedding_result
        }


def main():
    """
    Main function to run the RAG extraction pipeline from command line
    """
    parser = argparse.ArgumentParser(description="RAG Chatbot - Website Content Extraction and Embedding Pipeline")

    parser.add_argument(
        "--full-pipeline",
        action="store_true",
        help="Run the complete extraction and embedding pipeline"
    )
    parser.add_argument(
        "--extract-content",
        action="store_true",
        help="Run only the content extraction phase"
    )
    parser.add_argument(
        "--generate-embeddings",
        action="store_true",
        help="Run only the embedding generation phase"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Batch size for embedding generation (default: 10)"
    )
    parser.add_argument(
        "--sitemap-url",
        type=str,
        help="Sitemap URL to process (overrides config)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw_text",
        help="Directory to save extracted content (default: data/raw_text)"
    )

    args = parser.parse_args()

    # Initialize the pipeline
    pipeline = RAGExtractionPipeline()

    if args.full_pipeline:
        logger.info("Running full RAG pipeline...")
        result = pipeline.run_full_pipeline(
            sitemap_url=args.sitemap_url,
            output_dir=args.output_dir,
            batch_size=args.batch_size
        )
        print(f"Pipeline completed: {result}")

    elif args.extract_content:
        logger.info("Running content extraction only...")
        result = pipeline.run_extraction_pipeline(
            sitemap_url=args.sitemap_url,
            output_dir=args.output_dir
        )
        print(f"Extraction completed. Processed {len(result)} items.")

    elif args.generate_embeddings:
        logger.info("Running embedding generation only...")
        # Load previously extracted content from raw text storage
        raw_storage = RawTextStorage()
        extracted_contents = raw_storage.load_all_content()

        if not extracted_contents:
            print("No extracted content found in raw text storage. Please run extraction first.")
        else:
            print(f"Found {len(extracted_contents)} extracted content items. Generating embeddings...")
            result = pipeline.run_embedding_pipeline(extracted_contents, args.batch_size)
            print(f"Embedding generation completed: {result}")

    else:
        # Show help if no command provided
        parser.print_help()


if __name__ == "__main__":
    main()