"""
State persistence for the RAG pipeline.

This module handles the persistence of pipeline state to and from files.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from .state_machine import PipelineState, StateMachine


class StatePersistence:
    """
    Handles persistence of pipeline state to and from files.
    """

    def __init__(self, state_file_path: str):
        """
        Initialize the state persistence.

        Args:
            state_file_path: Path to the state file
        """
        self.state_file_path = Path(state_file_path)
        self.state_file_path.parent.mkdir(parents=True, exist_ok=True)

    def read_state(self) -> Dict[str, Any]:
        """
        Read the current state from the state file.

        Returns:
            Dict containing the state data
        """
        if not self.state_file_path.exists():
            return {}

        try:
            with open(self.state_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def write_state(self, state_data: Dict[str, Any]) -> bool:
        """
        Write state data to the state file.

        Args:
            state_data: Dictionary containing state data to write

        Returns:
            bool: True if write was successful, False otherwise
        """
        try:
            # Ensure the directory exists
            self.state_file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.state_file_path, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)

            return True
        except Exception:
            return False

    def update_state(self, new_state: PipelineState, additional_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update the state in the state file.

        Args:
            new_state: The new state to set
            additional_data: Additional data to include in the state file

        Returns:
            bool: True if update was successful, False otherwise
        """
        current_state = self.read_state()
        current_state['state'] = new_state.value
        current_state['timestamp'] = datetime.utcnow().isoformat()

        if additional_data:
            current_state.update(additional_data)

        return self.write_state(current_state)


class PipelineStateManager:
    """
    Manager for pipeline state that combines state machine and persistence.
    """

    def __init__(self, state_file_path: str):
        """
        Initialize the pipeline state manager.

        Args:
            state_file_path: Path to the state file
        """
        self.state_file_path = state_file_path
        self.state_persistence = StatePersistence(state_file_path)
        self.state_machine = StateMachine()

        # Load existing state if available
        self._load_state()

    def _load_state(self):
        """Load state from the state file."""
        state_data = self.state_persistence.read_state()
        if state_data and 'state' in state_data:
            try:
                state = PipelineState(state_data['state'])
                self.state_machine = StateMachine(state)
            except ValueError:
                # If the state is invalid, start with IDLE
                self.state_machine = StateMachine(PipelineState.IDLE)
        else:
            # If no state file exists, start with IDLE
            self.state_machine = StateMachine(PipelineState.IDLE)

    def get_pipeline_state(self) -> PipelineState:
        """
        Get the current pipeline state.

        Returns:
            Current pipeline state
        """
        return self.state_machine.state

    def transition_to_extraction_in_progress(self) -> bool:
        """Transition to EXTRACTION_IN_PROGRESS state."""
        if self.state_machine.can_transition_to(PipelineState.EXTRACTION_IN_PROGRESS):
            self.state_machine.transition_to(PipelineState.EXTRACTION_IN_PROGRESS)
            return self.state_persistence.update_state(PipelineState.EXTRACTION_IN_PROGRESS)
        return False

    def transition_to_extraction_complete(self) -> bool:
        """Transition to EXTRACTION_COMPLETE state."""
        if self.state_machine.can_transition_to(PipelineState.EXTRACTION_COMPLETE):
            self.state_machine.transition_to(PipelineState.EXTRACTION_COMPLETE)
            return self.state_persistence.update_state(PipelineState.EXTRACTION_COMPLETE)
        return False

    def transition_to_extraction_approved(self) -> bool:
        """Transition to EXTRACTION_APPROVED state."""
        if self.state_machine.can_transition_to(PipelineState.EXTRACTION_APPROVED):
            self.state_machine.transition_to(PipelineState.EXTRACTION_APPROVED)
            return self.state_persistence.update_state(PipelineState.EXTRACTION_APPROVED)
        return False

    def transition_to_chunking_in_progress(self) -> bool:
        """Transition to CHUNKING_IN_PROGRESS state."""
        if self.state_machine.can_transition_to(PipelineState.CHUNKING_IN_PROGRESS):
            self.state_machine.transition_to(PipelineState.CHUNKING_IN_PROGRESS)
            return self.state_persistence.update_state(PipelineState.CHUNKING_IN_PROGRESS)
        return False

    def transition_to_chunking_complete(self) -> bool:
        """Transition to CHUNKING_COMPLETE state."""
        if self.state_machine.can_transition_to(PipelineState.CHUNKING_COMPLETE):
            self.state_machine.transition_to(PipelineState.CHUNKING_COMPLETE)
            return self.state_persistence.update_state(PipelineState.CHUNKING_COMPLETE)
        return False

    def transition_to_chunking_approved(self) -> bool:
        """Transition to CHUNKING_APPROVED state."""
        if self.state_machine.can_transition_to(PipelineState.CHUNKING_APPROVED):
            self.state_machine.transition_to(PipelineState.CHUNKING_APPROVED)
            return self.state_persistence.update_state(PipelineState.CHUNKING_APPROVED)
        return False

    def transition_to_embedding_in_progress(self) -> bool:
        """Transition to EMBEDDING_IN_PROGRESS state."""
        if self.state_machine.can_transition_to(PipelineState.EMBEDDING_IN_PROGRESS):
            self.state_machine.transition_to(PipelineState.EMBEDDING_IN_PROGRESS)
            return self.state_persistence.update_state(PipelineState.EMBEDDING_IN_PROGRESS)
        return False

    def transition_to_embedding_complete(self) -> bool:
        """Transition to EMBEDDING_COMPLETE state."""
        if self.state_machine.can_transition_to(PipelineState.EMBEDDING_COMPLETE):
            self.state_machine.transition_to(PipelineState.EMBEDDING_COMPLETE)
            return self.state_persistence.update_state(PipelineState.EMBEDDING_COMPLETE)
        return False

    def transition_to_embedding_failed(self, error_message: str = "") -> bool:
        """Transition to EMBEDDING_FAILED state."""
        if self.state_machine.can_transition_to(PipelineState.EMBEDDING_FAILED):
            self.state_machine.transition_to(PipelineState.EMBEDDING_FAILED)
            return self.state_persistence.update_state(
                PipelineState.EMBEDDING_FAILED,
                {"error_message": error_message}
            )
        return False

    def transition_to_complete(self) -> bool:
        """Transition to COMPLETE state."""
        if self.state_machine.can_transition_to(PipelineState.COMPLETE):
            self.state_machine.transition_to(PipelineState.COMPLETE)
            return self.state_persistence.update_state(PipelineState.COMPLETE)
        return False

    def transition_to_failed(self, error_message: str = "") -> bool:
        """Transition to FAILED state."""
        if self.state_machine.can_transition_to(PipelineState.FAILED):
            self.state_machine.transition_to(PipelineState.FAILED)
            return self.state_persistence.update_state(
                PipelineState.FAILED,
                {"error_message": error_message}
            )
        return False