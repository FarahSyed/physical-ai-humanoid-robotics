"""
Unit tests for the approval engine module.
"""
import os
import tempfile
import unittest
from datetime import datetime

from src.pipeline.state_machine import PipelineState
from src.pipeline.state_persistence import StatePersistence
from src.pipeline.approval_engine import ApprovalEngine, ApprovalDecision, ApprovalRecord


class TestApprovalEngine(unittest.TestCase):
    """
    Test cases for ApprovalEngine class.
    """
    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()

        # Initialize components
        self.state_persistence = StatePersistence(self.temp_file.name)
        self.approval_engine = ApprovalEngine(self.state_persistence)

        # Initialize the pipeline
        self.state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)

    def tearDown(self):
        """
        Clean up after each test method.
        """
        # Remove the temporary file
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_approval_record_creation(self):
        """
        Test creating an approval record.
        """
        record = ApprovalRecord(
            approver_id="test_user",
            decision=ApprovalDecision.APPROVE,
            context="Test approval"
        )

        self.assertEqual(record.approver_id, "test_user")
        self.assertEqual(record.decision, ApprovalDecision.APPROVE)
        self.assertEqual(record.context, "Test approval")
        self.assertIsNotNone(record.timestamp)

    def test_approval_record_to_from_dict(self):
        """
        Test converting approval record to and from dictionary.
        """
        original_record = ApprovalRecord(
            approver_id="test_user",
            decision=ApprovalDecision.REJECT,
            context="Test rejection"
        )

        # Convert to dictionary
        record_dict = original_record.to_dict()

        # Convert back from dictionary
        restored_record = ApprovalRecord.from_dict(record_dict)

        self.assertEqual(original_record.approver_id, restored_record.approver_id)
        self.assertEqual(original_record.decision, restored_record.decision)
        self.assertEqual(original_record.context, restored_record.context)

    def test_request_approval(self):
        """
        Test requesting approval for extraction stage.
        """
        # Update state to EXTRACTION_COMPLETE to allow approval
        self.state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)

        success = self.approval_engine.request_approval("extraction", "Test content preview")
        self.assertTrue(success)

        # Check that approval status is PENDING
        status = self.approval_engine.check_approval_status("extraction")
        self.assertEqual(status, "PENDING")

    def test_process_approval_approve(self):
        """
        Test processing an approval with APPROVE decision.
        """
        # Update state to EXTRACTION_COMPLETE to allow approval
        self.state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)

        success = self.approval_engine.process_approval(
            stage="extraction",
            approver_id="test_approver",
            decision=ApprovalDecision.APPROVE,
            context="Test approval"
        )

        self.assertTrue(success)

        # Check that state changed to EXTRACTION_APPROVED
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_APPROVED)

        # Check that approval status is APPROVED
        status = self.approval_engine.check_approval_status("extraction")
        self.assertEqual(status, "APPROVED")

    def test_process_approval_reject(self):
        """
        Test processing an approval with REJECT decision.
        """
        # Update state to EXTRACTION_COMPLETE to allow approval
        self.state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)

        success = self.approval_engine.process_approval(
            stage="extraction",
            approver_id="test_approver",
            decision=ApprovalDecision.REJECT,
            context="Test rejection"
        )

        self.assertTrue(success)

        # Check that state changed to REJECTED
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.REJECTED)

        # Check that approval status is REJECTED
        status = self.approval_engine.check_approval_status("extraction")
        self.assertEqual(status, "REJECTED")

    def test_check_approval_status(self):
        """
        Test checking approval status.
        """
        # Initially should be None
        status = self.approval_engine.check_approval_status("extraction")
        self.assertIsNone(status)

        # Request approval
        self.state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)
        self.approval_engine.request_approval("extraction", "Test content")

        # Check status should be PENDING
        status = self.approval_engine.check_approval_status("extraction")
        self.assertEqual(status, "PENDING")

    def test_get_approval_record(self):
        """
        Test getting approval record.
        """
        # Request approval
        self.state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)
        self.approval_engine.request_approval("extraction", "Test content")

        # Get approval record
        record = self.approval_engine.get_approval_record("extraction")
        self.assertIsNotNone(record)
        self.assertEqual(record.get("status"), "PENDING")

    def test_validate_approvals(self):
        """
        Test validating approvals.
        """
        # Initially should be valid (no approvals to validate)
        is_valid = self.approval_engine.validate_approvals()
        self.assertTrue(is_valid)

        # Request approval
        self.state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)
        self.approval_engine.request_approval("extraction", "Test content")

        # Validate should still be valid
        is_valid = self.approval_engine.validate_approvals()
        self.assertTrue(is_valid)


if __name__ == '__main__':
    unittest.main()