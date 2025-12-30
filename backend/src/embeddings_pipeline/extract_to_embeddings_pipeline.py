"""
Skill for processing content from extraction to embeddings storage in Qdrant.
"""
import json
import os
import asyncio
from pathlib import Path
import sys

# Add the backend directory to the path so we can import modules
sys.path.insert(0, '../..')

from src.embeddings.config import EmbeddingConfig
from src.embeddings.provider import CohereEmbeddingProvider
from src.embeddings.qdrant_client import QdrantEmbeddingClient


def load_chunked_content(file_path: str):
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


async def process_and_store_embeddings(chunk_file_path: str = "../../data/chunked/chunked_content.json"):
    """
    Process content from extraction to embeddings storage in Qdrant.
    """
    print("Starting complete pipeline: Content Extraction -> Embeddings -> Qdrant Storage...")

    # Load the chunked content
    if not os.path.exists(chunk_file_path):
        print(f"Chunked content file not found: {chunk_file_path}")
        return

    chunks = load_chunked_content(chunk_file_path)

    if not chunks:
        print("No chunks found to process.")
        return

    print(f"First chunk example - ID: {chunks[0].get('id', 'N/A')}")
    print(f"Content preview: {'Content exists' if chunks[0].get('content') else 'N/A'}")
    print(f"Metadata: {chunks[0].get('metadata', {})}")

    # Load environment variables
    from dotenv import load_dotenv
    dotenv_path = Path('.env')
    if dotenv_path.exists():
        load_dotenv(dotenv_path)

    # Initialize embedding configuration
    print("\nInitializing embedding configuration...")
    try:
        config = EmbeddingConfig.load_from_environment()
        # Use classification input type to get consistent dimensions
        config.input_type = "classification"
        print(f"Configuration loaded: provider={config.provider}, model={config.model}, input_type={config.input_type}")
    except ValueError as e:
        print(f"Configuration error: {e}")
        return

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
    pipeline_id = f"extract_to_embeddings_{len(chunks)}_items_{hash(str(chunks[0])) % 10000}"
    print(f"\nProcessing pipeline ID: {pipeline_id}")

    # Process chunks in batches to avoid memory issues
    batch_size = 10  # Process 10 chunks at a time
    total_chunks = len(chunks)
    all_embeddings_data = []

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
                    all_embeddings_data.append(embedding_data)

                # Save embeddings locally as JSON
                local_dir = Path("../../data/embeddings")
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
                else:
                    print(f"    Failed to store {len(embeddings)} embeddings to Qdrant")

            except Exception as e:
                print(f"    Error during embedding generation: {e}")
                continue

        except Exception as e:
            print(f"  Error processing batch {i//batch_size + 1}: {e}")
            continue

    print(f"\nPipeline completed!")
    print(f"Total chunks processed: {total_chunks}")
    print(f"Embeddings stored in Qdrant collection: {config.qdrant_collection_name}")

    # Verify storage
    stats = qdrant_client.get_collection_stats()
    print(f"Qdrant collection stats: {stats}")

    print(f"\nEmbeddings saved locally to: data/embeddings/")
    print(f"Embeddings stored in Qdrant collection: {config.qdrant_collection_name}")
    print(f"Total vectors in Qdrant: {stats['vector_count']}")


def main(chunk_file_path: str = None):
    """Main entry point to run the complete pipeline."""
    if chunk_file_path is None:
        chunk_file_path = "../../data/chunked/chunked_content.json"

    asyncio.run(process_and_store_embeddings(chunk_file_path))


if __name__ == "__main__":
    main()