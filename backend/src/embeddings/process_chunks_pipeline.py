#!/usr/bin/env python3
"""
Complete pipeline to process existing chunks from chunked_content.json and convert them to embeddings stored in Qdrant.
"""
import json
import sys
import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# Import the necessary modules from the embeddings package
from .config import EmbeddingConfig
from .provider import CohereEmbeddingProvider
from .qdrant_client import QdrantEmbeddingClient


def load_chunked_content(file_path: str) -> List[Dict[str, Any]]:
    """
    Load chunked content from JSON file.
    """
    print(f"Loading chunked content from {file_path}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Check if the data is a dictionary with a 'chunks' key or a list of chunks
    if isinstance(data, dict) and 'chunks' in data:
        chunks = data['chunks']
    else:
        chunks = data

    print(f"Loaded {len(chunks)} chunks from the file")
    return chunks


async def process_chunks_to_embeddings():
    """
    Process existing chunks from chunked_content.json and convert them to embeddings stored in Qdrant.
    """
    print("Starting process to convert existing chunks to embeddings and store in Qdrant...")

    # Load the chunked content
    project_root = Path(__file__).parent.parent.parent
    chunk_file_path = project_root / "backend/data/chunked/chunked_content.json"

    # If running from backend directory directly, adjust the path
    if not chunk_file_path.exists():
        chunk_file_path = Path(__file__).parent.parent / "data/chunked/chunked_content.json"

    # If still not found, try relative to current working directory
    if not chunk_file_path.exists():
        chunk_file_path = Path("data/chunked/chunked_content.json")

    # Check if the file exists
    if not chunk_file_path.exists():
        print(f"Chunked content file not found: {chunk_file_path}")
        return

    chunks = load_chunked_content(str(chunk_file_path))

    if not chunks:
        print("No chunks found to process.")
        return

    print(f"First chunk example - ID: {chunks[0].get('id', 'N/A')}")
    print(f"Content preview: {'Content exists' if chunks[0].get('content') else 'N/A'}")
    print(f"Metadata: {chunks[0].get('metadata', {})}")

    # Initialize embedding configuration
    print("\nInitializing embedding configuration...")
    try:
        config = EmbeddingConfig.load_from_environment()
        # Update the input type to produce 384-dimensional embeddings to match Qdrant collection
        config.input_type = "classification"  # This produces 384-dimensional embeddings
        print(f"Configuration loaded: provider={config.provider}, model={config.model}, input_type={config.input_type}")
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please ensure environment variables are set (COHERE_API_KEY or EMBEDDING_API_KEY)")
        print("Using default configuration with placeholder API key for demonstration...")

        # Create a default configuration with a placeholder API key
        config = EmbeddingConfig(
            provider="cohere",
            model="embed-english-v3.0",
            api_key="placeholder-key-for-testing",  # This will fail in actual API calls
            input_type="classification",  # Use classification to get 384-dimensional embeddings
            truncate="END",
            batch_size=10,
            parallel_workers=2,
            qdrant_host="localhost",
            qdrant_port=6333,
            qdrant_collection_name="approved_chunks_embeddings"
        )

    # Initialize embedding provider
    print("\nInitializing embedding provider...")
    try:
        provider = CohereEmbeddingProvider(config)
        print("Embedding provider initialized successfully")
    except Exception as e:
        print(f"Error initializing embedding provider: {e}")
        return

    # Initialize Qdrant client
    print("\nInitializing Qdrant client...")
    try:
        qdrant_client = QdrantEmbeddingClient(config)
        qdrant_client.connect()
        print("Qdrant client connected successfully")
    except Exception as e:
        print(f"Error connecting to Qdrant: {e}")
        return

    # Prepare pipeline ID
    pipeline_id = f"existing_chunks_to_embeddings_{len(chunks)}_items_{hash(str(chunks[0])) % 10000}"
    print(f"\nProcessing pipeline ID: {pipeline_id}")

    # Process chunks in batches to avoid memory issues
    batch_size = 10  # Process 10 chunks at a time
    total_chunks = len(chunks)
    successful_embeddings = 0
    failed_embeddings = 0

    print(f"\nStarting to process {total_chunks} chunks in batches of {batch_size}...")

    for i in range(0, total_chunks, batch_size):
        batch = chunks[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(total_chunks + batch_size - 1)//batch_size} with {len(batch)} chunks...")

        # Prepare data for embedding
        chunk_ids = []
        contents = []
        metadata_list = []
        pipeline_ids = []

        for chunk in batch:
            chunk_id = chunk.get('id', f"chunk_{i}")
            content = chunk.get('content', '')
            metadata = chunk.get('metadata', {})

            if content:  # Only process chunks with content
                chunk_ids.append(chunk_id)
                contents.append(content)
                metadata_list.append(metadata)
                pipeline_ids.append(pipeline_id)

        if not contents:
            print(f"  No content in batch {i//batch_size + 1}, skipping...")
            continue

        # Generate embeddings for the batch
        try:
            print(f"  Generating embeddings for {len(contents)} items...")

            # Generate embeddings for the content batch using the async provider method
            try:
                embeddings = await provider.generate_embeddings(contents)

                # Prepare embeddings data for local storage
                import json
                batch_embeddings_data = []
                for j, embedding in enumerate(embeddings):
                    embedding_data = {
                        'chunk_id': chunk_ids[j],
                        'embedding': embedding,
                        'content': contents[j][:100] + "..." if len(contents[j]) > 100 else contents[j],  # Truncate content for storage
                        'metadata': metadata_list[j],
                        'pipeline_id': pipeline_id,
                        'model': config.model,
                        'provider': config.provider
                    }
                    batch_embeddings_data.append(embedding_data)

                # Save embeddings locally as JSON
                local_dir = Path("data/embeddings")
                local_dir.mkdir(parents=True, exist_ok=True)
                local_file = local_dir / f"embeddings_batch_{i//batch_size + 1}.json"
                with open(local_file, 'w', encoding='utf-8') as f:
                    json.dump(batch_embeddings_data, f, indent=2, ensure_ascii=False)
                print(f"    Saved {len(embeddings)} embeddings locally to {local_file}")

                # Store embeddings to Qdrant
                print(f"  Storing {len(embeddings)} embeddings to Qdrant...")

                # Store embeddings in Qdrant
                success = qdrant_client.store_embeddings(
                    chunk_ids=chunk_ids,
                    embeddings=embeddings,
                    pipeline_ids=[pipeline_id] * len(embeddings),
                    contents=contents,
                    metadata_list=metadata_list
                )

                if success:
                    print(f"    Successfully stored {len(embeddings)} embeddings to Qdrant")
                    successful_embeddings += len(embeddings)
                else:
                    print(f"    Failed to store {len(embeddings)} embeddings to Qdrant")
                    failed_embeddings += len(embeddings)

            except Exception as e:
                print(f"    Error during embedding generation (likely due to missing API key): {e}")
                print(f"    Skipping batch of {len(contents)} items due to API error")
                failed_embeddings += len(contents)

        except Exception as e:
            print(f"  Error processing batch {i//batch_size + 1}: {e}")
            failed_embeddings += len(contents)

    # Summary
    print(f"\nProcessing complete!")
    print(f"Total chunks processed: {total_chunks}")
    print(f"Successful embeddings: {successful_embeddings}")
    print(f"Failed embeddings: {failed_embeddings}")
    print(f"Embeddings stored in Qdrant collection: {config.qdrant_collection_name}")

    # Verify a few embeddings were stored
    try:
        stats = qdrant_client.get_collection_stats()
        print(f"Qdrant collection stats: {stats}")
    except Exception as e:
        print(f"Error getting collection stats: {e}")

    print("\nProcess completed!")


def main():
    """Main entry point to run the pipeline."""
    asyncio.run(process_chunks_to_embeddings())


if __name__ == "__main__":
    main()