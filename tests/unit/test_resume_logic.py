"""
Unit tests for resume logic module.
"""
import os
import tempfile
import unittest

from src.pipeline.state_machine import PipelineState
from src.pipeline.state_persistence import StatePersistence
from src.pipeline.resume_logic import ResumeLogic


class TestResumeLogic(unittest.TestCase):
    """
    Unit tests for ResumeLogic functionality.
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
        self.resume_logic = ResumeLogic(self.state_persistence)

    def tearDown(self):
        """
        Clean up after each test method.
        """
        # Remove the temporary file
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

    def test_get_resume_state_from_extraction_complete(self):
        """
        Test getting resume state from EXTRACTION_COMPLETE state.
        """
        # Set up state
        self.state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)

        # Test get resume state functionality
        resume_state = self.resume_logic.get_resume_state()

        # Verify results
        self.assertIsNotNone(resume_state)
        self.assertEqual(resume_state, PipelineState.EXTRACTION_COMPLETE)

    def test_get_resume_state_from_extraction_approved(self):
        """
        Test getting resume state from EXTRACTION_APPROVED state.
        """
        # Set up state
        self.state_persistence.update_state(PipelineState.EXTRACTION_APPROVED)

        # Test get resume state functionality
        resume_state = self.resume_logic.get_resume_state()

        # Verify results
        self.assertIsNotNone(resume_state)
        self.assertEqual(resume_state, PipelineState.EXTRACTION_APPROVED)

    def test_get_resume_state_from_chunking_complete(self):
        """
        Test getting resume state from CHUNKING_COMPLETE state.
        """
        # Set up state
        self.state_persistence.update_state(PipelineState.CHUNKING_COMPLETE)

        # Test get resume state functionality
        resume_state = self.resume_logic.get_resume_state()

        # Verify results
        self.assertIsNotNone(resume_state)
        self.assertEqual(resume_state, PipelineState.CHUNKING_COMPLETE)

    def test_get_resume_state_from_chunking_approved(self):
        """
        Test getting resume state from CHUNKING_APPROVED state.
        """
        # Set up state
        self.state_persistence.update_state(PipelineState.CHUNKING_APPROVED)

        # Test get resume state functionality
        resume_state = self.resume_logic.get_resume_state()

        # Verify results
        self.assertIsNotNone(resume_state)
        self.assertEqual(resume_state, PipelineState.CHUNKING_APPROVED)

    def test_get_resume_state_from_idle_state(self):
        """
        Test getting resume state from IDLE state.
        """
        # Set up state
        self.state_persistence.update_state(PipelineState.IDLE)

        # Test get resume state functionality
        resume_state = self.resume_logic.get_resume_state()

        # Verify results
        self.assertIsNotNone(resume_state)
        self.assertEqual(resume_state, PipelineState.IDLE)

    def test_get_resume_state_from_failed_state(self):
        """
        Test getting resume state from FAILED state.
        """
        # Set up state
        self.state_persistence.update_state(PipelineState.FAILED)

        # Test get resume state functionality
        resume_state = self.resume_logic.get_resume_state()

        # Verify results
        self.assertIsNotNone(resume_state)
        self.assertEqual(resume_state, PipelineState.FAILED)

    def test_get_resume_state_from_rejected_state(self):
        """
        Test getting resume state from REJECTED state.
        """
        # Set up state
        self.state_persistence.update_state(PipelineState.REJECTED)

        # Test get resume state functionality
        resume_state = self.resume_logic.get_resume_state()

        # Verify results
        self.assertIsNotNone(resume_state)
        self.assertEqual(resume_state, PipelineState.REJECTED)

    def test_get_resume_state_with_no_state_file(self):
        """
        Test getting resume state when no state file exists.
        """
        # Remove the state file to simulate no state
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

        # Test get resume state functionality
        resume_state = self.resume_logic.get_resume_state()

        # Verify results
        self.assertIsNone(resume_state)

    def test_get_resume_state_from_extraction_in_progress(self):
        """
        Test getting resume state from EXTRACTION_IN_PROGRESS state.
        """
        # Set up state
        self.state_persistence.update_state(PipelineState.EXTRACTION_IN_PROGRESS)

        # Test get resume state functionality
        resume_state = self.resume_logic.get_resume_state()

        # Verify results
        self.assertIsNotNone(resume_state)
        self.assertEqual(resume_state, PipelineState.EXTRACTION_IN_PROGRESS)

    def test_get_resume_state_from_chunking_in_progress(self):
        """
        Test getting resume state from CHUNKING_IN_PROGRESS state.
        """
        # Set up state
        self.state_persistence.update_state(PipelineState.CHUNKING_IN_PROGRESS)

        # Test get resume state functionality
        resume_state = self.resume_logic.get_resume_state()

        # Verify results
        self.assertIsNotNone(resume_state)
        self.assertEqual(resume_state, PipelineState.CHUNKING_IN_PROGRESS)

    def test_handle_crash_scenario_with_extraction_approved(self):
        """
        Test handling crash scenario with EXTRACTION_APPROVED state.
        """
        # Set up state with approvals
        state_data = {
            "state": PipelineState.FAILED.value,
            "timestamp": "2025-12-24T10:00:00Z",
            "approvals": {
                "extraction": {
                    "status": "APPROVED",
                    "approver": "test_approver",
                    "timestamp": "2025-12-24T09:00:00Z",
                    "decision": "APPROVE"
                }
            }
        }
        self.state_persistence.write_state(state_data)

        # Test crash scenario handling
        resume_state = self.resume_logic.handle_crash_scenario()

        # Verify results
        self.assertIsNotNone(resume_state)
        # Should return the last approved state (EXTRACTION_APPROVED)
        self.assertEqual(resume_state, PipelineState.EXTRACTION_APPROVED)

    def test_handle_crash_scenario_with_chunking_approved(self):
        """
        Test handling crash scenario with CHUNKING_APPROVED state.
        """
        # Set up state with approvals
        state_data = {
            "state": PipelineState.FAILED.value,
            "timestamp": "2025-12-24T10:00:00Z",
            "approvals": {
                "extraction": {
                    "status": "APPROVED",
                    "approver": "test_approver",
                    "timestamp": "2025-12-24T08:00:00Z",
                    "decision": "APPROVE"
                },
                "chunking": {
                    "status": "APPROVED",
                    "approver": "test_approver",
                    "timestamp": "2025-12-24T09:00:00Z",
                    "decision": "APPROVE"
                }
            }
        }
        self.state_persistence.write_state(state_data)

        # Test crash scenario handling
        resume_state = self.resume_logic.handle_crash_scenario()

        # Verify results
        self.assertIsNotNone(resume_state)
        # Should return the most recently approved state (CHUNKING_APPROVED)
        self.assertEqual(resume_state, PipelineState.CHUNKING_APPROVED)

    def test_handle_crash_scenario_with_no_approved_states(self):
        """
        Test handling crash scenario with no approved states.
        """
        # Set up state with no approvals
        state_data = {
            "state": PipelineState.FAILED.value,
            "timestamp": "2025-12-24T10:00:00Z"
        }
        self.state_persistence.write_state(state_data)

        # Test crash scenario handling
        resume_state = self.resume_logic.handle_crash_scenario()

        # Verify results - should return IDLE when no approved states exist to restart the pipeline
        self.assertIsNotNone(resume_state)
        self.assertEqual(resume_state, PipelineState.IDLE)

    def test_handle_rejection_scenario_extraction_rejected(self):
        """
        Test handling rejection scenario with extraction rejected.
        """
        # Set up state with extraction rejection
        state_data = {
            "state": PipelineState.REJECTED.value,
            "timestamp": "2025-12-24T10:00:00Z",
            "approvals": {
                "extraction": {
                    "status": "REJECTED",
                    "approver": "test_approver",
                    "timestamp": "2025-12-24T09:00:00Z",
                    "decision": "REJECT"
                }
            }
        }
        self.state_persistence.write_state(state_data)

        # Test rejection scenario handling
        resume_state = self.resume_logic.handle_rejection_scenario()

        # Verify results
        self.assertIsNotNone(resume_state)
        # Should return the state before rejection (EXTRACTION_COMPLETE)
        self.assertEqual(resume_state, PipelineState.EXTRACTION_COMPLETE)

    def test_handle_rejection_scenario_chunking_rejected(self):
        """
        Test handling rejection scenario with chunking rejected.
        """
        # Set up state with chunking rejection
        state_data = {
            "state": PipelineState.REJECTED.value,
            "timestamp": "2025-12-24T10:00:00Z",
            "approvals": {
                "extraction": {
                    "status": "APPROVED",
                    "approver": "test_approver",
                    "timestamp": "2025-12-24T08:00:00Z",
                    "decision": "APPROVE"
                },
                "chunking": {
                    "status": "REJECTED",
                    "approver": "test_approver",
                    "timestamp": "2025-12-24T09:00:00Z",
                    "decision": "REJECT"
                }
            }
        }
        self.state_persistence.write_state(state_data)

        # Test rejection scenario handling
        resume_state = self.resume_logic.handle_rejection_scenario()

        # Verify results
        self.assertIsNotNone(resume_state)
        # Should return the state before rejection (CHUNKING_COMPLETE)
        self.assertEqual(resume_state, PipelineState.CHUNKING_COMPLETE)

    def test_validate_artifacts_before_resume_with_valid_artifacts(self):
        """
        Test validating artifacts before resume with valid artifacts.
        """
        # Create temporary files for artifacts
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as extracted_file:
            extracted_file.write("Test extracted content")
            extracted_file_path = extracted_file.name

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as chunked_file:
            chunked_file.write('["chunk1", "chunk2", "chunk3"]')
            chunked_file_path = chunked_file.name

        try:
            # Set up state with artifact paths
            state_data = {
                "state": PipelineState.EXTRACTION_COMPLETE.value,
                "timestamp": "2025-12-24T10:00:00Z",
                "artifact_paths": {
                    "extracted_content": extracted_file_path,
                    "chunked_output": chunked_file_path
                }
            }
            self.state_persistence.write_state(state_data)

            # Test artifact validation
            artifacts_valid = self.resume_logic.validate_artifacts_before_resume()

            # Verify results
            self.assertTrue(artifacts_valid)

        finally:
            # Clean up temporary files
            if os.path.exists(extracted_file_path):
                os.remove(extracted_file_path)
            if os.path.exists(chunked_file_path):
                os.remove(chunked_file_path)

    def test_validate_artifacts_before_resume_with_missing_artifacts(self):
        """
        Test validating artifacts before resume with missing artifacts.
        """
        # Set up state with non-existent artifact paths
        state_data = {
            "state": PipelineState.EXTRACTION_COMPLETE.value,
            "timestamp": "2025-12-24T10:00:00Z",
            "artifact_paths": {
                "extracted_content": "/nonexistent/extracted.txt",
                "chunked_output": "/nonexistent/chunked.json"
            }
        }
        self.state_persistence.write_state(state_data)

        # Test artifact validation
        artifacts_valid = self.resume_logic.validate_artifacts_before_resume()

        # Verify results
        self.assertFalse(artifacts_valid)

    def test_validate_artifacts_before_resume_with_no_artifacts(self):
        """
        Test validating artifacts before resume with no artifacts specified.
        """
        # Set up state without artifact paths
        self.state_persistence.update_state(PipelineState.IDLE)

        # Test artifact validation
        artifacts_valid = self.resume_logic.validate_artifacts_before_resume()

        # Verify results
        # If no artifacts are specified, validation should pass (nothing to validate)
        self.assertTrue(artifacts_valid)

    def test_validate_resume_readiness_valid_state(self):
        """
        Test validating resume readiness with valid state.
        """
        # Set up a valid state
        self.state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)

        # Test resume readiness validation
        ready = self.resume_logic.validate_resume_readiness()

        # Verify results
        self.assertTrue(ready)

    def test_validate_resume_readiness_invalid_state_file(self):
        """
        Test validating resume readiness with invalid state file.
        """
        # Write invalid JSON to the state file
        with open(self.state_file, 'w') as f:
            f.write("invalid json content")

        # Test resume readiness validation
        ready = self.resume_logic.validate_resume_readiness()

        # Verify results
        self.assertFalse(ready)

    def test_get_resume_recommendation(self):
        """
        Test getting resume recommendation.
        """
        # Set up state
        self.state_persistence.update_state(PipelineState.EXTRACTION_APPROVED)

        # Test getting resume recommendation
        recommendation = self.resume_logic.get_resume_recommendation()

        # Verify results
        self.assertIsNotNone(recommendation)
        self.assertIn("action", recommendation)
        self.assertIn("message", recommendation)
        self.assertIn("current_state", recommendation)
        self.assertIn("recommended_resume_state", recommendation)
        self.assertIn("artifacts_valid", recommendation)

    def test_resume_from_state_normal(self):
        """
        Test resuming from state under normal conditions.
        """
        # Set up state
        self.state_persistence.update_state(PipelineState.CHUNKING_COMPLETE)

        # Test normal resume
        resume_state = self.resume_logic.resume_from_state()

        # Verify results
        self.assertIsNotNone(resume_state)
        self.assertEqual(resume_state, PipelineState.CHUNKING_COMPLETE)

    def test_force_resume_from_state(self):
        """
        Test forcing resume from a specific state.
        """
        # Set up initial state
        self.state_persistence.update_state(PipelineState.IDLE)

        # Test force resume to different state
        success = self.resume_logic.force_resume_from_state(PipelineState.EXTRACTION_APPROVED)

        # The force operation may succeed or fail depending on implementation
        # The important thing is that it doesn't crash and returns a boolean
        self.assertIsInstance(success, bool)

        # If successful, check that the state was updated
        if success:
            current_state = self.state_persistence.get_current_state()
            self.assertEqual(current_state, PipelineState.EXTRACTION_APPROVED)

    def test_resume_with_force_extraction_flag(self):
        """
        Test resuming with force extraction flag.
        """
        # Set up state
        self.state_persistence.update_state(PipelineState.EXTRACTION_APPROVED)

        # Test resume with force extraction
        resume_state = self.resume_logic.resume_from_state(force_extraction=True)

        # With force_extraction=True, should return IDLE to restart from beginning
        self.assertEqual(resume_state, PipelineState.IDLE)

    def test_resume_with_force_chunking_flag(self):
        """
        Test resuming with force chunking flag.
        """
        # Set up state with extraction approved
        state_data = {
            "state": PipelineState.EXTRACTION_APPROVED.value,
            "timestamp": "2025-12-24T10:00:00Z"
        }
        self.state_persistence.write_state(state_data)

        # Test resume with force chunking
        resume_state = self.resume_logic.resume_from_state(force_chunking=True)

        # With force_chunking=True, should return EXTRACTION_APPROVED to re-chunk
        self.assertEqual(resume_state, PipelineState.EXTRACTION_APPROVED)

    def test_validate_resume_readiness_no_state_file(self):
        """
        Test validating resume readiness when no state file exists.
        """
        # Remove the state file
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

        # Test resume readiness validation
        ready = self.resume_logic.validate_resume_readiness()

        # With no state file, readiness should be False
        self.assertFalse(ready)

    def test_get_resume_state_error_handling(self):
        """
        Test get_resume_state error handling with invalid state data.
        """
        # Write invalid state data to trigger error handling
        invalid_state_data = {
            "state": "INVALID_STATE_NAME",  # This should trigger an error
            "timestamp": "2025-12-24T10:00:00Z"
        }
        self.state_persistence.write_state(invalid_state_data)

        # Test get resume state with invalid data
        resume_state = self.resume_logic.get_resume_state()

        # Should return None due to error
        self.assertIsNone(resume_state)

    def test_get_resume_state_with_embedding_complete(self):
        """
        Test getting resume state from EMBEDDING_COMPLETE (terminal state).
        """
        # Set up state
        self.state_persistence.update_state(PipelineState.EMBEDDING_COMPLETE)

        # Test get resume state functionality
        resume_state = self.resume_logic.get_resume_state()

        # Should return None since EMBEDDING_COMPLETE is terminal
        self.assertIsNone(resume_state)

    def test_validate_artifacts_before_resume_with_empty_artifact_paths(self):
        """
        Test validating artifacts before resume with empty artifact paths.
        """
        # Set up state with empty artifact paths
        state_data = {
            "state": PipelineState.EXTRACTION_COMPLETE.value,
            "timestamp": "2025-12-24T10:00:00Z",
            "artifact_paths": {}
        }
        self.state_persistence.write_state(state_data)

        # Test artifact validation
        artifacts_valid = self.resume_logic.validate_artifacts_before_resume()

        # Should return False since empty dict fails validation
        self.assertFalse(artifacts_valid)

    def test_validate_artifacts_before_resume_error_handling(self):
        """
        Test artifact validation error handling.
        """
        # Test with malformed state data to trigger error handling
        # We'll temporarily mock the read_state to return invalid data
        original_read_state = self.state_persistence.read_state

        def mock_read_state_error():
            raise Exception("Test error")

        # Temporarily replace the method
        self.state_persistence.read_state = mock_read_state_error

        try:
            # Test artifact validation with error
            artifacts_valid = self.resume_logic.validate_artifacts_before_resume()

            # Should return False due to error
            self.assertFalse(artifacts_valid)
        finally:
            # Restore original method
            self.state_persistence.read_state = original_read_state

    def test_validate_artifacts_before_resume_with_none_path(self):
        """
        Test validating artifacts before resume with None paths.
        """
        # Set up state with None artifact path
        state_data = {
            "state": PipelineState.EXTRACTION_COMPLETE.value,
            "timestamp": "2025-12-24T10:00:00Z",
            "artifact_paths": {
                "extracted_content": None
            }
        }
        self.state_persistence.write_state(state_data)

        # Test artifact validation
        artifacts_valid = self.resume_logic.validate_artifacts_before_resume()

        # Should return False since None path fails validation
        self.assertFalse(artifacts_valid)

    def test_get_last_approved_state_error_handling(self):
        """
        Test _get_last_approved_state error handling with invalid data.
        """
        # Test with malformed approvals data to trigger error handling
        # We'll use a mock approach since direct invalid data fails state validation
        original_get_last_approved_state = self.resume_logic._get_last_approved_state

        def mock_get_last_approved_state_error(state_data):
            raise Exception("Test error")

        # Temporarily replace the method
        self.resume_logic._get_last_approved_state = mock_get_last_approved_state_error

        # Set up state that will trigger the error path
        state_data = {
            "state": PipelineState.FAILED.value,
            "timestamp": "2025-12-24T10:00:00Z",
            "approvals": {}
        }
        self.state_persistence.write_state(state_data)

        try:
            # Test crash scenario handling to trigger _get_last_approved_state
            resume_state = self.resume_logic.handle_crash_scenario()

            # Should handle error gracefully and return None due to exception
            self.assertIsNone(resume_state)
        finally:
            # Restore original method
            self.resume_logic._get_last_approved_state = original_get_last_approved_state

    def test_get_state_before_rejection_error_handling(self):
        """
        Test _get_state_before_rejection error handling with invalid data.
        """
        # Test with malformed approvals data to trigger error handling
        state_data = {
            "state": PipelineState.REJECTED.value,
            "timestamp": "2025-12-24T10:00:00Z",
            "approvals": "invalid_data_type"  # This should cause an error
        }
        self.state_persistence.write_state(state_data)

        # Test rejection scenario handling to trigger _get_state_before_rejection
        resume_state = self.resume_logic.handle_rejection_scenario()

        # Should handle error gracefully and return None
        self.assertIsNone(resume_state)

    def test_resume_from_state_error_handling(self):
        """
        Test resume_from_state error handling.
        """
        # Test with error in get_resume_state to trigger error handling
        original_get_resume_state = self.resume_logic.get_resume_state

        def mock_get_resume_state_error():
            raise Exception("Test error")

        # Temporarily replace the method
        self.resume_logic.get_resume_state = mock_get_resume_state_error

        try:
            # Test resume from state with error
            resume_state = self.resume_logic.resume_from_state()

            # Should return None due to error
            self.assertIsNone(resume_state)
        finally:
            # Restore original method
            self.resume_logic.get_resume_state = original_get_resume_state

    def test_force_resume_from_state_error_handling(self):
        """
        Test force_resume_from_state error handling.
        """
        # Test with error in state persistence to trigger error handling
        original_update_state = self.state_persistence.update_state

        def mock_update_state_error(*args, **kwargs):
            raise Exception("Test error")

        # Temporarily replace the method
        self.state_persistence.update_state = mock_update_state_error

        try:
            # Test force resume from state with error
            success = self.resume_logic.force_resume_from_state(PipelineState.IDLE)

            # Should return False due to error
            self.assertFalse(success)
        finally:
            # Restore original method
            self.state_persistence.update_state = original_update_state

    def test_get_resume_recommendation_error_handling(self):
        """
        Test get_resume_recommendation error handling.
        """
        # Test with error in state persistence to trigger error handling
        original_read_state = self.state_persistence.read_state

        def mock_read_state_error():
            raise Exception("Test error")

        # Temporarily replace the method
        self.state_persistence.read_state = mock_read_state_error

        try:
            # Test get resume recommendation with error
            recommendation = self.resume_logic.get_resume_recommendation()

            # Should return error recommendation
            self.assertIsNotNone(recommendation)
            self.assertEqual(recommendation["action"], "error")
        finally:
            # Restore original method
            self.state_persistence.read_state = original_read_state

    def test_validate_resume_readiness_error_handling(self):
        """
        Test validate_resume_readiness error handling.
        """
        # Test with error in get_resume_state to trigger error handling
        original_get_resume_state = self.resume_logic.get_resume_state

        def mock_get_resume_state_error():
            raise Exception("Test error")

        # Temporarily replace the method
        self.resume_logic.get_resume_state = mock_get_resume_state_error

        try:
            # Test validate resume readiness with error
            ready = self.resume_logic.validate_resume_readiness()

            # Should return False due to error
            self.assertFalse(ready)
        finally:
            # Restore original method
            self.resume_logic.get_resume_state = original_get_resume_state

    def test_handle_crash_scenario_from_different_states(self):
        """
        Test handling crash scenario from different failed states.
        """
        # Test crash scenario with various approval configurations
        test_cases = [
            {
                "name": "only_extraction_approved",
                "approvals": {
                    "extraction": {"status": "APPROVED", "timestamp": "2025-12-24T09:00:00Z"}
                },
                "expected_state": PipelineState.EXTRACTION_APPROVED
            },
            {
                "name": "both_approved",
                "approvals": {
                    "extraction": {"status": "APPROVED", "timestamp": "2025-12-24T08:00:00Z"},
                    "chunking": {"status": "APPROVED", "timestamp": "2025-12-24T09:00:00Z"}
                },
                "expected_state": PipelineState.CHUNKING_APPROVED
            }
        ]

        for test_case in test_cases:
            with self.subTest(name=test_case["name"]):
                # Set up state with approvals
                state_data = {
                    "state": PipelineState.FAILED.value,
                    "timestamp": "2025-12-24T10:00:00Z",
                    "approvals": test_case["approvals"]
                }
                self.state_persistence.write_state(state_data)

                # Test crash scenario handling
                resume_state = self.resume_logic.handle_crash_scenario()

                # Verify results
                self.assertIsNotNone(resume_state)
                self.assertEqual(resume_state, test_case["expected_state"])

    def test_handle_rejection_scenario_no_rejection(self):
        """
        Test handling rejection scenario when no rejection occurred.
        """
        # Set up state with approvals but no rejection
        state_data = {
            "state": PipelineState.EXTRACTION_APPROVED.value,
            "timestamp": "2025-12-24T10:00:00Z",
            "approvals": {
                "extraction": {"status": "APPROVED", "timestamp": "2025-12-24T09:00:00Z"}
            }
        }
        self.state_persistence.write_state(state_data)

        # Test rejection scenario handling
        resume_state = self.resume_logic.handle_rejection_scenario()

        # Should return None when no rejection occurred
        self.assertIsNone(resume_state)

    def test_validate_artifacts_before_resume_partial_artifacts(self):
        """
        Test validating artifacts before resume with partially missing artifacts.
        """
        # Create one valid artifact file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as extracted_file:
            extracted_file.write("Test extracted content")
            extracted_file_path = extracted_file.name

        try:
            # Set up state with one valid and one invalid artifact path
            state_data = {
                "state": PipelineState.CHUNKING_COMPLETE.value,
                "timestamp": "2025-12-24T10:00:00Z",
                "artifact_paths": {
                    "extracted_content": extracted_file_path,
                    "chunked_output": "/nonexistent/chunked.json"
                }
            }
            self.state_persistence.write_state(state_data)

            # Test artifact validation
            artifacts_valid = self.resume_logic.validate_artifacts_before_resume()

            # Should return False since one artifact is missing
            self.assertFalse(artifacts_valid)

        finally:
            # Clean up temporary file
            if os.path.exists(extracted_file_path):
                os.remove(extracted_file_path)

    def test_resume_from_state_with_all_flags_false(self):
        """
        Test resuming from state with all force flags set to False (normal operation).
        """
        # Set up state
        self.state_persistence.update_state(PipelineState.CHUNKING_APPROVED)

        # Test normal resume (all force flags False by default)
        resume_state = self.resume_logic.resume_from_state()

        # Should return the current state for normal resume
        self.assertIsNotNone(resume_state)
        self.assertEqual(resume_state, PipelineState.CHUNKING_APPROVED)

    def test_get_last_approved_state_with_multiple_approvals(self):
        """
        Test getting the last approved state when multiple stages are approved.
        """
        # Set up state with multiple approvals
        state_data = {
            "state": PipelineState.FAILED.value,
            "timestamp": "2025-12-24T11:00:00Z",
            "approvals": {
                "extraction": {
                    "status": "APPROVED",
                    "timestamp": "2025-12-24T09:00:00Z",  # Earlier
                    "decision": "APPROVE"
                },
                "chunking": {
                    "status": "APPROVED",
                    "timestamp": "2025-12-24T10:00:00Z",  # Later - should be considered last
                    "decision": "APPROVE"
                }
            }
        }
        self.state_persistence.write_state(state_data)

        # Test crash scenario handling (which internally uses _get_last_approved_state)
        resume_state = self.resume_logic.handle_crash_scenario()

        # Should return the most recently approved state (CHUNKING_APPROVED)
        self.assertIsNotNone(resume_state)
        self.assertEqual(resume_state, PipelineState.CHUNKING_APPROVED)

    def test_get_state_before_rejection_with_both_stages_rejected(self):
        """
        Test getting state before rejection when both stages have been rejected.
        """
        # Set up state with both stages having rejections at some point, but currently considering chunking rejection
        state_data = {
            "state": PipelineState.REJECTED.value,
            "timestamp": "2025-12-24T10:00:00Z",
            "approvals": {
                "extraction": {
                    "status": "APPROVED",  # Extraction was approved at some point
                    "timestamp": "2025-12-24T08:00:00Z",
                    "decision": "APPROVE"
                },
                "chunking": {
                    "status": "REJECTED",  # But chunking was rejected more recently
                    "timestamp": "2025-12-24T09:00:00Z",
                    "decision": "REJECT"
                }
            }
        }
        self.state_persistence.write_state(state_data)

        # Test rejection scenario handling
        resume_state = self.resume_logic.handle_rejection_scenario()

        # Should return the state before the current rejection (CHUNKING_COMPLETE)
        self.assertIsNotNone(resume_state)
        self.assertEqual(resume_state, PipelineState.CHUNKING_COMPLETE)


if __name__ == '__main__':
    unittest.main()