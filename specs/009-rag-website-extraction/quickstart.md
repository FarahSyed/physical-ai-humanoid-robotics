# Quickstart Guide: RAG Chatbot - Website Content Extraction and Embedding

## Overview
This guide provides step-by-step instructions to set up and run the RAG Chatbot content extraction and embedding pipeline.

## Prerequisites
- Python 3.11 or higher
- pip package manager
- Git
- Access to Cohere API (for embeddings)
- Access to Qdrant vector database
- Basic knowledge of command line operations

## Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Navigate to Backend Directory
```bash
cd backend
```

### 3. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

If requirements.txt doesn't exist yet, install the core dependencies:
```bash
pip install requests beautifulsoup4 cohere qdrant-client python-dotenv playwright lxml pytest
```

### 5. Set Up Environment Variables
Copy the example environment file:
```bash
cp .env.example .env
```

Edit the `.env` file with your specific values:
```env
COHERE_API_KEY=your_cohere_api_key_here
QDRANT_HOST=your_qdrant_host_url_here
QDRANT_API_KEY=your_qdrant_api_key_here
QDRANT_COLLECTION_NAME=book_content_embeddings
WEBSITE_CRAWL_DELAY=1
EXTRACTION_TIMEOUT=300
FRONTEND_SITEMAP_URL=https://your-docusaurus-website.com
```

### 6. Install Playwright Browser Drivers
```bash
playwright install
```

## Running the Pipeline

### Option 1: Run Full Pipeline (Recommended)
```bash
python src/main.py --full-pipeline
```

### Option 2: Run Pipeline Stages Separately

#### Stage 1: Content Extraction
```bash
python src/main.py --extract-content
```

#### Stage 2: Content Review
Review the extracted content in `backend/data/raw_text/` before proceeding to embedding generation.

#### Stage 3: Embedding Generation
```bash
python src/main.py --generate-embeddings --batch-size 10
```

#### Stage 4: Store in Qdrant
```bash
python src/main.py --store-embeddings
```

## Configuration Options

### Command Line Arguments
```bash
python src/main.py --help
```

Available options:
- `--full-pipeline`: Run the entire pipeline from extraction to storage
- `--extract-content`: Only run the content extraction phase
- `--generate-embeddings`: Only generate embeddings from extracted content
- `--store-embeddings`: Only store pre-generated embeddings in Qdrant
- `--batch-size`: Set the batch size for embedding generation (default: 10)
- `--deduplicate`: Enable/disable deduplication (default: True)
- `--limit-modules`: Limit extraction to specific modules only
- `--quality-threshold`: Set minimum quality score for embedding (default: 0.7)

### Environment Variables
- `COHERE_API_KEY`: API key for Cohere embedding service
- `QDRANT_HOST`: URL of your Qdrant instance
- `QDRANT_API_KEY`: API key for Qdrant authentication
- `QDRANT_COLLECTION_NAME`: Name of the collection in Qdrant
- `WEBSITE_CRAWL_DELAY`: Delay in seconds between requests (default: 1)
- `EXTRACTION_TIMEOUT`: Timeout in seconds for extraction operations (default: 300)
- `FRONTEND_SITEMAP_URL`: Base URL of the Docusaurus website to crawl and extract content from
- `EMBEDDING_BATCH_SIZE`: Default batch size for embedding generation (default: 10)

## Verification Steps

### 1. Check Extracted Content
Verify content was extracted successfully:
```bash
ls -la backend/data/raw_text/
head -20 backend/data/raw_text/*.json
```

### 2. Verify Embeddings Generation
Check embedding files:
```bash
ls -la backend/data/embeddings/
```

### 3. Confirm Qdrant Storage
Check that vectors were stored in Qdrant:
- Use Qdrant web UI or API to verify collection contents
- Check collection point count matches expected number

### 4. Run Tests
```bash
pytest tests/
```

## Troubleshooting

### Common Issues

#### Issue: Playwright Browser Errors
**Solution**:
```bash
playwright install chromium
```

#### Issue: Connection Timeout
**Solution**: Increase timeout values in `.env`:
```env
EXTRACTION_TIMEOUT=600
```

#### Issue: Rate Limiting
**Solution**: Increase crawl delay in `.env`:
```env
WEBSITE_CRAWL_DELAY=2
```

#### Issue: Qdrant Connection Failure
**Solution**: Verify Qdrant host and API key in `.env`

#### Issue: Duplicate Content Processing
**Solution**: Ensure the deduplication feature is enabled and content hashes are being generated properly

## Next Steps
1. Integrate with your RAG application to query the generated embeddings
2. Set up scheduled runs for content updates
3. Monitor pipeline logs for ongoing performance
4. Adjust quality thresholds based on results
5. Fine-tune the embedding batch size for optimal performance