# RAG Chatbot - Website Content Extraction and Embedding Pipeline

## Overview
This backend pipeline extracts content from Docusaurus websites, generates embeddings using Cohere, and stores them in Qdrant for RAG (Retrieval Augmented Generation) applications. The system is designed to automatically crawl and extract content from educational book websites, creating a queryable knowledge base for AI applications.

## Architecture
The system is organized into several modules:

### 1. Crawler Module (`src/crawler/`)
- **SitemapParser**: Parses sitemap.xml files to extract URLs for crawling
- **WebsiteCrawler**: Crawls websites and extracts content from pages
- **ContentExtractor**: Extracts and normalizes content, focusing on main content while removing navigation, footer, etc.

### 2. Storage Module (`src/storage/`)
- **RawTextStorage**: Temporarily stores extracted content for review
- **MetadataManager**: Manages content metadata and quality metrics
- **ContentValidator**: Validates content quality before embedding generation

### 3. Embeddings Module (`src/embeddings/`)
- **EmbeddingGenerator**: Generates vector embeddings using Cohere API
- **QdrantEmbeddingClient**: Handles storage and retrieval of embeddings in Qdrant vector database

### 4. Validation Module (`src/validation/`)
- **PreEmbeddingChecker**: Ensures content quality before embedding generation
- **VerificationReporter**: Generates reports on extraction and embedding processes

### 5. Utilities (`src/utils/`)
- **ConfigLoader**: Loads configuration from environment variables
- **Logger**: Provides logging functionality
- **HashUtils**: Generates content hashes for deduplication

## Pipeline Stages

### 1. Content Extraction
- Parse sitemap to discover all pages
- Crawl each page and extract main content
- Remove navigation, footer, ads, and other non-content elements
- Store extracted content temporarily for review

### 2. Content Validation & Review
- Validate content quality using multiple metrics
- Store content with metadata for review
- Allow for manual review before embedding generation

### 3. Embedding Generation
- Generate vector embeddings using Cohere models
- Apply quality checks and validation
- Handle API rate limits and errors

### 4. Storage in Qdrant
- Create Qdrant collection if it doesn't exist
- Store embeddings with complete metadata
- Implement deduplication using content hashes

## Setup

### Prerequisites
- Python 3.11+
- uv package manager

### Installation
1. Clone the repository
2. Navigate to the backend directory
3. Install dependencies:
   ```bash
   cd backend
   uv sync
   ```

### Environment Variables
Create a `.env` file with the following variables:

```env
COHERE_API_KEY=your_cohere_api_key_here
QDRANT_HOST=your_qdrant_host_url_here
QDRANT_API_KEY=your_qdrant_api_key_here
QDRANT_COLLECTION_NAME=book_content_embeddings
WEBSITE_CRAWL_DELAY=1
EXTRACTION_TIMEOUT=300
FRONTEND_SITEMAP_URL=https://your-docusaurus-website.com
EMBEDDING_BATCH_SIZE=10
```

## Usage

### Command Line Interface
The pipeline can be run using the main script:

```bash
# Run full pipeline (extraction + embedding)
python src/main.py --full-pipeline

# Run content extraction only
python src/main.py --extract-content

# Run embedding generation only (requires extracted content)
python src/main.py --generate-embeddings

# Run with custom sitemap URL
python src/main.py --full-pipeline --sitemap-url https://custom-site.com/sitemap.xml

# Run with custom batch size for embeddings
python src/main.py --generate-embeddings --batch-size 20
```

### Programmatic Usage
```python
from src.main import RAGExtractionPipeline

# Initialize pipeline
pipeline = RAGExtractionPipeline()

# Run full pipeline
result = pipeline.run_full_pipeline()

# Or run individual stages
extracted_content = pipeline.run_extraction_pipeline()
embedding_result = pipeline.run_embedding_pipeline(extracted_content)
```

## Features

