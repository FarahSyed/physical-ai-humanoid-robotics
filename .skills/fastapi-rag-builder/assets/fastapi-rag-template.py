"""
FastAPI RAG System Template

Complete implementation of a RAG system with:
- Qdrant vector search
- Cohere embeddings
- Content hydration
- Deduplication
- Error handling

Usage:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from datetime import datetime

import cohere
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment variables
load_dotenv()

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "rag_collection")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate required environment variables
if not all([QDRANT_HOST, QDRANT_API_KEY, COHERE_API_KEY, OPENAI_API_KEY]):
    raise ValueError("Missing required environment variables")

# Global variables
qdrant_client = None
content_cache = None


# Pydantic Models
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


# Lifespan Management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup resources"""
    global qdrant_client, content_cache

    print("Initializing resources...")

    # Load content cache for hydration
    chunked_file = Path(__file__).parent / "data" / "chunked" / "chunked_content.json"
    if chunked_file.exists():
        with open(chunked_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chunks = data.get('chunks', [])
            content_cache = {chunk['id']: chunk['content'] for chunk in chunks}
            print(f"Loaded {len(content_cache)} content chunks")
    else:
        print("Warning: chunked_content.json not found")
        content_cache = {}

    # Initialize Qdrant client
    qdrant_client = QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY)

    # Verify collection
    try:
        collection_info = qdrant_client.get_collection(QDRANT_COLLECTION_NAME)
        print(f"Connected to collection: {QDRANT_COLLECTION_NAME}")
        print(f"Vectors: {collection_info.points_count}")
    except Exception as e:
        print(f"Error connecting to collection: {e}")
        raise

    print("All resources initialized")

    yield  # Application runs

    # Cleanup
    print("Cleaning up resources...")
    qdrant_client = None
    content_cache = None


# Create FastAPI app
app = FastAPI(
    title="RAG API",
    version="1.0.0",
    description="Retrieval-Augmented Generation API with Qdrant and Cohere",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Search Function
def search_rag_context(query: str, top_k: int = 5) -> tuple[str, List[Dict]]:
    """
    Search Qdrant for relevant context.

    Returns:
        Tuple of (formatted_context_string, sources_list)
    """
    global qdrant_client, content_cache

    try:
        # Generate query embedding
        co = cohere.Client(COHERE_API_KEY)
        response = co.embed(
            texts=[query],
            model="embed-english-v3.0",
            input_type="search_query",  # For queries
            truncate="END"
        )
        query_embedding = response.embeddings[0]

        # Search Qdrant (request extra for deduplication)
        results = qdrant_client.query_points(
            collection_name=QDRANT_COLLECTION_NAME,
            query=query_embedding,
            limit=top_k * 7,  # Account for duplicates
            with_payload=True
        ).points

        # Deduplicate and hydrate
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

        # Format for LLM
        formatted = f"Found {len(context)} relevant documents:\n\n"
        for doc in context:
            formatted += f"Document [{doc['id']}] (score: {doc['score']:.3f}):\n"
            formatted += f"{doc['text'][:1000]}\n\n"

        return formatted, context

    except Exception as e:
        print(f"Search error: {e}")
        return f"Search failed: {str(e)}", []


# Chat Endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """Execute RAG query"""
    try:
        # Search Qdrant
        search_result, sources_data = search_rag_context(req.prompt, req.top_k or 5)

        # Check for failures
        if search_result.startswith("Search failed:"):
            search_result = "No relevant documents found in the knowledge base."

        # Create OpenAI client
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)

        # System prompt with context
        system_prompt = """You are a helpful assistant. Answer ONLY using the retrieved context below.
        If the context doesn't contain the answer, say "I don't have that information in the retrieved passages."

        Retrieved Context:
        {context}
        """

        messages = [
            {"role": "system", "content": system_prompt.format(context=search_result)},
            {"role": "user", "content": req.prompt}
        ]

        # Get response
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7
        )

        answer = response.choices[0].message.content

        # Convert sources to response format
        sources = [
            Source(
                id=src["id"],
                text=src["text"][:200],  # Preview
                score=src["score"],
                metadata=src.get("metadata")
            )
            for src in sources_data
        ]

        return ChatResponse(
            answer=answer,
            sources=sources,
            usage={"timestamp": int(datetime.utcnow().timestamp())}
        )

    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


# Health Endpoint
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
            "content_cache_size": len(content_cache) if content_cache else 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
