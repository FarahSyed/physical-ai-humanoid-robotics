import os
import asyncio
from dotenv import load_dotenv
from qdrant_client import QdrantClient
import cohere

# Load environment variables
load_dotenv()

# Initialize clients with the same configuration as main.py
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "humanoid-robotics-book")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

print("Initializing clients...")
qdrant_client = QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY)
co = cohere.Client(COHERE_API_KEY)

print(f"Connected to Qdrant collection: {QDRANT_COLLECTION_NAME}")

def search_rag_context_debug(query: str, top_k: int = 5):
    """Search Qdrant vector database for relevant context using cosine similarity."""
    try:
        # Get the correct embedding dimension from the collection
        collection_info = qdrant_client.get_collection(QDRANT_COLLECTION_NAME)
        vector_size = collection_info.config.params.vectors.size
        print(f"Vector size: {vector_size}")

        # Generate embedding for the query using Cohere with the same parameters as the pipeline
        response = co.embed(
            texts=[query],
            model="embed-english-v3.0",  # Same model as used in pipeline
            input_type="classification",  # Same input type as used in pipeline
            truncate="END"  # Same truncation as used in pipeline
        )
        query_embedding = response.embeddings[0]
        print(f"Query embedding dimension: {len(query_embedding)}")

        # Ensure the embedding dimension matches what's expected by Qdrant
        if len(query_embedding) != vector_size:
            print(f"Embedding dimension mismatch: expected {vector_size}, got {len(query_embedding)}")
            if len(query_embedding) > vector_size:
                query_embedding = query_embedding[:vector_size]
            else:
                # Pad with zeros if needed (though this is not ideal)
                query_embedding.extend([0.0] * (vector_size - len(query_embedding)))

        results = qdrant_client.search(
            collection_name=QDRANT_COLLECTION_NAME,
            query_vector=query_embedding,
            limit=top_k,
            query_filter=None,  # Add filters if needed
            search_params={"hnsw_ef": 128, "exact": False}
        )

        print(f"Search returned {len(results)} raw results:")
        for i, hit in enumerate(results):
            print(f"  {i+1}. ID: {hit.id}")
            print(f"     Score: {hit.score}")
            payload = hit.payload or {}
            content_preview = payload.get("content_preview", "")
            print(f"     Content preview: {content_preview[:100]}...")
            print(f"     Payload keys: {list(payload.keys())}")
            print()

        context = []
        for hit in results:
            payload = hit.payload or {}
            context.append({
                "id": str(hit.id),
                "text": payload.get("content_preview", ""),
                "score": hit.score,
                "metadata": payload.get("metadata", {})
            })

        print(f"Context list: {len(context)} items")

        result_str = f"Found {len(context)} relevant documents:\n" + \
               "\n".join([f"- [{doc['id']}]: {doc['text'][:200]}... (score: {doc['score']:.3f})"
                         for doc in context])

        print(f"Result string format: {repr(result_str[:200])}...")

        return result_str
    except Exception as e:
        print(f"Search failed: {str(e)}")
        return f"Search failed: {str(e)}"

# Test the search function directly
test_queries = ["robotics", "humanoid", "humanoid robotics"]
for query in test_queries:
    print(f"\n{'='*50}")
    print(f"Testing search for: '{query}'")
    print('='*50)
    result = search_rag_context_debug(query, top_k=3)
    print(f"Final result: {repr(result)}")

    # Test parsing logic
    print("\nTesting parsing logic:")
    lines = result.split('\n')
    source_lines = [line for line in lines if line.startswith('- [') and ']:' in line]
    print(f"Found {len(source_lines)} source lines for parsing")
    for i, line in enumerate(source_lines):
        print(f"  Source line {i+1}: {repr(line)}")