### 1. Content Extraction
- Automatic sitemap parsing to discover all pages
- Intelligent content extraction focusing on main content
- Removal of navigation, footer, ads, and other non-content elements
- Support for Docusaurus and similar documentation sites

### 2. Quality Assurance
- Content validation with quality scoring
- Duplicate detection and removal
- Pre-embedding verification checks
- Comprehensive logging and reporting

### 3. Scalability
- Configurable batch processing
- Rate limiting to respect website policies
- Error handling and retry mechanisms
- Progress tracking

### 4. Deduplication
- Content hash-based deduplication
- URL-based duplicate detection
- Idempotent operations

### 5. Metadata Management
- Complete metadata preservation
- Quality metrics tracking
- Source URL tracking
- Content structure information

## API Endpoints (Planned)
Future implementation will include:
- POST /api/v1/extraction/start - Initiate content extraction
- GET /api/v1/extraction/status/{job_id} - Check extraction status
- GET /api/v1/extraction/content - Retrieve extracted content for review
- POST /api/v1/embeddings/generate - Generate embeddings
- POST /api/v1/embeddings/store - Store embeddings in Qdrant
- GET /api/v1/health - Health check

## Configuration

### Environment Variables
- `COHERE_API_KEY`: API key for Cohere embedding service
- `QDRANT_HOST`: URL of your Qdrant instance
- `QDRANT_API_KEY`: API key for Qdrant authentication
- `QDRANT_COLLECTION_NAME`: Name of the collection in Qdrant
- `WEBSITE_CRAWL_DELAY`: Delay in seconds between requests (default: 1)
- `EXTRACTION_TIMEOUT`: Timeout in seconds for extraction operations (default: 300)
- `FRONTEND_SITEMAP_URL`: Base URL of the Docusaurus website to crawl and extract content from
- `EMBEDDING_BATCH_SIZE`: Batch size for embedding generation (default: 10)

### Quality Thresholds
- Minimum content length: 50 characters
- Minimum quality score: 0.5 for content to be embedded
- Maximum duplicate ratio: 10% of content

## Testing
Run the test suite to verify functionality:

```bash
python test_rag_extraction.py
```

## Example Usage
```python
from src.main import RAGExtractionPipeline

# Initialize the pipeline
pipeline = RAGExtractionPipeline()

# Run the full pipeline
result = pipeline.run_full_pipeline(
    sitemap_url="https://your-website.com/sitemap.xml",
    output_dir="data/raw_text",
    batch_size=10
)

print(f"Pipeline completed: {result}")
```

## Data Models

### ExtractedContent
Represents raw content extracted from the website:
- `id`: Unique identifier
- `url`: Source URL
- `title`: Page title
- `content`: Extracted content text
- `module`, `section`: Content organization
- `metadata`: Additional metadata dictionary
- `content_hash`: Hash for deduplication

### EmbeddingVector
Represents vector embeddings:
- `id`: Matches ExtractedContent.id
- `vector`: Embedding vector from Cohere
- `payload`: Metadata for Qdrant storage

### ContentMetadata
Contains content structure and quality information:
- `content_id`: Reference to ExtractedContent
- `source_url`: Original URL
- `quality_score`: Quality assessment (0.0-1.0)
- `content_structure`: Information about headings, code blocks, etc.

## Security Considerations
- API keys are loaded from environment variables
- No sensitive data is logged
- Input validation on all endpoints
- Rate limiting to prevent abuse

## Performance Considerations
- Configurable batch sizes for embedding generation
- Rate limiting for website crawling
- Efficient content hashing for deduplication
- Memory-efficient processing for large websites

## Troubleshooting

### Common Issues
1. **Missing environment variables**: Ensure all required environment variables are set
2. **Cohere API errors**: Check API key validity and rate limits
3. **Qdrant connection errors**: Verify host URL and API key
4. **Crawling timeouts**: Increase EXTRACTION_TIMEOUT value

### Logging
The system logs to both console and files in the `logs/` directory. Check logs for detailed error information.

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License
[Specify license here]