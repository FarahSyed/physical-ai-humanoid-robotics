"""
Integration tests for preview functionality.
This test verifies that the preview service integrates correctly with the state management
and approval system, allowing users to preview content at different stages of the pipeline.
"""
import os
import tempfile
import unittest
from unittest.mock import Mock

from src.pipeline.state_machine import PipelineState
from src.pipeline.state_persistence import StatePersistence, PipelineStateManager
from src.pipeline.preview_service import PreviewService
from src.pipeline.approval_engine import ApprovalEngine


class TestPreviewIntegration(unittest.TestCase):
    """
    Integration tests for preview functionality.
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.state_file = self.temp_file.name

        # Initialize components
        self.state_persistence = StatePersistence(self.state_file)
        self.state_manager = PipelineStateManager(self.state_file)
        self.preview_service = PreviewService()
        self.approval_engine = ApprovalEngine(self.state_persistence)

    def tearDown(self):
        """
        Clean up after each test method.
        """
        # Remove the temporary file
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

    def test_preview_integration_with_extraction_stage(self):
        """
        Integration test: Preview extracted content after extraction is complete.
        """
        # Initialize the pipeline
        self.state_manager.initialize_pipeline({"input_path": "dummy_input.txt"})

        # Transition to extraction in progress
        self.state_manager.transition_to_extraction_in_progress()

        # Create extracted content file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as extract_file:
            extract_file.write("This is extracted content for preview testing.")
            extract_file_path = extract_file.name

        try:
            # Transition to extraction complete
            success = self.state_manager.transition_to_extraction_complete(extract_file_path)
            self.assertTrue(success)

            # Verify state is EXTRACTION_COMPLETE
            current_state = self.state_manager.get_pipeline_state()
            self.assertEqual(current_state, PipelineState.EXTRACTION_COMPLETE)

            # Preview the extracted content
            result = self.preview_service.preview_extracted_content(
                content_path=extract_file_path,
                offset=0,
                limit=20
            )

            # Verify preview result
            self.assertIsNotNone(result)
            self.assertEqual(result["preview_type"], "extracted_content")
            self.assertEqual(result["preview_content"], "This is extracted co")  # First 19 chars
            self.assertEqual(result["total_length"], len("This is extracted content for preview testing."))

            # Also test with the state manager to get the path from state
            state_data = self.state_persistence.read_state()
            artifact_paths = state_data.get("artifact_paths", {})
            extracted_content_path = artifact_paths.get("extracted_content")

            if extracted_content_path:
                result2 = self.preview_service.preview_extracted_content(
                    content_path=extracted_content_path,
                    offset=5,
                    limit=10
                )
                self.assertIsNotNone(result2)
                # The content "This is extracted content for preview testing." from offset 5, limit 10 is "is extract"
                # Index 5="i", 6="s", 7=" ", 8="e", 9="x", 10="t", 11="r", 12="a", 13="c", 14="t" -> "is extract"
                self.assertEqual(result2["preview_content"], "is extract")

        finally:
            # Clean up the temporary extract file
            if os.path.exists(extract_file_path):
                os.remove(extract_file_path)

    def test_preview_integration_with_chunking_stage(self):
        """
        Integration test: Preview chunked content after chunking is complete.
        """
        # Initialize the pipeline
        self.state_manager.initialize_pipeline({"input_path": "dummy_input.txt"})

        # Go through the extraction stage first
        self.state_manager.transition_to_extraction_in_progress()

        # Create extracted content file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as extract_file:
            extract_file.write("This is extracted content that will be chunked.")
            extract_file_path = extract_file.name

        try:
            # Complete extraction
            self.state_manager.transition_to_extraction_complete(extract_file_path)

            # Process extraction approval
            success = self.approval_engine.process_approval(
                stage="extraction",
                approver_id="test_approver",
                decision="APPROVE",
                context="Content looks good"
            )
            self.assertTrue(success)

            # Transition to chunking in progress
            self.state_manager.transition_to_chunking_in_progress()

            # Create chunked content file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as chunk_file:
                chunk_file.write("Chunk 1 content. Chunk 2 content. Chunk 3 content.")
                chunk_file_path = chunk_file.name

            try:
                # Complete chunking
                success = self.state_manager.transition_to_chunking_complete(chunk_file_path)
                self.assertTrue(success)

                # Verify state is CHUNKING_COMPLETE
                current_state = self.state_manager.get_pipeline_state()
                self.assertEqual(current_state, PipelineState.CHUNKING_COMPLETE)

                # Preview the chunked content
                result = self.preview_service.preview_chunked_output(
                    chunks_path=chunk_file_path,
                    offset=0,
                    limit=15
                )

                # Verify preview result
                self.assertIsNotNone(result)
                self.assertEqual(result["preview_type"], "chunked_output")
                self.assertIn("Chunk 1 content", result["preview_content"])
                self.assertLessEqual(len(result["preview_content"]), 15)

                # Also test with the state manager to get the path from state
                state_data = self.state_persistence.read_state()
                artifact_paths = state_data.get("artifact_paths", {})
                chunked_output_path = artifact_paths.get("chunked_output")

                if chunked_output_path:
                    result2 = self.preview_service.preview_chunked_output(
                        chunks_path=chunked_output_path,
                        offset=7,
                        limit=10
                    )
                    self.assertIsNotNone(result2)
                    self.assertIn("content", result2["preview_content"])

            finally:
                # Clean up the temporary chunk file
                if os.path.exists(chunk_file_path):
                    os.remove(chunk_file_path)

        finally:
            # Clean up the temporary extract file
            if os.path.exists(extract_file_path):
                os.remove(extract_file_path)

    def test_preview_with_approval_workflow(self):
        """
        Integration test: Preview content during approval workflow.
        """
        # Initialize the pipeline
        self.state_manager.initialize_pipeline({"input_path": "dummy_input.txt"})

        # Go through extraction
        self.state_manager.transition_to_extraction_in_progress()

        # Create extracted content file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as extract_file:
            extract_file.write("This is extracted content for approval preview.")
            extract_file_path = extract_file.name

        try:
            # Complete extraction
            self.state_manager.transition_to_extraction_complete(extract_file_path)

            # Request approval for extraction (this should set approval status to PENDING)
            success = self.approval_engine.request_approval("extraction", "Preview of extracted content")
            self.assertTrue(success)

            # Verify approval status is PENDING
            status = self.approval_engine.check_approval_status("extraction")
            self.assertEqual(status, "PENDING")

            # Preview the content that is pending approval
            result = self.preview_service.preview_extracted_content(
                content_path=extract_file_path,
                offset=0,
                limit=25
            )

            # Verify preview result
            self.assertIsNotNone(result)
            self.assertIn("This is extracted content", result["preview_content"])
            self.assertLessEqual(len(result["preview_content"]), 25)

            # Process approval
            approval_success = self.approval_engine.process_approval(
                stage="extraction",
                approver_id="approver",
                decision="APPROVE",
                context="Content approved after preview"
            )
            self.assertTrue(approval_success)

            # Verify state transition to EXTRACTION_APPROVED
            current_state = self.state_manager.get_pipeline_state()
            self.assertEqual(current_state, PipelineState.EXTRACTION_APPROVED)

        finally:
            # Clean up the temporary extract file
            if os.path.exists(extract_file_path):
                os.remove(extract_file_path)

    def test_preview_with_state_persistence(self):
        """
        Integration test: Preview functionality with state persistence.
        """
        # Initialize the pipeline
        self.state_manager.initialize_pipeline({"input_path": "test_input.txt"})

        # Create content files and update state
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("Test content for preview with state persistence.")
            content_file_path = content_file.name

        try:
            # Update state with artifact paths
            state_data = {
                "state": PipelineState.EXTRACTION_COMPLETE.value,
                "timestamp": "2025-12-24T10:00:00Z",
                "artifact_paths": {
                    "extracted_content": content_file_path
                }
            }
            self.state_persistence.write_state(state_data)

            # Verify state was written
            read_state = self.state_persistence.read_state()
            self.assertEqual(read_state["state"], PipelineState.EXTRACTION_COMPLETE.value)
            self.assertEqual(read_state["artifact_paths"]["extracted_content"], content_file_path)

            # Preview the content using the path from state
            result = self.preview_service.preview_extracted_content(
                content_path=content_file_path,
                offset=5,
                limit=15
            )

            # Verify preview result
            self.assertIsNotNone(result)
            self.assertEqual(result["preview_content"], "content for pre")

            # Test state corruption detection still works with preview
            # Note: The state file exists and is valid JSON, so it shouldn't be corrupted
            is_corrupted = self.state_persistence.check_state_corruption()
            # The state is valid since we wrote it properly, so check_state_corruption should return True (valid)
            self.assertTrue(is_corrupted)

        finally:
            # Clean up the temporary content file
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_preview_safety_integration(self):
        """
        Integration test: Preview safety features with state and approval system.
        """
        # Create content with potentially unsafe elements
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write('<script>alert("test");</script>This is safe content.')
            content_file_path = content_file.name

        try:
            # Initialize the pipeline
            self.state_manager.initialize_pipeline({"input_path": "unsafe_input.txt"})

            # Go through proper state transitions
            success = self.state_manager.transition_to_extraction_in_progress()
            self.assertTrue(success)

            # Transition to extraction complete with potentially unsafe content
            success = self.state_manager.transition_to_extraction_complete(content_file_path)
            self.assertTrue(success)

            # Preview the content
            result = self.preview_service.preview_extracted_content(content_file_path)
            self.assertIsNotNone(result)

            # The preview should still contain the content but may be sanitized depending on implementation
            self.assertIn("This is safe content", result["preview_content"])

            # Test safety validation
            is_safe = self.preview_service.validate_preview_safety(result["preview_content"])
            # This should return False due to the script tag
            self.assertFalse(is_safe)

            # Test sanitization
            sanitized = self.preview_service.sanitize_preview_content(result["preview_content"])
            self.assertIsNotNone(sanitized)
            # Sanitized content should not contain the script tag
            self.assertNotIn("<script>", sanitized)

        finally:
            # Clean up the temporary content file
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_preview_large_content_integration(self):
        """
        Integration test: Preview large content with pagination and limits.
        """
        # Create large content file
        large_content = "Line " + "\nLine ".join(str(i) for i in range(2, 102))  # 100 lines
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write(large_content)
            content_file_path = content_file.name

        try:
            # Initialize the pipeline
            self.state_manager.initialize_pipeline({"input_path": "large_input.txt"})

            # Go through proper state transitions
            success = self.state_manager.transition_to_extraction_in_progress()
            self.assertTrue(success)

            # Transition to extraction complete
            success = self.state_manager.transition_to_extraction_complete(content_file_path)
            self.assertTrue(success)

            # Test preview with pagination
            result = self.preview_service.preview_large_content_with_pagination(
                content_path=content_file_path,
                page=1,
                page_size=10
            )

            # Verify pagination result
            self.assertIsNotNone(result)
            self.assertEqual(result["preview_type"], "paginated_content")
            self.assertEqual(result["page"], 1)
            self.assertEqual(result["page_size"], 10)
            self.assertGreater(result["total_pages"], 1)  # Should have multiple pages

            # Verify the content preview is properly paginated
            preview_lines = result["preview_content"].split('\n')
            self.assertLessEqual(len(preview_lines), 10)  # Should have at most 10 lines

            # Test with different page
            result_page2 = self.preview_service.preview_large_content_with_pagination(
                content_path=content_file_path,
                page=2,
                page_size=10
            )

            # Verify second page is different from first
            self.assertIsNotNone(result_page2)
            self.assertNotEqual(result["preview_content"], result_page2["preview_content"])

        finally:
            # Clean up the temporary content file
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_preview_sample_generation_integration(self):
        """
        Integration test: Content sample generation with state management.
        """
        # Create content file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("This is sample content for testing preview sample generation functionality.")
            content_file_path = content_file.name

        try:
            # Initialize the pipeline
            self.state_manager.initialize_pipeline({"input_path": "sample_input.txt"})

            # Go through proper state transitions
            success = self.state_manager.transition_to_extraction_in_progress()
            self.assertTrue(success)

            # Transition to extraction complete
            success = self.state_manager.transition_to_extraction_complete(content_file_path)
            self.assertTrue(success)

            # Generate content sample
            sample = self.preview_service.generate_content_sample(content_file_path, sample_size=25)
            self.assertIsNotNone(sample)
            self.assertLessEqual(len(sample), 25)
            self.assertIn("This is sample content", sample)

            # Test with different sample size
            sample2 = self.preview_service.generate_content_sample(content_file_path, sample_size=10)
            self.assertIsNotNone(sample2)
            self.assertLessEqual(len(sample2), 10)

            # Verify state remains unchanged after preview operations
            current_state = self.state_manager.get_pipeline_state()
            self.assertEqual(current_state, PipelineState.EXTRACTION_COMPLETE)

        finally:
            # Clean up the temporary content file
            if os.path.exists(content_file_path):
                os.remove(content_file_path)


if __name__ == '__main__':
    unittest.main()