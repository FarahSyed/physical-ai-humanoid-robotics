# FastAPI Patterns for RAG Systems

## Application Structure

### Lifespan Management

Use FastAPI's lifespan context manager for resource initialization:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources"""
    global qdrant_client, content_cache

    # Startup
    print("Initializing resources...")

    # 1. Load content cache for hydration
    import json
    from pathlib import Path

    chunked_file = Path(__file__).parent.parent / "data" / "chunked" / "chunked_content.json"
    if chunked_file.exists():
        with open(chunked_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chunks = data.get('chunks', [])
            content_cache = {chunk['id']: chunk['content'] for chunk in chunks}
            print(f"Loaded {len(content_cache)} content chunks")

    # 2. Initialize Qdrant client
    qdrant_client = QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY)

    # 3. Verify collection exists
    collection_info = qdrant_client.get_collection(QDRANT_COLLECTION_NAME)
    print(f"Connected to collection: {QDRANT_COLLECTION_NAME}")
    print(f"Vectors: {collection_info.points_count}")

    yield  # Application runs

    # Cleanup
    print("Cleaning up resources...")
    qdrant_client = None
    content_cache = None

app = FastAPI(
    title="RAG API",
    version="1.0.0",
    lifespan=lifespan
)
```

---

## CORS Configuration

Enable CORS for frontend integration:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Request/Response Models

### Pydantic Models

```python
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class ChatRequest(BaseModel):
    prompt: str
    history: Optional[List[Dict[str, str]]] = None
    top_k: Optional[int] = 5

class Source(BaseModel):
    id: str
    text: str
    score: float
    metadata: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    usage: Optional[Dict[str, int]] = None
```

---

## Search Function Pattern

### Complete Search Implementation

```python
def search_rag_context(query: str, top_k: int = 5) -> str:
    """Search Qdrant and return formatted context"""
    global qdrant_client, content_cache

    try:
        # 1. Generate query embedding
        co = cohere.Client(os.getenv("COHERE_API_KEY"))
        response = co.embed(
            texts=[query],
            model="embed-english-v3.0",
            input_type="search_query",  # Critical!
            truncate="END"
        )
        query_embedding = response.embeddings[0]

        # 2. Search Qdrant (request extra for deduplication)
        results = qdrant_client.query_points(
            collection_name=QDRANT_COLLECTION_NAME,
            query=query_embedding,
            limit=top_k * 7,  # Account for duplicates
            with_payload=True
        ).points

        # 3. Deduplicate and hydrate
        context = []
        seen_chunk_ids = set()

        for hit in results:
            if len(context) >= top_k:
                break

            payload = hit.payload or {}
            chunk_id = payload.get("chunk_id", "")

            # Skip duplicates
            if chunk_id in seen_chunk_ids:
                continue
            seen_chunk_ids.add(chunk_id)

            # Hydrate with full content
            if content_cache and chunk_id in content_cache:
                full_content = content_cache[chunk_id]
            else:
                full_content = payload.get("content_preview", "")

            context.append({
                "id": str(hit.id),
                "chunk_id": chunk_id,
                "text": full_content,
                "score": hit.score,
                "metadata": payload.get("metadata", {})
            })

        # 4. Format for LLM
        formatted = f"Found {len(context)} relevant documents:\n\n"
        for doc in context:
            formatted += f"Document [{doc['id']}] (score: {doc['score']:.3f}):\n"
            formatted += f"{doc['text'][:1000]}\n\n"

        return formatted

    except Exception as e:
        return f"Search failed: {str(e)}"
```

---

## Chat Endpoint Pattern

### Complete Implementation

```python
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """Execute RAG query"""
    try:
        # 1. Search Qdrant
        search_result = search_rag_context(req.prompt, req.top_k or 5)

        # 2. Check for failures
        if search_result.startswith("Search failed:"):
            search_result = "No relevant documents found."

        # 3. Build agent (no tools - context already retrieved)
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url="https://api.openai.com/v1"
        )

        # 4. Create prompt with context
        system_prompt = """You are a helpful assistant. Answer ONLY using the retrieved context below.
        If the context doesn't contain the answer, say "I don't have that information."

        Retrieved Context:
        {context}
        """

        messages = [
            {"role": "system", "content": system_prompt.format(context=search_result)},
            {"role": "user", "content": req.prompt}
        ]

        # 5. Get response
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7
        )

        answer = response.choices[0].message.content

        # 6. Parse sources from search_result
        sources = parse_sources(search_result)

        return ChatResponse(
            answer=answer,
            sources=sources,
            usage={"timestamp": int(datetime.utcnow().timestamp())}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## Health Endpoint Pattern

```python
@app.get("/health")
async def health_check():
    """Health check with collection stats"""
    global qdrant_client

    try:
        collection_info = qdrant_client.get_collection(QDRANT_COLLECTION_NAME)

        return {
            "status": "healthy",
            "collection": QDRANT_COLLECTION_NAME,
            "vector_count": collection_info.points_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
```

---

## Error Handling Patterns

### Global Exception Handler

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions"""
    import traceback

    error_details = traceback.format_exc()
    print(f"Unhandled error: {error_details}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url)
        }
    )
```

### Specific Error Handling

```python
from qdrant_client.http.exceptions import UnexpectedResponse

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        # ... implementation
        pass
    except UnexpectedResponse as e:
        raise HTTPException(
            status_code=503,
            detail="Vector database unavailable"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )
```

---

## Logging Pattern

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use in endpoints
@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    logger.info(f"Chat request: {req.prompt[:50]}...")

    try:
        result = search_rag_context(req.prompt)
        logger.info(f"Search returned {len(result)} chars")
        # ...
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}", exc_info=True)
        raise
```

---

## Testing Patterns

### Test Client Setup

```python
from fastapi.testclient import TestClient

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_chat():
    response = client.post("/chat", json={
        "prompt": "What is ROS 2?",
        "top_k": 3
    })
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
```

---

## Deployment Checklist

Before deploying:

- [ ] Environment variables validated on startup
- [ ] CORS configured for production domains
- [ ] Error handling for all endpoints
- [ ] Logging configured
- [ ] Health check returns collection stats
- [ ] Rate limiting implemented (if needed)
- [ ] API documentation enabled (`/docs`)
- [ ] Connection pooling for Qdrant
- [ ] Graceful shutdown handling
