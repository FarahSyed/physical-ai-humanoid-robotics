# Debugging Guide for RAG Systems

Common issues encountered when building RAG systems and their solutions.

## Issue 1: Embedding Dimension Mismatch

**Symptom**: Search returns 0 results or very low similarity scores

**Cause**: Query embeddings have different dimensions than stored embeddings

**Solution**:
```python
# Check stored embedding dimension
collection_info = client.get_collection(collection_name)
stored_dim = collection_info.config.params.vectors.size

# Ensure query embedding matches
query_embedding = co.embed(
    texts=[query],
    model="embed-english-v3.0",
    input_type="search_query",  # Must match indexing input_type
    truncate="END"
)
assert len(query_embedding[0]) == stored_dim
```

**Prevention**: Always use consistent `input_type` and `model` for indexing and querying.

---

## Issue 2: Qdrant API Version Conflicts

**Symptom**: `AttributeError: 'QdrantClient' object has no attribute 'search'`

**Cause**: Using API methods from newer versions with older qdrant-client

**Diagnosis**:
```python
import qdrant_client
print(qdrant_client.__version__)  # Check version
```

**Solution**:
- **Version <1.9.0**: Use `query_points()` instead of `search()`
- **Version >=1.9.0**: Use `search()` method

```python
# For qdrant-client <1.9.0
results = client.query_points(
    collection_name=collection_name,
    query=query_embedding,
    limit=top_k,
    with_payload=True
).points

# For qdrant-client >=1.9.0
results = client.search(
    collection_name=collection_name,
    query_vector=query_embedding,
    limit=top_k,
    with_payload=True
)
```

---

## Issue 3: Duplicate Search Results

**Symptom**: Same content returned multiple times with identical scores

**Cause**: Same chunk stored multiple times in Qdrant (pipeline ran multiple times)

**Diagnosis**:
```python
from collections import Counter

results = client.scroll(collection_name=collection_name, limit=1000)
chunk_ids = [p.payload.get('chunk_id') for p in results[0]]
duplicates = Counter(chunk_ids)
print(f"Duplicates: {[(k, v) for k, v in duplicates.items() if v > 1]}")
```

**Solution**: Deduplicate results by chunk_id
```python
seen_chunk_ids = set()
unique_results = []

for hit in results:
    chunk_id = hit.payload.get("chunk_id")
    if chunk_id not in seen_chunk_ids:
        seen_chunk_ids.add(chunk_id)
        unique_results.append(hit)
```

**Prevention**: Implement idempotent uploads with unique point IDs based on chunk_id.

---

## Issue 4: Truncated Content in Responses

**Symptom**: Agent says "I don't have information" despite relevant results

**Cause**: Only storing content previews (200 chars) instead of full content

**Diagnosis**:
```python
# Check what's stored in payload
sample = client.scroll(collection_name=collection_name, limit=1)[0][0]
print(f"Content length: {len(sample.payload.get('content_preview', ''))}")
```

**Solution**: Hydrate results with full content from source file
```python
# Load full content cache on startup
with open('data/chunked/chunked_content.json', 'r') as f:
    data = json.load(f)
    content_cache = {chunk['id']: chunk['content'] for chunk in data['chunks']}

# Hydrate during search
for hit in results:
    chunk_id = hit.payload.get("chunk_id")
    full_content = content_cache.get(chunk_id, hit.payload.get("content_preview"))
```

---

## Issue 5: Input Type Mismatch

**Symptom**: Low similarity scores for obviously relevant content

**Cause**: Using wrong `input_type` for Cohere embeddings

**Solution**:
- **Indexing**: Use `input_type="search_document"`
- **Querying**: Use `input_type="search_query"`

```python
# During indexing
embeddings = co.embed(
    texts=documents,
    model="embed-english-v3.0",
    input_type="search_document",  # For documents
    truncate="END"
)

# During querying
query_embedding = co.embed(
    texts=[query],
    model="embed-english-v3.0",
    input_type="search_query",  # For queries
    truncate="END"
)
```

**Why**: Cohere uses different vector spaces for different input types.

---

## Issue 6: Agent Not Using Retrieved Context

**Symptom**: Agent provides generic answers despite having relevant context

**Cause**: Weak system instructions or context not properly formatted

**Solution**: Strengthen system prompt
```python
SYSTEM_INSTRUCTIONS = """
CRITICAL RULES - YOU MUST FOLLOW THESE EXACTLY:
1. You can ONLY answer using information from the retrieved passages
2. If context is empty, respond: "I don't have information about that"
3. NEVER use your general knowledge
4. NEVER make up information
5. Always cite which retrieved passage you're using

Retrieved Context:
{retrieved_context}

User Query:
{user_query}
"""
```

---

## Issue 7: Slow Response Times

**Symptom**: Queries take >10 seconds

**Causes & Solutions**:

1. **Multiple redundant searches**
   - Don't give agent access to search tool if you already retrieved context
   - Remove `tools=[search_tool]` if context is pre-fetched

2. **Large context windows**
   - Limit retrieved content to 1000 chars per document
   - Use `top_k=3-5` instead of 10+

3. **Synchronous operations**
   - Use async operations for Qdrant and LLM calls
   - Implement connection pooling

---

## Debugging Checklist

When RAG system isn't working:

1. **Verify data pipeline**:
   - [ ] Content extracted correctly
   - [ ] Embeddings generated with correct model/input_type
   - [ ] Vectors stored in Qdrant (check collection stats)

2. **Test search independently**:
   - [ ] Run `test_search.py` to verify retrieval works
   - [ ] Check similarity scores (should be >0.5 for relevant content)
   - [ ] Verify full content is available

3. **Check API integration**:
   - [ ] Qdrant client version compatible with API calls
   - [ ] Environment variables set correctly
   - [ ] CORS configured for frontend

4. **Validate LLM integration**:
   - [ ] System prompt includes retrieved context
   - [ ] Agent not calling redundant tools
   - [ ] Response grounded in retrieved content
