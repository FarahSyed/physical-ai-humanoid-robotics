#!/usr/bin/env python3
"""
Generate embeddings and store in Qdrant.

Usage:
    python generate_embeddings.py --input data/chunked/chunked_content.json
"""

import json
import argparse
import os
from pathlib import Path
from typing import List, Dict, Any
from uuid import uuid4
import asyncio

import cohere
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv


def load_chunks(file_path: Path) -> List[Dict[str, Any]]:
    """Load chunked content from JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('chunks', [])


def generate_embeddings_batch(
    texts: List[str],
    cohere_client: cohere.Client,
    model: str = "embed-english-v3.0"
) -> List[List[float]]:
    """Generate embeddings for a batch of texts."""
    response = cohere_client.embed(
        texts=texts,
        model=model,
        input_type="search_document",  # For indexing
        truncate="END"
    )
    return response.embeddings


def create_collection_if_not_exists(
    client: QdrantClient,
    collection_name: str,
    vector_size: int = 1024
):
    """Create Qdrant collection if it doesn't exist."""
    try:
        client.get_collection(collection_name)
        print(f"Collection '{collection_name}' already exists")
    except Exception:
        print(f"Creating collection '{collection_name}'...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )
        print("Collection created successfully")


def store_embeddings(
    client: QdrantClient,
    collection_name: str,
    chunks: List[Dict[str, Any]],
    embeddings: List[List[float]]
):
    """Store embeddings in Qdrant."""
    points = []

    for chunk, embedding in zip(chunks, embeddings):
        point = PointStruct(
            id=str(uuid4()),
            vector=embedding,
            payload={
                "chunk_id": chunk['id'],
                "content_preview": chunk['content'][:200],
                "timestamp": chunk['metadata'].get('timestamp', ''),
                "embedding_model": "embed-english-v3.0",
                "embedding_provider": "cohere",
                **chunk['metadata']
            }
        )
        points.append(point)

    # Upload in batches
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(collection_name=collection_name, points=batch)
        print(f"Uploaded batch {i//batch_size + 1}/{(len(points) + batch_size - 1)//batch_size}")


def main():
    parser = argparse.ArgumentParser(description="Generate embeddings and store in Qdrant")
    parser.add_argument("--input", type=str, required=True, help="Input chunked content JSON file")
    parser.add_argument("--batch-size", type=int, default=96, help="Batch size for embedding generation")

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    COHERE_API_KEY = os.getenv("COHERE_API_KEY")
    QDRANT_HOST = os.getenv("QDRANT_HOST")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "rag_collection")

    if not all([COHERE_API_KEY, QDRANT_HOST, QDRANT_API_KEY]):
        print("Error: Missing required environment variables")
        print("Required: COHERE_API_KEY, QDRANT_HOST, QDRANT_API_KEY")
        return

    # Initialize clients
    print("Initializing clients...")
    co = cohere.Client(COHERE_API_KEY)
    qdrant_client = QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY)

    # Load chunks
    input_file = Path(args.input)
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return

    print(f"Loading chunks from {input_file}...")
    chunks = load_chunks(input_file)
    print(f"Loaded {len(chunks)} chunks")

    # Create collection
    create_collection_if_not_exists(qdrant_client, QDRANT_COLLECTION_NAME)

    # Generate and store embeddings in batches
    batch_size = args.batch_size
    total_batches = (len(chunks) + batch_size - 1) // batch_size

    print(f"\nGenerating embeddings in {total_batches} batches...")

    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i + batch_size]
        batch_texts = [chunk['content'] for chunk in batch_chunks]

        print(f"\nBatch {i//batch_size + 1}/{total_batches}")
        print(f"Generating embeddings for {len(batch_texts)} chunks...")

        try:
            embeddings = generate_embeddings_batch(batch_texts, co)
            print(f"Generated {len(embeddings)} embeddings")

            print("Storing in Qdrant...")
            store_embeddings(qdrant_client, QDRANT_COLLECTION_NAME, batch_chunks, embeddings)
            print("Batch complete")

        except Exception as e:
            print(f"Error processing batch: {e}")
            continue

    # Verify storage
    collection_info = qdrant_client.get_collection(QDRANT_COLLECTION_NAME)
    print(f"\n✓ Pipeline complete!")
    print(f"Total vectors in Qdrant: {collection_info.points_count}")


if __name__ == "__main__":
    main()
