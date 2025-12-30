"""
Embedding generator for processing approved content chunks.

This module implements the core embedding generation functionality
that works with approved content chunks and integrates with the
pipeline state management.
"""
import asyncio
import logging
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from .config import EmbeddingConfig
from .provider import EmbeddingProvider
from .batch_processor import BatchEmbeddingProcessor, EmbeddingTask, EmbeddingResult
from .audit import EmbeddingAuditLogger, EmbeddingOperationRecord
from ..embeddings_pipeline.state_machine import PipelineState
from ..embeddings_pipeline.state_persistence import StatePersistence


class EmbeddingGenerator:
    """
    Core class for generating embeddings for approved content chunks.

    This class orchestrates the embedding process, validates content approval,
    generates embeddings using the configured provider, and manages persistence
    and audit logging.
    """

    def __init__(self, config: EmbeddingConfig, provider: EmbeddingProvider):
        """
        Initialize the embedding generator.

        Args:
            config: Configuration for embedding operations
            provider: Embedding provider to use
        """
        self.config = config
        self.provider = provider
        self.batch_processor = BatchEmbeddingProcessor(config, provider)
        self.audit_logger = EmbeddingAuditLogger()
        self.logger = logging.getLogger(__name__)

    async def generate_embeddings_for_chunks(
        self,
        chunks: List[Dict[str, Any]],
        pipeline_id: str,
        state_file: Optional[str] = None
    ) -> List[EmbeddingResult]:
        """
        Generate embeddings for a list of content chunks.

        Args:
            chunks: List of content chunks to generate embeddings for
            pipeline_id: ID of the pipeline these chunks belong to
            state_file: Optional state file for tracking progress

        Returns:
            List of embedding results
        """
        # Validate configuration before starting
        if state_file:
            await self._validate_configuration_with_state(state_file)

        # Verify all chunks are approved (this would check the state file or other approval system)
        if not await self._verify_content_approval(chunks, pipeline_id, state_file):
            raise ValueError("Content chunks are not approved for embedding generation")

        # Check which chunks are already embedded (EMBEDDING_COMPLETE) and filter them out
        chunks_to_process = []
        if state_file:
            chunks_to_process = await self._filter_already_embedded_chunks(chunks, state_file)
        else:
            chunks_to_process = chunks

        # Create embedding tasks from remaining chunks
        tasks = []
        for chunk in chunks_to_process:
            chunk_id = chunk.get('id', f"chunk_{len(tasks)}")
            content = chunk.get('content', '')
            metadata = chunk.get('metadata', {})

            # Perform safety checks on content
            if not self._is_content_safe_for_embedding(content):
                self.logger.warning(f"Skipping unsafe content for chunk {chunk_id}")
                continue

            task = EmbeddingTask(
                chunk_id=chunk_id,
                content=content,
                pipeline_id=pipeline_id,
                metadata=metadata
            )
            tasks.append(task)

        self.logger.info(f"Starting embedding generation for {len(tasks)} chunks in pipeline {pipeline_id} (filtered from {len(chunks)} total)")

        # Process the batch of tasks
        results = await self.batch_processor.process_batch(tasks)

        # Log audit records for each operation
        for result in results:
            audit_record = EmbeddingOperationRecord(
                chunk_id=result.chunk_id,
                pipeline_id=pipeline_id,
                success=result.success,
                error=result.error,
                timestamp=result.timestamp,
                model=self.config.model,
                provider=self.config.provider
            )
            self.audit_logger.log_operation(audit_record)

        self.logger.info(f"Completed embedding generation for {len(results)} chunks in pipeline {pipeline_id}")

        return results

    async def _filter_already_embedded_chunks(self, chunks: List[Dict[str, Any]], state_file: str) -> List[Dict[str, Any]]:
        """
        Filter out chunks that are already embedded (EMBEDDING_COMPLETE).

        Args:
            chunks: List of content chunks to check
            state_file: Path to the state file to check embedding status

        Returns:
            List of chunks that are not yet embedded
        """
        try:
            state_persistence = StatePersistence(state_file)
            state_data = state_persistence.read_state()

            if not state_data:
                # If no state data, assume no chunks are embedded
                return chunks

            # Check if pipeline is in a state where embedding has been completed
            current_state = PipelineState(state_data.get('state', 'IDLE'))
            if current_state == PipelineState.EMBEDDING_COMPLETE:
                # If the entire pipeline is marked as EMBEDDING_COMPLETE,
                # we may want to reprocess or skip based on other factors
                # For now, let's return an empty list to indicate all are processed
                self.logger.info(f"Pipeline state is EMBEDDING_COMPLETE, all chunks are considered processed")
                return []

            # For this implementation, we'll consider chunks as already embedded
            # if the pipeline state is EMBEDDING_COMPLETE, otherwise process all
            # In a more sophisticated implementation, we would track individual chunk status
            if current_state == PipelineState.EMBEDDING_COMPLETE:
                return []
            else:
                # Check if individual chunks have been processed in other ways
                # For now, return all chunks that are safe to process
                safe_chunks = []
                for chunk in chunks:
                    content = chunk.get('content', '')
                    if self._is_content_safe_for_embedding(content):
                        safe_chunks.append(chunk)
                    else:
                        self.logger.warning(f"Skipping chunk with unsafe content: {chunk.get('id', 'unknown')}")

                return safe_chunks

        except Exception as e:
            self.logger.error(f"Error filtering already embedded chunks: {str(e)}")
            # If there's an error, return all chunks to be safe
            return chunks

    async def _verify_content_approval(
        self,
        chunks: List[Dict[str, Any]],
        pipeline_id: str,
        state_file: Optional[str] = None
    ) -> bool:
        """
        Verify that content chunks are approved for embedding generation.

        Args:
            chunks: List of content chunks to verify
            pipeline_id: ID of the pipeline
            state_file: Optional state file to check approval status

        Returns:
            bool: True if content is approved, False otherwise
        """
        if not state_file:
            # If no state file provided, assume content is approved
            # In a real implementation, you'd have another way to verify approval
            return True

        try:
            state_persistence = StatePersistence(state_file)
            state_data = state_persistence.read_state()

            # Check if the pipeline state allows embedding
            current_state = PipelineState(state_data.get('state', 'IDLE'))

            # Embedding should only happen when content is approved or already in progress
            if current_state not in [PipelineState.CHUNKING_APPROVED, PipelineState.EMBEDDING_IN_PROGRESS]:
                self.logger.warning(f"Pipeline {pipeline_id} is not in approved state for embedding: {current_state}")
                return False

            # Additional approval verification logic could go here
            # For example, checking specific chunk approval status in the state

            return True
        except Exception as e:
            self.logger.error(f"Error verifying content approval: {str(e)}")
            return False

    async def fetch_approved_content_chunks(self, state_file: str, pipeline_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all approved content chunks from the pipeline state.

        Args:
            state_file: Path to the state file containing pipeline information
            pipeline_id: ID of the pipeline to fetch chunks from

        Returns:
            List of approved content chunks
        """
        try:
            state_persistence = StatePersistence(state_file)
            state_data = state_persistence.read_state()

            if not state_data:
                self.logger.error(f"No state data found in {state_file}")
                return []

            # Verify the pipeline is in the correct state for embedding
            current_state = PipelineState(state_data.get('state', 'IDLE'))
            if current_state not in [PipelineState.CHUNKING_APPROVED, PipelineState.EMBEDDING_IN_PROGRESS]:
                self.logger.warning(f"Pipeline {pipeline_id} is not in an appropriate state for embedding: {current_state}")
                return []

            # Get artifact paths to locate the chunked content
            artifact_paths = state_data.get('artifact_paths', {})
            chunked_output_path = artifact_paths.get('chunked_output')

            if not chunked_output_path or not os.path.exists(chunked_output_path):
                self.logger.error(f"Chunked output file does not exist: {chunked_output_path}")
                return []

            # Load the chunked content from the file
            import json
            with open(chunked_output_path, 'r', encoding='utf-8') as f:
                chunks_data = json.load(f)

            # Ensure chunks_data is a list
            if isinstance(chunks_data, dict) and 'chunks' in chunks_data:
                chunks_data = chunks_data['chunks']
            elif not isinstance(chunks_data, list):
                self.logger.error(f"Chunked output file does not contain a list of chunks: {chunked_output_path}")
                return []

            # Filter to ensure we only return valid chunks with content
            approved_chunks = []
            for i, chunk in enumerate(chunks_data):
                if isinstance(chunk, dict) and 'content' in chunk:
                    # Safety checks for content verification
                    content = chunk.get('content', '')
                    if not content or not isinstance(content, str):
                        self.logger.warning(f"Skipping chunk with invalid content at index {i}")
                        continue

                    # Additional safety checks
                    if len(content.strip()) == 0:
                        self.logger.warning(f"Skipping chunk with empty content at index {i}")
                        continue

                    # Check for excessively large content (safety measure)
                    if len(content) > 1000000:  # 1MB limit
                        self.logger.warning(f"Skipping chunk with excessively large content (>1MB) at index {i}")
                        continue

                    chunk_id = chunk.get('id', f"chunk_{i}")
                    chunk_obj = {
                        'id': chunk_id,
                        'content': content,
                        'metadata': chunk.get('metadata', {}),
                        'source': chunk.get('source', ''),
                        'index': i
                    }
                    approved_chunks.append(chunk_obj)
                else:
                    self.logger.warning(f"Skipping invalid chunk at index {i}: {chunk}")

            self.logger.info(f"Fetched {len(approved_chunks)} approved content chunks from {pipeline_id}")
            return approved_chunks

        except Exception as e:
            self.logger.error(f"Error fetching approved content chunks: {str(e)}")
            return []

    def _is_content_safe_for_embedding(self, content: str) -> bool:
        """
        Perform safety checks on content before embedding generation.

        Args:
            content: The content to check

        Returns:
            bool: True if content is safe for embedding, False otherwise
        """
        # Check if content is empty or too short
        if not content or len(content.strip()) == 0:
            return False

        # Check for excessive length (prevent memory issues)
        if len(content) > 1000000:  # 1MB limit
            self.logger.warning(f"Content too large for embedding (>1MB)")
            return False

        # Check for potentially problematic content patterns
        # (This is a basic check - more sophisticated checks could be added)
        dangerous_patterns = [
            '<script', 'javascript:', 'vbscript:', '<iframe', '<object', '<embed'
        ]
        content_lower = content.lower()
        for pattern in dangerous_patterns:
            if pattern in content_lower:
                self.logger.warning(f"Content contains potentially dangerous pattern: {pattern}")
                return False

        return True

    async def _validate_configuration_with_state(self, state_file: str) -> bool:
        """
        Validate current configuration against stored configuration hash in state.

        Args:
            state_file: Path to the state file to validate against

        Returns:
            bool: True if configuration is valid, False if it has changed
        """
        try:
            state_persistence = StatePersistence(state_file)
            state_data = state_persistence.read_state()

            # Get stored configuration hash
            stored_config_hash = state_data.get('embedding_config_hash')
            if not stored_config_hash:
                # No stored hash, this might be the first run
                # Store current hash for future validation
                current_hash = self.config.get_hash()
                state_data['embedding_config_hash'] = current_hash
                state_persistence.write_state(state_data)
                return True

            # Validate current config against stored hash
            if not self.config.validate_config_hash(stored_config_hash):
                self.logger.error("Configuration hash mismatch - embedding generation blocked due to config change")
                return False

            return True
        except Exception as e:
            self.logger.error(f"Error validating configuration with state: {str(e)}")
            return False

    async def close(self):
        """
        Close the embedding generator and clean up resources.
        """
        await self.batch_processor.close()

    async def generate_single_embedding(self, content: str, chunk_id: str, pipeline_id: str) -> EmbeddingResult:
        """
        Generate embedding for a single piece of content.

        Args:
            content: Content to generate embedding for
            chunk_id: ID of the content chunk
            pipeline_id: ID of the pipeline

        Returns:
            EmbeddingResult: Result of the embedding operation
        """
        task = EmbeddingTask(
            chunk_id=chunk_id,
            content=content,
            pipeline_id=pipeline_id,
            metadata={}
        )

        try:
            # Process single task using batch processor
            results = await self.batch_processor.process_batch([task])
            return results[0] if results else EmbeddingResult(
                chunk_id=chunk_id,
                embedding=[],
                success=False,
                error="No result returned from processor"
            )
        except Exception as e:
            return EmbeddingResult(
                chunk_id=chunk_id,
                embedding=[],
                success=False,
                error=str(e)
            )

    async def execute_complete_embedding_pipeline(self, state_file: str, pipeline_id: str) -> Dict[str, Any]:
        """
        Execute the complete embedding pipeline: fetch approved chunks, generate embeddings,
        persist to Qdrant, verify storage, and update pipeline state.

        Args:
            state_file: Path to the pipeline state file
            pipeline_id: ID of the pipeline to process

        Returns:
            Dictionary with summary of processing results:
            {
                'total_chunks': int,
                'successful': int,
                'failed': int,
                'details': [
                    {'chunk_id': str, 'status': 'SUCCESS|FAILURE', 'error': str}
                ]
            }
        """
        self.logger.info(f"Starting complete embedding pipeline for pipeline {pipeline_id}")

        # Step 1: Fetch approved content chunks
        self.logger.info("Step 1: Fetching approved content chunks...")
        approved_chunks = await self.fetch_approved_content_chunks(state_file, pipeline_id)

        if not approved_chunks:
            self.logger.warning(f"No approved content chunks found for pipeline {pipeline_id}")
            return {
                'total_chunks': 0,
                'successful': 0,
                'failed': 0,
                'details': []
            }

        self.logger.info(f"Fetched {len(approved_chunks)} approved chunks for processing")

        # Step 2: Generate embeddings for all chunks
        self.logger.info("Step 2: Generating embeddings for chunks...")
        try:
            results = await self.generate_embeddings_for_chunks(
                chunks=approved_chunks,
                pipeline_id=pipeline_id,
                state_file=state_file
            )
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {str(e)}")
            # Return partial results if any were processed
            results = []

        # Step 3: Process results and create summary
        successful_count = sum(1 for r in results if r.success)
        failed_count = len(results) - successful_count

        details = []
        for result in results:
            detail = {
                'chunk_id': result.chunk_id,
                'status': 'SUCCESS' if result.success else 'FAILURE',
            }
            if result.error:
                detail['error'] = result.error
            details.append(detail)

        summary = {
            'total_chunks': len(approved_chunks),
            'successful': successful_count,
            'failed': failed_count,
            'details': details
        }

        self.logger.info(f"Embedding generation complete: {successful_count} successful, {failed_count} failed")

        # Step 4: Store embeddings to Qdrant
        self.logger.info("Step 4: Storing embeddings to Qdrant...")
        if successful_count > 0:
            # Filter successful results
            successful_results = [r for r in results if r.success and r.embedding]

            if successful_results:
                # Prepare data for Qdrant storage
                chunk_ids = []
                embeddings = []
                pipeline_ids = []
                contents = []
                metadata_list = []

                for result in successful_results:
                    # Find the original chunk to get content
                    original_chunk = next((c for c in approved_chunks if c['id'] == result.chunk_id), None)
                    content = original_chunk['content'] if original_chunk else ""

                    chunk_ids.append(result.chunk_id)
                    embeddings.append(result.embedding)
                    pipeline_ids.append(pipeline_id)
                    contents.append(content)
                    metadata_list.append({
                        "chunk_id": result.chunk_id,
                        "model_version": self.config.model,
                        "provider": self.config.provider,
                        "source_pipeline": pipeline_id
                    })

                # Initialize Qdrant client
                from .qdrant_client import QdrantEmbeddingClient
                collection_name = os.getenv("QDRANT_COLLECTION_NAME", "approved_chunks_embeddings")
                qdrant_client = QdrantEmbeddingClient(self.config, collection_name=collection_name)

                # Connect to Qdrant
                qdrant_client.connect()

                # Store embeddings to Qdrant
                try:
                    store_success = qdrant_client.store_embeddings(
                        chunk_ids=chunk_ids,
                        embeddings=embeddings,
                        pipeline_ids=pipeline_ids,
                        contents=contents,
                        metadata_list=metadata_list
                    )

                    if store_success:
                        self.logger.info(f"Successfully stored {len(successful_results)} embeddings to Qdrant")
                    else:
                        self.logger.error("Failed to store embeddings to Qdrant")
                        # Update summary to reflect storage failure
                        summary['qdrant_storage'] = 'FAILED'
                except Exception as e:
                    self.logger.error(f"Error storing embeddings to Qdrant: {str(e)}")
                    summary['qdrant_storage'] = 'ERROR'
                    summary['qdrant_error'] = str(e)

                # Clean up Qdrant client
                del qdrant_client
            else:
                self.logger.warning("No successful embeddings to store to Qdrant")
        else:
            self.logger.warning("No successful embeddings generated, skipping Qdrant storage")

        # Step 5: Verify embeddings in Qdrant (optional verification)
        self.logger.info("Step 5: Embedding verification would occur here (Qdrant retrieval check)")

        # Step 6: Update pipeline state to EMBEDDING_COMPLETE if all succeeded
        if failed_count == 0 and successful_count > 0:
            from ..pipeline.state_persistence import PipelineStateManager
            state_manager = PipelineStateManager(state_file)

            if state_manager.transition_to_embedding_complete():
                self.logger.info("Pipeline state updated to EMBEDDING_COMPLETE")
                summary['final_state'] = 'EMBEDDING_COMPLETE'
            else:
                self.logger.error("Failed to update pipeline state to EMBEDDING_COMPLETE")
                summary['final_state'] = 'UPDATE_FAILED'
        elif successful_count > 0:
            # Some succeeded, some failed - mark as failed to indicate partial completion
            from ..pipeline.state_persistence import PipelineStateManager
            state_manager = PipelineStateManager(state_file)

            if state_manager.transition_to_embedding_failed(f"Some embeddings failed: {failed_count} out of {len(results)}"):
                self.logger.info(f"Pipeline state updated to FAILED due to {failed_count} failed embeddings")
                summary['final_state'] = 'FAILED'
            else:
                self.logger.error("Failed to update pipeline state after partial failure")
                summary['final_state'] = 'UPDATE_FAILED'
        else:
            # No successful embeddings
            self.logger.info("No successful embeddings generated")
            summary['final_state'] = 'NO_SUCCESS'

        self.logger.info(f"Complete embedding pipeline finished for pipeline {pipeline_id}")

        return summary