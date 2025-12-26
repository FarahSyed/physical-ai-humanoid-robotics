"""
End-to-end integration tests for the pipeline verification system.

This module tests the complete pipeline workflow from start to finish,
validating that all components work together as expected.
"""
import os
import tempfile
import unittest
from pathlib import Path

from src.pipeline.state_machine import PipelineState
from src.pipeline.state_persistence import StatePersistence, PipelineStateManager
from src.pipeline.approval_engine import ApprovalEngine, ApprovalDecision
from src.pipeline.preview_service import PreviewService
from src.pipeline.resume_logic import ResumeLogic
from src.pipeline.verification_service import VerificationService
from src.cli.pipeline_cli import main as cli_main


class TestEndToEndPipeline(unittest.TestCase):
    """
    End-to-end tests for the complete pipeline workflow.
    """
    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()

        # Create temporary content files for testing
        self.temp_content_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        self.temp_content_file.write(b"This is test content for extraction.")
        self.temp_content_file.close()

        self.temp_chunked_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_chunked_file.write(b'["chunk1", "chunk2", "chunk3"]')
        self.temp_chunked_file.close()

    def tearDown(self):
        """
        Clean up after each test method.
        """
        # Remove the temporary files
        for temp_file in [self.temp_file.name, self.temp_content_file.name, self.temp_chunked_file.name]:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_complete_pipeline_workflow(self):
        """
        Test the complete pipeline workflow from start to approval gates.
        """
        # Initialize components
        state_persistence = StatePersistence(self.temp_file.name)
        approval_engine = ApprovalEngine(state_persistence)
        preview_service = PreviewService()
        resume_logic = ResumeLogic(state_persistence)
        verification_service = VerificationService()

        # Initialize the pipeline
        state_manager = PipelineStateManager(self.temp_file.name)
        state_manager.initialize_pipeline({"input_path": self.temp_content_file.name})

        # Verify initial state
        current_state = state_manager.get_pipeline_state()
        self.assertEqual(current_state, PipelineState.IDLE)

        # Transition to extraction in progress
        success = state_manager.transition_to_extraction_in_progress({"input_path": self.temp_content_file.name})
        self.assertTrue(success)

        current_state = state_manager.get_pipeline_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_IN_PROGRESS)

        # Simulate extraction completion
        success = state_manager.transition_to_extraction_complete(self.temp_content_file.name)
        self.assertTrue(success)

        current_state = state_manager.get_pipeline_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_COMPLETE)

        # At this point, the pipeline should pause for approval
        # Check that approval status is pending
        approval_status = approval_engine.check_approval_status("extraction")
        self.assertEqual(approval_status, "PENDING")

        # Process approval for extraction
        success = approval_engine.process_approval(
            stage="extraction",
            approver_id="test_approver",
            decision=ApprovalDecision.APPROVE,
            context="Approved for chunking"
        )
        self.assertTrue(success)

        # Verify state transition after approval
        current_state = state_manager.get_pipeline_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_APPROVED)

        # Transition to chunking in progress
        success = state_manager.transition_to_chunking_in_progress()
        self.assertTrue(success)

        current_state = state_manager.get_pipeline_state()
        self.assertEqual(current_state, PipelineState.CHUNKING_IN_PROGRESS)

        # Simulate chunking completion
        success = state_manager.transition_to_chunking_complete(self.temp_chunked_file.name)
        self.assertTrue(success)

        current_state = state_manager.get_pipeline_state()
        self.assertEqual(current_state, PipelineState.CHUNKING_COMPLETE)

        # Check that approval status is pending for chunking
        approval_status = approval_engine.check_approval_status("chunking")
        self.assertEqual(approval_status, "PENDING")

        # Process approval for chunking
        success = approval_engine.process_approval(
            stage="chunking",
            approver_id="test_approver",
            decision=ApprovalDecision.APPROVE,
            context="Approved for embedding"
        )
        self.assertTrue(success)

        # Verify state transition after chunking approval
        current_state = state_manager.get_pipeline_state()
        self.assertEqual(current_state, PipelineState.CHUNKING_APPROVED)

        # At this point, the pipeline would proceed to embedding (not implemented in this test)
        print(f"Pipeline successfully completed approval workflow. Final state: {current_state.value}")

    def test_preview_functionality(self):
        """
        Test the preview functionality for extracted content and chunks.
        """
        preview_service = PreviewService()

        # Test preview of extracted content
        preview_result = preview_service.preview_extracted_content(
            content_path=self.temp_content_file.name,
            offset=0,
            limit=20
        )

        self.assertIsNotNone(preview_result)
        self.assertIn("preview_content", preview_result)
        self.assertIn("total_length", preview_result)
        self.assertEqual(preview_result["preview_type"], "extracted_content")
        self.assertEqual(preview_result["preview_content"], "This is test content")

        # Test preview of chunked content
        preview_result = preview_service.preview_chunked_output(
            chunks_path=self.temp_chunked_file.name,
            chunk_index=0,
            offset=0,
            limit=10
        )

        self.assertIsNotNone(preview_result)
        self.assertIn("preview_content", preview_result)
        self.assertEqual(preview_result["preview_type"], "chunked_output")

    def test_resume_functionality(self):
        """
        Test the resume functionality after state changes.
        """
        state_persistence = StatePersistence(self.temp_file.name)
        resume_logic = ResumeLogic(state_persistence)

        # Initialize state
        state_persistence.update_state(PipelineState.EXTRACTION_APPROVED)

        # Test resume logic
        resume_state = resume_logic.get_resume_state()
        self.assertIsNotNone(resume_state)
        self.assertEqual(resume_state, PipelineState.EXTRACTION_APPROVED)

        # Validate artifacts before resume
        artifacts_valid = resume_logic.validate_artifacts_before_resume()
        # This might be False since we don't have real artifacts in this test
        # but the method should execute without error

        # Get resume recommendation
        recommendation = resume_logic.get_resume_recommendation()
        self.assertIn("current_state", recommendation)
        self.assertIn("recommended_resume_state", recommendation)
        self.assertIn("action", recommendation)

    def test_dry_run_functionality(self):
        """
        Test the dry-run functionality.
        """
        verification_service = VerificationService()
        verification_service.enable_dry_run_mode()

        self.assertTrue(verification_service.is_dry_run_mode())

        # Perform a dry-run operation
        dry_run_result = verification_service.perform_dry_run(
            operation="test_operation",
            params={"param1": "value1"}
        )

        self.assertIn("dry_run", dry_run_result)
        self.assertTrue(dry_run_result["dry_run"])
        self.assertIn("would_perform", dry_run_result)

        # Disable dry-run mode
        verification_service.disable_dry_run_mode()
        self.assertFalse(verification_service.is_dry_run_mode())

    def test_state_transitions_comprehensive(self):
        """
        Test comprehensive state transitions throughout the pipeline.
        """
        state_manager = PipelineStateManager(self.temp_file.name)

        # Start with IDLE
        state_manager.initialize_pipeline()
        self.assertEqual(state_manager.get_pipeline_state(), PipelineState.IDLE)

        # Move through extraction phase
        success = state_manager.transition_to_extraction_in_progress()
        self.assertTrue(success)
        self.assertEqual(state_manager.get_pipeline_state(), PipelineState.EXTRACTION_IN_PROGRESS)

        success = state_manager.transition_to_extraction_complete(self.temp_content_file.name)
        self.assertTrue(success)
        self.assertEqual(state_manager.get_pipeline_state(), PipelineState.EXTRACTION_COMPLETE)

        # Approve extraction
        state_persistence = StatePersistence(self.temp_file.name)
        approval_engine = ApprovalEngine(state_persistence)
        success = approval_engine.process_approval(
            stage="extraction",
            approver_id="test_approver",
            decision=ApprovalDecision.APPROVE
        )
        self.assertTrue(success)
        self.assertEqual(state_manager.get_pipeline_state(), PipelineState.EXTRACTION_APPROVED)

        # Move through chunking phase
        success = state_manager.transition_to_chunking_in_progress()
        self.assertTrue(success)
        self.assertEqual(state_manager.get_pipeline_state(), PipelineState.CHUNKING_IN_PROGRESS)

        success = state_manager.transition_to_chunking_complete(self.temp_chunked_file.name)
        self.assertTrue(success)
        self.assertEqual(state_manager.get_pipeline_state(), PipelineState.CHUNKING_COMPLETE)

        # Approve chunking
        success = approval_engine.process_approval(
            stage="chunking",
            approver_id="test_approver",
            decision=ApprovalDecision.APPROVE
        )
        self.assertTrue(success)
        self.assertEqual(state_manager.get_pipeline_state(), PipelineState.CHUNKING_APPROVED)

        # All transitions completed successfully
        print("All state transitions completed successfully in sequence.")


if __name__ == '__main__':
    unittest.main()