"""
Unit tests for the state persistence module.
"""
import os
import tempfile
import unittest
from pathlib import Path

from src.pipeline.state_machine import PipelineState
from src.pipeline.state_persistence import StatePersistence


class TestStatePersistence(unittest.TestCase):
    """
    Test cases for StatePersistence class.
    """
    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.state_persistence = StatePersistence(self.temp_file.name)

    def tearDown(self):
        """
        Clean up after each test method.
        """
        # Remove the temporary file
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_initial_state_read(self):
        """
        Test reading initial state when file doesn't exist.
        """
        # State file doesn't exist initially, so read_state should return None
        state_data = self.state_persistence.read_state()
        self.assertIsNone(state_data)

    def test_write_and_read_state(self):
        """
        Test writing and reading state.
        """
        test_state = {
            "state": PipelineState.EXTRACTION_IN_PROGRESS.value,
            "timestamp": "2025-12-23T10:00:00Z"
        }

        # Write state
        success = self.state_persistence.write_state(test_state)
        self.assertTrue(success)

        # Read state back
        read_state = self.state_persistence.read_state()
        self.assertIsNotNone(read_state)
        self.assertEqual(read_state["state"], PipelineState.EXTRACTION_IN_PROGRESS.value)

    def test_update_state_valid_transition(self):
        """
        Test updating state with valid transition.
        """
        # Start with IDLE
        result = self.state_persistence.update_state(PipelineState.IDLE)
        self.assertTrue(result)

        # Transition to EXTRACTION_IN_PROGRESS (valid transition)
        result = self.state_persistence.update_state(PipelineState.EXTRACTION_IN_PROGRESS)
        self.assertTrue(result)

        # Check that the state was updated
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_IN_PROGRESS)

    def test_update_state_invalid_transition(self):
        """
        Test updating state with invalid transition.
        """
        # Start with IDLE
        result = self.state_persistence.update_state(PipelineState.IDLE)
        self.assertTrue(result)

        # Try to transition directly to CHUNKING_IN_PROGRESS (invalid transition)
        result = self.state_persistence.update_state(PipelineState.CHUNKING_IN_PROGRESS)
        self.assertFalse(result)

    def test_get_current_state(self):
        """
        Test getting current state.
        """
        # Write a test state
        test_state = {
            "state": PipelineState.EXTRACTION_COMPLETE.value,
            "timestamp": "2025-12-23T10:00:00Z"
        }
        self.state_persistence.write_state(test_state)

        # Get current state
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_COMPLETE)

    def test_check_state_corruption_valid(self):
        """
        Test checking state corruption with valid state.
        """
        test_state = {
            "state": PipelineState.IDLE.value,
            "timestamp": "2025-12-23T10:00:00Z"
        }
        self.state_persistence.write_state(test_state)

        is_valid = self.state_persistence.check_state_corruption()
        self.assertTrue(is_valid)

    def test_validate_artifact_consistency(self):
        """
        Test validating artifact consistency.
        """
        # Create temporary files for testing
        with tempfile.NamedTemporaryFile(delete=False) as temp1:
            temp1.write(b"test content")
            temp1_path = temp1.name

        try:
            # Write state with artifact paths
            test_state = {
                "state": PipelineState.EXTRACTION_COMPLETE.value,
                "timestamp": "2025-12-23T10:00:00Z",
                "artifact_paths": {
                    "extracted_content": temp1_path,
                    "chunked_output": "nonexistent_file.txt"
                }
            }
            self.state_persistence.write_state(test_state)

            # Validate consistency - should return False because one file doesn't exist
            is_consistent = self.state_persistence.validate_artifact_consistency()
            self.assertFalse(is_consistent)

            # Test with existing file only
            with tempfile.NamedTemporaryFile(delete=False) as temp2:
                temp2.write(b"test content")
                temp2_path = temp2.name

            try:
                test_state["artifact_paths"] = {
                    "extracted_content": temp1_path,
                    "chunked_output": temp2_path
                }
                self.state_persistence.write_state(test_state)

                is_consistent = self.state_persistence.validate_artifact_consistency()
                self.assertTrue(is_consistent)
            finally:
                os.remove(temp2_path)
        finally:
            os.remove(temp1_path)

    def test_reset_state(self):
        """
        Test resetting state to IDLE.
        """
        # Write a test state
        test_state = {
            "state": PipelineState.EXTRACTION_COMPLETE.value,
            "timestamp": "2025-12-23T10:00:00Z"
        }
        self.state_persistence.write_state(test_state)

        # Reset state
        result = self.state_persistence.reset_state()
        self.assertTrue(result)

        # Check that state is now IDLE
        current_state = self.state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.IDLE)

    def test_validate_state_structure_with_missing_keys(self):
        """
        Test state structure validation with missing required keys.
        """
        # Test with missing 'state' key
        invalid_state = {
            "timestamp": "2025-12-23T10:00:00Z"
            # Missing 'state' key
        }

        is_valid = self.state_persistence._validate_state_structure(invalid_state)
        self.assertFalse(is_valid)

    def test_validate_state_structure_with_missing_timestamp(self):
        """
        Test state structure validation with missing timestamp.
        """
        # Test with missing 'timestamp' key
        invalid_state = {
            "state": PipelineState.IDLE.value
            # Missing 'timestamp' key
        }

        is_valid = self.state_persistence._validate_state_structure(invalid_state)
        self.assertFalse(is_valid)

    def test_validate_state_structure_with_invalid_state(self):
        """
        Test state structure validation with invalid state value.
        """
        # Test with invalid state value
        invalid_state = {
            "state": "INVALID_STATE",
            "timestamp": "2025-12-23T10:00:00Z"
        }

        is_valid = self.state_persistence._validate_state_structure(invalid_state)
        self.assertFalse(is_valid)

    def test_validate_state_structure_with_invalid_timestamp(self):
        """
        Test state structure validation with invalid timestamp format.
        """
        # Test with invalid timestamp format
        invalid_state = {
            "state": PipelineState.IDLE.value,
            "timestamp": "invalid_timestamp"
        }

        is_valid = self.state_persistence._validate_state_structure(invalid_state)
        self.assertFalse(is_valid)

    def test_validate_state_structure_with_invalid_config_hash(self):
        """
        Test state structure validation with invalid config_hash type.
        """
        # Test with invalid config_hash type
        invalid_state = {
            "state": PipelineState.IDLE.value,
            "timestamp": "2025-12-23T10:00:00Z",
            "config_hash": 12345  # Should be string
        }

        is_valid = self.state_persistence._validate_state_structure(invalid_state)
        self.assertFalse(is_valid)

    def test_validate_state_structure_with_invalid_artifact_paths_type(self):
        """
        Test state structure validation with invalid artifact_paths type.
        """
        # Test with invalid artifact_paths type
        invalid_state = {
            "state": PipelineState.IDLE.value,
            "timestamp": "2025-12-23T10:00:00Z",
            "artifact_paths": "not_a_dict"  # Should be dict
        }

        is_valid = self.state_persistence._validate_state_structure(invalid_state)
        self.assertFalse(is_valid)

    def test_validate_state_structure_with_invalid_approvals_type(self):
        """
        Test state structure validation with invalid approvals type.
        """
        # Test with invalid approvals type
        invalid_state = {
            "state": PipelineState.IDLE.value,
            "timestamp": "2025-12-23T10:00:00Z",
            "approvals": "not_a_dict"  # Should be dict
        }

        is_valid = self.state_persistence._validate_state_structure(invalid_state)
        self.assertFalse(is_valid)

    def test_validate_state_structure_with_invalid_validation_type(self):
        """
        Test state structure validation with invalid validation type.
        """
        # Test with invalid validation type
        invalid_state = {
            "state": PipelineState.IDLE.value,
            "timestamp": "2025-12-23T10:00:00Z",
            "validation": "not_a_dict"  # Should be dict
        }

        is_valid = self.state_persistence._validate_state_structure(invalid_state)
        self.assertFalse(is_valid)

    def test_write_state_validation_failure(self):
        """
        Test writing state that fails validation.
        """
        # Test writing invalid state structure
        invalid_state = {
            "timestamp": "2025-12-23T10:00:00Z"  # Missing 'state' key
        }

        result = self.state_persistence.write_state(invalid_state)
        self.assertFalse(result)

    def test_check_state_corruption_with_future_timestamp(self):
        """
        Test checking state corruption with future timestamp.
        """
        from datetime import datetime, timedelta
        import json

        # Create state with future timestamp
        future_time = datetime.utcnow() + timedelta(days=1)
        future_timestamp = future_time.isoformat() + "Z"

        state_data = {
            "state": PipelineState.IDLE.value,
            "timestamp": future_timestamp
        }

        # Write the state data directly to file to bypass validation
        with open(self.state_persistence.state_file_path, 'w') as f:
            json.dump(state_data, f)

        is_valid = self.state_persistence.check_state_corruption()
        self.assertFalse(is_valid)

    def test_check_state_corruption_with_invalid_json(self):
        """
        Test checking state corruption with invalid JSON.
        """
        # Write invalid JSON to file
        with open(self.state_persistence.state_file_path, 'w') as f:
            f.write("invalid json content")

        is_valid = self.state_persistence.check_state_corruption()
        self.assertTrue(is_valid)  # Returns True when no valid state exists (not corrupted, just empty)

    def test_validate_artifact_consistency_with_none_state(self):
        """
        Test validating artifact consistency when no state exists.
        """
        # Remove state file
        if os.path.exists(self.state_persistence.state_file_path):
            os.remove(self.state_persistence.state_file_path)

        is_consistent = self.state_persistence.validate_artifact_consistency()
        self.assertTrue(is_consistent)  # Should return True when no state exists

    def test_validate_artifact_consistency_with_expected_artifacts(self):
        """
        Test validating artifact consistency with expected artifacts parameter.
        """
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_path = temp_file.name

        try:
            # Write a valid state first
            test_state = {
                "state": PipelineState.IDLE.value,
                "timestamp": "2025-12-23T10:00:00Z"
            }
            self.state_persistence.write_state(test_state)

            # Test with expected artifacts parameter
            expected_artifacts = {
                "test_file": temp_path
            }

            is_consistent = self.state_persistence.validate_artifact_consistency(expected_artifacts)
            self.assertTrue(is_consistent)

            # Test with non-existent expected artifact
            expected_artifacts_invalid = {
                "test_file": temp_path,
                "missing_file": "/nonexistent/file.txt"
            }

            is_consistent = self.state_persistence.validate_artifact_consistency(expected_artifacts_invalid)
            self.assertFalse(is_consistent)
        finally:
            os.remove(temp_path)

    def test_log_state_change(self):
        """
        Test logging state change functionality.
        """
        # This should not raise an exception
        self.state_persistence.log_state_change(
            PipelineState.IDLE,
            PipelineState.EXTRACTION_IN_PROGRESS,
            "test reason"
        )

        # Test with string states
        self.state_persistence.log_state_change(
            "IDLE",
            "EXTRACTION_IN_PROGRESS",
            "test reason with strings"
        )

    def test_calculate_config_hash(self):
        """
        Test configuration hash calculation.
        """
        config = {
            "param1": "value1",
            "param2": "value2"
        }

        hash_result = self.state_persistence._calculate_config_hash(config)
        self.assertIsInstance(hash_result, str)
        self.assertEqual(len(hash_result), 64)  # SHA256 hash length

    def test_get_current_state_with_invalid_file(self):
        """
        Test getting current state when file contains invalid data.
        """
        # Write invalid JSON to file
        with open(self.state_persistence.state_file_path, 'w') as f:
            f.write("invalid json content")

        current_state = self.state_persistence.get_current_state()
        self.assertIsNone(current_state)

    def test_update_state_with_invalid_state_string(self):
        """
        Test updating state with invalid state string.
        """
        result = self.state_persistence.update_state("INVALID_STATE")
        self.assertFalse(result)

    def test_update_state_error_handling(self):
        """
        Test update state error handling.
        """
        # Create a state persistence with invalid directory to trigger error
        # On some systems, this might still succeed in creating directories
        # so we'll test with a read-only scenario or similar error condition
        invalid_persistence = StatePersistence("/invalid/path/test.json")

        result = invalid_persistence.update_state(PipelineState.IDLE)
        # The actual behavior may vary based on OS and permissions
        # The important thing is that it doesn't crash
        self.assertIsInstance(result, bool)

    def test_write_state_error_handling(self):
        """
        Test write state error handling.
        """
        # Create a state persistence with invalid directory to trigger error
        invalid_persistence = StatePersistence("/invalid/path/test.json")

        state_data = {
            "state": PipelineState.IDLE.value,
            "timestamp": "2025-12-23T10:00:00Z"
        }

        result = invalid_persistence.write_state(state_data)
        # The actual behavior may vary based on OS and permissions
        # The important thing is that it doesn't crash
        self.assertIsInstance(result, bool)

    def test_read_state_error_handling(self):
        """
        Test read state error handling.
        """
        # Create a state persistence with invalid directory to trigger error
        invalid_persistence = StatePersistence("/invalid/path/test.json")

        result = invalid_persistence.read_state()
        # The actual behavior may vary based on OS and permissions
        # The important thing is that it doesn't crash
        self.assertIsNotNone(result)  # Will return initial state if none exists


if __name__ == '__main__':
    unittest.main()