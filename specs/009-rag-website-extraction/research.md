# Research: RAG Chatbot - Website Content Extraction and Embedding

## Overview
This research document addresses the technical requirements for creating a backend pipeline that crawls a Docusaurus website, extracts content, generates embeddings using Cohere, and stores them in Qdrant.

## Decision: Web Crawling Approach
**Rationale**: Need to select an appropriate web crawling method for Docusaurus sites that can handle dynamic content and respect crawl delays.
**Alternatives considered**:
- requests + BeautifulSoup: Simple, good for static content
- Scrapy: More robust, handles complex crawling scenarios
- Playwright: Best for JavaScript-heavy sites like Docusaurus
- Selenium: Good for dynamic content but resource-heavy

**Chosen**: Playwright for Docusaurus sites since they often have dynamic content and client-side rendering. It can properly render JavaScript content that BeautifulSoup might miss.

## Decision: Content Extraction Method
**Rationale**: Need to extract structured content while preserving important elements like code blocks, headings, and metadata.
**Alternatives considered**:
- BeautifulSoup with custom parsing: Good control over extraction
- Trafilatura: Specialized for content extraction
- Newspaper3k: Good for article-style content
- Custom parsing with lxml: Fast and flexible

**Chosen**: Combination of Playwright for initial page rendering and BeautifulSoup for structured extraction, allowing us to handle both static and dynamic content effectively.

## Decision: Embedding Model Selection
**Rationale**: Need to select the appropriate Cohere embedding model for the use case.
**Alternatives considered**:
- Cohere embed-english-v3.0: Latest model, optimized for English
- Cohere embed-multilingual-v3.0: For multilingual content
- Cohere embed-english-light-v3.0: Lighter version for faster processing

**Chosen**: Cohere embed-english-v3.0 as it's optimized for English content which matches the educational book content.

## Decision: Qdrant Collection Strategy
**Rationale**: Need to determine how to organize embeddings in Qdrant for optimal retrieval.
**Alternatives considered**:
- Single collection with metadata: Simple, good for small datasets
- Multiple collections by module/chapter: Better organization but more complex
- Single collection with semantic partitioning: Good balance of simplicity and organization

**Chosen**: Single collection with metadata approach, using module, section, and version metadata for organization and filtering.

## Decision: Data Storage Format
**Rationale**: Need to determine how to store raw extracted content for review.
**Alternatives considered**:
- JSON with metadata: Structured, includes metadata
- Markdown files: Human-readable, preserves formatting
- Pickle files: Python-specific, efficient
- CSV: Simple tabular format

**Chosen**: JSON format as it preserves metadata and structure while being easily readable for review.

## Decision: Pipeline Architecture
**Rationale**: Need to design a modular pipeline that can be tested and maintained easily.
**Alternatives considered**:
- Monolithic script: Simple but hard to maintain
- Modular functions: Good separation of concerns
- Object-oriented approach: More complex but better for large codebase
- Microservices: Overkill for this use case

**Chosen**: Modular functions approach with separate modules for crawling, extraction, embedding, and storage to maintain separation of concerns.

## Decision: Configuration Management
**Rationale**: Need to manage environment variables and configuration settings securely.
**Alternatives considered**:
- Hardcoded values: Insecure and inflexible
- Environment variables: Standard practice
- Configuration files: Good for complex settings
- Hybrid approach: Combines environment variables with defaults

**Chosen**: Hybrid approach using python-dotenv for environment variables with sensible defaults for non-sensitive settings.

## Decision: Target Website URL Configuration
**Rationale**: Need to specify the base URL for the Docusaurus website to crawl.
**Alternatives considered**:
- Command-line parameter: Flexible but requires input each time
- Configuration file: Good for complex settings
- Environment variable: Standard practice for deployment-specific values
- Hardcoded value: Inflexible and insecure

**Chosen**: Environment variable (FRONTEND_SITEMAP_URL) as it provides flexibility for different deployment environments while maintaining security best practices.

## Decision: Deduplication Strategy
**Rationale**: Need to implement deduplication to ensure idempotency during re-runs of the pipeline.
**Alternatives considered**:
- URL-based deduplication: Simple but may miss content changes
- Content hash matching: Effective for detecting content changes
- Semantic similarity: More complex but catches near-duplicates
- Combination approach: Uses multiple methods for robust deduplication

**Chosen**: Combination of URL and content hash matching as it provides a good balance between catching duplicates while avoiding false positives, which is important for content quality in a RAG system.

## Decision: Metadata Storage
**Rationale**: Need to determine how much metadata to store with extracted content.
**Alternatives considered**:
- Minimal metadata: Reduces storage requirements
- Complete original metadata: Preserves important information for RAG retrieval
- Configurable metadata: Allows user to choose what to store
- Metadata in separate lookup table: Optimizes storage but adds complexity

**Chosen**: Complete original metadata as it preserves important information for RAG retrieval and maintains the educational context of the content, which is critical for the intended use case.

## Decision: Embedding Batch Size Configuration
**Rationale**: Need to determine how to handle the batch size for embedding generation.
**Alternatives considered**:
- Fixed batch size: Simple but may not be optimal for all scenarios
- Configurable batch size: Allows optimization based on available resources
- Adaptive batch size: Automatically adjusts based on performance
- Predefined options: Set common batch sizes as options

**Chosen**: Configurable embedding batch size as it provides flexibility to optimize processing performance based on available resources and requirements.