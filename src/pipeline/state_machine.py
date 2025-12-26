"""
Pipeline state machine implementation for the verification system.

This module defines the PipelineState enum and state transition validation logic
for the human approval gates and persisted state control system.
"""
from enum import Enum
from typing import Set, Dict, Tuple


class PipelineState(Enum):
    """
    Enum representing the current state of the pipeline with allowed values:
    IDLE, EXTRACTION_IN_PROGRESS, EXTRACTION_COMPLETE, EXTRACTION_APPROVED,
    CHUNKING_IN_PROGRESS, CHUNKING_COMPLETE, CHUNKING_APPROVED,
    EMBEDDING_IN_PROGRESS, EMBEDDING_COMPLETE, FAILED, REJECTED

    State definitions:
    - IDLE: Initial state, pipeline is ready to start
    - EXTRACTION_IN_PROGRESS: Content extraction is currently in progress
    - EXTRACTION_COMPLETE: Content extraction has completed successfully
    - EXTRACTION_APPROVED: Content extraction has been approved by human reviewer
    - CHUNKING_IN_PROGRESS: Content chunking is currently in progress
    - CHUNKING_COMPLETE: Content chunking has completed successfully
    - CHUNKING_APPROVED: Content chunking has been approved by human reviewer
    - EMBEDDING_IN_PROGRESS: Embedding generation is currently in progress
    - EMBEDDING_COMPLETE: Embedding generation has completed successfully (terminal state)
    - FAILED: Pipeline has failed due to an error (recoverable state)
    - REJECTED: Pipeline has been rejected by human reviewer (recoverable state)
    """
    IDLE = "IDLE"
    EXTRACTION_IN_PROGRESS = "EXTRACTION_IN_PROGRESS"
    EXTRACTION_COMPLETE = "EXTRACTION_COMPLETE"
    EXTRACTION_APPROVED = "EXTRACTION_APPROVED"
    CHUNKING_IN_PROGRESS = "CHUNKING_IN_PROGRESS"
    CHUNKING_COMPLETE = "CHUNKING_COMPLETE"
    CHUNKING_APPROVED = "CHUNKING_APPROVED"
    EMBEDDING_IN_PROGRESS = "EMBEDDING_IN_PROGRESS"
    EMBEDDING_COMPLETE = "EMBEDDING_COMPLETE"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class StateTransitionValidator:
    """
    Validates state transitions according to the defined rules:
    IDLE→EXTRACTION_IN_PROGRESS→EXTRACTION_COMPLETE→EXTRACTION_APPROVED→
    CHUNKING_IN_PROGRESS→CHUNKING_COMPLETE→CHUNKING_APPROVED→
    EMBEDDING_IN_PROGRESS→EMBEDDING_COMPLETE,
    EXTRACTION_COMPLETE→REJECTED, CHUNKING_COMPLETE→REJECTED,
    any_state→FAILED (on system error)

    The validator ensures that only valid state transitions occur in the pipeline,
    preventing invalid state changes that could corrupt the pipeline state.
    """

    # Define valid state transitions
    VALID_TRANSITIONS: Dict[PipelineState, Set[PipelineState]] = {
        PipelineState.IDLE: {PipelineState.EXTRACTION_IN_PROGRESS},
        PipelineState.EXTRACTION_IN_PROGRESS: {PipelineState.EXTRACTION_COMPLETE, PipelineState.FAILED},
        PipelineState.EXTRACTION_COMPLETE: {PipelineState.EXTRACTION_APPROVED, PipelineState.REJECTED},
        PipelineState.EXTRACTION_APPROVED: {PipelineState.CHUNKING_IN_PROGRESS},
        PipelineState.CHUNKING_IN_PROGRESS: {PipelineState.CHUNKING_COMPLETE, PipelineState.FAILED},
        PipelineState.CHUNKING_COMPLETE: {PipelineState.CHUNKING_APPROVED, PipelineState.REJECTED},
        PipelineState.CHUNKING_APPROVED: {PipelineState.EMBEDDING_IN_PROGRESS},
        PipelineState.EMBEDDING_IN_PROGRESS: {PipelineState.EMBEDDING_COMPLETE, PipelineState.FAILED},
        PipelineState.EMBEDDING_COMPLETE: set(),  # Terminal state
        PipelineState.FAILED: {PipelineState.IDLE},  # Can restart from failure
        PipelineState.REJECTED: set()  # Terminal state for rejected pipelines
    }

    # Error messages for invalid transitions
    TRANSITION_ERROR_MESSAGES = {
        (PipelineState.IDLE, PipelineState.CHUNKING_IN_PROGRESS): "Cannot start chunking without first completing extraction",
        (PipelineState.IDLE, PipelineState.EMBEDDING_IN_PROGRESS): "Cannot start embedding without completing extraction and chunking",
        (PipelineState.EXTRACTION_IN_PROGRESS, PipelineState.CHUNKING_IN_PROGRESS): "Cannot start chunking while extraction is in progress",
        (PipelineState.EXTRACTION_COMPLETE, PipelineState.CHUNKING_IN_PROGRESS): "Cannot start chunking without approval of extracted content",
        (PipelineState.EXTRACTION_APPROVED, PipelineState.EXTRACTION_APPROVED): "Cannot transition to same state",
        (PipelineState.CHUNKING_IN_PROGRESS, PipelineState.EXTRACTION_IN_PROGRESS): "Cannot go back to extraction from chunking",
        (PipelineState.CHUNKING_COMPLETE, PipelineState.EMBEDDING_IN_PROGRESS): "Cannot start embedding without approval of chunked content",
        (PipelineState.CHUNKING_APPROVED, PipelineState.CHUNKING_APPROVED): "Cannot transition to same state",
        (PipelineState.EMBEDDING_COMPLETE, PipelineState.IDLE): "Cannot restart from terminal EMBEDDING_COMPLETE state",
        (PipelineState.EMBEDDING_COMPLETE, PipelineState.EXTRACTION_IN_PROGRESS): "Cannot start extraction from terminal EMBEDDING_COMPLETE state",
        (PipelineState.REJECTED, PipelineState.IDLE): "Cannot restart from REJECTED state without manual intervention",
        (PipelineState.REJECTED, PipelineState.EXTRACTION_IN_PROGRESS): "Cannot start extraction from REJECTED state without manual intervention"
    }

    @classmethod
    def is_valid_transition(cls, from_state: PipelineState, to_state: PipelineState) -> bool:
        """
        Check if a state transition is valid.

        Args:
            from_state: The current state
            to_state: The target state

        Returns:
            True if the transition is valid, False otherwise
        """
        if from_state is None or to_state is None:
            return False
        return to_state in cls.VALID_TRANSITIONS.get(from_state, set())

    @classmethod
    def get_transition_error_message(cls, from_state: PipelineState, to_state: PipelineState) -> str:
        """
        Get a descriptive error message for an invalid state transition.

        Args:
            from_state: The current state
            to_state: The target state

        Returns:
            Descriptive error message for the invalid transition
        """
        error_key = (from_state, to_state)
        if error_key in cls.TRANSITION_ERROR_MESSAGES:
            return cls.TRANSITION_ERROR_MESSAGES[error_key]

        # Generate a generic error message if no specific one exists
        return f"Invalid state transition from {from_state.value} to {to_state.value}. " \
               f"Valid transitions from {from_state.value} are: {[s.value for s in cls.VALID_TRANSITIONS.get(from_state, set())]}"

    @classmethod
    def get_valid_next_states(cls, current_state: PipelineState) -> Set[PipelineState]:
        """
        Get all valid next states for the current state.

        Args:
            current_state: The current pipeline state

        Returns:
            Set of valid next states
        """
        return cls.VALID_TRANSITIONS.get(current_state, set())

    @classmethod
    def is_terminal_state(cls, state: PipelineState) -> bool:
        """
        Check if a state is terminal (no further transitions allowed).

        Args:
            state: The pipeline state to check

        Returns:
            True if the state is terminal, False otherwise
        """
        return len(cls.VALID_TRANSITIONS.get(state, set())) == 0


def validate_state_transition(from_state: PipelineState, to_state: PipelineState) -> bool:
    """
    Public function to validate state transitions.

    Args:
        from_state: The current state
        to_state: The target state

    Returns:
        True if the transition is valid, False otherwise
    """
    return StateTransitionValidator.is_valid_transition(from_state, to_state)


def get_transition_error_message(from_state: PipelineState, to_state: PipelineState) -> str:
    """
    Get a descriptive error message for an invalid state transition.

    Args:
        from_state: The current state
        to_state: The target state

    Returns:
        Descriptive error message for the invalid transition
    """
    return StateTransitionValidator.get_transition_error_message(from_state, to_state)


# Alias for backward compatibility
StateTransitionValidator = StateTransitionValidator