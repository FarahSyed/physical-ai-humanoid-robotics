# Dependencies for FastAPI RAG System

## Core Dependencies

```bash
pip install fastapi uvicorn qdrant-client cohere python-dotenv pydantic
```

### Package Versions

```
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
qdrant-client>=1.8.0  # Note: API differs between versions
cohere>=5.5.0
python-dotenv>=1.0.0
pydantic>=2.5.0
```

## Optional Dependencies

### For OpenAI Integration
```bash
pip install openai>=1.0.0
```

### For OpenAI Agents SDK
```bash
pip install openai-agents>=0.6.4
```

### For Development
```bash
pip install pytest pytest-asyncio httpx
```

---

## Version-Specific Notes

### qdrant-client

**Version <1.9.0**:
- Use `query_points()` method
- Returns `.points` attribute

```python
results = client.query_points(
    collection_name=name,
    query=embedding,
    limit=5
).points
```

**Version >=1.9.0**:
- Use `search()` method
- Returns list directly

```python
results = client.search(
    collection_name=name,
    query_vector=embedding,
    limit=5
)
```

### Cohere

**Version >=5.0.0**:
- New API structure
- `co.embed()` returns response object

```python
response = co.embed(texts=[...], model="...", input_type="...")
embeddings = response.embeddings
```

---

## Installation Methods

### Using pip

```bash
pip install -r requirements.txt
```

### Using uv (Recommended)

```bash
uv sync
```

### Using poetry

```bash
poetry add fastapi uvicorn qdrant-client cohere python-dotenv pydantic
```

---

## requirements.txt

```
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
qdrant-client>=1.8.0
cohere>=5.5.0
python-dotenv>=1.0.0
pydantic>=2.5.0
openai>=1.0.0
```

---

## pyproject.toml (for uv)

```toml
[project]
name = "rag-backend"
version = "0.1.0"
dependencies = [
    "fastapi>=0.104.1",
    "uvicorn[standard]>=0.24.0",
    "qdrant-client>=1.8.0",
    "cohere>=5.5.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.5.0",
    "openai>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.24.0",
]
```

---

## Compatibility Matrix

| Python | FastAPI | qdrant-client | Cohere |
|--------|---------|---------------|--------|
| 3.11+  | 0.104+  | 1.8.0+        | 5.5.0+ |
| 3.10+  | 0.100+  | 1.7.0+        | 5.0.0+ |
| 3.9+   | 0.95+   | 1.6.0+        | 4.0.0+ |

---

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'qdrant_client'`

**Solution**:
```bash
pip install qdrant-client
```

### Version Conflicts

**Problem**: `AttributeError: 'QdrantClient' object has no attribute 'search'`

**Solution**: Check qdrant-client version
```bash
pip show qdrant-client
# If <1.9.0, use query_points() instead of search()
```

### SSL Errors with Qdrant Cloud

**Problem**: SSL certificate verification failed

**Solution**:
```bash
pip install --upgrade certifi
```
