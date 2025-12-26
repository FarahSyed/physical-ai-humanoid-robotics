"""
Approval engine for the pipeline verification system.

This module implements the approval workflow with APPROVE, REJECT, REQUEST_CHANGE outcomes,
including approval persistence, validation, audit logging, and pause/resume logic.
"""
from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional, Union
import logging

from src.pipeline.state_machine import PipelineState
from src.pipeline.state_persistence import StatePersistence
from src.utils.validation_utils import validate_approval_decision, validate_approval_status


class ApprovalDecision(Enum):
    """Enum for approval outcomes."""
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_CHANGE = "REQUEST_CHANGE"


class ApprovalStatus(Enum):
    """Enum for approval status."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ApprovalRecord:
    """
    Represents a single approval record with approver information and decision.
    """
    def __init__(self, approver_id: str, decision: Union[ApprovalDecision, str],
                 context: str = "", pipeline_state: Optional[PipelineState] = None):
        """
        Initialize an approval record.

        Args:
            approver_id: String identifier for the approving user
            decision: Approval decision (APPROVE, REJECT, REQUEST_CHANGE)
            context: String describing the approval context
            pipeline_state: PipelineState at time of approval
        """
        if isinstance(decision, str):
            decision = ApprovalDecision(decision.upper())
        self.approver_id = approver_id
        self.decision = decision
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.context = context
        self.pipeline_state = pipeline_state

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the approval record to a dictionary.

        Returns:
            Dictionary representation of the approval record
        """
        return {
            "approver_id": self.approver_id,
            "decision": self.decision.value,
            "timestamp": self.timestamp,
            "context": self.context,
            "pipeline_state": self.pipeline_state.value if self.pipeline_state else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApprovalRecord':
        """
        Create an approval record from a dictionary.

        Args:
            data: Dictionary containing approval record data

        Returns:
            ApprovalRecord instance
        """
        record = cls.__new__(cls)
        record.approver_id = data["approver_id"]
        record.decision = ApprovalDecision(data["decision"])
        record.timestamp = data["timestamp"]
        record.context = data.get("context", "")
        state_value = data.get("pipeline_state")
        record.pipeline_state = PipelineState(state_value) if state_value else None
        return record


class ApprovalEngine:
    """
    Engine for managing the approval workflow in the pipeline system.
    """
    def __init__(self, state_persistence: StatePersistence):
        """
        Initialize the approval engine.

        Args:
            state_persistence: StatePersistence instance for managing state
        """
        self.state_persistence = state_persistence

    def request_approval(self, stage: str, content_preview: str = "") -> bool:
        """
        Request approval for a specific stage (extraction or chunking).

        Args:
            stage: The stage requiring approval ("extraction" or "chunking")
            content_preview: Preview of the content being approved

        Returns:
            True if approval request is successful, False otherwise
        """
        try:
            # Validate stage
            if stage not in ["extraction", "chunking"]:
                logging.error(f"Invalid approval stage: {stage}")
                return False

            # Get current state data
            current_state_data = self.state_persistence.read_state()
            if not current_state_data:
                logging.error("Cannot request approval: no current state data")
                return False

            # Update approval status to PENDING
            approvals = current_state_data.get("approvals", {})
            stage_approval = approvals.get(stage, {})
            stage_approval["status"] = ApprovalStatus.PENDING.value
            stage_approval["timestamp"] = datetime.utcnow().isoformat() + "Z"
            stage_approval["content_preview"] = content_preview

            approvals[stage] = stage_approval
            current_state_data["approvals"] = approvals

            # Write updated state
            return self.state_persistence.write_state(current_state_data)
        except Exception as e:
            logging.error(f"Error requesting approval for {stage}: {str(e)}")
            return False

    def process_approval(self, stage: str, approver_id: str, decision: Union[ApprovalDecision, str],
                       context: str = "") -> bool:
        """
        Process an approval decision for a specific stage.

        Args:
            stage: The stage being approved ("extraction" or "chunking")
            approver_id: Identifier of the approver
            decision: Approval decision (APPROVE, REJECT, REQUEST_CHANGE)
            context: Context or reason for the decision

        Returns:
            True if approval processing is successful, False otherwise
        """
        try:
            # Validate inputs
            if stage not in ["extraction", "chunking"]:
                logging.error(f"Invalid approval stage: {stage}")
                return False

            decision_str = decision.value if isinstance(decision, ApprovalDecision) else str(decision).upper()
            if not validate_approval_decision(decision_str):
                logging.error(f"Invalid approval decision: {decision}")
                return False

            if isinstance(decision, str):
                decision = ApprovalDecision(decision.upper())

            # Get current state data
            current_state_data = self.state_persistence.read_state()
            if not current_state_data:
                logging.error("Cannot process approval: no current state data")
                return False

            # Get current pipeline state
            current_state = self.state_persistence.get_current_state()

            # Validate that we're at the right point for approval
            expected_states = {
                "extraction": [PipelineState.EXTRACTION_COMPLETE],
                "chunking": [PipelineState.CHUNKING_COMPLETE]
            }
            if current_state not in expected_states[stage]:
                logging.error(f"Cannot approve {stage} from state {current_state.value if current_state else 'None'}")
                return False

            # Create approval record
            approval_record = ApprovalRecord(
                approver_id=approver_id,
                decision=decision,
                context=context,
                pipeline_state=current_state
            )

            # Update approval data
            approvals = current_state_data.get("approvals", {})
            stage_approval = approvals.get(stage, {})

            # Add approval record data
            stage_approval.update({
                "status": ApprovalStatus.APPROVED.value if decision == ApprovalDecision.APPROVE else ApprovalStatus.REJECTED.value,
                "approver": approver_id,
                "timestamp": approval_record.timestamp,
                "decision": decision.value,
                "context": context
            })

            approvals[stage] = stage_approval
            current_state_data["approvals"] = approvals

            # Log the approval decision
            self._log_approval_decision(stage, approver_id, decision.value, context)

            # Handle the decision outcome
            if decision == ApprovalDecision.APPROVE:
                return self._handle_approval_approved(stage, current_state_data)
            elif decision == ApprovalDecision.REJECT:
                return self._handle_approval_rejected(stage, current_state_data)
            elif decision == ApprovalDecision.REQUEST_CHANGE:
                return self._handle_approval_request_change(stage, current_state_data)

        except Exception as e:
            logging.error(f"Error processing approval for {stage}: {str(e)}")
            return False

    def _handle_approval_approved(self, stage: str, state_data: Dict[str, Any]) -> bool:
        """
        Handle the case when an approval is approved.

        Args:
            stage: The stage that was approved
            state_data: Current state data to update

        Returns:
            True if handling is successful, False otherwise
        """
        try:
            # Determine the next state based on the stage
            if stage == "extraction":
                next_state = PipelineState.EXTRACTION_APPROVED
            elif stage == "chunking":
                next_state = PipelineState.CHUNKING_APPROVED
            else:
                logging.error(f"Unknown stage for approval: {stage}")
                return False

            # Update the pipeline state
            state_data["state"] = next_state.value
            state_data["timestamp"] = datetime.utcnow().isoformat() + "Z"

            # Write the updated state
            success = self.state_persistence.write_state(state_data)
            if success:
                logging.info(f"{stage.capitalize()} stage approved, transitioning to {next_state.value}")
            return success
        except Exception as e:
            logging.error(f"Error handling approval for {stage}: {str(e)}")
            return False

    def _handle_approval_rejected(self, stage: str, state_data: Dict[str, Any]) -> bool:
        """
        Handle the case when an approval is rejected.

        Args:
            stage: The stage that was rejected
            state_data: Current state data to update

        Returns:
            True if handling is successful, False otherwise
        """
        try:
            # Update the pipeline state to REJECTED
            state_data["state"] = PipelineState.REJECTED.value
            state_data["timestamp"] = datetime.utcnow().isoformat() + "Z"

            # Write the updated state
            success = self.state_persistence.write_state(state_data)
            if success:
                logging.info(f"{stage.capitalize()} stage rejected, pipeline marked as REJECTED")
            return success
        except Exception as e:
            logging.error(f"Error handling rejection for {stage}: {str(e)}")
            return False

    def _handle_approval_request_change(self, stage: str, state_data: Dict[str, Any]) -> bool:
        """
        Handle the case when an approval requests changes.

        Args:
            stage: The stage that requested changes
            state_data: Current state data to update

        Returns:
            True if handling is successful, False otherwise
        """
        try:
            # For REQUEST_CHANGE, we might need to revert to a previous state
            # This implementation keeps the state as is but logs the request
            current_state = state_data.get("state", "")
            state_data["timestamp"] = datetime.utcnow().isoformat() + "Z"

            # Write the updated state
            success = self.state_persistence.write_state(state_data)
            if success:
                logging.info(f"{stage.capitalize()} stage requested changes, remaining at {current_state}")
            return success
        except Exception as e:
            logging.error(f"Error handling change request for {stage}: {str(e)}")
            return False

    def _log_approval_decision(self, stage: str, approver_id: str, decision: str, context: str):
        """
        Log the approval decision for audit purposes.

        Args:
            stage: The stage being approved
            approver_id: Identifier of the approver
            decision: The decision made
            context: Context or reason for the decision
        """
        log_msg = f"Approval decision: {stage} stage, approver={approver_id}, decision={decision}"
        if context:
            log_msg += f", context={context}"
        logging.info(log_msg)

    def check_approval_status(self, stage: str) -> Optional[str]:
        """
        Check the approval status for a specific stage.

        Args:
            stage: The stage to check ("extraction" or "chunking")

        Returns:
            Approval status (PENDING, APPROVED, REJECTED) or None if error
        """
        try:
            state_data = self.state_persistence.read_state()
            if not state_data or "approvals" not in state_data:
                return None

            approvals = state_data["approvals"]
            if stage not in approvals:
                return None

            stage_approval = approvals[stage]
            return stage_approval.get("status")
        except Exception as e:
            logging.error(f"Error checking approval status for {stage}: {str(e)}")
            return None

    def pause_pipeline_for_approval(self, stage: str) -> bool:
        """
        Pause the pipeline execution to wait for approval.

        Args:
            stage: The stage requiring approval ("extraction" or "chunking")

        Returns:
            True if pausing is successful, False otherwise
        """
        try:
            status = self.check_approval_status(stage)
            if status == ApprovalStatus.PENDING.value:
                logging.info(f"Pipeline paused for {stage} approval")
                return True
            else:
                logging.warning(f"Pipeline not paused - {stage} approval status is {status}")
                return False
        except Exception as e:
            logging.error(f"Error pausing pipeline for {stage} approval: {str(e)}")
            return False

    def resume_pipeline_after_approval(self, stage: str) -> bool:
        """
        Resume the pipeline execution after approval is received.

        Args:
            stage: The stage that was approved ("extraction" or "chunking")

        Returns:
            True if resuming is successful, False otherwise
        """
        try:
            status = self.check_approval_status(stage)
            if status == ApprovalStatus.APPROVED.value:
                logging.info(f"Pipeline resuming after {stage} approval")
                return True
            else:
                logging.warning(f"Pipeline not resuming - {stage} approval status is {status}")
                return False
        except Exception as e:
            logging.error(f"Error resuming pipeline after {stage} approval: {str(e)}")
            return False

    def get_approval_record(self, stage: str) -> Optional[Dict[str, Any]]:
        """
        Get the approval record for a specific stage.

        Args:
            stage: The stage to get approval record for ("extraction" or "chunking")

        Returns:
            Approval record dictionary or None if not found
        """
        try:
            state_data = self.state_persistence.read_state()
            if not state_data or "approvals" not in state_data:
                return None

            approvals = state_data["approvals"]
            if stage not in approvals:
                return None

            return approvals[stage]
        except Exception as e:
            logging.error(f"Error getting approval record for {stage}: {str(e)}")
            return None

    def validate_approvals(self) -> bool:
        """
        Validate all approvals in the current state.

        Returns:
            True if all approvals are valid, False otherwise
        """
        try:
            state_data = self.state_persistence.read_state()
            if not state_data or "approvals" not in state_data:
                return True  # No approvals to validate

            approvals = state_data["approvals"]
            for stage, approval in approvals.items():
                # Validate status
                status = approval.get("status")
                if status and not validate_approval_status(status):
                    logging.error(f"Invalid approval status for {stage}: {status}")
                    return False

                # Validate decision
                decision = approval.get("decision")
                if decision and not validate_approval_decision(decision):
                    logging.error(f"Invalid approval decision for {stage}: {decision}")
                    return False

            return True
        except Exception as e:
            logging.error(f"Error validating approvals: {str(e)}")
            return False