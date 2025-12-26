"""
Integration tests for chunking approval CLI functionality.
This test verifies that the CLI commands for chunking approval work correctly
with the approval engine and state management.
"""
import os
import tempfile
import unittest
import argparse
from unittest.mock import Mock, patch

from src.pipeline.state_machine import PipelineState
from src.pipeline.state_persistence import StatePersistence
from src.pipeline.approval_engine import ApprovalEngine, ApprovalDecision
from src.pipeline.preview_service import PreviewService
from src.cli.approval_cli import (
    create_approval_parser,
    handle_approve_command,
    handle_reject_command,
    handle_request_change_command,
    handle_preview_command,
    run_approval_cli
)


class TestChunkingApprovalCLI(unittest.TestCase):
    """
    Integration tests for chunking approval CLI functionality.
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
        self.preview_service = PreviewService()

    def tearDown(self):
        """
        Clean up after each test method.
        """
        # Remove the temporary file
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

    def test_approve_chunking_command(self):
        """
        Test the approve chunking CLI command.
        """
        # Initialize state to CHUNKING_COMPLETE
        self.state_persistence.update_state(PipelineState.CHUNKING_COMPLETE)

        # Create mock args for approve command
        args = argparse.Namespace()
        args.approval_command = "approve"
        args.stage = "chunking"
        args.approver = "test_approver"
        args.reason = "Chunks look good"

        # Test the approve command
        success = handle_approve_command(args, self.approval_engine)

        # Verify success
        self.assertTrue(success)

        # Verify state transition to CHUNKING_APPROVED
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.CHUNKING_APPROVED)

        # Verify approval status
        status = self.approval_engine.check_approval_status("chunking")
        self.assertEqual(status, "APPROVED")

    def test_reject_chunking_command(self):
        """
        Test the reject chunking CLI command.
        """
        # Initialize state to CHUNKING_COMPLETE
        self.state_persistence.update_state(PipelineState.CHUNKING_COMPLETE)

        # Create mock args for reject command
        args = argparse.Namespace()
        args.approval_command = "reject"
        args.stage = "chunking"
        args.approver = "test_approver"
        args.reason = "Chunks need revision"

        # Test the reject command
        success = handle_reject_command(args, self.approval_engine)

        # Verify success
        self.assertTrue(success)

        # Verify state transition to REJECTED
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.REJECTED)

        # Verify approval status
        status = self.approval_engine.check_approval_status("chunking")
        self.assertEqual(status, "REJECTED")

    def test_request_change_chunking_command(self):
        """
        Test the request change chunking CLI command.
        """
        # Initialize state to CHUNKING_COMPLETE
        self.state_persistence.update_state(PipelineState.CHUNKING_COMPLETE)

        # Create mock args for request-change command
        args = argparse.Namespace()
        args.approval_command = "request-change"
        args.stage = "chunking"
        args.approver = "test_approver"
        args.reason = "Please fix formatting"

        # Test the request-change command
        success = handle_request_change_command(args, self.approval_engine)

        # Verify success
        self.assertTrue(success)

        # For REQUEST_CHANGE, state should remain at CHUNKING_COMPLETE
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.CHUNKING_COMPLETE)

        # Verify approval decision was recorded
        approval_record = self.approval_engine.get_approval_record("chunking")
        self.assertIsNotNone(approval_record)
        self.assertEqual(approval_record["decision"], "REQUEST_CHANGE")
        self.assertEqual(approval_record["context"], "Please fix formatting")

    def test_preview_chunking_command(self):
        """
        Test the preview chunking CLI command.
        """
        # Create a temporary chunked content file for testing
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as chunk_file:
            chunk_file.write("This is chunked content for preview testing.")
            chunk_file_path = chunk_file.name

        try:
            # Initialize state with chunked content path
            state_data = {
                "state": PipelineState.CHUNKING_COMPLETE.value,
                "timestamp": "2025-12-24T10:00:00Z",
                "artifact_paths": {
                    "chunked_output": chunk_file_path
                }
            }
            self.state_persistence.write_state(state_data)

            # Create mock args for preview command
            args = argparse.Namespace()
            args.approval_command = "preview"
            args.stage = "chunking"
            args.offset = 0
            args.limit = 20

            # Test the preview command
            success = handle_preview_command(args, self.state_persistence, self.preview_service)

            # Verify success
            self.assertTrue(success)

        finally:
            # Clean up the temporary chunk file
            if os.path.exists(chunk_file_path):
                os.remove(chunk_file_path)

    def test_chunking_approval_from_invalid_state(self):
        """
        Test that chunking approval commands fail from invalid states.
        """
        # Initialize state to IDLE (not ready for chunking approval)
        self.state_persistence.update_state(PipelineState.IDLE)

        # Create mock args for approve command
        args = argparse.Namespace()
        args.approval_command = "approve"
        args.stage = "chunking"
        args.approver = "test_approver"
        args.reason = "Test approval"

        # Test the approve command (should fail because state is not CHUNKING_COMPLETE)
        success = handle_approve_command(args, self.approval_engine)

        # Verify failure
        self.assertFalse(success)

        # Verify state remains unchanged
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.IDLE)

    def test_parser_accepts_chunking_stage(self):
        """
        Test that the CLI parser accepts chunking as a valid stage.
        """
        parser = create_approval_parser()

        # Test approve command with chunking stage
        args = parser.parse_args(["approve", "chunking", "--approver", "test"])
        self.assertEqual(args.stage, "chunking")
        self.assertEqual(args.approval_command, "approve")

        # Test reject command with chunking stage
        args = parser.parse_args(["reject", "chunking", "--approver", "test"])
        self.assertEqual(args.stage, "chunking")
        self.assertEqual(args.approval_command, "reject")

        # Test request-change command with chunking stage
        args = parser.parse_args(["request-change", "chunking", "--approver", "test"])
        self.assertEqual(args.stage, "chunking")
        self.assertEqual(args.approval_command, "request-change")

        # Test preview command with chunking stage
        args = parser.parse_args(["preview", "chunking"])
        self.assertEqual(args.stage, "chunking")
        self.assertEqual(args.approval_command, "preview")

    def test_run_approval_cli_approve_chunking(self):
        """
        Test running the full approval CLI for chunking approval.
        """
        # Initialize state to CHUNKING_COMPLETE
        self.state_persistence.update_state(PipelineState.CHUNKING_COMPLETE)

        # Create mock args for approve command
        args = argparse.Namespace()
        args.approval_command = "approve"
        args.stage = "chunking"
        args.approver = "cli_tester"
        args.reason = "CLI approval test"

        # Test the full CLI runner
        exit_code = run_approval_cli(
            args,
            self.approval_engine,
            self.state_persistence,
            self.preview_service
        )

        # Verify success (exit code 0)
        self.assertEqual(exit_code, 0)

        # Verify state transition
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.CHUNKING_APPROVED)

    def test_run_approval_cli_reject_chunking(self):
        """
        Test running the full approval CLI for chunking rejection.
        """
        # Initialize state to CHUNKING_COMPLETE
        self.state_persistence.update_state(PipelineState.CHUNKING_COMPLETE)

        # Create mock args for reject command
        args = argparse.Namespace()
        args.approval_command = "reject"
        args.stage = "chunking"
        args.approver = "cli_tester"
        args.reason = "CLI rejection test"

        # Test the full CLI runner
        exit_code = run_approval_cli(
            args,
            self.approval_engine,
            self.state_persistence,
            self.preview_service
        )

        # Verify success (exit code 0)
        self.assertEqual(exit_code, 0)

        # Verify state transition to REJECTED
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.REJECTED)


if __name__ == '__main__':
    unittest.main()