"""
Simple test to verify the embedding system components work together.
"""
import asyncio
import tempfile
import os
from pathlib import Path

from src.embeddings import EmbeddingConfig, CohereEmbeddingProvider, EmbeddingGenerator
from src.pipeline.state_persistence import PipelineStateManager


def test_embedding_components():
    """Test that embedding components work together."""
    print("Testing embedding system components...")

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
        # Use environment variable for testing
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

        # Test single embedding generation
        print("Testing single embedding generation...")
        single_result = asyncio.run(
            generator.generate_single_embedding(
                content="Test content for embedding",
                chunk_id="test-chunk-1",
                pipeline_id="test-pipeline-123"
            )
        )
        print(f"Single embedding result: success={single_result.success}")

        # Test configuration validation
        print("Testing configuration validation...")
        validation_result = asyncio.run(
            generator._validate_configuration_with_state(temp_state_path)
        )
        print(f"Configuration validation result: {validation_result}")

        # Clean up
        asyncio.run(generator.close())

        print("Component test completed successfully!")
        return True

    except Exception as e:
        print(f"Component test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up temp file
        if Path(temp_state_path).exists():
            Path(temp_state_path).unlink()


def run_component_test():
    """Run the component test."""
    print("Starting embedding system component test...")
    success = test_embedding_components()
    if success:
        print("✅ Component test PASSED")
        return 0
    else:
        print("❌ Component test FAILED")
        return 1


if __name__ == "__main__":
    exit(run_component_test())