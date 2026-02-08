#!/usr/bin/env python3
"""
Test Qdrant search functionality.

Usage:
    python test_search.py
"""

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
import cohere


def test_search(query_text: str, top_k: int = 5):
    """Test search with a query."""
    load_dotenv()

    # Initialize clients
    QDRANT_HOST = os.getenv("QDRANT_HOST")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "rag_collection")
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")

    print("Initializing clients...")
    qdrant_client = QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY)
    co = cohere.Client(COHERE_API_KEY)

    # Check collection
    collection_info = qdrant_client.get_collection(QDRANT_COLLECTION_NAME)
    print(f"Collection: {QDRANT_COLLECTION_NAME}")
    print(f"Vectors: {collection_info.points_count}\n")

    # Generate query embedding
    print(f"Query: {query_text}")
    response = co.embed(
        texts=[query_text],
        model="embed-english-v3.0",
        input_type="search_query",  # For queries
        truncate="END"
    )
    query_embedding = response.embeddings[0]
    print(f"Query embedding dimension: {len(query_embedding)}\n")

    # Search
    print("Searching...")
    try:
        # Try query_points (for qdrant-client <1.9.0)
        results = qdrant_client.query_points(
            collection_name=QDRANT_COLLECTION_NAME,
            query=query_embedding,
            limit=top_k,
            with_payload=True
        ).points
    except AttributeError:
        # Try search (for qdrant-client >=1.9.0)
        results = qdrant_client.search(
            collection_name=QDRANT_COLLECTION_NAME,
            query_vector=query_embedding,
            limit=top_k,
            with_payload=True
        )

    print(f"Found {len(results)} results:\n")

    for i, hit in enumerate(results, 1):
        payload = hit.payload or {}
        print(f"{i}. Score: {hit.score:.4f}")
        print(f"   Chunk ID: {payload.get('chunk_id', 'N/A')}")
        print(f"   Title: {payload.get('title', 'N/A')}")
        print(f"   Preview: {payload.get('content_preview', 'N/A')[:100]}...")
        print()


if __name__ == "__main__":
    # Test with sample queries
    test_queries = [
        "What is ROS 2?",
        "How to use Gazebo simulation?",
        "Humanoid robot control systems"
    ]

    for query in test_queries:
        print("=" * 80)
        test_search(query, top_k=3)
        print()
