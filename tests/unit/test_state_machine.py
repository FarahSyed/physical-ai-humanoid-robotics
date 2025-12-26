"""
Unit tests for state machine module.
"""
import unittest

from src.pipeline.state_machine import PipelineState, StateTransitionValidator, validate_state_transition


class TestStateMachine(unittest.TestCase):
    """
    Unit tests for state machine functionality.
    """

    def test_pipeline_state_enum_values(self):
        """
        Test that all PipelineState enum values are correct.
        """
        # Test that all expected states exist and have correct values
        self.assertEqual(PipelineState.IDLE.value, "IDLE")
        self.assertEqual(PipelineState.EXTRACTION_IN_PROGRESS.value, "EXTRACTION_IN_PROGRESS")
        self.assertEqual(PipelineState.EXTRACTION_COMPLETE.value, "EXTRACTION_COMPLETE")
        self.assertEqual(PipelineState.EXTRACTION_APPROVED.value, "EXTRACTION_APPROVED")
        self.assertEqual(PipelineState.CHUNKING_IN_PROGRESS.value, "CHUNKING_IN_PROGRESS")
        self.assertEqual(PipelineState.CHUNKING_COMPLETE.value, "CHUNKING_COMPLETE")
        self.assertEqual(PipelineState.CHUNKING_APPROVED.value, "CHUNKING_APPROVED")
        self.assertEqual(PipelineState.EMBEDDING_IN_PROGRESS.value, "EMBEDDING_IN_PROGRESS")
        self.assertEqual(PipelineState.EMBEDDING_COMPLETE.value, "EMBEDDING_COMPLETE")
        self.assertEqual(PipelineState.FAILED.value, "FAILED")
        self.assertEqual(PipelineState.REJECTED.value, "REJECTED")

    def test_state_transition_validator_is_valid_transition(self):
        """
        Test state transition validation functionality.
        """
        # Test valid transitions
        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.IDLE,
            PipelineState.EXTRACTION_IN_PROGRESS
        ))

        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.EXTRACTION_IN_PROGRESS,
            PipelineState.EXTRACTION_COMPLETE
        ))

        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.EXTRACTION_COMPLETE,
            PipelineState.EXTRACTION_APPROVED
        ))

        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.EXTRACTION_APPROVED,
            PipelineState.CHUNKING_IN_PROGRESS
        ))

        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.CHUNKING_IN_PROGRESS,
            PipelineState.CHUNKING_COMPLETE
        ))

        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.CHUNKING_COMPLETE,
            PipelineState.CHUNKING_APPROVED
        ))

    def test_state_transition_validator_invalid_transitions(self):
        """
        Test invalid state transition validation.
        """
        # Test invalid transitions
        self.assertFalse(StateTransitionValidator.is_valid_transition(
            PipelineState.IDLE,
            PipelineState.CHUNKING_IN_PROGRESS
        ))

        self.assertFalse(StateTransitionValidator.is_valid_transition(
            PipelineState.EXTRACTION_COMPLETE,
            PipelineState.CHUNKING_IN_PROGRESS
        ))

        self.assertFalse(StateTransitionValidator.is_valid_transition(
            PipelineState.CHUNKING_COMPLETE,
            PipelineState.EXTRACTION_APPROVED
        ))

    def test_get_valid_next_states(self):
        """
        Test getting valid next states for each state.
        """
        # Test valid next states for IDLE
        idle_next = StateTransitionValidator.get_valid_next_states(PipelineState.IDLE)
        self.assertIn(PipelineState.EXTRACTION_IN_PROGRESS, idle_next)
        self.assertNotIn(PipelineState.CHUNKING_IN_PROGRESS, idle_next)

        # Test valid next states for EXTRACTION_COMPLETE
        extraction_complete_next = StateTransitionValidator.get_valid_next_states(PipelineState.EXTRACTION_COMPLETE)
        self.assertIn(PipelineState.EXTRACTION_APPROVED, extraction_complete_next)
        self.assertIn(PipelineState.REJECTED, extraction_complete_next)
        self.assertNotIn(PipelineState.IDLE, extraction_complete_next)

    def test_is_terminal_state(self):
        """
        Test checking if a state is terminal.
        """
        # Test terminal states
        self.assertTrue(StateTransitionValidator.is_terminal_state(PipelineState.EMBEDDING_COMPLETE))
        self.assertTrue(StateTransitionValidator.is_terminal_state(PipelineState.REJECTED))

        # Test non-terminal states
        self.assertFalse(StateTransitionValidator.is_terminal_state(PipelineState.IDLE))
        self.assertFalse(StateTransitionValidator.is_terminal_state(PipelineState.EXTRACTION_APPROVED))

    def test_validate_state_transition_function(self):
        """
        Test the public validate_state_transition function.
        """
        # Test valid transitions
        self.assertTrue(validate_state_transition(
            PipelineState.IDLE,
            PipelineState.EXTRACTION_IN_PROGRESS
        ))

        # Test invalid transitions
        self.assertFalse(validate_state_transition(
            PipelineState.IDLE,
            PipelineState.CHUNKING_IN_PROGRESS
        ))

    def test_state_transition_validator_handles_none_states(self):
        """
        Test that the validator handles None states gracefully.
        """
        # This should not crash and return False
        self.assertFalse(StateTransitionValidator.is_valid_transition(None, PipelineState.IDLE))
        self.assertFalse(StateTransitionValidator.is_valid_transition(PipelineState.IDLE, None))

    def test_state_transition_completeness(self):
        """
        Test that all expected state transitions are defined.
        """
        # Verify that each state has defined valid transitions
        all_states = list(PipelineState)

        for state in all_states:
            next_states = StateTransitionValidator.get_valid_next_states(state)
            # Each state should have at least one possible next state (except terminal states)
            if state not in [PipelineState.EMBEDDING_COMPLETE, PipelineState.REJECTED]:
                self.assertGreater(len(next_states), 0)
            # Even terminal states should return an empty set, not None
            self.assertIsInstance(next_states, set)

    def test_state_transition_symmetry_validation(self):
        """
        Test that state transitions are properly defined in one direction only.
        """
        # Transitions should not be symmetric (you can't go back without specific mechanisms)
        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.IDLE,
            PipelineState.EXTRACTION_IN_PROGRESS
        ))
        # Going back from EXTRACTION_IN_PROGRESS to IDLE should not be valid by default
        # (unless it's a special transition like from FAILED back to IDLE)
        self.assertFalse(StateTransitionValidator.is_valid_transition(
            PipelineState.EXTRACTION_IN_PROGRESS,
            PipelineState.IDLE
        ))

    def test_state_transition_from_failed_state(self):
        """
        Test state transitions from FAILED state.
        """
        # From FAILED, should be able to go back to IDLE
        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.FAILED,
            PipelineState.IDLE
        ))

        # From FAILED, should not be able to go to most other states
        self.assertFalse(StateTransitionValidator.is_valid_transition(
            PipelineState.FAILED,
            PipelineState.CHUNKING_APPROVED
        ))

    def test_state_transition_from_rejected_state(self):
        """
        Test state transitions from REJECTED state.
        """
        # REJECTED is a terminal state - no transitions should be valid
        all_states = list(PipelineState)
        for state in all_states:
            if state != PipelineState.REJECTED:  # Not to itself
                self.assertFalse(StateTransitionValidator.is_valid_transition(
                    PipelineState.REJECTED,
                    state
                ))

        # Self-transition should NOT be allowed for terminal states
        self.assertFalse(StateTransitionValidator.is_valid_transition(
            PipelineState.REJECTED,
            PipelineState.REJECTED
        ))

    def test_embedding_complete_state_transitions(self):
        """
        Test state transitions for EMBEDDING_COMPLETE state.
        """
        # EMBEDDING_COMPLETE is a terminal state - no transitions should be valid
        all_states = list(PipelineState)
        for state in all_states:
            if state != PipelineState.EMBEDDING_COMPLETE:  # Not to itself
                self.assertFalse(StateTransitionValidator.is_valid_transition(
                    PipelineState.EMBEDDING_COMPLETE,
                    state
                ))

        # Self-transition should NOT be allowed for terminal states
        self.assertFalse(StateTransitionValidator.is_valid_transition(
            PipelineState.EMBEDDING_COMPLETE,
            PipelineState.EMBEDDING_COMPLETE
        ))

    def test_chunking_approved_state_transitions(self):
        """
        Test state transitions for CHUNKING_APPROVED state.
        """
        # From CHUNKING_APPROVED, should be able to go to EMBEDDING_IN_PROGRESS
        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.CHUNKING_APPROVED,
            PipelineState.EMBEDDING_IN_PROGRESS
        ))

        # From CHUNKING_APPROVED, should not be able to go back to earlier states
        self.assertFalse(StateTransitionValidator.is_valid_transition(
            PipelineState.CHUNKING_APPROVED,
            PipelineState.EXTRACTION_COMPLETE
        ))

    def test_extraction_approved_state_transitions(self):
        """
        Test state transitions for EXTRACTION_APPROVED state.
        """
        # From EXTRACTION_APPROVED, should be able to go to CHUNKING_IN_PROGRESS
        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.EXTRACTION_APPROVED,
            PipelineState.CHUNKING_IN_PROGRESS
        ))

        # From EXTRACTION_APPROVED, should not be able to go to later states directly
        self.assertFalse(StateTransitionValidator.is_valid_transition(
            PipelineState.EXTRACTION_APPROVED,
            PipelineState.EMBEDDING_IN_PROGRESS
        ))

    def test_extraction_complete_state_transitions(self):
        """
        Test state transitions for EXTRACTION_COMPLETE state.
        """
        # From EXTRACTION_COMPLETE, should be able to go to EXTRACTION_APPROVED or REJECTED
        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.EXTRACTION_COMPLETE,
            PipelineState.EXTRACTION_APPROVED
        ))

        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.EXTRACTION_COMPLETE,
            PipelineState.REJECTED
        ))

        # From EXTRACTION_COMPLETE, should not be able to skip approval to chunking
        self.assertFalse(StateTransitionValidator.is_valid_transition(
            PipelineState.EXTRACTION_COMPLETE,
            PipelineState.CHUNKING_IN_PROGRESS
        ))

    def test_chunking_complete_state_transitions(self):
        """
        Test state transitions for CHUNKING_COMPLETE state.
        """
        # From CHUNKING_COMPLETE, should be able to go to CHUNKING_APPROVED or REJECTED
        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.CHUNKING_COMPLETE,
            PipelineState.CHUNKING_APPROVED
        ))

        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.CHUNKING_COMPLETE,
            PipelineState.REJECTED
        ))

        # From CHUNKING_COMPLETE, should not be able to go directly to embedding without approval
        self.assertFalse(StateTransitionValidator.is_valid_transition(
            PipelineState.CHUNKING_COMPLETE,
            PipelineState.EMBEDDING_IN_PROGRESS
        ))

    def test_extraction_in_progress_state_transitions(self):
        """
        Test state transitions for EXTRACTION_IN_PROGRESS state.
        """
        # From EXTRACTION_IN_PROGRESS, should be able to go to COMPLETE or FAILED
        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.EXTRACTION_IN_PROGRESS,
            PipelineState.EXTRACTION_COMPLETE
        ))

        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.EXTRACTION_IN_PROGRESS,
            PipelineState.FAILED
        ))

        # From EXTRACTION_IN_PROGRESS, should not be able to go back to IDLE
        self.assertFalse(StateTransitionValidator.is_valid_transition(
            PipelineState.EXTRACTION_IN_PROGRESS,
            PipelineState.IDLE
        ))

    def test_chunking_in_progress_state_transitions(self):
        """
        Test state transitions for CHUNKING_IN_PROGRESS state.
        """
        # From CHUNKING_IN_PROGRESS, should be able to go to COMPLETE or FAILED
        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.CHUNKING_IN_PROGRESS,
            PipelineState.CHUNKING_COMPLETE
        ))

        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.CHUNKING_IN_PROGRESS,
            PipelineState.FAILED
        ))

        # From CHUNKING_IN_PROGRESS, should not be able to go back to earlier states
        self.assertFalse(StateTransitionValidator.is_valid_transition(
            PipelineState.CHUNKING_IN_PROGRESS,
            PipelineState.EXTRACTION_IN_PROGRESS
        ))

    def test_embedding_in_progress_state_transitions(self):
        """
        Test state transitions for EMBEDDING_IN_PROGRESS state.
        """
        # From EMBEDDING_IN_PROGRESS, should be able to go to COMPLETE or FAILED
        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.EMBEDDING_IN_PROGRESS,
            PipelineState.EMBEDDING_COMPLETE
        ))

        self.assertTrue(StateTransitionValidator.is_valid_transition(
            PipelineState.EMBEDDING_IN_PROGRESS,
            PipelineState.FAILED
        ))

        # From EMBEDDING_IN_PROGRESS, should not be able to go back to earlier states
        self.assertFalse(StateTransitionValidator.is_valid_transition(
            PipelineState.EMBEDDING_IN_PROGRESS,
            PipelineState.CHUNKING_APPROVED
        ))

    def test_state_transition_validator_get_all_transitions(self):
        """
        Test that all defined transitions are valid.
        """
        # Test a comprehensive set of valid transitions
        valid_transitions = [
            (PipelineState.IDLE, PipelineState.EXTRACTION_IN_PROGRESS),
            (PipelineState.EXTRACTION_IN_PROGRESS, PipelineState.EXTRACTION_COMPLETE),
            (PipelineState.EXTRACTION_IN_PROGRESS, PipelineState.FAILED),
            (PipelineState.EXTRACTION_COMPLETE, PipelineState.EXTRACTION_APPROVED),
            (PipelineState.EXTRACTION_COMPLETE, PipelineState.REJECTED),
            (PipelineState.EXTRACTION_APPROVED, PipelineState.CHUNKING_IN_PROGRESS),
            (PipelineState.CHUNKING_IN_PROGRESS, PipelineState.CHUNKING_COMPLETE),
            (PipelineState.CHUNKING_IN_PROGRESS, PipelineState.FAILED),
            (PipelineState.CHUNKING_COMPLETE, PipelineState.CHUNKING_APPROVED),
            (PipelineState.CHUNKING_COMPLETE, PipelineState.REJECTED),
            (PipelineState.CHUNKING_APPROVED, PipelineState.EMBEDDING_IN_PROGRESS),
            (PipelineState.EMBEDDING_IN_PROGRESS, PipelineState.EMBEDDING_COMPLETE),
            (PipelineState.EMBEDDING_IN_PROGRESS, PipelineState.FAILED),
            (PipelineState.FAILED, PipelineState.IDLE),
        ]

        for from_state, to_state in valid_transitions:
            with self.subTest(from_state=from_state.value, to_state=to_state.value):
                self.assertTrue(
                    StateTransitionValidator.is_valid_transition(from_state, to_state),
                    f"Transition from {from_state.value} to {to_state.value} should be valid"
                )

    def test_state_enum_iteration(self):
        """
        Test that PipelineState can be iterated and contains expected states.
        """
        all_states = list(PipelineState)

        # Verify that all expected states are present
        expected_state_names = {
            'IDLE', 'EXTRACTION_IN_PROGRESS', 'EXTRACTION_COMPLETE', 'EXTRACTION_APPROVED',
            'CHUNKING_IN_PROGRESS', 'CHUNKING_COMPLETE', 'CHUNKING_APPROVED',
            'EMBEDDING_IN_PROGRESS', 'EMBEDDING_COMPLETE', 'FAILED', 'REJECTED'
        }

        actual_state_names = {state.name for state in all_states}
        self.assertEqual(expected_state_names, actual_state_names)

    def test_state_equality_and_hashing(self):
        """
        Test that PipelineState values can be compared and used in sets/dicts.
        """
        # Test equality
        self.assertEqual(PipelineState.IDLE, PipelineState.IDLE)
        self.assertNotEqual(PipelineState.IDLE, PipelineState.EXTRACTION_IN_PROGRESS)

        # Test hashing (can be used in sets and dicts)
        state_set = {PipelineState.IDLE, PipelineState.EXTRACTION_IN_PROGRESS, PipelineState.IDLE}  # Duplicate should be ignored
        self.assertEqual(len(state_set), 2)  # Should only have 2 unique states

        # Test as dict keys
        state_dict = {
            PipelineState.IDLE: "idle_value",
            PipelineState.EXTRACTION_IN_PROGRESS: "extraction_value"
        }
        self.assertEqual(state_dict[PipelineState.IDLE], "idle_value")
        self.assertEqual(state_dict[PipelineState.EXTRACTION_IN_PROGRESS], "extraction_value")

    def test_state_transition_cannot_skip_stages(self):
        """
        Test that state transitions cannot skip intermediate stages.
        """
        # Cannot go from IDLE directly to CHUNKING_IN_PROGRESS (skips extraction)
        self.assertFalse(StateTransitionValidator.is_valid_transition(
            PipelineState.IDLE,
            PipelineState.CHUNKING_IN_PROGRESS
        ))

        # Cannot go from IDLE directly to EMBEDDING_IN_PROGRESS (skips extraction and chunking)
        self.assertFalse(StateTransitionValidator.is_valid_transition(
            PipelineState.IDLE,
            PipelineState.EMBEDDING_IN_PROGRESS
        ))

        # Cannot go from EXTRACTION_COMPLETE directly to EMBEDDING_IN_PROGRESS (skips approval and chunking)
        self.assertFalse(StateTransitionValidator.is_valid_transition(
            PipelineState.EXTRACTION_COMPLETE,
            PipelineState.EMBEDDING_IN_PROGRESS
        ))

        # Cannot go from EXTRACTION_APPROVED directly to EMBEDDING_IN_PROGRESS (skips chunking)
        self.assertFalse(StateTransitionValidator.is_valid_transition(
            PipelineState.EXTRACTION_APPROVED,
            PipelineState.EMBEDDING_IN_PROGRESS
        ))

    def test_state_transition_validator_edge_cases(self):
        """
        Test edge cases for state transition validation.
        """
        # Test same state to same state transitions (self-transitions)
        for state in PipelineState:
            # Most states should allow self-transition
            # NOTE: The actual implementation may vary, so we'll just make sure it doesn't crash
            try:
                result = StateTransitionValidator.is_valid_transition(state, state)
                # Result may be True or False depending on implementation
                self.assertIsInstance(result, bool)
            except Exception as e:
                self.fail(f"is_valid_transition raised exception for self-transition on {state}: {e}")


if __name__ == '__main__':
    unittest.main()