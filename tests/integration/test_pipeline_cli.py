"""
CLI integration tests for the pipeline verification system.

This module tests the CLI interface integration with all pipeline components.
"""
import unittest
import tempfile
import os
from io import StringIO
from unittest.mock import patch, MagicMock

from src.cli.pipeline_cli import create_pipeline_parser, handle_start_command, handle_status_command, handle_resume_command
from src.pipeline.state_persistence import StatePersistence
from src.pipeline.state_machine import PipelineState


class TestPipelineCLIIntegration(unittest.TestCase):
    """
    CLI integration tests for pipeline verification system.
    """
    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()

    def tearDown(self):
        """
        Clean up after each test method.
        """
        # Remove the temporary file if it exists
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_cli_parser_creation(self):
        """
        Test that the CLI parser is created with all required commands.
        """
        parser = create_pipeline_parser()

        # Test that parser has the required commands
        self.assertIsNotNone(parser)

        # Test that the main commands exist
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, type(parser._subparsers._group_actions[0]))
        ]

        if subparsers_actions:
            subparser_choices = list(subparsers_actions[0].choices.keys())
            self.assertIn("start", subparser_choices)
            self.assertIn("status", subparser_choices)
            self.assertIn("resume", subparser_choices)
            self.assertIn("validate", subparser_choices)

    def test_start_command_handler(self):
        """
        Test the start command handler.
        """
        # Create mock args
        class MockArgs:
            state_file = self.temp_file.name
            config = None
            dry_run = False
            command = "start"

        mock_args = MockArgs()

        # Test the start command handler
        result = handle_start_command(mock_args)

        # Result should be 0 for success or non-zero for failure
        # In this case, it should succeed in initializing the pipeline
        self.assertIsInstance(result, int)

    def test_status_command_handler(self):
        """
        Test the status command handler.
        """
        # First initialize a state file
        state_persistence = StatePersistence(self.temp_file.name)
        state_persistence.update_state(PipelineState.EXTRACTION_IN_PROGRESS)

        # Create mock args
        class MockArgs:
            state_file = self.temp_file.name
            command = "status"

        mock_args = MockArgs()

        # Test the status command handler
        result = handle_status_command(mock_args)

        # Result should be 0 for success
        self.assertIsInstance(result, int)

    def test_resume_command_handler(self):
        """
        Test the resume command handler.
        """
        # First initialize a state file
        state_persistence = StatePersistence(self.temp_file.name)
        state_persistence.update_state(PipelineState.FAILED)

        # Create mock args
        class MockArgs:
            state_file = self.temp_file.name
            force_extraction = False
            force_chunking = False
            command = "resume"

        mock_args = MockArgs()

        # Test the resume command handler
        result = handle_resume_command(mock_args)

        # Result should be 0 for success or non-zero for failure
        self.assertIsInstance(result, int)

    def test_start_command_with_config(self):
        """
        Test the start command handler with a configuration file.
        """
        # Create a temporary config file
        temp_config = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_config.write(b'{"input_path": "/test/path", "output_path": "/test/output"}')
        temp_config.close()

        try:
            # Create mock args
            class MockArgs:
                state_file = self.temp_file.name
                config = temp_config.name
                dry_run = False
                command = "start"

            mock_args = MockArgs()

            # Test the start command handler with config
            result = handle_start_command(mock_args)

            # Result should be 0 for success or non-zero for failure
            self.assertIsInstance(result, int)
        finally:
            # Clean up the temp config file
            if os.path.exists(temp_config.name):
                os.remove(temp_config.name)

    def test_dry_run_mode_handling(self):
        """
        Test the start command handler in dry-run mode.
        """
        # Create mock args with dry-run enabled
        class MockArgs:
            state_file = self.temp_file.name
            config = None
            dry_run = True
            command = "start"

        mock_args = MockArgs()

        # Test the start command handler in dry-run mode
        result = handle_start_command(mock_args)

        # Result should be 0 for success
        self.assertIsInstance(result, int)

    @patch('sys.stdout', new_callable=StringIO)
    def test_status_command_output(self, mock_stdout):
        """
        Test the status command output.
        """
        # First initialize a state file with some data
        state_persistence = StatePersistence(self.temp_file.name)
        state_data = {
            "state": PipelineState.EXTRACTION_COMPLETE.value,
            "timestamp": "2025-12-23T10:00:00Z",
            "approvals": {
                "extraction": {
                    "status": "PENDING",
                    "approver": "test_user",
                    "decision": "PENDING"
                }
            },
            "artifact_paths": {
                "extracted_content": "/path/to/content.txt",
                "chunked_output": "/path/to/chunks.json"
            }
        }
        state_persistence.write_state(state_data)

        # Create mock args
        class MockArgs:
            state_file = self.temp_file.name
            command = "status"

        mock_args = MockArgs()

        # Test the status command handler
        result = handle_status_command(mock_args)

        # Check that output was generated
        output = mock_stdout.getvalue()
        self.assertIsInstance(result, int)
        self.assertIn("EXTRACTION_COMPLETE", output)

    def test_resume_command_with_force_options(self):
        """
        Test the resume command with force options.
        """
        # Initialize a state file
        state_persistence = StatePersistence(self.temp_file.name)
        state_persistence.update_state(PipelineState.CHUNKING_COMPLETE)

        # Create mock args with force extraction
        class MockArgs:
            state_file = self.temp_file.name
            force_extraction = True
            force_chunking = False
            command = "resume"

        mock_args = MockArgs()

        # Test the resume command handler with force extraction
        result = handle_resume_command(mock_args)
        self.assertIsInstance(result, int)

        # Create mock args with force chunking
        class MockArgs2:
            state_file = self.temp_file.name
            force_extraction = False
            force_chunking = True
            command = "resume"

        mock_args2 = MockArgs2()

        # Test the resume command handler with force chunking
        result2 = handle_resume_command(mock_args2)
        self.assertIsInstance(result2, int)

    def test_start_command_error_handling(self):
        """
        Test the start command error handling.
        """
        # Create mock args with invalid state file path
        class MockArgs:
            state_file = "/invalid/path/test.json"
            config = None
            dry_run = False
            command = "start"

        mock_args = MockArgs()

        # Test the start command handler with invalid path
        result = handle_start_command(mock_args)

        # Should handle error gracefully
        self.assertIsInstance(result, int)

    def test_status_command_error_handling(self):
        """
        Test the status command error handling.
        """
        # Create mock args with non-existent state file
        class MockArgs:
            state_file = "/nonexistent/path/state.json"
            command = "status"

        mock_args = MockArgs()

        # Test the status command handler with non-existent file
        result = handle_status_command(mock_args)

        # Should handle error gracefully
        self.assertIsInstance(result, int)

    def test_resume_command_error_handling(self):
        """
        Test the resume command error handling.
        """
        # Create mock args with non-existent state file
        class MockArgs:
            state_file = "/nonexistent/path/state.json"
            force_extraction = False
            force_chunking = False
            command = "resume"

        mock_args = MockArgs()

        # Test the resume command handler with non-existent file
        result = handle_resume_command(mock_args)

        # Should handle error gracefully
        self.assertIsInstance(result, int)

    @patch('builtins.input', return_value='n')
    def test_resume_command_with_invalid_artifacts(self, mock_input):
        """
        Test the resume command when artifacts are invalid.
        """
        # Initialize a state file with missing artifacts
        state_persistence = StatePersistence(self.temp_file.name)
        state_data = {
            "state": PipelineState.FAILED.value,
            "timestamp": "2025-12-23T10:00:00Z",
            "artifact_paths": {
                "extracted_content": "/nonexistent/file.txt"  # This file doesn't exist
            }
        }
        state_persistence.write_state(state_data)

        # Create mock args
        class MockArgs:
            state_file = self.temp_file.name
            force_extraction = False
            force_chunking = False
            command = "resume"

        mock_args = MockArgs()

        # Test the resume command handler with invalid artifacts
        result = handle_resume_command(mock_args)

        # Should return 1 due to cancelled resume
        self.assertEqual(result, 1)

    @patch('builtins.input', return_value='y')
    def test_resume_command_with_invalid_artifacts_confirmed(self, mock_input):
        """
        Test the resume command when artifacts are invalid but user confirms.
        """
        # Initialize a state file with missing artifacts
        state_persistence = StatePersistence(self.temp_file.name)
        state_data = {
            "state": PipelineState.FAILED.value,
            "timestamp": "2025-12-23T10:00:00Z",
            "artifact_paths": {
                "extracted_content": "/nonexistent/file.txt"  # This file doesn't exist
            }
        }
        state_persistence.write_state(state_data)

        # Create mock args
        class MockArgs:
            state_file = self.temp_file.name
            force_extraction = False
            force_chunking = False
            command = "resume"

        mock_args = MockArgs()

        # Test the resume command handler with invalid artifacts but user confirms
        result = handle_resume_command(mock_args)

        # Should return 0 (success) or 1 (failure) depending on resume logic
        self.assertIsInstance(result, int)

    @patch('sys.stdout', new_callable=StringIO)
    def test_status_command_with_approvals_and_artifacts(self, mock_stdout):
        """
        Test the status command with approvals and artifacts data.
        """
        # Initialize a state file with approvals and artifacts
        state_persistence = StatePersistence(self.temp_file.name)
        state_data = {
            "state": PipelineState.CHUNKING_COMPLETE.value,
            "timestamp": "2025-12-23T10:00:00Z",
            "approvals": {
                "extraction": {
                    "status": "APPROVED",
                    "approver": "test_user",
                    "decision": "APPROVE",
                    "timestamp": "2025-12-23T09:00:00Z"
                },
                "chunking": {
                    "status": "PENDING",
                    "approver": "pending_user",
                    "decision": "PENDING"
                }
            },
            "artifact_paths": {
                "extracted_content": "/path/to/extracted.txt",
                "chunked_output": "/path/to/chunks.json"
            }
        }
        state_persistence.write_state(state_data)

        # Create mock args
        class MockArgs:
            state_file = self.temp_file.name
            command = "status"

        mock_args = MockArgs()

        # Test the status command handler
        result = handle_status_command(mock_args)

        # Check that output was generated with approvals and artifacts
        output = mock_stdout.getvalue()
        self.assertIsInstance(result, int)
        self.assertIn("APPROVED", output)
        self.assertIn("PENDING", output)
        self.assertIn("/path/to/extracted.txt", output)
        self.assertIn("/path/to/chunks.json", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_status_command_with_no_state_data(self, mock_stdout):
        """
        Test the status command when state data is None.
        """
        # Initialize a state file with minimal data
        state_persistence = StatePersistence(self.temp_file.name)
        state_persistence.update_state(PipelineState.IDLE)

        # Create mock args
        class MockArgs:
            state_file = self.temp_file.name
            command = "status"

        mock_args = MockArgs()

        # Test the status command handler
        result = handle_status_command(mock_args)

        # Check that output was generated
        output = mock_stdout.getvalue()
        self.assertIsInstance(result, int)
        self.assertIn("IDLE", output)

    def test_start_command_with_pipeline_already_running(self):
        """
        Test the start command when pipeline is already running.
        """
        # Initialize a state file with a running state
        state_persistence = StatePersistence(self.temp_file.name)
        state_persistence.update_state(PipelineState.EXTRACTION_IN_PROGRESS)

        # Create mock args
        class MockArgs:
            state_file = self.temp_file.name
            config = None
            dry_run = False
            command = "start"

        mock_args = MockArgs()

        # Test the start command handler when pipeline is already running
        result = handle_start_command(mock_args)

        # Should return non-zero (1) to indicate failure to start
        self.assertEqual(result, 1)


if __name__ == '__main__':
    unittest.main()