# Implementation Plan: RAG Website Content Extraction and Embedding Pipeline

**Branch**: `009-rag-website-extraction` | **Date**: 2025-12-21 | **Spec**: [link to spec.md]
**Input**: Feature specification from `/specs/009-rag-website-extraction/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement a single-process RAG pipeline that extracts content from Docusaurus websites, performs deterministic token-based chunking, generates embeddings using Cohere models, and stores them in Qdrant with complete metadata. The pipeline must support resuming at stage boundaries, implement idempotent writes via content hashing, and maintain complete traceability to source URLs. The system will be configured via environment variables and config files with configurable retry/backoff strategies and atomic batch operations.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: requests, beautifulsoup4, cohere, qdrant-client, python-dotenv, lxml, playwright, pytest
**Storage**: Qdrant vector database for embeddings, local file system for temporary content storage
**Testing**: pytest for unit and integration testing
**Target Platform**: Linux server environment for pipeline execution
**Project Type**: Single project backend pipeline (single project structure)
**Performance Goals**: Extract 100% of pages within 30 minutes for sites up to 50,000 pages, maintain 99% embedding generation success rate, achieve 99.9% atomic batch write success during failures
**Constraints**: Single worker process, resume only at stage boundaries (extraction → validation → embedding → storage), deterministic token-based chunking, idempotent operations via content hashing, no distributed systems
**Scale/Scope**: Handle websites up to 50,000 pages, maintain 99% uptime under normal conditions, recovery from failures within 5 minutes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Based on constitution file, the following gates must be satisfied:
- Code Quality & Technical Excellence: All scripts must follow TDD principles with comprehensive tests
- Content Accuracy & Verification Standards: Extracted content must maintain 95% fidelity to original
- Technical Rigor & Reproducibility Standards: Pipeline must be reproducible and testable
- RAG Chatbot Content Standards: All book modules and chapters must be indexed into Qdrant with complete metadata
- RAG Chatbot Operational Rules: Database operations must maintain transactional integrity
- RAG Chatbot Deployment Integration: Include automated tests for retrieval accuracy
- RAG Chatbot Global Principles: Ensure grounding to verified content and scope enforcement

**RAG Chatbot Compliance Check (if applicable)**:
- Verify that any RAG system implementation adheres to RAG Chatbot Global Principles (accuracy, grounding, scope enforcement, deterministic refusal, confidence tracking)
- Confirm that content indexing follows RAG Chatbot Content Standards (Qdrant embeddings with semantic similarity and metadata tags)
- Ensure operational rules are followed (API validation, database integrity, logging, security)
- Validate deployment integration (frontend embedding, attribution, testing)

## Project Structure

### Documentation (this feature)

```text
specs/009-rag-website-extraction/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── content_extractor.py          # Extract content using config-driven selectors
│   │   ├── sitemap_parser.py             # Parse sitemap to get URLs
│   │   └── url_crawler.py                # Crawl URLs and extract content
│   ├── chunking/
│   │   ├── __init__.py
│   │   ├── token_chunker.py              # Deterministic token-based chunking
│   │   └── chunk_validator.py            # Validate chunk quality
│   ├── embedding/
│   │   ├── __init__.py
│   │   ├── embedding_generator.py        # Generate embeddings with Cohere
│   │   └── qdrant_client.py              # Store embeddings in Qdrant
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── raw_content_storage.py        # Store raw extracted content
│   │   ├── batch_operation.py            # Handle atomic batch operations
│   │   └── content_hasher.py             # Generate content hashes for deduplication
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── content_validator.py          # Validate content quality
│   │   └── pipeline_resume.py            # Handle pipeline resumption logic
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config_loader.py              # Load config from files/env vars
│   │   └── selectors_config.py           # Manage CSS selectors from config
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py                     # Logging functionality
│   │   ├── retry_handler.py              # Configurable retry/backoff logic
│   │   └── progress_tracker.py           # Track pipeline progress
│   └── main.py                           # Pipeline orchestrator
├── config/
│   └── selectors.yaml                    # CSS selectors configuration
├── data/
│   └── raw_content/                      # Temporary storage for extracted content
├── logs/
│   └── pipeline.log                      # Pipeline execution logs
├── tests/
│   ├── unit/
│   │   ├── test_content_extractor.py
│   │   ├── test_token_chunker.py
│   │   ├── test_embedding_generator.py
│   │   └── test_pipeline_resume.py
│   ├── integration/
│   │   ├── test_extraction_pipeline.py
│   │   └── test_embedding_pipeline.py
│   └── contract/
│       └── test_api_contracts.py
├── requirements.txt
├── .env.example
└── README.md
```

**Structure Decision**: Single project backend pipeline structure selected with dedicated modules for extraction, chunking, embedding, storage, validation, and configuration. The pipeline will be organized in a modular fashion to separate concerns and ensure maintainability. Configuration will be loaded from YAML files with environment variable overrides as specified in the feature requirements.

## Pipeline Implementation Plan

### Phase 1: Content Extraction Module
**Responsibilities**: Parse sitemap, crawl URLs, extract content using config-driven selectors
- Input: Sitemap URL, CSS selector configuration
- Output: Raw extracted content with metadata
- Guarantees: Complete content extraction with source URL traceability
- Failure handling: Configurable retry/backoff for network failures, skip failed URLs with logging
- Resume checkpoints: After each batch of URL extractions

### Phase 2: Content Validation & Chunking Module
**Responsibilities**: Validate content quality, perform deterministic token-based chunking
- Input: Raw extracted content
- Output: Validated, chunked content ready for embedding
- Guarantees: Content quality standards met, consistent chunking using fixed token counts
- Failure handling: Reject low-quality content, retry chunking on failures
- Resume checkpoints: After each batch of content validation/chunking

### Phase 3: Embedding Generation Module
**Responsibilities**: Generate embeddings using Cohere, prepare for storage with metadata
- Input: Validated, chunked content
- Output: Embedding vectors with complete metadata (model name, version, chunking version)
- Guarantees: High-quality embeddings with complete traceability metadata
- Failure handling: Retry embedding generation with exponential backoff, atomic batch operations
- Resume checkpoints: After each batch of embedding generation

### Phase 4: Storage Module
**Responsibilities**: Store embeddings in Qdrant with atomic batch operations and idempotency
- Input: Embedding vectors with metadata
- Output: Stored embeddings in Qdrant database
- Guarantees: Atomic batch writes, idempotent operations via content hashing
- Failure handling: Atomic batch rollback on failure, retry with backoff
- Resume checkpoints: After each batch of storage operations

## Out of Scope (Spec 1)
- Distributed systems and multi-worker ingestion
- Adaptive or model-driven chunking strategies
- Auto-healing or self-repairing pipeline orchestration
- Multi-tenant isolation or access control
- Advanced pipeline orchestration frameworks
- Real-time processing capabilities
- Streaming ingestion patterns

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [N/A] | [No violations identified] | [All constitutional requirements satisfied] |
