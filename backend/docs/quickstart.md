# Quick Start Guide - RAG Website Extraction Pipeline

## Overview
This guide will help you quickly set up and run the RAG website content extraction pipeline. The pipeline automatically crawls a Docusaurus website, extracts content, generates embeddings, and stores them in Qdrant for RAG applications.

## Prerequisites
- Python 3.11+
- uv package manager
- Access to Cohere API
- Access to Qdrant vector database

## Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd physical-ai-humanoid-robotics/backend
```

### 2. Install dependencies using uv
```bash
uv sync
```

### 3. Set up environment variables
Create a `.env` file in the backend directory with your API keys and configuration:

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

## Quick Run

### 1. Run the full pipeline
```bash
python src/main.py --full-pipeline
```

This will:
- Parse the sitemap from `FRONTEND_SITEMAP_URL`
- Crawl and extract content from all pages
- Store raw content in `data/raw_text/` for review
- Generate embeddings using Cohere
- Store embeddings in Qdrant database

### 2. Run individual stages

If you want to run the pipeline in stages:

```bash
# Step 1: Extract content only
python src/main.py --extract-content

# Step 2: Generate embeddings (requires extracted content)
python src/main.py --generate-embeddings
```

## Verification

### Check extracted content
After running extraction, check the `data/raw_text/` directory for extracted content files.

### Verify embeddings in Qdrant
You can use the Qdrant dashboard or API to verify that embeddings were stored correctly.

## Example with Custom Parameters

```bash
# Run with custom sitemap URL and batch size
python src/main.py --full-pipeline \
  --sitemap-url https://docs.example.com/sitemap.xml \
  --batch-size 20 \
  --output-dir ./custom_output
```

## Troubleshooting

### Common Issues

1. **Environment variables not found**: Make sure your `.env` file is in the backend directory
2. **Cohere API errors**: Verify your API key and check rate limits
3. **Qdrant connection errors**: Check host URL and API key
4. **Crawling timeouts**: Increase the `EXTRACTION_TIMEOUT` value in your `.env` file

### Check logs
Logs are stored in the `logs/` directory. Check these files for detailed error information.

## Next Steps

1. **Review extracted content**: Check the files in `data/raw_text/` to ensure quality
2. **Test RAG queries**: Once embeddings are in Qdrant, you can perform similarity searches
3. **Integrate with your application**: Use the Qdrant client to retrieve relevant content for your RAG application

## Sample Output

When running the pipeline, you should see output similar to:

```
Starting full RAG pipeline
Found 25 URLs to process
Processing URL 1/25: https://example.com/docs/intro
Successfully extracted content from https://example.com/docs/intro - 1245 chars
...
Saved 25 raw content files to data/raw_text
Starting embedding pipeline with 25 items
Generated 25 validated embeddings
Embedding pipeline completed: {'status': 'success', 'upserted_count': 25, ...}
Full RAG pipeline completed
```

## API Usage (Planned)

Future versions will include API endpoints for programmatic access:

```python
from src.main import RAGExtractionPipeline

pipeline = RAGExtractionPipeline()
result = pipeline.run_full_pipeline()
```

## Support

If you encounter issues, please check:
- The README.md for detailed configuration options
- The logs in the `logs/` directory
- Common troubleshooting steps in the main documentation