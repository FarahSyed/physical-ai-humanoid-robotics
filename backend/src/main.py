"""
FastAPI RAG Agent with Qwen and Qdrant Cloud

This implementation provides a minimal RAG (Retrieval-Augmented Generation) system
that uses Qwen API for response generation and Qdrant Cloud for vector storage and retrieval.

The system exposes two endpoints:
- /chat: Processes user queries using RAG methodology with Qwen API
- /health: Returns system health status and collection information
"""
import os
import asyncio
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    RunConfig,
    ModelSettings,
    OpenAIChatCompletionsModel,
    function_tool,
    set_default_openai_client,
)
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, Filter
from dotenv import load_dotenv
from datetime import datetime
import cohere


# Load environment variables
load_dotenv()

# Configuration (Immutable)
MODEL_ID = "openai/gpt-3.5-turbo-0613"  # Using OpenAI model compatible with OpenRouter
# SYSTEM_INSTRUCTIONS = """You are an insightful book tutor named 'Prof. Neuronik Spark', specialized in helping students and readers deeply understand 'Physical AI Humanoid Robotics' by 'Farah Syed'. Your expertise includes technical concepts, algorithms, system architectures, control theory, AI integration, and practical applications in humanoid robots. Always base your responses on the provided retrieved passages from the book to ensure factual accuracy; do not mention the author name until asked; do not invent details or rely on external knowledge.

# For each user query:
# 1. Analyze the query to identify the core question or need (e.g., explanation of a chapter, concept clarification, algorithm breakdown, or system design).
# 2. Retrieve and review the most relevant passages from the book (provided in the context below). If no relevant passages are retrieved, politely state that and suggest rephrasing the query.
# 3. Think step by step:
#    - Summarize the key facts from the retrieved passages.
#    - Connect them to the query with clear explanations.
#    - Highlight educational insights, such as algorithmic efficiency, engineering trade-offs, or real-world implementations.
# 4. Generate a helpful response that is engaging, easy to understand, and tailored to the user's level (assume beginner unless specified).
# 5. Structure your output as follows:
#    - **Summary**: A concise overview of the answer.
#    - **Key Excerpts**: 2-3 relevant quotes or passages from the book, with page/chapter references if available.
#    - **Analysis**: In-depth explanation with examples.
#    - **Questions for You**: 1-2 follow-up questions to encourage deeper engagement.
#    - **Further Reading**: Suggest related sections in the book.

# Context (retrieved passages): {retrieved_context}

# User query: {user_query}

# Respond only to the user query, keeping responses under 500 words unless more detail is requested. Use positive, encouraging language to foster learning.

# """
SYSTEM_INSTRUCTIONS = """You are 'Prof. Neuronik Spark', a book tutor for 'Physical AI Humanoid Robotics' by Farah Syed.

  CRITICAL RULES - YOU MUST FOLLOW THESE EXACTLY:
  1. You can ONLY answer using information from the retrieved passages provided in the context below
  2. If the context is empty or says "No relevant documents found", you MUST respond: "I don't have information about that in the retrieved passages. Please try rephrasing
  your question or ask about a different topic from the book."
  3. NEVER use your general knowledge or training data
  4. NEVER make up information not present in the retrieved context
  5. Always cite which retrieved passage you're using (by ID)

  Retrieved Context:
  {retrieved_context}

  User Query:
  {user_query}

  If the context above contains relevant information, answer the question using ONLY that information. If not, say you don't have that information in the retrieved
  passages.
  """

QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "humanoid-robotics-book")
QDRANT_HOST = os.getenv("QDRANT_HOST")  # e.g., https://your-cluster.qdrant.io:6333
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QWEN_API_KEY = os.getenv("QWEN_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Validate required env vars
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
if not all([QDRANT_HOST, QDRANT_API_KEY, QWEN_API_KEY, COHERE_API_KEY, GEMINI_API_KEY]):
    raise ValueError("Missing required env vars: QDRANT_HOST, QDRANT_API_KEY, QWEN_API_KEY, COHERE_API_KEY, GEMINI_API_KEY")


# Global variables for clients
qdrant_client = None
chunked_content_cache = None  # Cache for full content lookup


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to initialize and cleanup resources
    """
    global qdrant_client, chunked_content_cache

    # Initialize clients during startup
    print("Initializing clients...")

    # Load full content from chunked_content.json for hydration
    import json
    from pathlib import Path
    chunked_file = Path(__file__).parent.parent / "data" / "chunked" / "chunked_content.json"
    if chunked_file.exists():
        with open(chunked_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            chunks = data.get('chunks', [])
            chunked_content_cache = {chunk['id']: chunk['content'] for chunk in chunks}
            print(f"Loaded {len(chunked_content_cache)} full content chunks for hydration")
    else:
        print("Warning: chunked_content.json not found, will use preview only")
        chunked_content_cache = {}

    # Initialize Qdrant Client (singleton for connection pooling)
    qdrant_client = QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY)

    # Verify collection exists
    try:
        collection_info = qdrant_client.get_collection(QDRANT_COLLECTION_NAME)
        print(f"Connected to Qdrant collection: {QDRANT_COLLECTION_NAME}")
    except Exception as e:
        print(f"Error connecting to Qdrant collection {QDRANT_COLLECTION_NAME}: {e}")
        raise

    print("All clients initialized successfully")

    yield  # Application runs here

    # Cleanup during shutdown
    print("Cleaning up resources...")
    qdrant_client = None


# FastAPI Pydantic Schemas
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


# Create FastAPI app with lifespan
app = FastAPI(
    title="RAG Agent API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Docusaurus dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_embedding_dimension():
    """Get the embedding dimension from the Qdrant collection."""
    global qdrant_client
    try:
        collection_info = qdrant_client.get_collection(QDRANT_COLLECTION_NAME)
        if hasattr(collection_info.config.params, 'vectors'):
            if isinstance(collection_info.config.params.vectors, dict):
                return collection_info.config.params.vectors['size']
            else:
                return collection_info.config.params.vectors.size
        else:
            # Default fallback size if not found
            return 1536
    except Exception:
        # Default fallback size if collection info cannot be retrieved
        return 1536


# Qdrant Search Tool (deterministic, cosine metric)
def search_rag_context(query: str, top_k: int = 5) -> str:
    """Search Qdrant vector database for relevant context using cosine similarity."""
    global qdrant_client

    print(f"\n{'='*80}")
    print(f"SEARCH FUNCTION CALLED")
    print(f"Query: {query}")
    print(f"Top K: {top_k}")

    # Check for nested client objects
    if hasattr(qdrant_client, 'http'):
        print(f"qdrant_client.http exists: {type(qdrant_client.http)}")
        print(f"qdrant_client.http has search: {hasattr(qdrant_client.http, 'search')}")
    if hasattr(qdrant_client, 'grpc_points'):
        print(f"qdrant_client.grpc_points exists: {type(qdrant_client.grpc_points)}")
        print(f"qdrant_client.grpc_points has search: {hasattr(qdrant_client.grpc_points, 'search')}")

    # Try to get the search method directly from the class
    print(f"Trying to get search from class...")
    search_method = getattr(qdrant_client.__class__, 'search', None)
    print(f"Class has search method: {search_method is not None}")
    print(f"{'='*80}\n")

    try:
        # Get the correct embedding dimension from the collection
        vector_size = get_embedding_dimension()
        print(f"Vector size from collection: {vector_size}")

        # For better compatibility with stored embeddings, we'll use Cohere
        # since the existing pipeline uses Cohere for embedding generation
        co = cohere.Client(os.getenv("COHERE_API_KEY"))

        # Generate embedding for the query using Cohere with the same parameters as the pipeline
        response = co.embed(
            texts=[query],
            model="embed-english-v3.0",  # Same model as used in pipeline
            input_type="search_query",  # Use search_query for queries (documents were indexed with search_document)
            truncate="END"  # Same truncation as used in pipeline
        )
        query_embedding = response.embeddings[0]

        # Ensure the embedding dimension matches what's expected by Qdrant
        if len(query_embedding) != vector_size:
            print(f"Embedding dimension mismatch: expected {vector_size}, got {len(query_embedding)}")
            # This is a critical issue - embeddings must match the stored dimension
            # In a real scenario, we'd need to use the exact same model that was used for indexing
            if len(query_embedding) > vector_size:
                query_embedding = query_embedding[:vector_size]
                print("query_embedding if block", query_embedding)
            else:
                # Pad with zeros if needed (though this is not ideal)
                query_embedding.extend([0.0] * (vector_size - len(query_embedding)))
                print("query_embedding else block", query_embedding)

        # Use query_points method (available in qdrant-client 1.8.2)
        print(f"Calling qdrant_client.query_points()...")
        results = qdrant_client.query_points(
            collection_name=QDRANT_COLLECTION_NAME,
            query=query_embedding,
            limit=top_k * 7,  # Request 7x to account for ~6-7 duplicates per chunk
            with_payload=True
        ).points
        print(f"Query completed successfully! Got {len(results)} results")
        # ADD THIS DEBUG:
        print(f"DEBUG - Query: {query}")
        print(f"DEBUG - Query embedding dimension: {len(query_embedding)}")
        print(f"DEBUG - Number of results: {len(results)}")
        if results:
            print(f"DEBUG - Top result score: {results[0].score}")
            print(f"DEBUG - Top result payload keys: {list(results[0].payload.keys())}")
        else:
            print("DEBUG - NO RESULTS RETURNED FROM QDRANT")

        context = []
        seen_chunk_ids = set()  # Track seen chunks to avoid duplicates

        for hit in results:
            # Stop once we have enough unique chunks
            if len(context) >= top_k:
                break

            payload = hit.payload or {}
            chunk_id = payload.get("chunk_id", "")

            # Skip if we've already seen this chunk_id
            if chunk_id in seen_chunk_ids:
                print(f"  Skipping duplicate chunk {chunk_id}")
                continue

            seen_chunk_ids.add(chunk_id)

            # Try to get full content from cache, fallback to preview
            if chunked_content_cache and chunk_id in chunked_content_cache:
                full_content = chunked_content_cache[chunk_id]
                print(f"  Hydrated chunk {chunk_id} with full content ({len(full_content)} chars)")
            else:
                full_content = payload.get("content_preview", "")
                print(f"  Using preview for chunk {chunk_id} ({len(full_content)} chars)")

            context.append({
                "id": str(hit.id),
                "chunk_id": chunk_id,  # Add chunk_id for reference
                "text": full_content,  # Use full content instead of preview
                "score": hit.score,
                "metadata": payload.get("metadata", {})
            })
        print(f"Found {len(context)} relevant documents:\n" + "\n".join([f"- [{doc['id']}]: {doc['text'][:200]}... (score: {doc['score']:.3f})" for doc in context]))

        return f"Found {len(context)} relevant documents:\n" + \
               "\n\n".join([f"Document [{doc['id']}] (score: {doc['score']:.3f}):\n{doc['text'][:1000]}{'...' if len(doc['text']) > 1000 else ''}"
                         for doc in context])
    except Exception as e:
        return f"Search failed: {str(e)}"

# Create the tool after defining the function
search_rag_context_tool = function_tool(search_rag_context)


# Configure the OpenAI client for the agents framework
def configure_agents_client():
    """Configure the OpenAI client for the agents framework."""
    # client = AsyncOpenAI(
    #     api_key=GEMINI_API_KEY,
    #     base_url="https://generativelanguage.googleapis.com/v1beta/openai/",  # Qwen OpenAI-compatible endpoint
    # )
    client = AsyncOpenAI(
        api_key=os.getenv("OPEN_ROUTER_API_KEY"),  # Use API key from environment
        base_url="https://openrouter.ai/api/v1",  # OpenRouter OpenAI-compatible endpoint
    )
    set_default_openai_client(client, use_for_tracing=False)


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """Execute RAG agent with Qdrant retrieval."""
    try:
        # Configure the agents client
        configure_agents_client()

        # Step 1: Search Qdrant (deterministic tool)
        print(f"\n>>> CHAT ENDPOINT: About to call search_rag_context")
        search_result = search_rag_context(req.prompt, req.top_k or 5)
        print(f">>> CHAT ENDPOINT: Search result length: {len(search_result)}")
        print(f">>> CHAT ENDPOINT: Search result preview: {search_result[:200]}...")

        # Check if search failed
        if search_result.startswith("Search failed:"):
            # Even if search failed, we can still try to generate a response
            # Just with empty context
            search_result = "No relevant documents found in the knowledge base."

        # Step 2: Build the agent with system instructions (no tools needed - context already retrieved)
        # Use OpenAIChatCompletionsModel with properly configured client
        agent = Agent(
            name="RAG-Agent",
            instructions=SYSTEM_INSTRUCTIONS,
            tools=[],  # No tools - we already retrieved and injected the context
            model=OpenAIChatCompletionsModel(
                model=MODEL_ID,
                # openai_client=AsyncOpenAI(
                #     api_key=GEMINI_API_KEY,
                #     base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                # )
                openai_client=AsyncOpenAI(
                    api_key=os.getenv("OPEN_ROUTER_API_KEY"),  # Use API key from environment
                    base_url="https://openrouter.ai/api/v1"
                )
            )
        )

        # Step 3: Prepare the input with context
        input_with_context = f"{req.prompt}\n\nContext:\n{search_result}"

        # Step 4: Run the agent
        response = await Runner.run(agent, input_with_context)

        # Parse sources (extract from search_result)
        sources = []
        # Parse the search_result string to extract source information (new format)
        lines = search_result.split('\n')
        for line in lines:
            # New format: "Document [id] (score: X):"
            if line.startswith('Document [') and '(score:' in line:
                try:
                    id_part = line.split('[')[1].split(']')[0]
                    score_part = float(line.split('(score: ')[1].split(')')[0])

                    # Get the text from the next line(s) - take first 200 chars as preview
                    line_index = lines.index(line)
                    if line_index + 1 < len(lines):
                        text_part = lines[line_index + 1][:200]
                    else:
                        text_part = ""

                    sources.append(Source(
                        id=id_part,
                        text=text_part,
                        score=score_part
                    ))
                except Exception as e:
                    print(f"Error parsing source: {e}")
                    continue  # Skip if parsing fails

        return ChatResponse(
            answer=str(response.final_output) if response.final_output else "No response generated",
            sources=sources,
            usage={"timestamp": int(datetime.utcnow().timestamp())}
        )

    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_details = traceback.format_exc()
        print(f"Full error details: {error_details}")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    global qdrant_client

    try:
        # Get collection information to verify it exists and is accessible
        collection_info = qdrant_client.get_collection(QDRANT_COLLECTION_NAME)
        vector_count = collection_info.points_count

        return {
            "status": "healthy",
            "collection": QDRANT_COLLECTION_NAME,
            "vector_count": vector_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

























# import os
# import cohere
# from qdrant_client import QdrantClient
# from qdrant_client.http.models import SearchParams
# from dotenv import load_dotenv

# load_dotenv()

# # ==============================
# # CONFIG
# # ==============================

# QDRANT_URL = os.getenv("QDRANT_HOST")
# QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
# QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME")
# COHERE_API_KEY = os.getenv("COHERE_API_KEY")

# if not all([QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION_NAME, COHERE_API_KEY]):
#     raise RuntimeError("Missing required environment variables")

# print(QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION_NAME, COHERE_API_KEY)
# # ==============================
# # CLIENTS
# # ==============================

# qdrant_client = QdrantClient(
#     url=QDRANT_URL,
#     api_key=QDRANT_API_KEY
# )

# co = cohere.Client(COHERE_API_KEY)

# # ==============================
# # HELPERS
# # ==============================

# def get_embedding_dimension():
#     """Fetch embedding dimension directly from Qdrant collection."""
#     collection_info = qdrant_client.get_collection(QDRANT_COLLECTION_NAME)

#     vectors = collection_info.config.params.vectors

#     if isinstance(vectors, dict):
#         return vectors["size"]

#     return vectors.size


# def search_rag_context(query: str, top_k: int = 5):
#     """Search Qdrant using Cohere embeddings and cosine similarity."""

#     vector_size = get_embedding_dimension()

#     response = co.embed(
#         texts=[query],
#         model="embed-english-v3.0",
#         input_type="search_query",
#         truncate="END"
#     )

#     query_embedding = response.embeddings[0]

#     if len(query_embedding) != vector_size:
#         raise RuntimeError(
#             f"Embedding dimension mismatch. Expected {vector_size}, got {len(query_embedding)}"
#         )

#     results = qdrant_client.search(
#         collection_name=QDRANT_COLLECTION_NAME,
#         query_vector=query_embedding,
#         limit=top_k,
#         search_params=SearchParams(
#             hnsw_ef=128,
#             exact=False
#         )
#     )

#     if not results:
#         print("No results found. Your embeddings or indexing are bad.")
#         return

#     print("\nTop Retrieved Context:\n")

#     for idx, hit in enumerate(results, start=1):
#         payload = hit.payload or {}
#         text = payload.get("content_preview") or payload.get("text") or ""

#         print(f"{idx}. Score: {hit.score:.4f}")
#         print(text.strip()[:500])
#         print("-" * 80)


# # ==============================
# # MAIN TEST
# # ==============================

# def main():
#     query = (
#         "What role does ROS 2 play in humanoid robot systems, "
#         "and what advantages does it have over ROS 1?"
#     )

#     print("\nQuery:")
#     print(query)
#     print("\nSearching Qdrant...\n")

#     search_rag_context(query)


# if __name__ == "__main__":
#     main()
