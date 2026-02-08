# Content Extraction to Qdrant Embeddings Skill

This skill processes content from extraction to vector embeddings storage in Qdrant database.

## Overview

The skill implements a complete pipeline that:
1. Loads chunked content from JSON files
2. Generates vector embeddings using Cohere API
3. Stores embeddings in Qdrant vector database
4. Saves embeddings locally as backup

## Prerequisites

- Cohere API key in environment variables
- Qdrant cloud instance access
- Required Python packages installed

## Configuration

The skill uses environment variables from `.env` file:
- `COHERE_API_KEY` - Cohere API key
- `QDRANT_HOST` - Qdrant cloud instance URL
- `QDRANT_API_KEY` - Qdrant API key
- `QDRANT_COLLECTION_NAME` - Target collection name

## Usage

### From Python
```python
from backend.src.embeddings_pipeline.extract_to_embeddings_pipeline import main
main()
```

### With custom file path
```python
from backend.src.embeddings_pipeline.extract_to_embeddings_pipeline import main
main('path/to/chunked_content.json')
```

## Parameters

- `chunk_file_path` (optional): Path to the chunked content JSON file (default: `data/chunked/chunked_content.json`)

## Output

- Embeddings stored in Qdrant collection
- Local backup in `data/embeddings/` directory as JSON files
- Console output with processing status

## Technical Details

- Uses Cohere's `embed-english-v3.0` model
- Generates 1024-dimensional embeddings
- Stores vectors with associated metadata in Qdrant
- Implements batch processing for memory efficiency
- Supports both local storage and cloud Qdrant