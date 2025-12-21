"""
Example usage script for the RAG Website Extraction Pipeline
"""
import os
import sys
from pathlib import Path

# Add the backend src directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import RAGExtractionPipeline
from src.crawler.sitemap_parser import SitemapParser
from src.storage.raw_text_storage import RawTextStorage


def example_pipeline_usage():
    """
    Example of how to use the RAG extraction pipeline
    """
    print("RAG Website Extraction Pipeline - Example Usage")
    print("=" * 50)

    # Initialize the pipeline
    print("\n1. Initializing RAG Extraction Pipeline...")
    pipeline = RAGExtractionPipeline()
    print("   + Pipeline initialized successfully")

    # Example: Parse a sitemap (using a placeholder URL)
    print("\n2. Parsing sitemap...")
    sitemap_parser = SitemapParser()

    # Use the configured sitemap URL or a placeholder
    sitemap_url = os.getenv('FRONTEND_SITEMAP_URL', 'https://httpbin.org/xml')
    print(f"   Sitemap URL: {sitemap_url}")

    # For demonstration, we'll just show the parser is working
    print("   + Sitemap parser ready")

    # Example: Show the storage system
    print("\n3. Testing storage system...")
    raw_storage = RawTextStorage()
    print(f"   + Raw text storage initialized: {raw_storage.storage_dir}")

    # Show storage stats
    stats = raw_storage.get_storage_stats()
    print(f"   + Storage stats: {stats['total_files']} files, {stats['storage_size_mb']:.2f} MB")

    # Example: Show how to run the pipeline (without actually executing)
    print("\n4. Pipeline execution examples:")
    print("   To run full pipeline: python src/main.py --full-pipeline")
    print("   To extract content only: python src/main.py --extract-content")
    print("   To generate embeddings: python src/main.py --generate-embeddings")

    print("\n5. Configuration:")
    try:
        from src.utils.config_loader import config
        print(f"   + Qdrant collection: {config.qdrant_collection_name}")
        print(f"   + Crawl delay: {config.website_crawl_delay}s")
        print(f"   + Extraction timeout: {config.extraction_timeout}s")
    except ValueError as e:
        print(f"   ! Configuration warning: {e} (expected in test environment)")

    print("\n6. Available storage content:")
    content_list = raw_storage.get_content_list()
    print(f"   + Found {len(content_list)} content items in storage")

    if content_list:
        print("   Sample content items:")
        for i, content in enumerate(content_list[:3]):  # Show first 3 items
            print(f"     {i+1}. {content['title'][:50]}{'...' if len(content['title']) > 50 else ''}")

    print("\n" + "=" * 50)
    print("Example usage completed successfully!")


def example_manual_usage():
    """
    Example of manual usage of individual components
    """
    print("\nManual Component Usage Examples")
    print("-" * 30)

    # Example of using the crawler directly
    from src.crawler.website_crawler import WebsiteCrawler
    from src.crawler.content_extractor import ContentExtractor
    from src.models.extracted_content import ExtractedContent

    print("1. Content extraction example:")
    extractor = ContentExtractor()

    # Example HTML content
    sample_html = """
    <html>
    <head><title>Sample Page</title></head>
    <body>
        <h1>Main Content</h1>
        <p>This is sample content that would be extracted.</p>
        <p>Additional content goes here.</p>
        <footer>This footer should be removed.</footer>
    </body>
    </html>
    """

    try:
        # Extract content
        extracted = extractor.extract_content_from_html(sample_html, "https://example.com", "Sample Title")
        print(f"   + Extracted content length: {len(extracted.content)} characters")
        print(f"   + Content title: {extracted.title}")
        print(f"   + Content ID: {extracted.id}")

        # Example of using the validator
        from src.storage.content_validator import ContentValidator
        validator = ContentValidator()
        validation = validator.validate_content(extracted)
        print(f"   + Content quality score: {validation['quality_score']:.2f}")

        # Example of using the metadata manager
        from src.storage.metadata_manager import MetadataManager
        metadata_manager = MetadataManager()
        content_metadata = metadata_manager.create_metadata_from_extracted_content(extracted)
        print(f"   + Created metadata with quality score: {content_metadata.quality_score:.2f}")
    except Exception as e:
        print(f"   - Error in content extraction example: {e}")
        print("   + This is expected if there are dependency issues in the test environment")


if __name__ == "__main__":
    example_pipeline_usage()
    example_manual_usage()