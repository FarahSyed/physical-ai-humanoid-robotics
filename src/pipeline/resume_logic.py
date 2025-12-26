"""
Resume logic for the pipeline verification system.

This module implements comprehensive resume and restart functionality for failures and rejections,
including artifact validation before resume and restart behavior for different scenarios.
"""
from typing import Dict, Any, Optional, List
import logging
from pathlib import Path

from src.pipeline.state_machine import PipelineState
from src.pipeline.state_persistence import StatePersistence
from src.utils.file_utils import file_exists
from src.utils.validation_utils import validate_artifact_paths


class ResumeLogic:
    """
    Handles resume and restart functionality for the pipeline system.
    """
    def __init__(self, state_persistence: StatePersistence):
        """
        Initialize resume logic.

        Args:
            state_persistence: StatePersistence instance for managing state
        """
        self.state_persistence = state_persistence

    def get_resume_state(self) -> Optional[PipelineState]:
        """
        Determine the state from which the pipeline should resume.

        Returns:
            PipelineState to resume from, or None if no valid resume point
        """
        try:
            state_data = self.state_persistence.read_state()
            if not state_data or "state" not in state_data:
                logging.info("No existing state found, cannot resume")
                return None

            current_state = PipelineState(state_data["state"])
            logging.info(f"Current state is {current_state.value}")

            # For FAILED state, resume from the last approved state
            if current_state == PipelineState.FAILED:
                last_approved = self._get_last_approved_state(state_data)
                if last_approved is not None:
                    return last_approved
                else:
                    # If no approved state found, return the current FAILED state
                    return current_state

            # For REJECTED state, user intervention is needed but can resume from the rejection point
            if current_state == PipelineState.REJECTED:
                # Return the state before rejection (where approval was pending)
                return self._get_state_before_rejection(state_data)

            # For terminal states, resume is not applicable
            if current_state in [PipelineState.EMBEDDING_COMPLETE]:
                logging.info(f"Pipeline is in terminal state {current_state.value}, no resume needed")
                return None

            # For other states, resume from current state
            return current_state
        except Exception as e:
            logging.error(f"Error determining resume state: {str(e)}")
            return None

    def _get_last_approved_state(self, state_data: Dict[str, Any]) -> Optional[PipelineState]:
        """
        Get the last approved state from the state data.

        Args:
            state_data: Current state data

        Returns:
            Last approved PipelineState or None
        """
        try:
            # Check approval status to determine last approved state
            approvals = state_data.get("approvals", {})

            # If chunking was approved, resume from after chunking
            chunking_approval = approvals.get("chunking", {})
            if chunking_approval.get("status") == "APPROVED":
                return PipelineState.CHUNKING_APPROVED

            # If extraction was approved, resume from after extraction
            extraction_approval = approvals.get("extraction", {})
            if extraction_approval.get("status") == "APPROVED":
                return PipelineState.EXTRACTION_APPROVED

            # If no approvals exist, we can't resume meaningfully from an approved state
            # Return None to indicate no valid resume point from approved states
            return None
        except Exception as e:
            logging.error(f"Error getting last approved state: {str(e)}")
            return None

    def _get_state_before_rejection(self, state_data: Dict[str, Any]) -> Optional[PipelineState]:
        """
        Get the state before rejection occurred.

        Args:
            state_data: Current state data

        Returns:
            PipelineState before rejection or None
        """
        try:
            # Check approval status to determine state before rejection
            approvals = state_data.get("approvals", {})

            # If chunking was rejected, it was at CHUNKING_COMPLETE
            chunking_approval = approvals.get("chunking", {})
            if chunking_approval.get("status") == "REJECTED":
                return PipelineState.CHUNKING_COMPLETE

            # If extraction was rejected, it was at EXTRACTION_COMPLETE
            extraction_approval = approvals.get("extraction", {})
            if extraction_approval.get("status") == "REJECTED":
                return PipelineState.EXTRACTION_COMPLETE

            # If no specific rejection info, but the current state is REJECTED,
            # we return the REJECTED state itself to indicate the current state
            current_state = PipelineState(state_data["state"])
            if current_state == PipelineState.REJECTED:
                # If we're in REJECTED state but don't know which stage was rejected,
                # return the REJECTED state itself so the system knows the current state
                return current_state
            else:
                # If current state is not REJECTED, no rejection occurred
                return None
        except Exception as e:
            logging.error(f"Error getting state before rejection: {str(e)}")
            return None

    def validate_artifacts_before_resume(self) -> bool:
        """
        Validate that required artifacts exist before resuming.

        Returns:
            True if all required artifacts exist, False otherwise
        """
        try:
            state_data = self.state_persistence.read_state()
            if not state_data or "artifact_paths" not in state_data:
                logging.info("No artifact paths to validate")
                return True

            artifact_paths = state_data["artifact_paths"]
            return self._validate_artifact_paths(artifact_paths)
        except Exception as e:
            logging.error(f"Error validating artifacts before resume: {str(e)}")
            return False

    def _validate_artifact_paths(self, artifact_paths: Dict[str, str]) -> bool:
        """
        Validate that artifact paths exist and are accessible.

        Args:
            artifact_paths: Dictionary of artifact paths to validate

        Returns:
            True if all paths are valid, False otherwise
        """
        try:
            # Validate the structure first
            if not validate_artifact_paths(artifact_paths):
                logging.error("Artifact paths validation failed")
                return False

            # Check if each file exists
            for name, path in artifact_paths.items():
                if path and not file_exists(path):
                    logging.error(f"Required artifact does not exist: {name} at {path}")
                    return False

            logging.info("All required artifacts exist and are accessible")
            return True
        except Exception as e:
            logging.error(f"Error validating artifact paths: {str(e)}")
            return False

    def resume_from_state(self, force_extraction: bool = False,
                         force_chunking: bool = False) -> Optional[PipelineState]:
        """
        Resume the pipeline from the appropriate state.

        Args:
            force_extraction: If True, force re-extraction even if already completed
            force_chunking: If True, force re-chunking even if already completed

        Returns:
            Current state after resume attempt, or None if failed
        """
        try:
            # If forcing extraction, go back to IDLE
            if force_extraction:
                logging.info("Forcing re-extraction, resuming from IDLE state")
                success = self.state_persistence.update_state(PipelineState.IDLE, validate_transition=False)
                return PipelineState.IDLE if success else None

            # If forcing chunking, go back to EXTRACTION_APPROVED
            if force_chunking:
                logging.info("Forcing re-chunking, resuming from EXTRACTION_APPROVED state")
                success = self.state_persistence.update_state(PipelineState.EXTRACTION_APPROVED, validate_transition=False)
                return PipelineState.EXTRACTION_APPROVED if success else None

            # Get normal resume state
            resume_state = self.get_resume_state()
            if not resume_state:
                logging.info("No valid resume state found")
                return None

            # Validate artifacts before resuming
            if not self.validate_artifacts_before_resume():
                logging.error("Artifacts validation failed, cannot resume safely")
                return None

            logging.info(f"Resuming pipeline from state: {resume_state.value}")
            return resume_state
        except Exception as e:
            logging.error(f"Error resuming from state: {str(e)}")
            return None

    def handle_crash_scenario(self) -> Optional[PipelineState]:
        """
        Handle a crash scenario by resuming from the last safe point.

        Returns:
            PipelineState to resume from, or None if no valid resume point
        """
        try:
            logging.info("Handling crash scenario, attempting to resume from last safe point")

            # In a crash scenario, we want to resume from the last approved state
            state_data = self.state_persistence.read_state()
            if not state_data:
                logging.error("No state data found for crash recovery")
                return None

            # Mark current state as failed if it was in progress
            current_state = PipelineState(state_data["state"])
            if current_state in [PipelineState.EXTRACTION_IN_PROGRESS, PipelineState.CHUNKING_IN_PROGRESS]:
                logging.info(f"Marking in-progress state {current_state.value} as FAILED due to crash")
                self.state_persistence.update_state(PipelineState.FAILED)

            # Get the appropriate resume state
            resume_state = self._get_last_approved_state(state_data)
            if resume_state:
                logging.info(f"Crash recovery: resuming from {resume_state.value}")
                return resume_state
            else:
                # If no approved state found, return to IDLE to restart the pipeline
                logging.info("No approved resume point found after crash, returning to IDLE to restart")
                return PipelineState.IDLE
        except Exception as e:
            logging.error(f"Error handling crash scenario: {str(e)}")
            return None

    def handle_rejection_scenario(self) -> Optional[PipelineState]:
        """
        Handle a rejection scenario where user rejected the content.

        Returns:
            PipelineState before rejection, or None if no valid state
        """
        try:
            logging.info("Handling rejection scenario")

            state_data = self.state_persistence.read_state()
            if not state_data:
                logging.error("No state data found for rejection handling")
                return None

            # Get the state before rejection
            resume_state = self._get_state_before_rejection(state_data)
            if resume_state:
                logging.info(f"Rejection recovery: can resume from {resume_state.value}")
            else:
                logging.error("No valid state found before rejection")
                return None

            return resume_state
        except Exception as e:
            logging.error(f"Error handling rejection scenario: {str(e)}")
            return None

    def get_resume_recommendation(self) -> Dict[str, Any]:
        """
        Get a recommendation for how to resume the pipeline.

        Returns:
            Dictionary with resume recommendation
        """
        try:
            state_data = self.state_persistence.read_state()
            if not state_data:
                return {
                    "action": "start_new",
                    "message": "No existing state found, start new pipeline"
                }

            current_state = PipelineState(state_data["state"])
            resume_state = self.get_resume_state()

            recommendation = {
                "current_state": current_state.value,
                "recommended_resume_state": resume_state.value if resume_state else None,
                "action": "",
                "message": "",
                "artifacts_valid": self.validate_artifacts_before_resume()
            }

            if current_state == PipelineState.FAILED:
                recommendation["action"] = "resume_from_failure"
                recommendation["message"] = f"Pipeline failed, resume from {resume_state.value if resume_state else 'unknown state'}"
            elif current_state == PipelineState.REJECTED:
                recommendation["action"] = "resume_from_rejection"
                recommendation["message"] = f"Pipeline rejected, resume from {resume_state.value if resume_state else 'unknown state'}"
            elif current_state == PipelineState.EMBEDDING_COMPLETE:
                recommendation["action"] = "pipeline_complete"
                recommendation["message"] = "Pipeline already completed successfully"
            else:
                recommendation["action"] = "continue_from_state"
                recommendation["message"] = f"Continue from current state {current_state.value}"

            return recommendation
        except Exception as e:
            logging.error(f"Error getting resume recommendation: {str(e)}")
            return {
                "action": "error",
                "message": f"Error getting resume recommendation: {str(e)}"
            }

    def force_resume_from_state(self, target_state: PipelineState) -> bool:
        """
        Force resume from a specific state (useful for debugging or recovery).

        Args:
            target_state: State to force resume from

        Returns:
            True if successful, False otherwise
        """
        try:
            logging.info(f"Forcing resume from state: {target_state.value}")
            success = self.state_persistence.update_state(target_state)
            if success:
                logging.info(f"Successfully forced resume to state: {target_state.value}")
            else:
                logging.error(f"Failed to force resume to state: {target_state.value}")
            return success
        except Exception as e:
            logging.error(f"Error forcing resume from state {target_state.value}: {str(e)}")
            return False

    def validate_resume_readiness(self) -> bool:
        """
        Validate that the system is ready to resume the pipeline.

        Returns:
            True if ready to resume, False otherwise
        """
        try:
            # Check if state file exists and is readable
            if not self.state_persistence.read_state():
                logging.warning("No state file found, cannot resume")
                return False

            # Check if required artifacts exist
            if not self.validate_artifacts_before_resume():
                logging.warning("Required artifacts missing, cannot resume safely")
                return False

            # Check if current state allows for resumption
            resume_state = self.get_resume_state()
            if not resume_state:
                logging.warning("No valid resume state found")
                return False

            logging.info("System is ready to resume the pipeline")
            return True
        except Exception as e:
            logging.error(f"Error validating resume readiness: {str(e)}")
            return False