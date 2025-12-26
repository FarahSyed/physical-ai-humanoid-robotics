"""
Integration tests for state persistence and state machine functionality.
"""
import os
import tempfile
import unittest
from pathlib import Path

from src.pipeline.state_machine import PipelineState
from src.pipeline.state_persistence import StatePersistence, PipelineStateManager
from src.utils.file_utils import read_json_file


class TestStateIntegration(unittest.TestCase):
    """
    Integration test cases for state management functionality.
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

    def test_state_persistence_full_cycle(self):
        """
        Test complete state persistence cycle: write, read, validate, update.
        """
        # Initialize state persistence
        state_persistence = StatePersistence(self.state_file)

        # Write initial state
        initial_state_data = {
            "state": PipelineState.IDLE.value,
            "timestamp": "2025-12-23T10:00:00Z"
        }
        success = state_persistence.write_state(initial_state_data)
        self.assertTrue(success)

        # Read the state back
        read_state = state_persistence.read_state()
        self.assertIsNotNone(read_state)
        self.assertEqual(read_state["state"], PipelineState.IDLE.value)

        # Update the state
        update_success = state_persistence.update_state(PipelineState.EXTRACTION_IN_PROGRESS)
        self.assertTrue(update_success)

        # Verify the state was updated
        updated_state = state_persistence.get_current_state()
        self.assertEqual(updated_state, PipelineState.EXTRACTION_IN_PROGRESS)

    def test_pipeline_state_manager_full_workflow(self):
        """
        Test complete workflow using PipelineStateManager.
        """
        # Initialize state manager
        state_manager = PipelineStateManager(self.state_file)

        # Initialize the pipeline
        init_success = state_manager.initialize_pipeline()
        self.assertTrue(init_success)

        # Verify initial state is IDLE
        current_state = state_manager.get_pipeline_state()
        self.assertEqual(current_state, PipelineState.IDLE)

        # Transition to EXTRACTION_IN_PROGRESS
        transition_success = state_manager.transition_to_extraction_in_progress()
        self.assertTrue(transition_success)
        current_state = state_manager.get_pipeline_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_IN_PROGRESS)

        # Transition to EXTRACTION_COMPLETE
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp:
            temp.write(b"test content")
            temp_path = temp.name
        try:
            transition_success = state_manager.transition_to_extraction_complete(temp_path)
            self.assertTrue(transition_success)
            current_state = state_manager.get_pipeline_state()
            self.assertEqual(current_state, PipelineState.EXTRACTION_COMPLETE)
        finally:
            os.remove(temp_path)

        # Transition to EXTRACTION_APPROVED
        transition_success = state_manager.transition_to_extraction_approved("test_approver")
        self.assertTrue(transition_success)
        current_state = state_manager.get_pipeline_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_APPROVED)

        # Transition to CHUNKING_IN_PROGRESS
        transition_success = state_manager.transition_to_chunking_in_progress()
        self.assertTrue(transition_success)
        current_state = state_manager.get_pipeline_state()
        self.assertEqual(current_state, PipelineState.CHUNKING_IN_PROGRESS)

    def test_state_corruption_detection_and_recovery(self):
        """
        Test state corruption detection and recovery mechanisms.
        """
        state_persistence = StatePersistence(self.state_file)

        # Write a valid state
        valid_state = {
            "state": PipelineState.IDLE.value,
            "timestamp": "2025-12-23T10:00:00Z"
        }
        state_persistence.write_state(valid_state)

        # Verify it's not corrupted
        is_valid = state_persistence.check_state_corruption()
        self.assertTrue(is_valid)

        # Read the state and verify it's valid
        state_data = state_persistence.read_state()
        self.assertIsNotNone(state_data)
        self.assertTrue(state_persistence._validate_state_structure(state_data))

    def test_state_transition_validation_integration(self):
        """
        Test state transition validation in the context of persistence.
        """
        state_persistence = StatePersistence(self.state_file)

        # Start with IDLE
        success = state_persistence.update_state(PipelineState.IDLE)
        self.assertTrue(success)

        # Valid transition should succeed
        success = state_persistence.update_state(PipelineState.EXTRACTION_IN_PROGRESS)
        self.assertTrue(success)

        # Read current state
        current_state = state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_IN_PROGRESS)

        # Invalid transition should fail (can't go from EXTRACTION_IN_PROGRESS to CHUNKING_IN_PROGRESS)
        success = state_persistence.update_state(PipelineState.CHUNKING_IN_PROGRESS)
        self.assertFalse(success)

    def test_state_file_persistence_across_instances(self):
        """
        Test that state is properly persisted across different StatePersistence instances.
        """
        # First instance - write state
        state_persistence1 = StatePersistence(self.state_file)
        success1 = state_persistence1.update_state(PipelineState.EXTRACTION_COMPLETE)
        self.assertTrue(success1)

        # Second instance - read same state
        state_persistence2 = StatePersistence(self.state_file)
        current_state = state_persistence2.get_current_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_COMPLETE)

        # Third instance - update state
        state_persistence3 = StatePersistence(self.state_file)
        success3 = state_persistence3.update_state(PipelineState.EXTRACTION_APPROVED)
        self.assertTrue(success3)

        # Fourth instance - verify updated state
        state_persistence4 = StatePersistence(self.state_file)
        final_state = state_persistence4.get_current_state()
        self.assertEqual(final_state, PipelineState.EXTRACTION_APPROVED)

    def test_state_manager_state_transitions(self):
        """
        Test state transitions through PipelineStateManager.
        """
        state_manager = PipelineStateManager(self.state_file)

        # Initialize
        state_manager.initialize_pipeline()
        self.assertEqual(state_manager.get_pipeline_state(), PipelineState.IDLE)

        # Transition to EXTRACTION_IN_PROGRESS
        success = state_manager.transition_to_extraction_in_progress()
        self.assertTrue(success)
        current_state = state_manager.get_pipeline_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_IN_PROGRESS)

        # Transition to EXTRACTION_COMPLETE
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp:
            temp.write(b"test content")
            temp_path = temp.name
        try:
            success = state_manager.transition_to_extraction_complete(temp_path)
            self.assertTrue(success)
            current_state = state_manager.get_pipeline_state()
            self.assertEqual(current_state, PipelineState.EXTRACTION_COMPLETE)
        finally:
            os.remove(temp_path)

        # Transition to EXTRACTION_APPROVED
        success = state_manager.transition_to_extraction_approved("test_approver")
        self.assertTrue(success)
        current_state = state_manager.get_pipeline_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_APPROVED)

        # Transition to CHUNKING_IN_PROGRESS
        success = state_manager.transition_to_chunking_in_progress()
        self.assertTrue(success)
        current_state = state_manager.get_pipeline_state()
        self.assertEqual(current_state, PipelineState.CHUNKING_IN_PROGRESS)

        # Transition to CHUNKING_COMPLETE
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as temp:
            temp.write(b"chunked content")
            temp_path = temp.name
        try:
            success = state_manager.transition_to_chunking_complete(temp_path)
            self.assertTrue(success)
            current_state = state_manager.get_pipeline_state()
            self.assertEqual(current_state, PipelineState.CHUNKING_COMPLETE)
        finally:
            os.remove(temp_path)

        # Transition to CHUNKING_APPROVED
        success = state_manager.transition_to_chunking_approved("test_approver")
        self.assertTrue(success)
        current_state = state_manager.get_pipeline_state()
        self.assertEqual(current_state, PipelineState.CHUNKING_APPROVED)

    def test_state_reset_functionality(self):
        """
        Test state reset functionality.
        """
        state_persistence = StatePersistence(self.state_file)

        # Set a non-IDLE state
        success = state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)
        self.assertTrue(success)

        current_state = state_persistence.get_current_state()
        self.assertEqual(current_state, PipelineState.EXTRACTION_COMPLETE)

        # Reset the state
        reset_success = state_persistence.reset_state()
        self.assertTrue(reset_success)

        # Verify state is now IDLE
        final_state = state_persistence.get_current_state()
        self.assertEqual(final_state, PipelineState.IDLE)


def suite():
    """
    Create a test suite for state integration tests.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(TestStateIntegration))
    return test_suite


if __name__ == '__main__':
    unittest.main()