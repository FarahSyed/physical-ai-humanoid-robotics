# Data Model: RAG Chatbot - Website Content Extraction and Embedding

## Overview
This document defines the data structures and entities used in the RAG Chatbot content extraction and embedding pipeline.

## Core Entities

### ExtractedContent
Represents the raw content extracted from the website with associated metadata.

**Fields**:
- `id` (string): Unique identifier for the content chunk (UUID)
- `url` (string): Source URL of the content
- `title` (string): Page title
- `content` (string): Extracted text content
- `module` (string): Module name (e.g., "Module 1: The Robotic Nervous System")
- `section` (string): Section name (e.g., "Week 3-5", "ROS 2 Nodes, Topics, and Services")
- `version` (string): Version identifier for the content
- `created_at` (datetime): Timestamp when content was extracted
- `updated_at` (datetime): Timestamp when content was last updated
- `content_type` (string): Type of content (e.g., "text", "code", "documentation")
- `word_count` (integer): Number of words in the content
- `content_hash` (string): Hash of the content for deduplication purposes
- `metadata` (object): Additional metadata as key-value pairs

**Validation Rules**:
- `url` must be a valid URL format
- `content` must not be empty
- `created_at` must be a valid timestamp
- `word_count` must be non-negative
- `content_hash` must be a valid hash value

### EmbeddingVector
Represents the vector embedding of content stored in Qdrant.

**Fields**:
- `id` (string): Unique identifier matching the ExtractedContent.id
- `vector` (array[float]): The embedding vector from Cohere
- `payload` (object): Metadata object containing:
  - `url` (string): Source URL
  - `title` (string): Page title
  - `module` (string): Module name
  - `section` (string): Section name
  - `version` (string): Version identifier
  - `content_type` (string): Type of content
  - `word_count` (integer): Number of words
  - `created_at` (datetime): Creation timestamp
  - `updated_at` (datetime): Update timestamp
  - `content_hash` (string): Hash of the content for deduplication

**Validation Rules**:
- `vector` must have consistent dimensions (expected by Cohere model)
- `id` must match an existing ExtractedContent.id
- `payload` must contain all required metadata fields

### ContentMetadata
Contains information about the extracted content structure and quality.

**Fields**:
- `content_id` (string): Reference to ExtractedContent.id
- `source_url` (string): Original URL of the content
- `module` (string): Module identifier
- `section` (string): Section identifier
- `version` (string): Content version
- `extraction_date` (datetime): When content was extracted
- `quality_score` (float): Quality assessment score (0.0-1.0)
- `content_length` (integer): Length of extracted content in characters
- `word_count` (integer): Number of words in content
- `language` (string): Detected language of content
- `content_structure` (object): Information about headings, code blocks, etc.
- `content_hash` (string): Hash of the content for deduplication purposes

**Validation Rules**:
- `quality_score` must be between 0.0 and 1.0
- `content_length` must be non-negative
- `word_count` must be non-negative
- `content_hash` must be a valid hash value

## Relationships

```
ExtractedContent (1) <---> (1) EmbeddingVector
ExtractedContent (1) <---> (1) ContentMetadata
```

Each extracted content item has one corresponding embedding vector and one metadata record.

## State Transitions

### Content Extraction Process
1. **Pending**: Content URL identified but not yet crawled
2. **Extracting**: Content is being crawled and extracted
3. **Extracted**: Content successfully extracted and stored temporarily
4. **Validated**: Content quality verified and approved for embedding
5. **Embedded**: Content successfully converted to embedding vector
6. **Stored**: Embedding vector stored in Qdrant database

### Quality States
- **Low Quality**: Quality score < 0.5, requires review or re-extraction
- **Medium Quality**: Quality score 0.5-0.7, acceptable for embedding
- **High Quality**: Quality score > 0.7, excellent for embedding

## Deduplication Strategy

The system implements deduplication using a combination of URL and content hash matching:
- Each content item is assigned a content_hash based on its text content
- Before processing, the system checks for existing content with the same URL or content_hash
- If a duplicate is detected, the system skips processing to ensure idempotency
- This approach ensures that re-running the pipeline does not create duplicate embeddings