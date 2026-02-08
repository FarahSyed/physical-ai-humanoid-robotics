# Implementation Plan: FastAPI RAG Agent with Qwen and Qdrant

## Overview
This plan outlines the implementation of a minimal FastAPI RAG agent that uses Qwen API for response generation and Qdrant Cloud for vector storage and retrieval.

## Architecture
- FastAPI server with /chat and /health endpoints
- Qwen API integration for response generation
- Qdrant Cloud integration for vector storage and retrieval
- Embedding generation for queries and documents

## Implementation Tasks

### Phase 1: Project Setup and Dependencies
1. **Setup project structure**
   - Create main FastAPI application file
   - Set up requirements.txt with dependencies (fastapi, uvicorn, qwen-sdk, qdrant-client)
   - Create configuration module for API keys and settings

2. **Install dependencies**
   - FastAPI and Uvicorn for web server
   - Qwen SDK for API integration
   - Qdrant client for vector database operations
   - Pydantic for data validation

### Phase 2: Qdrant Integration
3. **Initialize Qdrant client**
   - Connect to Qdrant Cloud using API key and host
   - Verify connection and collection availability

4. **Implement document embedding and storage**
   - Create function to upsert embeddings with payload text to Qdrant
   - Handle document preprocessing and chunking
   - Ensure embeddings are stored with proper metadata

### Phase 3: Core RAG Functionality
5. **Implement query embedding**
   - Create function to embed user queries using the same model as documents
   - Ensure query embeddings match the stored vector dimensions

6. **Implement vector search**
   - Query Qdrant with embedded user query
   - Retrieve top K results (K=3 as specified)
   - Extract payload texts from search results

7. **Implement prompt injection**
   - Create system prompt template
   - Inject retrieved context into agent prompt
   - Ensure proper formatting for Qwen API

8. **Implement agent response generation**
   - Call Qwen API with constructed prompt
   - Process and return the response
   - Handle API errors gracefully

### Phase 4: API Endpoints
9. **Create /chat endpoint**
   - Accept user query via POST request
   - Validate input parameters
   - Execute RAG flow: embed query → search Qdrant → inject context → generate response
   - Return agent response in JSON format

10. **Create /health endpoint**
    - Check Qdrant connection
    - Verify collection exists and has vectors
    - Return collection name and vector count
    - Report healthy status only if all dependencies are accessible

### Phase 5: Testing and Validation
11. **Implement basic tests**
    - Test /health endpoint returns proper status
    - Test /chat endpoint processes queries and returns responses
    - Validate that responses are grounded in retrieved context

12. **Performance validation**
    - Verify response times are under 3 seconds
    - Test concurrent request handling up to 10 requests
    - Validate error handling when dependencies are unavailable

## Technical Details

### Qwen API Integration
- Use qwen3-coder-plus model for response generation
- Format prompts with retrieved context following best practices
- Handle API rate limits and errors gracefully

### Qdrant Integration
- Connect to Qdrant Cloud instance
- Use collection specified in environment variables
- Perform vector search with cosine similarity
- Retrieve top 3 most relevant documents based on query similarity

### Embedding Consistency
- Ensure query embeddings use the same model as document embeddings
- Maintain consistent vector dimensions between stored and query vectors
- Handle embedding generation errors gracefully

## Success Criteria
- API responds to /health with status and vector count
- API responds to /chat with contextually relevant answers within 3 seconds
- System handles up to 10 concurrent requests without degradation
- Responses are grounded in retrieved context from Qdrant
- Proper error handling when Qdrant or Qwen API is unavailable