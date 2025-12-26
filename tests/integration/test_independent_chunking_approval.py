"""
Independent test for chunking approval functionality.
This test verifies that the chunking approval workflow works correctly in isolation,
ensuring that chunked content can be approved or rejected and the state transitions properly.
"""
import os
import tempfile
import unittest
from datetime import datetime

from src.pipeline.state_machine import PipelineState
from src.pipeline.state_persistence import StatePersistence, PipelineStateManager
from src.pipeline.approval_engine import ApprovalEngine, ApprovalDecision, ApprovalRecord


class TestIndependentChunkingApproval(unittest.TestCase):
    """
    Independent test for chunking approval functionality.
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
        self.approval_engine = ApprovalEngine(self.state_persistence)

    def tearDown(self):
        """
        Clean up after each test method.
        """
        # Remove the temporary file
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

    def test_chunking_approval_workflow_complete(self):
        """
        Independent test: Complete chunking approval workflow with approve decision.
        """
        # Initialize state to CHUNKING_COMPLETE (simulating completed chunking)
        self.state_persistence.update_state(PipelineState.CHUNKING_COMPLETE)

        # Verify initial state
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.CHUNKING_COMPLETE)

        # Request approval for chunking
        success = self.approval_engine.request_approval("chunking", "Test chunked content preview")
        self.assertTrue(success)

        # Check that approval status is PENDING
        status = self.approval_engine.check_approval_status("chunking")
        self.assertEqual(status, "PENDING")

        # Process approval with APPROVE decision
        success = self.approval_engine.process_approval(
            stage="chunking",
            approver_id="test_approver",
            decision=ApprovalDecision.APPROVE,
            context="Chunks look good"
        )
        self.assertTrue(success)

        # Verify state transition to CHUNKING_APPROVED
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.CHUNKING_APPROVED)

        # Verify approval status is APPROVED
        status = self.approval_engine.check_approval_status("chunking")
        self.assertEqual(status, "APPROVED")

        # Verify approval record contains correct information
        approval_record = self.approval_engine.get_approval_record("chunking")
        self.assertIsNotNone(approval_record)
        self.assertEqual(approval_record["status"], "APPROVED")
        self.assertEqual(approval_record["approver"], "test_approver")
        self.assertEqual(approval_record["decision"], "APPROVE")
        self.assertEqual(approval_record["context"], "Chunks look good")

    def test_chunking_rejection_workflow(self):
        """
        Independent test: Chunking rejection workflow with reject decision.
        """
        # Initialize state to CHUNKING_COMPLETE
        self.state_persistence.update_state(PipelineState.CHUNKING_COMPLETE)

        # Verify initial state
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.CHUNKING_COMPLETE)

        # Request approval for chunking
        success = self.approval_engine.request_approval("chunking", "Test chunked content preview")
        self.assertTrue(success)

        # Check that approval status is PENDING
        status = self.approval_engine.check_approval_status("chunking")
        self.assertEqual(status, "PENDING")

        # Process approval with REJECT decision
        success = self.approval_engine.process_approval(
            stage="chunking",
            approver_id="test_approver",
            decision=ApprovalDecision.REJECT,
            context="Chunks need revision"
        )
        self.assertTrue(success)

        # Verify state transition to REJECTED
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.REJECTED)

        # Verify approval status is REJECTED
        status = self.approval_engine.check_approval_status("chunking")
        self.assertEqual(status, "REJECTED")

        # Verify approval record contains correct information
        approval_record = self.approval_engine.get_approval_record("chunking")
        self.assertIsNotNone(approval_record)
        self.assertEqual(approval_record["status"], "REJECTED")
        self.assertEqual(approval_record["approver"], "test_approver")
        self.assertEqual(approval_record["decision"], "REJECT")
        self.assertEqual(approval_record["context"], "Chunks need revision")

    def test_chunking_request_change_workflow(self):
        """
        Independent test: Chunking workflow with request change decision.
        """
        # Initialize state to CHUNKING_COMPLETE
        self.state_persistence.update_state(PipelineState.CHUNKING_COMPLETE)

        # Verify initial state
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.CHUNKING_COMPLETE)

        # Request approval for chunking
        success = self.approval_engine.request_approval("chunking", "Test chunked content preview")
        self.assertTrue(success)

        # Check that approval status is PENDING
        status = self.approval_engine.check_approval_status("chunking")
        self.assertEqual(status, "PENDING")

        # Process approval with REQUEST_CHANGE decision
        success = self.approval_engine.process_approval(
            stage="chunking",
            approver_id="test_approver",
            decision=ApprovalDecision.REQUEST_CHANGE,
            context="Please fix chunk boundaries"
        )
        self.assertTrue(success)

        # Verify state remains at CHUNKING_COMPLETE (REQUEST_CHANGE doesn't advance state)
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.CHUNKING_COMPLETE)

        # Verify approval record contains correct information
        approval_record = self.approval_engine.get_approval_record("chunking")
        self.assertIsNotNone(approval_record)
        self.assertEqual(approval_record["decision"], "REQUEST_CHANGE")
        self.assertEqual(approval_record["context"], "Please fix chunk boundaries")

    def test_chunking_approval_with_invalid_state(self):
        """
        Independent test: Attempt chunking approval from invalid state should fail.
        """
        # Initialize state to IDLE (not ready for chunking approval)
        self.state_persistence.update_state(PipelineState.IDLE)

        # Verify initial state
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.IDLE)

        # Attempt to process approval (should fail because state is not CHUNKING_COMPLETE)
        success = self.approval_engine.process_approval(
            stage="chunking",
            approver_id="test_approver",
            decision=ApprovalDecision.APPROVE,
            context="Test approval"
        )
        self.assertFalse(success)

        # Verify state remains unchanged
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.IDLE)

        # Verify no approval was recorded
        approval_record = self.approval_engine.get_approval_record("chunking")
        self.assertIsNone(approval_record)

    def test_chunking_approval_validation(self):
        """
        Independent test: Chunking approval validation and state persistence.
        """
        # Initialize state to CHUNKING_COMPLETE
        self.state_persistence.update_state(PipelineState.CHUNKING_COMPLETE)

        # Request approval
        success = self.approval_engine.request_approval("chunking", "Test chunked content")
        self.assertTrue(success)

        # Verify state is persisted with approval information
        state_data = self.state_persistence.read_state()
        self.assertIsNotNone(state_data)
        self.assertIn("approvals", state_data)
        self.assertIn("chunking", state_data["approvals"])
        self.assertEqual(state_data["approvals"]["chunking"]["status"], "PENDING")

        # Process approval
        success = self.approval_engine.process_approval(
            stage="chunking",
            approver_id="validator",
            decision=ApprovalDecision.APPROVE,
            context="Chunks validated successfully"
        )
        self.assertTrue(success)

        # Verify state is updated and persisted
        updated_state_data = self.state_persistence.read_state()
        self.assertIsNotNone(updated_state_data)
        self.assertEqual(updated_state_data["state"], PipelineState.CHUNKING_APPROVED.value)
        self.assertIn("approvals", updated_state_data)
        self.assertIn("chunking", updated_state_data["approvals"])
        self.assertEqual(updated_state_data["approvals"]["chunking"]["status"], "APPROVED")
        self.assertEqual(updated_state_data["approvals"]["chunking"]["approver"], "validator")

    def test_chunking_approval_record_serialization(self):
        """
        Independent test: Chunking approval record creation and serialization.
        """
        # Create an approval record
        record = ApprovalRecord(
            approver_id="test_user",
            decision=ApprovalDecision.REJECT,
            context="Test chunking rejection context",
            pipeline_state=PipelineState.CHUNKING_COMPLETE
        )

        # Verify record properties
        self.assertEqual(record.approver_id, "test_user")
        self.assertEqual(record.decision, ApprovalDecision.REJECT)
        self.assertEqual(record.context, "Test chunking rejection context")
        self.assertEqual(record.pipeline_state, PipelineState.CHUNKING_COMPLETE)
        self.assertIsNotNone(record.timestamp)

        # Convert to dictionary
        record_dict = record.to_dict()
        self.assertEqual(record_dict["approver_id"], "test_user")
        self.assertEqual(record_dict["decision"], "REJECT")
        self.assertEqual(record_dict["context"], "Test chunking rejection context")
        self.assertEqual(record_dict["pipeline_state"], "CHUNKING_COMPLETE")
        self.assertEqual(record_dict["timestamp"], record.timestamp)

        # Restore from dictionary
        restored_record = ApprovalRecord.from_dict(record_dict)
        self.assertEqual(restored_record.approver_id, "test_user")
        self.assertEqual(restored_record.decision, ApprovalDecision.REJECT)
        self.assertEqual(restored_record.context, "Test chunking rejection context")
        self.assertEqual(restored_record.pipeline_state, PipelineState.CHUNKING_COMPLETE)
        self.assertEqual(restored_record.timestamp, record.timestamp)

    def test_multiple_chunking_approvals(self):
        """
        Independent test: Multiple chunking approval attempts and state consistency.
        """
        # Initialize state to CHUNKING_COMPLETE
        self.state_persistence.update_state(PipelineState.CHUNKING_COMPLETE)

        # Request approval first time
        success1 = self.approval_engine.request_approval("chunking", "First request")
        self.assertTrue(success1)

        # Verify PENDING status
        status1 = self.approval_engine.check_approval_status("chunking")
        self.assertEqual(status1, "PENDING")

        # Process approval with APPROVE
        success2 = self.approval_engine.process_approval(
            stage="chunking",
            approver_id="approver1",
            decision=ApprovalDecision.APPROVE,
            context="First approval"
        )
        self.assertTrue(success2)

        # Verify state is now CHUNKING_APPROVED
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.CHUNKING_APPROVED)

        # Attempt another approval (should fail since state is no longer CHUNKING_COMPLETE)
        success3 = self.approval_engine.process_approval(
            stage="chunking",
            approver_id="approver2",
            decision=ApprovalDecision.APPROVE,
            context="Second approval attempt"
        )
        # This should fail because the state is no longer CHUNKING_COMPLETE
        self.assertFalse(success3)

        # Verify state remains CHUNKING_APPROVED
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.CHUNKING_APPROVED)

        # Verify only the first approval is recorded
        approval_record = self.approval_engine.get_approval_record("chunking")
        self.assertIsNotNone(approval_record)
        self.assertEqual(approval_record["approver"], "approver1")
        self.assertEqual(approval_record["decision"], "APPROVE")
        self.assertEqual(approval_record["context"], "First approval")

    def test_chunking_approval_state_transitions(self):
        """
        Independent test: Verify correct state transitions during chunking approval.
        """
        # Initialize the pipeline
        self.state_manager.initialize_pipeline({"input_path": "dummy_input.txt"})

        # Transition to EXTRACTION_IN_PROGRESS
        success1 = self.state_manager.transition_to_extraction_in_progress()
        self.assertTrue(success1)

        current_state = self.state_manager.get_pipeline_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_IN_PROGRESS)

        # Create a temporary file for extracted content
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as extract_file:
            extract_file.write(b"Test extracted content")
            extract_file_path = extract_file.name

        try:
            # Transition to EXTRACTION_COMPLETE
            success2 = self.state_manager.transition_to_extraction_complete(extract_file_path)
            self.assertTrue(success2)

            current_state = self.state_manager.get_pipeline_state()
            self.assertEqual(current_state, PipelineState.EXTRACTION_COMPLETE)

            # Process extraction approval to get to EXTRACTION_APPROVED
            success3 = self.approval_engine.process_approval(
                stage="extraction",
                approver_id="test_approver",
                decision=ApprovalDecision.APPROVE,
                context="Approving extracted content"
            )
            self.assertTrue(success3)

            current_state = self.state_manager.get_pipeline_state()
            self.assertEqual(current_state, PipelineState.EXTRACTION_APPROVED)

            # Transition to CHUNKING_IN_PROGRESS
            success4 = self.state_manager.transition_to_chunking_in_progress()
            self.assertTrue(success4)

            current_state = self.state_manager.get_pipeline_state()
            self.assertEqual(current_state, PipelineState.CHUNKING_IN_PROGRESS)

            # Create a temporary file for chunked output
            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as chunk_file:
                chunk_file.write(b"Test chunked content")
                chunk_file_path = chunk_file.name

            try:
                # Transition to CHUNKING_COMPLETE
                success5 = self.state_manager.transition_to_chunking_complete(chunk_file_path)
                self.assertTrue(success5)

                current_state = self.state_manager.get_pipeline_state()
                self.assertEqual(current_state, PipelineState.CHUNKING_COMPLETE)

                # Process approval with APPROVE
                success6 = self.approval_engine.process_approval(
                    stage="chunking",
                    approver_id="test_approver",
                    decision=ApprovalDecision.APPROVE,
                    context="Approving chunks"
                )
                self.assertTrue(success6)

                # Verify final state is CHUNKING_APPROVED
                current_state = self.state_manager.get_pipeline_state()
                self.assertEqual(current_state, PipelineState.CHUNKING_APPROVED)

                # Verify artifact paths are preserved
                state_data = self.state_persistence.read_state()
                self.assertIn("artifact_paths", state_data)
                self.assertIn("chunked_output", state_data["artifact_paths"])
                self.assertEqual(state_data["artifact_paths"]["chunked_output"], chunk_file_path)

            finally:
                # Clean up the temporary chunk file if it wasn't already cleaned up
                if os.path.exists(chunk_file_path):
                    os.remove(chunk_file_path)

        finally:
            # Clean up the temporary extract file
            if os.path.exists(extract_file_path):
                os.remove(extract_file_path)


if __name__ == '__main__':
    unittest.main()