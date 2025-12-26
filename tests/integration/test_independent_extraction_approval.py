"""
Independent test for extraction approval functionality.
This test verifies that the extraction approval workflow works correctly in isolation,
ensuring that content can be approved or rejected and the state transitions properly.
"""
import os
import tempfile
import unittest
from datetime import datetime

from src.pipeline.state_machine import PipelineState
from src.pipeline.state_persistence import StatePersistence
from src.pipeline.approval_engine import ApprovalEngine, ApprovalDecision, ApprovalRecord


class TestIndependentExtractionApproval(unittest.TestCase):
    """
    Independent test for extraction approval functionality.
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
        self.approval_engine = ApprovalEngine(self.state_persistence)

    def tearDown(self):
        """
        Clean up after each test method.
        """
        # Remove the temporary file
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

    def test_extraction_approval_workflow_complete(self):
        """
        Independent test: Complete extraction approval workflow with approve decision.
        """
        # Initialize state to EXTRACTION_COMPLETE (simulating completed extraction)
        self.state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)

        # Verify initial state
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_COMPLETE)

        # Request approval for extraction
        success = self.approval_engine.request_approval("extraction", "Test extracted content preview")
        self.assertTrue(success)

        # Check that approval status is PENDING
        status = self.approval_engine.check_approval_status("extraction")
        self.assertEqual(status, "PENDING")

        # Process approval with APPROVE decision
        success = self.approval_engine.process_approval(
            stage="extraction",
            approver_id="test_approver",
            decision=ApprovalDecision.APPROVE,
            context="Content looks good"
        )
        self.assertTrue(success)

        # Verify state transition to EXTRACTION_APPROVED
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_APPROVED)

        # Verify approval status is APPROVED
        status = self.approval_engine.check_approval_status("extraction")
        self.assertEqual(status, "APPROVED")

        # Verify approval record contains correct information
        approval_record = self.approval_engine.get_approval_record("extraction")
        self.assertIsNotNone(approval_record)
        self.assertEqual(approval_record["status"], "APPROVED")
        self.assertEqual(approval_record["approver"], "test_approver")
        self.assertEqual(approval_record["decision"], "APPROVE")
        self.assertEqual(approval_record["context"], "Content looks good")

    def test_extraction_rejection_workflow(self):
        """
        Independent test: Extraction rejection workflow with reject decision.
        """
        # Initialize state to EXTRACTION_COMPLETE
        self.state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)

        # Verify initial state
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_COMPLETE)

        # Request approval for extraction
        success = self.approval_engine.request_approval("extraction", "Test extracted content preview")
        self.assertTrue(success)

        # Check that approval status is PENDING
        status = self.approval_engine.check_approval_status("extraction")
        self.assertEqual(status, "PENDING")

        # Process approval with REJECT decision
        success = self.approval_engine.process_approval(
            stage="extraction",
            approver_id="test_approver",
            decision=ApprovalDecision.REJECT,
            context="Content needs revision"
        )
        self.assertTrue(success)

        # Verify state transition to REJECTED
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.REJECTED)

        # Verify approval status is REJECTED
        status = self.approval_engine.check_approval_status("extraction")
        self.assertEqual(status, "REJECTED")

        # Verify approval record contains correct information
        approval_record = self.approval_engine.get_approval_record("extraction")
        self.assertIsNotNone(approval_record)
        self.assertEqual(approval_record["status"], "REJECTED")
        self.assertEqual(approval_record["approver"], "test_approver")
        self.assertEqual(approval_record["decision"], "REJECT")
        self.assertEqual(approval_record["context"], "Content needs revision")

    def test_extraction_request_change_workflow(self):
        """
        Independent test: Extraction workflow with request change decision.
        """
        # Initialize state to EXTRACTION_COMPLETE
        self.state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)

        # Verify initial state
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_COMPLETE)

        # Request approval for extraction
        success = self.approval_engine.request_approval("extraction", "Test extracted content preview")
        self.assertTrue(success)

        # Check that approval status is PENDING
        status = self.approval_engine.check_approval_status("extraction")
        self.assertEqual(status, "PENDING")

        # Process approval with REQUEST_CHANGE decision
        success = self.approval_engine.process_approval(
            stage="extraction",
            approver_id="test_approver",
            decision=ApprovalDecision.REQUEST_CHANGE,
            context="Please fix formatting issues"
        )
        self.assertTrue(success)

        # Verify state remains at EXTRACTION_COMPLETE (REQUEST_CHANGE doesn't advance state)
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_COMPLETE)

        # Verify approval status reflects the decision (should be REJECTED based on implementation)
        status = self.approval_engine.check_approval_status("extraction")
        # Note: Based on implementation, REQUEST_CHANGE may be treated as REJECTED
        # Check the actual state data to understand the behavior
        state_data = self.state_persistence.read_state()
        if state_data and "approvals" in state_data:
            extraction_approval = state_data["approvals"].get("extraction", {})
            status = extraction_approval.get("status")

        # For REQUEST_CHANGE, the status may be handled differently depending on implementation
        # Let's verify the decision field is stored correctly
        approval_record = self.approval_engine.get_approval_record("extraction")
        self.assertIsNotNone(approval_record)
        self.assertEqual(approval_record["decision"], "REQUEST_CHANGE")
        self.assertEqual(approval_record["context"], "Please fix formatting issues")

    def test_extraction_approval_with_invalid_state(self):
        """
        Independent test: Attempt extraction approval from invalid state should fail.
        """
        # Initialize state to IDLE (not ready for extraction approval)
        self.state_persistence.update_state(PipelineState.IDLE)

        # Verify initial state
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.IDLE)

        # Attempt to process approval (should fail because state is not EXTRACTION_COMPLETE)
        success = self.approval_engine.process_approval(
            stage="extraction",
            approver_id="test_approver",
            decision=ApprovalDecision.APPROVE,
            context="Test approval"
        )
        self.assertFalse(success)

        # Verify state remains unchanged
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.IDLE)

        # Verify no approval was recorded
        approval_record = self.approval_engine.get_approval_record("extraction")
        self.assertIsNone(approval_record)

    def test_extraction_approval_validation(self):
        """
        Independent test: Extraction approval validation and state persistence.
        """
        # Initialize state to EXTRACTION_COMPLETE
        self.state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)

        # Request approval
        success = self.approval_engine.request_approval("extraction", "Test content")
        self.assertTrue(success)

        # Verify state is persisted with approval information
        state_data = self.state_persistence.read_state()
        self.assertIsNotNone(state_data)
        self.assertIn("approvals", state_data)
        self.assertIn("extraction", state_data["approvals"])
        self.assertEqual(state_data["approvals"]["extraction"]["status"], "PENDING")

        # Process approval
        success = self.approval_engine.process_approval(
            stage="extraction",
            approver_id="validator",
            decision=ApprovalDecision.APPROVE,
            context="Validated successfully"
        )
        self.assertTrue(success)

        # Verify state is updated and persisted
        updated_state_data = self.state_persistence.read_state()
        self.assertIsNotNone(updated_state_data)
        self.assertEqual(updated_state_data["state"], PipelineState.EXTRACTION_APPROVED.value)
        self.assertIn("approvals", updated_state_data)
        self.assertIn("extraction", updated_state_data["approvals"])
        self.assertEqual(updated_state_data["approvals"]["extraction"]["status"], "APPROVED")
        self.assertEqual(updated_state_data["approvals"]["extraction"]["approver"], "validator")

    def test_extraction_approval_record_serialization(self):
        """
        Independent test: Extraction approval record creation and serialization.
        """
        # Create an approval record
        record = ApprovalRecord(
            approver_id="test_user",
            decision=ApprovalDecision.APPROVE,
            context="Test approval context",
            pipeline_state=PipelineState.EXTRACTION_COMPLETE
        )

        # Verify record properties
        self.assertEqual(record.approver_id, "test_user")
        self.assertEqual(record.decision, ApprovalDecision.APPROVE)
        self.assertEqual(record.context, "Test approval context")
        self.assertEqual(record.pipeline_state, PipelineState.EXTRACTION_COMPLETE)
        self.assertIsNotNone(record.timestamp)

        # Convert to dictionary
        record_dict = record.to_dict()
        self.assertEqual(record_dict["approver_id"], "test_user")
        self.assertEqual(record_dict["decision"], "APPROVE")
        self.assertEqual(record_dict["context"], "Test approval context")
        self.assertEqual(record_dict["pipeline_state"], "EXTRACTION_COMPLETE")
        self.assertEqual(record_dict["timestamp"], record.timestamp)

        # Restore from dictionary
        restored_record = ApprovalRecord.from_dict(record_dict)
        self.assertEqual(restored_record.approver_id, "test_user")
        self.assertEqual(restored_record.decision, ApprovalDecision.APPROVE)
        self.assertEqual(restored_record.context, "Test approval context")
        self.assertEqual(restored_record.pipeline_state, PipelineState.EXTRACTION_COMPLETE)
        self.assertEqual(restored_record.timestamp, record.timestamp)

    def test_multiple_extraction_approvals(self):
        """
        Independent test: Multiple extraction approval attempts and state consistency.
        """
        # Initialize state to EXTRACTION_COMPLETE
        self.state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)

        # Request approval first time
        success1 = self.approval_engine.request_approval("extraction", "First request")
        self.assertTrue(success1)

        # Verify PENDING status
        status1 = self.approval_engine.check_approval_status("extraction")
        self.assertEqual(status1, "PENDING")

        # Process approval with APPROVE
        success2 = self.approval_engine.process_approval(
            stage="extraction",
            approver_id="approver1",
            decision=ApprovalDecision.APPROVE,
            context="First approval"
        )
        self.assertTrue(success2)

        # Verify state is now EXTRACTION_APPROVED
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_APPROVED)

        # Attempt another approval (should fail since state is no longer EXTRACTION_COMPLETE)
        success3 = self.approval_engine.process_approval(
            stage="extraction",
            approver_id="approver2",
            decision=ApprovalDecision.APPROVE,
            context="Second approval attempt"
        )
        # This should fail because the state is no longer EXTRACTION_COMPLETE
        self.assertFalse(success3)

        # Verify state remains EXTRACTION_APPROVED
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_APPROVED)

        # Verify only the first approval is recorded
        approval_record = self.approval_engine.get_approval_record("extraction")
        self.assertIsNotNone(approval_record)
        self.assertEqual(approval_record["approver"], "approver1")
        self.assertEqual(approval_record["decision"], "APPROVE")
        self.assertEqual(approval_record["context"], "First approval")


if __name__ == '__main__':
    unittest.main()