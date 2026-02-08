---
name: fastapi-rag-builder
description: |
  Build production-ready FastAPI RAG (Retrieval-Augmented Generation) systems with Qdrant vector database.
  This skill should be used when users want to create a new RAG API, set up vector search endpoints,
  or implement question-answering systems with document retrieval. Handles markdown content extraction,
  embedding generation with Cohere, vector storage in Qdrant, and includes debugging patterns for common
  RAG issues (embedding mismatches, API version conflicts, deduplication, content hydration).
---

# FastAPI RAG Builder

Build production-ready RAG systems with FastAPI, Qdrant, and Cohere.

## What This Skill Does

- Creates FastAPI RAG endpoints (`/chat`, `/health`)
- Sets up Qdrant vector database integration
- Implements content extraction from markdown files
- Generates embeddings with Cohere
- Handles common RAG issues (deduplication, content hydration, API mismatches)
- Provides debugging patterns from real-world issues

## What This Skill Does NOT Do

- Deploy to production (use deployment tools)
- Handle non-markdown content (PDFs, images, etc.)
- Support vector databases other than Qdrant
- Manage user authentication/authorization

---

## Before Implementation

Gather context to ensure successful implementation:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing FastAPI structure, data directory, environment setup |
| **Conversation** | User's content source, API requirements, performance needs |
| **Skill References** | RAG patterns from `references/` (Qdrant best practices, debugging patterns) |
| **User Guidelines** | Project conventions, coding standards |

Ensure all required context is gathered before implementing.

---

## Implementation Workflow

### Step 1: Project Setup

1. **Verify dependencies** (see `references/dependencies.md`):
   ```bash
   pip install fastapi uvicorn qdrant-client cohere python-dotenv pydantic
   ```

2. **Create environment file** (`.env`):
   ```env
   QDRANT_HOST=https://your-cluster.qdrant.io:6333
   QDRANT_API_KEY=your_api_key
   QDRANT_COLLECTION_NAME=your_collection
   COHERE_API_KEY=your_cohere_key
   OPENAI_API_KEY=your_openai_key  # or OPEN_ROUTER_API_KEY
   ```

3. **Initialize project structure**:
   ```
   project/
   ├── backend/
   │   ├── src/
   │   │   └── main.py
   │   ├── data/
   │   │   └── chunked/
   │   │       └── chunked_content.json
   │   └── .env
   ```

### Step 2: Content Extraction & Chunking

Use `scripts/extract_markdown.py` to extract and chunk markdown content:

```bash
python scripts/extract_markdown.py --input docs/ --output data/chunked/chunked_content.json
```

**Output format**:
```json
{
  "chunks": [
    {
      "id": "chunk_1",
      "content": "Full content text...",
      "metadata": {
        "source_url": "...",
        "title": "...",
        "chunk_index": 0
      }
    }
  ]
}
```

### Step 3: Generate & Store Embeddings

Use `scripts/generate_embeddings.py`:

```bash
python scripts/generate_embeddings.py --input data/chunked/chunked_content.json
```

**Critical**: Use `input_type="search_document"` for indexing, `input_type="search_query"` for queries.

See `references/embedding-best-practices.md` for details.

### Step 4: Build FastAPI Endpoints

Use the template from `assets/fastapi-rag-template.py` as starting point.

**Key components**:
1. **Lifespan management** - Initialize Qdrant client, load content cache
2. **Search function** - Handle embedding generation, deduplication, content hydration
3. **Chat endpoint** - Retrieve context, inject into LLM prompt, return grounded response
4. **Health endpoint** - Verify Qdrant connection, return collection stats

See `references/fastapi-patterns.md` for implementation details.

### Step 5: Debug Common Issues

If encountering problems, consult `references/debugging-guide.md`:

**Common issues**:
- Embedding dimension mismatch → Check `input_type` parameter
- API version conflicts → Use `query_points()` for qdrant-client <1.9.0
- Duplicate results → Implement deduplication by `chunk_id`
- Truncated content → Hydrate with full content from source file
- Empty results → Verify similarity threshold, check embedding model

---

## Quality Checklist

Before considering the RAG system complete:

- [ ] `/chat` endpoint returns relevant, grounded responses
- [ ] `/health` endpoint shows correct collection stats
- [ ] Deduplication prevents duplicate results
- [ ] Content hydration provides full context (not truncated previews)
- [ ] Response time <5 seconds for typical queries
- [ ] Sources returned with similarity scores
- [ ] CORS configured for frontend integration
- [ ] Error handling for Qdrant/API failures
- [ ] Environment variables validated on startup
- [ ] Logging configured for debugging

---

## Reference Files

| File | When to Read |
|------|--------------|
| `references/qdrant-best-practices.md` | Qdrant integration patterns, search strategies |
| `references/embedding-best-practices.md` | Cohere embedding generation, input types, dimensions |
| `references/debugging-guide.md` | Common RAG issues and solutions |
| `references/fastapi-patterns.md` | FastAPI implementation patterns, lifespan management |
| `references/dependencies.md` | Required packages and versions |

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/extract_markdown.py` | Extract and chunk markdown content |
| `scripts/generate_embeddings.py` | Generate embeddings and store in Qdrant |
| `scripts/test_search.py` | Test Qdrant search functionality |

---

## Assets

| Asset | Purpose |
|-------|---------|
| `assets/fastapi-rag-template.py` | Complete FastAPI RAG implementation template |
| `assets/.env.example` | Environment variables template |
