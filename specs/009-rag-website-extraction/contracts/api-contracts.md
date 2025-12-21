# API Contracts: RAG Chatbot - Website Content Extraction and Embedding

## Overview
This document defines the API contracts for the backend pipeline that handles website content extraction and embedding generation.

## Pipeline Execution Endpoints

### 1. Content Extraction Endpoint
**Purpose**: Initiate the content extraction process from a specified website URL

```
POST /api/v1/extraction/start
```

**Request Body**:
```json
{
  "website_url": "https://example-docusaurus-site.com",
  "crawl_depth": 3,
  "include_patterns": ["/docs/*", "/modules/*"],
  "exclude_patterns": ["/tags/*", "/blog/*"],
  "delay_between_requests": 1,
  "timeout": 300,
  "deduplicate": true
}
```

**Response**:
```json
{
  "job_id": "uuid-string",
  "status": "started",
  "estimated_completion": "2025-12-20T15:30:00Z",
  "message": "Content extraction process initiated successfully"
}
```

### 2. Extraction Status Endpoint
**Purpose**: Check the status of an ongoing extraction job

```
GET /api/v1/extraction/status/{job_id}
```

**Response**:
```json
{
  "job_id": "uuid-string",
  "status": "in_progress",
  "progress": 65,
  "pages_processed": 125,
  "total_pages": 190,
  "duplicates_skipped": 5,
  "errors": [],
  "start_time": "2025-12-20T14:30:00Z",
  "estimated_completion": "2025-12-20T15:30:00Z"
}
```

### 3. Raw Content Review Endpoint
**Purpose**: Retrieve extracted content for review before embedding generation

```
GET /api/v1/extraction/content
```

**Query Parameters**:
- `limit`: Number of items to return (default: 10)
- `offset`: Number of items to skip (default: 0)
- `module`: Filter by module name (optional)
- `quality_score_min`: Minimum quality score (optional)
- `include_duplicates`: Include duplicate content in results (default: false)

**Response**:
```json
{
  "items": [
    {
      "id": "uuid-string",
      "url": "https://example.com/docs/intro",
      "title": "Introduction to Physical AI",
      "module": "Module 1: Introduction",
      "section": "Week 1-2",
      "content": "Full extracted content...",
      "content_hash": "sha256-hash-value",
      "quality_score": 0.85,
      "word_count": 1200,
      "created_at": "2025-12-20T14:35:00Z"
    }
  ],
  "total_count": 190,
  "limit": 10,
  "offset": 0
}
```

### 4. Embedding Generation Endpoint
**Purpose**: Generate embeddings for extracted content and store in Qdrant

```
POST /api/v1/embeddings/generate
```

**Request Body**:
```json
{
  "content_filter": {
    "quality_score_min": 0.7,
    "modules": ["Module 1", "Module 2"],
    "exclude_content_types": ["code", "table"]
  },
  "batch_size": 10,
  "model": "embed-english-v3.0",
  "deduplicate": true
}
```

**Response**:
```json
{
  "job_id": "uuid-string",
  "status": "started",
  "content_processed": 150,
  "duplicates_skipped": 5,
  "message": "Embedding generation process initiated"
}
```

### 5. Qdrant Storage Endpoint
**Purpose**: Store generated embeddings in Qdrant vector database

```
POST /api/v1/embeddings/store
```

**Request Body**:
```json
{
  "collection_name": "book_content_embeddings",
  "embeddings": [
    {
      "id": "uuid-string",
      "vector": [0.1, 0.2, 0.3, ...],
      "payload": {
        "url": "https://example.com/docs/intro",
        "title": "Introduction to Physical AI",
        "module": "Module 1: Introduction",
        "section": "Week 1-2",
        "version": "1.0.0",
        "content_type": "text",
        "word_count": 1200,
        "content_hash": "sha256-hash-value",
        "created_at": "2025-12-20T14:35:00Z"
      }
    }
  ]
}
```

**Response**:
```json
{
  "status": "success",
  "stored_count": 150,
  "failed_count": 0,
  "duplicates_skipped": 0,
  "collection_name": "book_content_embeddings"
}
```

### 6. Pipeline Health Check Endpoint
**Purpose**: Check the health and status of the entire pipeline

```
GET /api/v1/health
```

**Response**:
```json
{
  "status": "healthy",
  "services": {
    "crawler": "operational",
    "embedding_generator": "operational",
    "qdrant_connection": "operational",
    "storage": "operational"
  },
  "last_extraction_run": "2025-12-20T14:30:00Z",
  "total_embeddings_stored": 1500,
  "total_duplicates_skipped": 50
}
```

## Error Responses

All endpoints return standard error responses:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Descriptive error message",
    "details": "Additional error details if applicable"
  }
}
```

## Common Error Codes
- `EXTRACTION_FAILED`: Content extraction process failed
- `EMBEDDING_GENERATION_FAILED`: Embedding generation failed
- `QDRANT_CONNECTION_ERROR`: Unable to connect to Qdrant
- `INVALID_INPUT`: Request parameters are invalid
- `RESOURCE_NOT_FOUND`: Requested resource does not exist
- `INTERNAL_ERROR`: Unexpected internal error occurred
- `DUPLICATE_DETECTED`: Content duplicate detected during processing