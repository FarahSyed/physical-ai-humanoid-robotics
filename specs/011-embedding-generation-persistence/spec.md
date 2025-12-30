# Spec: 011 Embedding Generation and Persistence

## Clarifications
### Session 2025-12-27
- Q: How should embedding-specific states be implemented? → A: Add new embedding-specific states to the existing PipelineState enum (EMBEDDING_IN_PROGRESS, EMBEDDING_COMPLETE, etc.)
- Q: How should the Qdrant persistence contract be defined? → A: Define specific payload schema and ID strategy for Qdrant collection
- Q: How should determinism enforcement work when configuration changes are detected? → A: Store hashes in state file and block embedding if configuration changes detected
- Q: What concurrency model should be used for embedding operations? → A: Parallel per pipeline with queue management
- Q: What should be the granularity of audit records? → A: Hybrid approach with summary and detail records

## Feature Overview
Implement embedding generation and persistence for previously extracted and approved content, following the existing pipeline architecture. This feature will generate vector embeddings for approved content chunks and persist them to the Qdrant vector database.

## Functional Requirements
- **FR-001**: Trigger embedding generation immediately after content chunks have been approved
- **FR-002**: Use the configured embedding provider (e.g., Cohere) to generate vector embeddings for each approved chunk
- **FR-003**: Persist generated embeddings to the existing Qdrant vector database with specific payload schema and ID strategy
- **FR-004**: Ensure execution determinism by locking the embedding model version and recording configuration hashes in state file, blocking embedding if configuration changes detected
- **FR-005**: Log and audit all embedding operations with chunk IDs, timestamps, model versions, and outcomes using hybrid approach with summary and detail records
- **FR-006**: Enforce safety by verifying content approval status and detecting configuration changes
- **FR-007**: Define CLI commands for embedding operations (pipeline embed start, pipeline embed resume)
- **FR-008**: Implement state transitions for the embedding process (EMBEDDING_IN_PROGRESS, EMBEDDING_COMPLETE, etc.) using the existing PipelineState enum
- **FR-009**: Support parallel embedding operations per pipeline with queue management

## Non-Functional Requirements
- **NFR-001**: Performance - Generate embeddings within 10 seconds per 1000 tokens
- **NFR-002**: Reliability - Achieve 99.9% success rate for embedding operations
- **NFR-003**: Security - Secure API key handling for embedding providers and configuration hash validation
- **NFR-004**: Scalability - Support parallel embedding operations per pipeline with queue management for multiple pipelines
- **NFR-005**: Auditability - Maintain complete audit trail of all embedding operations using hybrid approach with summary and detail records
- **NFR-006**: Determinism - Ensure consistent results by locking embedding model version and blocking operations on configuration changes

## Key Entities
- **EmbeddingGenerator**: Orchestrates the embedding process using configured provider with parallel queue management
- **EmbeddingPersistence**: Handles storage of embeddings to Qdrant database with specific payload schema and ID strategy
- **EmbeddingState**: PipelineState extension for embedding-specific states (EMBEDDING_IN_PROGRESS, EMBEDDING_COMPLETE, etc.)
- **EmbeddingConfig**: Configuration for embedding provider and parameters with configuration hash validation
- **EmbeddingRecord**: Audit record for each embedding operation using hybrid approach with summary and detail records
- **EmbeddingQueue**: Manages parallel embedding operations per pipeline with queue management

## Success Criteria
- Embeddings are generated only for approved content chunks
- Embeddings are successfully persisted to Qdrant database
- Configuration determinism is maintained with version locking
- All operations are properly logged and audited
- CLI commands work as expected for embedding operations
- State transitions follow the defined workflow
- No regression in existing pipeline functionality

## Implementation Constraints
- Must integrate with existing pipeline state machine
- Must use existing Qdrant database connection
- Must maintain backward compatibility with existing components
- Must follow the same architecture patterns as existing modules
- Must not duplicate functionality already implemented in other modules