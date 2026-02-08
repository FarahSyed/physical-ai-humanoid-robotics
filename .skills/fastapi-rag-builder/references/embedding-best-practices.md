# Embedding Best Practices for RAG

## Cohere Embedding Models

### Model Selection

**embed-english-v3.0** (Recommended for English RAG):
- Dimension: 1024
- Best for: Semantic search, RAG applications
- Supports: `search_document`, `search_query`, `classification`, `clustering`

### Critical: Input Type Parameter

Cohere embeddings use **different vector spaces** for different input types:

```python
# WRONG - Using same input_type for both
documents_embeddings = co.embed(texts=docs, input_type="classification")
query_embedding = co.embed(texts=[query], input_type="classification")
# Result: Poor similarity scores

# CORRECT - Use appropriate input types
documents_embeddings = co.embed(texts=docs, input_type="search_document")
query_embedding = co.embed(texts=[query], input_type="search_query")
# Result: Accurate similarity scores
```

**Input Types**:
- `search_document` - For indexing documents in vector DB
- `search_query` - For user queries during search
- `classification` - For classification tasks (NOT for RAG)
- `clustering` - For clustering tasks

---

## Embedding Generation Pipeline

### Step 1: Prepare Content

```python
chunks = [
    {
        "id": "chunk_1",
        "content": "Full text content...",
        "metadata": {"source": "...", "title": "..."}
    }
]
```

### Step 2: Generate Embeddings

```python
import cohere

co = cohere.Client(api_key=COHERE_API_KEY)

# Batch processing for efficiency
batch_size = 96  # Cohere limit
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i + batch_size]
    texts = [chunk['content'] for chunk in batch]

    response = co.embed(
        texts=texts,
        model="embed-english-v3.0",
        input_type="search_document",  # For indexing
        truncate="END"  # Handle long texts
    )

    embeddings = response.embeddings
```

### Step 3: Store in Qdrant

```python
from qdrant_client.models import PointStruct

points = []
for chunk, embedding in zip(batch, embeddings):
    points.append(PointStruct(
        id=str(uuid4()),  # Unique point ID
        vector=embedding,
        payload={
            "chunk_id": chunk['id'],
            "content_preview": chunk['content'][:200],
            "metadata": chunk['metadata']
        }
    ))

client.upsert(collection_name=collection_name, points=points)
```

---

## Query-Time Best Practices

### Generate Query Embedding

```python
def search_rag_context(query: str, top_k: int = 5):
    # Use search_query input type
    response = co.embed(
        texts=[query],
        model="embed-english-v3.0",
        input_type="search_query",  # Different from indexing!
        truncate="END"
    )
    query_embedding = response.embeddings[0]

    # Verify dimension matches
    assert len(query_embedding) == 1024

    return query_embedding
```

---

## Common Pitfalls

### 1. Dimension Mismatch

**Problem**: Query embedding dimension doesn't match stored embeddings

**Cause**: Different models or configurations

**Solution**:
```python
# Always verify dimensions match
collection_info = client.get_collection(collection_name)
expected_dim = collection_info.config.params.vectors.size

if len(query_embedding) != expected_dim:
    raise ValueError(f"Dimension mismatch: {len(query_embedding)} != {expected_dim}")
```

### 2. Input Type Confusion

**Problem**: Using `classification` for both indexing and querying

**Why it fails**: Different vector spaces, poor similarity

**Solution**: Always use `search_document` + `search_query` pair

### 3. Rate Limiting

**Problem**: Cohere API rate limits (100 requests/min for trial)

**Solution**:
```python
import time

def embed_with_retry(texts, max_retries=3):
    for attempt in range(max_retries):
        try:
            return co.embed(texts=texts, model="embed-english-v3.0",
                          input_type="search_document")
        except Exception as e:
            if "rate" in str(e).lower():
                wait_time = 2 ** attempt  # Exponential backoff
                time.sleep(wait_time)
            else:
                raise
```

### 4. Content Truncation

**Problem**: Storing only embedding, losing original content

**Solution**: Store content preview in payload, keep full content in separate file

```python
payload = {
    "chunk_id": chunk_id,
    "content_preview": content[:200],  # For quick reference
    # Full content loaded from chunked_content.json during retrieval
    "metadata": metadata
}
```

---

## Performance Optimization

### Batch Processing

```python
# Process in batches for efficiency
batch_size = 96  # Cohere's max batch size

for i in range(0, len(documents), batch_size):
    batch = documents[i:i + batch_size]
    embeddings = co.embed(texts=batch, ...)
```

### Caching

```python
# Cache embeddings to avoid regeneration
import hashlib

def get_embedding_cache_key(text, model, input_type):
    content = f"{text}:{model}:{input_type}"
    return hashlib.md5(content.encode()).hexdigest()

# Use Redis or file-based cache
```

---

## Validation

### Test Embedding Quality

```python
def test_embedding_quality():
    # Test similar content
    doc1 = "ROS 2 is a robot operating system"
    doc2 = "ROS 2 provides robot middleware"

    emb1 = co.embed(texts=[doc1], input_type="search_document").embeddings[0]
    emb2 = co.embed(texts=[doc2], input_type="search_document").embeddings[0]

    # Calculate cosine similarity
    from numpy import dot
    from numpy.linalg import norm

    similarity = dot(emb1, emb2) / (norm(emb1) * norm(emb2))

    assert similarity > 0.7, f"Similar content should have high similarity: {similarity}"
```

---

## Checklist

Before deploying embeddings:

- [ ] Using `search_document` for indexing
- [ ] Using `search_query` for queries
- [ ] Dimension verified (1024 for embed-english-v3.0)
- [ ] Batch processing implemented
- [ ] Rate limiting handled
- [ ] Content preview stored in payload
- [ ] Full content available for hydration
- [ ] Embedding quality tested
