# Qdrant Best Practices for RAG

## Collection Setup

### Create Collection with Proper Configuration

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

client = QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY)

client.create_collection(
    collection_name="my_rag_collection",
    vectors_config=VectorParams(
        size=1024,  # Match embedding dimension
        distance=Distance.COSINE  # Best for semantic similarity
    )
)
```

**Distance Metrics**:
- `COSINE` - Best for semantic similarity (recommended for RAG)
- `EUCLID` - Euclidean distance
- `DOT` - Dot product (for normalized vectors)

---

## Search Strategies

### Basic Search

```python
# For qdrant-client >=1.9.0
results = client.search(
    collection_name="my_collection",
    query_vector=query_embedding,
    limit=5,
    with_payload=True,
    with_vectors=False  # Don't return vectors (saves bandwidth)
)

# For qdrant-client <1.9.0
results = client.query_points(
    collection_name="my_collection",
    query=query_embedding,
    limit=5,
    with_payload=True
).points
```

### Search with Filters

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

results = client.search(
    collection_name="my_collection",
    query_vector=query_embedding,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="source_type",
                match=MatchValue(value="documentation")
            )
        ]
    ),
    limit=5
)
```

### Search Parameters

```python
results = client.search(
    collection_name="my_collection",
    query_vector=query_embedding,
    limit=5,
    search_params={
        "hnsw_ef": 128,  # Higher = more accurate but slower
        "exact": False   # True for exact search (slower)
    },
    score_threshold=0.5  # Minimum similarity score
)
```

---

## Deduplication Strategies

### Problem: Multiple Copies of Same Content

**Cause**: Pipeline ran multiple times, creating duplicate points

**Solution 1: Deduplicate at Query Time**

```python
seen_chunk_ids = set()
unique_results = []

for hit in results:
    chunk_id = hit.payload.get("chunk_id")
    if chunk_id not in seen_chunk_ids:
        seen_chunk_ids.add(chunk_id)
        unique_results.append(hit)
        if len(unique_results) >= top_k:
            break
```

**Solution 2: Idempotent Uploads**

```python
import hashlib

def generate_deterministic_id(chunk_id: str, collection_name: str) -> str:
    """Generate same ID for same chunk_id"""
    content = f"{collection_name}:{chunk_id}"
    return hashlib.md5(content.encode()).hexdigest()

# Use when uploading
point_id = generate_deterministic_id(chunk_id, collection_name)
client.upsert(
    collection_name=collection_name,
    points=[PointStruct(id=point_id, vector=embedding, payload=payload)]
)
```

**Solution 3: Clean Duplicates**

```python
from collections import defaultdict

# Find duplicates
all_points = client.scroll(collection_name=collection_name, limit=10000)[0]
chunk_to_points = defaultdict(list)

for point in all_points:
    chunk_id = point.payload.get("chunk_id")
    chunk_to_points[chunk_id].append(point.id)

# Delete duplicates (keep first occurrence)
ids_to_delete = []
for chunk_id, point_ids in chunk_to_points.items():
    if len(point_ids) > 1:
        ids_to_delete.extend(point_ids[1:])  # Keep first, delete rest

if ids_to_delete:
    client.delete(collection_name=collection_name, points_selector=ids_to_delete)
```

---

## Payload Management

### Store Minimal Data in Payload

```python
# Good: Store only what's needed for retrieval
payload = {
    "chunk_id": "chunk_123",
    "content_preview": content[:200],  # Short preview
    "source_url": "https://...",
    "title": "Document Title",
    "chunk_index": 0
}

# Bad: Storing full content (wastes storage and bandwidth)
payload = {
    "chunk_id": "chunk_123",
    "full_content": content,  # Don't do this!
    # ... other fields
}
```

### Create Payload Indexes for Filtering

```python
from qdrant_client.models import PayloadSchemaType

# Index frequently filtered fields
client.create_payload_index(
    collection_name="my_collection",
    field_name="source_type",
    field_schema=PayloadSchemaType.KEYWORD
)

client.create_payload_index(
    collection_name="my_collection",
    field_name="chunk_index",
    field_schema=PayloadSchemaType.INTEGER
)
```

---

## Performance Optimization

### Batch Operations

```python
# Upload in batches
batch_size = 100
points = []

for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
    points.append(PointStruct(
        id=str(uuid4()),
        vector=embedding,
        payload=create_payload(chunk)
    ))

    if len(points) >= batch_size or i == len(chunks) - 1:
        client.upsert(collection_name=collection_name, points=points)
        points = []
```

### Connection Pooling

```python
# Initialize once, reuse throughout application
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    global qdrant_client

    # Initialize on startup
    qdrant_client = QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY)

    yield

    # Cleanup on shutdown
    qdrant_client = None
```

### Limit Result Size

```python
# Request more than needed to account for deduplication
results = client.search(
    collection_name="my_collection",
    query_vector=query_embedding,
    limit=top_k * 7,  # Account for ~6-7x duplication
    with_payload=True,
    with_vectors=False  # Don't return vectors
)
```

---

## Monitoring & Health Checks

### Collection Stats

```python
def get_collection_health():
    try:
        info = client.get_collection(collection_name)
        return {
            "status": "healthy",
            "points_count": info.points_count,
            "vectors_count": info.vectors_count,
            "indexed_vectors_count": info.indexed_vectors_count,
            "segments_count": len(info.segments) if info.segments else 0
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### Test Search Quality

```python
def test_search_quality():
    test_queries = [
        "What is ROS 2?",
        "How to use Gazebo?",
        "Humanoid robot control"
    ]

    for query in test_queries:
        embedding = generate_query_embedding(query)
        results = client.search(
            collection_name=collection_name,
            query_vector=embedding,
            limit=3
        )

        print(f"Query: {query}")
        print(f"Top score: {results[0].score if results else 0}")
        print(f"Results: {len(results)}")
        print()
```

---

## Error Handling

### Graceful Degradation

```python
def search_with_fallback(query: str, top_k: int = 5):
    try:
        # Try primary search
        results = client.search(
            collection_name=collection_name,
            query_vector=generate_embedding(query),
            limit=top_k
        )
        return results
    except Exception as e:
        logger.error(f"Qdrant search failed: {e}")

        # Fallback: Return empty results
        return []
```

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def search_with_retry(query_vector, limit):
    return client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit
    )
```

---

## Security Best Practices

### API Key Management

```python
# Use environment variables
import os
from dotenv import load_dotenv

load_dotenv()

QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
if not QDRANT_API_KEY:
    raise ValueError("QDRANT_API_KEY not set")

# Never hardcode
# QDRANT_API_KEY = "abc123..."  # DON'T DO THIS
```

### Read-Only Access for Production

```python
# Use read-only API keys for production queries
# Create separate keys for:
# - Read-only (production queries)
# - Write access (indexing pipeline)
# - Admin access (collection management)
```

---

## Checklist

Before deploying Qdrant integration:

- [ ] Collection created with correct vector dimension
- [ ] Distance metric set to COSINE
- [ ] Payload indexes created for filtered fields
- [ ] Deduplication strategy implemented
- [ ] Batch operations for uploads
- [ ] Connection pooling configured
- [ ] Health checks implemented
- [ ] Error handling with fallbacks
- [ ] API keys in environment variables
- [ ] Search quality tested with sample queries
