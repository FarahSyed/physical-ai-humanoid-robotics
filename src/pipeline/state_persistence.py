"""
State persistence implementation for the pipeline verification system.

This module handles the persistence of pipeline state to disk in JSON format,
including state read/write operations, corruption detection, audit logging,
and state validation.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging

from src.pipeline.state_machine import PipelineState, validate_state_transition, get_transition_error_message
from src.utils.file_utils import read_json_file, write_json_file, create_directory
from src.utils.validation_utils import (
    is_valid_iso_datetime, validate_artifact_paths
)


class StatePersistence:
    """
    Handles persistence of pipeline state to disk in JSON format.

    The state schema includes:
    {
      "state": "PipelineState",
      "timestamp": "ISO 8601 datetime",
      "config_hash": "SHA256 hash of pipeline configuration",
      "artifact_paths": {
        "extracted_content": "path to extracted content file",
        "chunked_output": "path to chunked output file"
      },
      "approvals": {
        "extraction": {
          "status": "APPROVED|REJECTED|PENDING",
          "approver": "user identifier",
          "timestamp": "ISO 8601 datetime",
          "decision": "APPROVE|REJECT|REQUEST_CHANGE"
        },
        "chunking": {
          "status": "APPROVED|REJECTED|PENDING",
          "approver": "user identifier",
          "timestamp": "ISO 8601 datetime",
          "decision": "APPROVE|REJECT|REQUEST_CHANGE"
        }
      },
      "validation": {
        "determinism_check": "boolean",
        "config_consistency": "boolean"
      }
    }
    """

    def __init__(self, state_file_path: str = "pipeline_state.json"):
        """
        Initialize state persistence.

        Args:
            state_file_path: Path to the state file (default: pipeline_state.json)
        """
        self.state_file_path = state_file_path
        self.state_dir = Path(state_file_path).parent
        self.ensure_state_directory()

    def ensure_state_directory(self):
        """Ensure the state file directory exists."""
        if not create_directory(str(self.state_dir)):
            logging.warning(f"Could not create state directory: {self.state_dir}")

    def read_state(self) -> Optional[Dict[str, Any]]:
        """
        Read the current pipeline state from disk.

        Returns:
            State dictionary if successful, None otherwise
        """
        try:
            state_data = read_json_file(self.state_file_path)
            if state_data is None:
                logging.info(f"No existing state file found at {self.state_file_path}")
                return None

            # Validate the state structure
            if self._validate_state_structure(state_data):
                logging.debug(f"Successfully read state from {self.state_file_path}")
                return state_data
            else:
                logging.error(f"State file {self.state_file_path} has invalid structure")
                return None
        except Exception as e:
            logging.error(f"Error reading state from {self.state_file_path}: {str(e)}")
            return None

    def write_state(self, state_data: Dict[str, Any]) -> bool:
        """
        Write the pipeline state to disk.

        Args:
            state_data: State dictionary to write

        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate the state structure before writing
            if not self._validate_state_structure(state_data):
                logging.error("Attempted to write invalid state structure")
                return False

            # Add or update timestamp
            state_data["timestamp"] = datetime.utcnow().isoformat() + "Z"

            # Ensure directory exists
            self.ensure_state_directory()

            success = write_json_file(self.state_file_path, state_data)
            if success:
                logging.debug(f"Successfully wrote state to {self.state_file_path}")
            else:
                logging.error(f"Failed to write state to {self.state_file_path}")
            return success
        except Exception as e:
            logging.error(f"Error writing state to {self.state_file_path}: {str(e)}")
            return False

    def _validate_state_structure(self, state_data: Dict[str, Any]) -> bool:
        """
        Validate the structure of the state data.

        Args:
            state_data: State dictionary to validate

        Returns:
            True if structure is valid, False otherwise
        """
        try:
            # Check for required keys
            required_keys = {"state", "timestamp"}
            if not all(key in state_data for key in required_keys):
                logging.debug("State data missing required keys")
                return False

            # Validate state value
            if state_data["state"] not in [state.value for state in PipelineState]:
                logging.debug(f"Invalid pipeline state: {state_data['state']}")
                return False

            # Validate timestamp format
            if not is_valid_iso_datetime(state_data["timestamp"]):
                logging.debug(f"Invalid timestamp format: {state_data['timestamp']}")
                return False

            # Validate optional keys if present
            if "config_hash" in state_data and not isinstance(state_data["config_hash"], str):
                logging.debug("Invalid config_hash type")
                return False

            if "artifact_paths" in state_data:
                if not isinstance(state_data["artifact_paths"], dict):
                    logging.debug("Invalid artifact_paths type")
                    return False
                # Further validation is done by validate_artifact_paths

            if "approvals" in state_data:
                if not isinstance(state_data["approvals"], dict):
                    logging.debug("Invalid approvals type")
                    return False

            if "validation" in state_data:
                if not isinstance(state_data["validation"], dict):
                    logging.debug("Invalid validation type")
                    return False

            return True
        except Exception as e:
            logging.error(f"Error validating state structure: {str(e)}")
            return False

    def update_state(self, new_state: Union[PipelineState, str],
                     config: Optional[Dict[str, Any]] = None,
                     artifact_paths: Optional[Dict[str, str]] = None,
                     additional_data: Optional[Dict[str, Any]] = None,
                     validate_transition: bool = True) -> bool:
        """
        Update the pipeline state with optional validation.

        Args:
            new_state: New state to set (PipelineState enum or string)
            config: Optional configuration for hash calculation
            artifact_paths: Optional artifact paths to store
            additional_data: Optional additional data to merge
            validate_transition: Whether to validate the state transition (default: True)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert state to PipelineState enum if it's a string
            if isinstance(new_state, str):
                try:
                    new_state = PipelineState(new_state)
                except ValueError:
                    logging.error(f"Invalid state string: {new_state}")
                    return False

            # Read current state
            current_state_data = self.read_state()

            # If there's no existing state file, we're initializing the state
            # In this case, we don't validate the transition, just set the initial state
            if current_state_data is None:
                # Create initial state data
                updated_state_data = {
                    "state": new_state.value,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            else:
                # Optionally validate state transition from existing state to new state
                if validate_transition:
                    current_state = PipelineState(current_state_data["state"])
                    if not validate_state_transition(current_state, new_state):
                        error_msg = get_transition_error_message(current_state, new_state)
                        logging.error(error_msg)
                        return False

                # Prepare new state data
                updated_state_data = current_state_data.copy()
                updated_state_data["state"] = new_state.value

            # Add config hash if provided
            if config is not None:
                updated_state_data["config_hash"] = self._calculate_config_hash(config)

            # Add artifact paths if provided
            if artifact_paths is not None:
                updated_state_data["artifact_paths"] = artifact_paths

            # Add additional data if provided
            if additional_data is not None:
                updated_state_data.update(additional_data)

            # Write the updated state
            return self.write_state(updated_state_data)
        except Exception as e:
            logging.error(f"Error updating state: {str(e)}")
            return False

    def _calculate_config_hash(self, config: Dict[str, Any]) -> str:
        """
        Calculate a hash of the configuration for determinism validation.

        Args:
            config: Configuration dictionary to hash

        Returns:
            SHA256 hash string of the configuration
        """
        import hashlib
        import json

        # Convert config to a consistent string representation
        config_str = json.dumps(config, sort_keys=True, default=str)
        return hashlib.sha256(config_str.encode()).hexdigest()

    def get_current_state(self) -> Optional[PipelineState]:
        """
        Get the current pipeline state.

        Returns:
            Current PipelineState if available, None otherwise
        """
        try:
            state_data = self.read_state()
            if state_data and "state" in state_data:
                return PipelineState(state_data["state"])
            return None
        except Exception as e:
            logging.error(f"Error getting current state: {str(e)}")
            return None

    def check_state_corruption(self) -> bool:
        """
        Check for state file corruption by validating its structure and content.

        Returns:
            True if state appears valid, False if corrupted
        """
        try:
            state_data = self.read_state()
            if state_data is None:
                # No state file is not corruption, it's just empty
                return True

            # Perform validation checks
            if not self._validate_state_structure(state_data):
                logging.warning("State structure validation failed")
                return False

            # Check if timestamp is reasonable (not in the future)
            timestamp_str = state_data.get("timestamp", "")
            if timestamp_str and is_valid_iso_datetime(timestamp_str):
                try:
                    # Handle 'Z' suffix for UTC time
                    clean_timestamp = timestamp_str.replace('Z', '+00:00')

                    # Parse the timestamp appropriately
                    if '+' in clean_timestamp or (len(clean_timestamp) >= 6 and clean_timestamp[-6] in ['+', '-']):
                        # This has timezone info, remove it for comparison with naive utcnow()
                        # Split at the timezone indicator (+ or -) and take the datetime part
                        if '+' in clean_timestamp:
                            dt_part = clean_timestamp.split('+')[0]
                        else:
                            # Handle negative offset - find the last occurrence of '-' that indicates timezone
                            tz_pos = -1
                            for i in range(len(clean_timestamp)-1, -1, -1):
                                if clean_timestamp[i] in ['+', '-'] and i > 10:  # Basic check that it's likely a timezone
                                    tz_pos = i
                                    break
                            if tz_pos != -1:
                                dt_part = clean_timestamp[:tz_pos]
                            else:
                                dt_part = clean_timestamp

                        timestamp = datetime.fromisoformat(dt_part)
                    else:
                        # Naive datetime, parse directly
                        timestamp = datetime.fromisoformat(clean_timestamp.replace('Z', ''))

                    current_time = datetime.utcnow()
                    # Compare only the datetime parts to avoid timezone issues
                    if timestamp.replace(tzinfo=None) > current_time:
                        logging.warning("State timestamp is in the future")
                        return False
                except ValueError:
                    logging.warning("Could not parse state timestamp")
                    return False

            return True
        except Exception as e:
            logging.error(f"Error checking state corruption: {str(e)}")
            return False

    def reset_state(self) -> bool:
        """
        Reset the pipeline state to IDLE.

        Returns:
            True if successful, False otherwise
        """
        try:
            initial_state = {
                "state": PipelineState.IDLE.value,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            return self.write_state(initial_state)
        except Exception as e:
            logging.error(f"Error resetting state: {str(e)}")
            return False

    def log_state_change(self, from_state: Union[PipelineState, str],
                        to_state: Union[PipelineState, str],
                        reason: str = ""):
        """
        Log a state change for audit purposes.

        Args:
            from_state: Previous state
            to_state: New state
            reason: Reason for the state change
        """
        try:
            if isinstance(from_state, PipelineState):
                from_state = from_state.value
            if isinstance(to_state, PipelineState):
                to_state = to_state.value

            log_msg = f"State transition: {from_state} -> {to_state}"
            if reason:
                log_msg += f" (reason: {reason})"
            logging.info(log_msg)
        except Exception as e:
            logging.error(f"Error logging state change: {str(e)}")

    def validate_artifact_consistency(self, expected_artifacts: Optional[Dict[str, str]] = None) -> bool:
        """
        Validate that the artifacts referenced in the state actually exist.

        Args:
            expected_artifacts: Optional dictionary of expected artifacts to validate

        Returns:
            True if artifacts are consistent, False otherwise
        """
        try:
            state_data = self.read_state()
            if not state_data:
                return True  # No state to validate

            artifacts_to_check = expected_artifacts or state_data.get("artifact_paths", {})

            for name, path in artifacts_to_check.items():
                if path and not os.path.exists(path):
                    logging.warning(f"Expected artifact does not exist: {name} at {path}")
                    return False

            return True
        except Exception as e:
            logging.error(f"Error validating artifact consistency: {str(e)}")
            return False


class PipelineStateManager:
    """
    Higher-level class to orchestrate state operations for the pipeline.
    """

    def __init__(self, state_file_path: str = "pipeline_state.json"):
        """
        Initialize the pipeline state manager.

        Args:
            state_file_path: Path to the state file
        """
        self.persistence = StatePersistence(state_file_path)

    def initialize_pipeline(self, initial_config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Initialize the pipeline with IDLE state.

        Args:
            initial_config: Optional initial configuration for hash calculation

        Returns:
            True if successful, False otherwise
        """
        try:
            initial_state = {
                "state": PipelineState.IDLE.value,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

            if initial_config:
                initial_state["config_hash"] = self.persistence._calculate_config_hash(initial_config)

            return self.persistence.write_state(initial_state)
        except Exception as e:
            logging.error(f"Error initializing pipeline: {str(e)}")
            return False

    def get_pipeline_state(self) -> Optional[PipelineState]:
        """
        Get the current pipeline state.

        Returns:
            Current PipelineState if available, None otherwise
        """
        return self.persistence.get_current_state()

    def transition_to_extraction_in_progress(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Transition to EXTRACTION_IN_PROGRESS state.

        Args:
            config: Optional configuration for hash calculation

        Returns:
            True if successful, False otherwise
        """
        current_state = self.get_pipeline_state()
        if current_state in [None, PipelineState.IDLE]:
            return self.persistence.update_state(
                PipelineState.EXTRACTION_IN_PROGRESS,
                config=config,
                additional_data={"approvals": {"extraction": {"status": "PENDING"}}}
            )
        else:
            logging.error(f"Cannot transition from {current_state.value} to EXTRACTION_IN_PROGRESS")
            return False

    def transition_to_extraction_complete(self, extracted_content_path: str) -> bool:
        """
        Transition to EXTRACTION_COMPLETE state.

        Args:
            extracted_content_path: Path to the extracted content file

        Returns:
            True if successful, False otherwise
        """
        current_state = self.get_pipeline_state()
        if current_state == PipelineState.EXTRACTION_IN_PROGRESS:
            artifact_paths = {"extracted_content": extracted_content_path}
            return self.persistence.update_state(
                PipelineState.EXTRACTION_COMPLETE,
                artifact_paths=artifact_paths
            )
        else:
            logging.error(f"Cannot transition from {current_state.value} to EXTRACTION_COMPLETE")
            return False

    def transition_to_extraction_approved(self, approver: str) -> bool:
        """
        Transition to EXTRACTION_APPROVED state.

        Args:
            approver: Identifier of the approver

        Returns:
            True if successful, False otherwise
        """
        current_state = self.get_pipeline_state()
        if current_state == PipelineState.EXTRACTION_COMPLETE:
            additional_data = {
                "approvals": {
                    "extraction": {
                        "status": "APPROVED",
                        "approver": approver,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "decision": "APPROVE"
                    }
                }
            }
            return self.persistence.update_state(
                PipelineState.EXTRACTION_APPROVED,
                additional_data=additional_data
            )
        else:
            logging.error(f"Cannot transition from {current_state.value} to EXTRACTION_APPROVED")
            return False

    def transition_to_chunking_in_progress(self) -> bool:
        """
        Transition to CHUNKING_IN_PROGRESS state.

        Returns:
            True if successful, False otherwise
        """
        current_state = self.get_pipeline_state()
        if current_state == PipelineState.EXTRACTION_APPROVED:
            return self.persistence.update_state(
                PipelineState.CHUNKING_IN_PROGRESS,
                additional_data={"approvals": {"chunking": {"status": "PENDING"}}}
            )
        else:
            logging.error(f"Cannot transition from {current_state.value} to CHUNKING_IN_PROGRESS")
            return False

    def transition_to_chunking_complete(self, chunked_output_path: str) -> bool:
        """
        Transition to CHUNKING_COMPLETE state.

        Args:
            chunked_output_path: Path to the chunked output file

        Returns:
            True if successful, False otherwise
        """
        current_state = self.get_pipeline_state()
        if current_state == PipelineState.CHUNKING_IN_PROGRESS:
            artifact_paths = {"chunked_output": chunked_output_path}
            return self.persistence.update_state(
                PipelineState.CHUNKING_COMPLETE,
                artifact_paths=artifact_paths
            )
        else:
            logging.error(f"Cannot transition from {current_state.value} to CHUNKING_COMPLETE")
            return False

    def transition_to_chunking_approved(self, approver: str) -> bool:
        """
        Transition to CHUNKING_APPROVED state.

        Args:
            approver: Identifier of the approver

        Returns:
            True if successful, False otherwise
        """
        current_state = self.get_pipeline_state()
        if current_state == PipelineState.CHUNKING_COMPLETE:
            additional_data = {
                "approvals": {
                    "chunking": {
                        "status": "APPROVED",
                        "approver": approver,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "decision": "APPROVE"
                    }
                }
            }
            return self.persistence.update_state(
                PipelineState.CHUNKING_APPROVED,
                additional_data=additional_data
            )
        else:
            logging.error(f"Cannot transition from {current_state.value} to CHUNKING_APPROVED")
            return False

    def mark_as_failed(self, error_message: str = "") -> bool:
        """
        Mark the pipeline as FAILED.

        Args:
            error_message: Optional error message to log

        Returns:
            True if successful, False otherwise
        """
        current_state = self.get_pipeline_state()
        if current_state:
            if error_message:
                logging.error(f"Pipeline failed from state {current_state.value}: {error_message}")
            else:
                logging.error(f"Pipeline failed from state {current_state.value}")

            return self.persistence.update_state(PipelineState.FAILED)
        else:
            logging.error("Cannot mark pipeline as failed: no current state")
            return False

    def mark_as_rejected(self, rejection_reason: str = "") -> bool:
        """
        Mark the pipeline as REJECTED.

        Args:
            rejection_reason: Optional reason for rejection

        Returns:
            True if successful, False otherwise
        """
        current_state = self.get_pipeline_state()
        if current_state in [PipelineState.EXTRACTION_COMPLETE, PipelineState.CHUNKING_COMPLETE]:
            if rejection_reason:
                logging.info(f"Pipeline rejected from state {current_state.value}: {rejection_reason}")
            else:
                logging.info(f"Pipeline rejected from state {current_state.value}")

            return self.persistence.update_state(PipelineState.REJECTED)
        else:
            logging.error(f"Cannot reject pipeline from state {current_state.value}")
            return False