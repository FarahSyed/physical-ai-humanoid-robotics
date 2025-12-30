"""
State machine for the RAG pipeline.

This module defines the states and transitions for the RAG pipeline.
"""
from enum import Enum
from typing import Optional, Dict, Any
import json
from datetime import datetime


class PipelineState(Enum):
    """
    States for the RAG pipeline.
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
    EMBEDDING_FAILED = "EMBEDDING_FAILED"
    VERIFICATION_IN_PROGRESS = "VERIFICATION_IN_PROGRESS"
    VERIFICATION_COMPLETE = "VERIFICATION_COMPLETE"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class StateMachine:
    """
    State machine for managing pipeline state transitions.
    """

    def __init__(self, initial_state: PipelineState = PipelineState.IDLE):
        self._state = initial_state
        self._timestamp = datetime.utcnow()
        self._transitions = []

    @property
    def state(self) -> PipelineState:
        """Get the current state."""
        return self._state

    def transition_to(self, new_state: PipelineState) -> bool:
        """
        Transition to a new state.

        Args:
            new_state: The new state to transition to

        Returns:
            bool: True if the transition was successful, False otherwise
        """
        # Log the transition
        self._transitions.append({
            'from': self._state.value,
            'to': new_state.value,
            'timestamp': datetime.utcnow().isoformat()
        })

        self._state = new_state
        self._timestamp = datetime.utcnow()
        return True

    def can_transition_to(self, new_state: PipelineState) -> bool:
        """
        Check if a transition to the new state is valid.

        Args:
            new_state: The state to check transition to

        Returns:
            bool: True if the transition is valid, False otherwise
        """
        # Define valid state transitions
        valid_transitions = {
            PipelineState.IDLE: [
                PipelineState.EXTRACTION_IN_PROGRESS,
                PipelineState.FAILED
            ],
            PipelineState.EXTRACTION_IN_PROGRESS: [
                PipelineState.EXTRACTION_COMPLETE,
                PipelineState.FAILED
            ],
            PipelineState.EXTRACTION_COMPLETE: [
                PipelineState.EXTRACTION_APPROVED,
                PipelineState.FAILED
            ],
            PipelineState.EXTRACTION_APPROVED: [
                PipelineState.CHUNKING_IN_PROGRESS,
                PipelineState.FAILED
            ],
            PipelineState.CHUNKING_IN_PROGRESS: [
                PipelineState.CHUNKING_COMPLETE,
                PipelineState.FAILED
            ],
            PipelineState.CHUNKING_COMPLETE: [
                PipelineState.CHUNKING_APPROVED,
                PipelineState.FAILED
            ],
            PipelineState.CHUNKING_APPROVED: [
                PipelineState.EMBEDDING_IN_PROGRESS,
                PipelineState.FAILED
            ],
            PipelineState.EMBEDDING_IN_PROGRESS: [
                PipelineState.EMBEDDING_COMPLETE,
                PipelineState.EMBEDDING_FAILED,
                PipelineState.FAILED
            ],
            PipelineState.EMBEDDING_COMPLETE: [
                PipelineState.VERIFICATION_IN_PROGRESS,
                PipelineState.FAILED
            ],
            PipelineState.EMBEDDING_FAILED: [
                PipelineState.FAILED,
                PipelineState.EMBEDDING_IN_PROGRESS
            ],
            PipelineState.VERIFICATION_IN_PROGRESS: [
                PipelineState.VERIFICATION_COMPLETE,
                PipelineState.FAILED
            ],
            PipelineState.VERIFICATION_COMPLETE: [
                PipelineState.COMPLETE,
                PipelineState.FAILED
            ]
        }

        return new_state in valid_transitions.get(self._state, [])

    def to_dict(self) -> Dict[str, Any]:
        """Convert the state machine to a dictionary."""
        return {
            'state': self._state.value,
            'timestamp': self._timestamp.isoformat(),
            'transitions': self._transitions
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateMachine':
        """Create a state machine from a dictionary."""
        state_machine = cls(PipelineState(data.get('state', 'IDLE')))
        state_machine._timestamp = datetime.fromisoformat(data.get('timestamp', datetime.utcnow().isoformat()))
        state_machine._transitions = data.get('transitions', [])
        return state_machine


def get_pipeline_state_from_file(state_file_path: str) -> Optional[PipelineState]:
    """
    Get the pipeline state from a state file.

    Args:
        state_file_path: Path to the state file

    Returns:
        PipelineState: The current state or None if file doesn't exist or is invalid
    """
    try:
        with open(state_file_path, 'r', encoding='utf-8') as f:
            state_data = json.load(f)

        state_value = state_data.get('state', 'IDLE')
        return PipelineState(state_value)
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        return None