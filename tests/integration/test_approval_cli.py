"""
Integration tests for approval CLI functionality.
"""
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import sys
from io import StringIO
import argparse

from src.pipeline.state_machine import PipelineState
from src.pipeline.state_persistence import StatePersistence
from src.pipeline.approval_engine import ApprovalEngine, ApprovalDecision
from src.pipeline.preview_service import PreviewService
from src.cli.approval_cli import (
    handle_approve_command, handle_reject_command, handle_preview_command,
    interactive_approve_content
)


class TestApprovalCLIIntegration(unittest.TestCase):
    """
    Integration test cases for approval CLI functionality.
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.state_file = self.temp_file.name

    def tearDown(self):
        """
        Clean up after each test method.
        """
        # Remove the temporary file
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

    def test_approve_extraction_command_integration(self):
        """
        Test the approve extraction command integration with state persistence.
        """
        # Set up state with EXTRACTION_COMPLETE
        state_persistence = StatePersistence(self.state_file)
        state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)

        # Create approval engine
        approval_engine = ApprovalEngine(state_persistence)

        # Create mock args for approve command
        args = argparse.Namespace()
        args.stage = "extraction"
        args.approver = "test_approver"
        args.reason = "Test approval"

        # Execute approval command
        result = handle_approve_command(args, approval_engine)

        # Verify the result
        self.assertTrue(result)

        # Check that the state was updated to EXTRACTION_APPROVED
        current_state = state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_APPROVED)

    def test_reject_extraction_command_integration(self):
        """
        Test the reject extraction command integration with state persistence.
        """
        # Set up state with EXTRACTION_COMPLETE
        state_persistence = StatePersistence(self.state_file)
        state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)

        # Create approval engine
        approval_engine = ApprovalEngine(state_persistence)

        # Create mock args for reject command
        args = argparse.Namespace()
        args.stage = "extraction"
        args.approver = "test_approver"
        args.reason = "Test rejection"

        # Execute rejection command
        result = handle_reject_command(args, approval_engine)

        # Verify the result
        self.assertTrue(result)

        # Check that the state was updated to REJECTED
        current_state = state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.REJECTED)

    def test_approve_chunking_command_integration(self):
        """
        Test the approve chunking command integration with state persistence.
        """
        # Set up state with CHUNKING_COMPLETE
        state_persistence = StatePersistence(self.state_file)
        state_persistence.update_state(PipelineState.CHUNKING_COMPLETE)

        # Create approval engine
        approval_engine = ApprovalEngine(state_persistence)

        # Create mock args for approve command
        args = argparse.Namespace()
        args.stage = "chunking"
        args.approver = "test_approver"
        args.reason = "Test approval"

        # Execute approval command
        result = handle_approve_command(args, approval_engine)

        # Verify the result
        self.assertTrue(result)

        # Check that the state was updated to CHUNKING_APPROVED
        current_state = state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.CHUNKING_APPROVED)

    def test_reject_chunking_command_integration(self):
        """
        Test the reject chunking command integration with state persistence.
        """
        # Set up state with CHUNKING_COMPLETE
        state_persistence = StatePersistence(self.state_file)
        state_persistence.update_state(PipelineState.CHUNKING_COMPLETE)

        # Create approval engine
        approval_engine = ApprovalEngine(state_persistence)

        # Create mock args for reject command
        args = argparse.Namespace()
        args.stage = "chunking"
        args.approver = "test_approver"
        args.reason = "Test rejection"

        # Execute rejection command
        result = handle_reject_command(args, approval_engine)

        # Verify the result
        self.assertTrue(result)

        # Check that the state was updated to REJECTED
        current_state = state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.REJECTED)

    def test_approve_command_with_invalid_state(self):
        """
        Test that approval commands fail when pipeline is not in the correct state.
        """
        # Set up state with IDLE (not ready for approval)
        state_persistence = StatePersistence(self.state_file)
        state_persistence.update_state(PipelineState.IDLE)

        # Create approval engine
        approval_engine = ApprovalEngine(state_persistence)

        # Create mock args for approve command
        args = argparse.Namespace()
        args.stage = "extraction"
        args.approver = "test_approver"
        args.reason = "Test approval"

        # Attempt to approve extraction when in IDLE state (should fail)
        result = handle_approve_command(args, approval_engine)

        # Verify the result is False
        self.assertFalse(result)

    def test_preview_extraction_command_integration(self):
        """
        Test the preview extraction command integration with preview service.
        """
        # Set up state with EXTRACTION_COMPLETE
        state_persistence = StatePersistence(self.state_file)
        state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)

        # Create a temporary content file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("This is test content for extraction preview.")
            content_file_path = content_file.name

        try:
            # Update state to include artifact path
            current_state_data = state_persistence.read_state()
            current_state_data["artifact_paths"] = {"extracted_content": content_file_path}
            state_persistence.write_state(current_state_data)

            # Create preview service
            preview_service = PreviewService()

            # Create mock args for preview command
            args = argparse.Namespace()
            args.stage = "extraction"
            args.offset = 0
            args.limit = 50

            # Capture the output
            captured_output = StringIO()
            sys.stdout = captured_output

            try:
                # Execute preview command
                result = handle_preview_command(args, state_persistence, preview_service)

                # Verify the result
                self.assertTrue(result)

                # Check that preview content was output
                output = captured_output.getvalue()
                self.assertIn("This is test content for extraction preview.", output)
            finally:
                sys.stdout = sys.__stdout__  # Reset stdout
        finally:
            # Clean up temporary content file
            os.remove(content_file_path)

    def test_preview_chunking_command_integration(self):
        """
        Test the preview chunking command integration with preview service.
        """
        # Set up state with CHUNKING_COMPLETE
        state_persistence = StatePersistence(self.state_file)
        state_persistence.update_state(PipelineState.CHUNKING_COMPLETE)

        # Create a temporary chunked file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as chunk_file:
            chunk_file.write("This is test chunked content for preview.")
            chunk_file_path = chunk_file.name

        try:
            # Update state to include artifact path
            current_state_data = state_persistence.read_state()
            current_state_data["artifact_paths"] = {"chunked_output": chunk_file_path}
            state_persistence.write_state(current_state_data)

            # Create preview service
            preview_service = PreviewService()

            # Create mock args for preview command
            args = argparse.Namespace()
            args.stage = "chunking"
            args.offset = 0
            args.limit = 50

            # Capture the output
            captured_output = StringIO()
            sys.stdout = captured_output

            try:
                # Execute preview command
                result = handle_preview_command(args, state_persistence, preview_service)

                # Verify the result
                self.assertTrue(result)

                # Check that preview content was output
                output = captured_output.getvalue()
                self.assertIn("This is test chunked content for preview.", output)
            finally:
                sys.stdout = sys.__stdout__  # Reset stdout
        finally:
            # Clean up temporary chunk file
            os.remove(chunk_file_path)

    def test_interactive_approve_content(self):
        """
        Test the interactive approval functionality.
        """
        # Set up state with EXTRACTION_COMPLETE
        state_persistence = StatePersistence(self.state_file)
        state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)

        # Create approval engine
        approval_engine = ApprovalEngine(state_persistence)

        # Mock user inputs for interactive approval
        with patch('builtins.input', side_effect=['test_user', '1', 'Test approval']):
            # Execute interactive approval
            result = interactive_approve_content("extraction", approval_engine)

            # Verify the result
            self.assertTrue(result)

            # Check that the state was updated to EXTRACTION_APPROVED
            current_state = state_persistence.get_current_state()
            self.assertEqual(current_state, PipelineState.EXTRACTION_APPROVED)


if __name__ == '__main__':
    unittest.main()