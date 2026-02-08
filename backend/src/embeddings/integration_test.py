"""
Integration test to demonstrate the embedding system functionality.
"""
import asyncio
import tempfile
import os
from pathlib import Path

from src.embeddings import EmbeddingConfig, CohereEmbeddingProvider, EmbeddingGenerator
from src.pipeline.state_persistence import PipelineStateManager


async def test_embedding_integration():
    """Test the complete embedding workflow integration."""
    print("Testing embedding system integration...")

    # Set up a temporary state file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_state_file:
        temp_state_path = temp_state_file.name

    try:
        # Initialize pipeline state manager
        state_manager = PipelineStateManager(temp_state_path)

        # Initialize the pipeline to a valid state for embedding
        # For this test, we'll manually set it to CHUNKING_APPROVED state
        initial_state = {
            "state": "CHUNKING_APPROVED",
            "timestamp": "2025-12-27T10:00:00Z",
            "approvals": {
                "extraction": {"status": "APPROVED"},
                "chunking": {"status": "APPROVED"}
            }
        }

        # Write the initial state
        from src.pipeline.state_persistence import StatePersistence
        persistence = StatePersistence(temp_state_path)
        persistence.write_state(initial_state)

        print(f"Pipeline initialized in state: {state_manager.get_pipeline_state().value}")

        # Create embedding configuration
        # Use environment variable or mock API key for testing
        os.environ["COHERE_API_KEY"] = "test-key-for-integration-testing"
        config = EmbeddingConfig(batch_size=2, parallel_workers=2)

        print(f"Embedding configuration created with model: {config.model}")
        print(f"Configuration hash: {config.get_hash()[:16]}...")

        # Create provider (mock for testing without actual API call)
        from unittest.mock import Mock, AsyncMock
        provider = Mock()
        provider.generate_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
        provider.validate_connection = AsyncMock(return_value=True)

        # Create embedding generator
        generator = EmbeddingGenerator(config, provider)

        # Prepare test content chunks
        test_chunks = [
            {
                "id": "chunk-1",
                "content": "This is the first test document for embedding generation.",
                "metadata": {"source": "test", "type": "paragraph"}
            },
            {
                "id": "chunk-2",
                "content": "This is the second test document for embedding generation.",
                "metadata": {"source": "test", "type": "paragraph"}
            }
        ]

        print(f"Processing {len(test_chunks)} content chunks...")

        # Generate embeddings for the test chunks
        results = await generator.generate_embeddings_for_chunks(
            chunks=test_chunks,
            pipeline_id="test-pipeline-123",
            state_file=temp_state_path
        )

        print(f"Generated embeddings for {len(results)} chunks:")
        for i, result in enumerate(results):
            status = "SUCCESS" if result.success else "FAILED"
            print(f"  Chunk {i+1} ({result.chunk_id}): {status}")
            if result.error:
                print(f"    Error: {result.error}")

        # Check final state
        final_state = state_manager.get_pipeline_state()
        print(f"Final pipeline state: {final_state.value if final_state else 'NO_STATE'}")

        # Clean up
        await generator.close()

        print("Integration test completed successfully!")
        return True

    except Exception as e:
        print(f"Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up temp file
        if Path(temp_state_path).exists():
            Path(temp_state_path).unlink()


def run_integration_test():
    """Run the integration test."""
    print("Starting embedding system integration test...")
    success = asyncio.run(test_embedding_integration())
    if success:
        print("✅ Integration test PASSED")
        return 0
    else:
        print("❌ Integration test FAILED")
        return 1


if __name__ == "__main__":
    exit(run_integration_test())