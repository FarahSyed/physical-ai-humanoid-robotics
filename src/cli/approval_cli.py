"""
CLI commands for approval workflows in the pipeline verification system.

This module implements CLI commands for approval, rejection, and preview functionality.
"""
import argparse
import sys
from typing import Optional
import logging

from src.pipeline.approval_engine import ApprovalEngine, ApprovalDecision
from src.pipeline.state_persistence import StatePersistence
from src.pipeline.preview_service import PreviewService


def create_approval_parser():
    """Create the argument parser for approval commands."""
    parser = argparse.ArgumentParser(
        description="Approval commands for pipeline verification system. These commands allow you to approve, reject, or request changes to content at different stages of the pipeline.",
        prog="approval"
    )

    subparsers = parser.add_subparsers(dest="approval_command", help="Approval command")

    # Approve command
    approve_parser = subparsers.add_parser("approve", help="Approve content at specified stage")
    approve_parser.add_argument(
        "stage",
        choices=["extraction", "chunking"],
        help="Stage to approve (extraction or chunking)"
    )
    approve_parser.add_argument(
        "--approver",
        required=True,
        help="Identifier of the approver"
    )
    approve_parser.add_argument(
        "--reason",
        help="Reason or context for the approval"
    )

    # Reject command
    reject_parser = subparsers.add_parser("reject", help="Reject content at specified stage")
    reject_parser.add_argument(
        "stage",
        choices=["extraction", "chunking"],
        help="Stage to reject (extraction or chunking)"
    )
    reject_parser.add_argument(
        "--approver",
        required=True,
        help="Identifier of the person rejecting"
    )
    reject_parser.add_argument(
        "--reason",
        help="Reason for rejection"
    )

    # Request change command
    request_change_parser = subparsers.add_parser("request-change", help="Request changes to content at specified stage")
    request_change_parser.add_argument(
        "stage",
        choices=["extraction", "chunking"],
        help="Stage to request changes for (extraction or chunking)"
    )
    request_change_parser.add_argument(
        "--approver",
        required=True,
        help="Identifier of the person requesting changes"
    )
    request_change_parser.add_argument(
        "--reason",
        help="Reason for requesting changes"
    )

    # Preview command
    preview_parser = subparsers.add_parser("preview", help="Preview content at specified stage")
    preview_parser.add_argument(
        "stage",
        choices=["extraction", "chunking"],
        help="Stage to preview (extraction or chunking)"
    )
    preview_parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Starting position for preview (default: 0)"
    )
    preview_parser.add_argument(
        "--limit",
        type=int,
        help="Number of characters to include in preview (default: system default)"
    )

    return parser


def handle_approve_command(args: argparse.Namespace, approval_engine: ApprovalEngine) -> bool:
    """
    Handle the approve command.

    Args:
        args: Parsed command line arguments
        approval_engine: ApprovalEngine instance

    Returns:
        True if successful, False otherwise
    """
    try:
        decision = ApprovalDecision.APPROVE
        success = approval_engine.process_approval(
            stage=args.stage,
            approver_id=args.approver,
            decision=decision,
            context=args.reason or ""
        )

        if success:
            print(f"Content at {args.stage} stage approved by {args.approver}")
            if args.reason:
                print(f"Reason: {args.reason}")
            return True
        else:
            print(f"Failed to approve content at {args.stage} stage")
            return False
    except Exception as e:
        logging.error(f"Error handling approve command: {str(e)}")
        print(f"Error approving content: {str(e)}")
        return False


def handle_reject_command(args: argparse.Namespace, approval_engine: ApprovalEngine) -> bool:
    """
    Handle the reject command.

    Args:
        args: Parsed command line arguments
        approval_engine: ApprovalEngine instance

    Returns:
        True if successful, False otherwise
    """
    try:
        decision = ApprovalDecision.REJECT
        success = approval_engine.process_approval(
            stage=args.stage,
            approver_id=args.approver,
            decision=decision,
            context=args.reason or ""
        )

        if success:
            print(f"Content at {args.stage} stage rejected by {args.approver}")
            if args.reason:
                print(f"Reason: {args.reason}")
            return True
        else:
            print(f"Failed to reject content at {args.stage} stage")
            return False
    except Exception as e:
        logging.error(f"Error handling reject command: {str(e)}")
        print(f"Error rejecting content: {str(e)}")
        return False


def handle_request_change_command(args: argparse.Namespace, approval_engine: ApprovalEngine) -> bool:
    """
    Handle the request-change command.

    Args:
        args: Parsed command line arguments
        approval_engine: ApprovalEngine instance

    Returns:
        True if successful, False otherwise
    """
    try:
        decision = ApprovalDecision.REQUEST_CHANGE
        success = approval_engine.process_approval(
            stage=args.stage,
            approver_id=args.approver,
            decision=decision,
            context=args.reason or ""
        )

        if success:
            print(f"Change requested for content at {args.stage} stage by {args.approver}")
            if args.reason:
                print(f"Reason: {args.reason}")
            return True
        else:
            print(f"Failed to request changes for content at {args.stage} stage")
            return False
    except Exception as e:
        logging.error(f"Error handling request-change command: {str(e)}")
        print(f"Error requesting changes: {str(e)}")
        return False


def handle_preview_command(args: argparse.Namespace, state_persistence: StatePersistence, preview_service: PreviewService) -> bool:
    """
    Handle the preview command.

    Args:
        args: Parsed command line arguments
        state_persistence: StatePersistence instance
        preview_service: PreviewService instance

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get current state to determine the path to preview
        current_state_data = state_persistence.read_state()
        if not current_state_data:
            print("No pipeline state found to preview")
            return False

        # Get the appropriate path based on the stage
        artifact_paths = current_state_data.get("artifact_paths", {})
        if args.stage == "extraction":
            content_path = artifact_paths.get("extracted_content")
        elif args.stage == "chunking":
            content_path = artifact_paths.get("chunked_output")
        else:
            print(f"Unknown stage: {args.stage}")
            return False

        if not content_path:
            print(f"No content path found for {args.stage} stage")
            return False

        # Generate preview
        if args.stage == "extraction":
            preview_result = preview_service.preview_extracted_content(
                content_path=content_path,
                offset=args.offset,
                limit=args.limit
            )
        else:  # chunking
            preview_result = preview_service.preview_chunked_output(
                chunks_path=content_path,
                offset=args.offset,
                limit=args.limit
            )

        if preview_result and "preview_content" in preview_result:
            print(f"Preview for {args.stage} stage:")
            print("-" * 40)
            print(preview_result["preview_content"])
            print("-" * 40)
            print(f"Total length: {preview_result.get('total_length', 'N/A')}")
            print(f"Preview length: {preview_result.get('preview_length', 'N/A')}")
            if "chunk_total" in preview_result:
                print(f"Total chunks: {preview_result['chunk_total']}")
            return True
        else:
            print(f"Failed to generate preview for {args.stage} stage")
            return False
    except Exception as e:
        logging.error(f"Error handling preview command: {str(e)}")
        print(f"Error generating preview: {str(e)}")
        return False


def run_approval_cli(args: argparse.Namespace, approval_engine: ApprovalEngine,
                    state_persistence: StatePersistence, preview_service: PreviewService) -> int:
    """
    Run the approval CLI with the provided arguments.

    Args:
        args: Parsed command line arguments
        approval_engine: ApprovalEngine instance
        state_persistence: StatePersistence instance
        preview_service: PreviewService instance

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        if args.approval_command == "approve":
            success = handle_approve_command(args, approval_engine)
        elif args.approval_command == "reject":
            success = handle_reject_command(args, approval_engine)
        elif args.approval_command == "request-change":
            success = handle_request_change_command(args, approval_engine)
        elif args.approval_command == "preview":
            success = handle_preview_command(args, state_persistence, preview_service)
        else:
            print(f"Unknown approval command: {args.approval_command}")
            return 1

        return 0 if success else 1
    except Exception as e:
        logging.error(f"Error running approval CLI: {str(e)}")
        print(f"Error running approval command: {str(e)}")
        return 1


def interactive_approve_content(stage: str, approval_engine: ApprovalEngine) -> bool:
    """
    Interactive approval of content with user prompts.

    Args:
        stage: Stage to approve ("extraction" or "chunking")
        approval_engine: ApprovalEngine instance

    Returns:
        True if approved, False otherwise
    """
    try:
        print(f"Interactive approval for {stage} stage")
        approver = input("Enter your identifier (name/user ID): ").strip()

        if not approver:
            print("Approver identifier is required")
            return False

        print("\nOptions:")
        print("1. Approve")
        print("2. Reject")
        print("3. Request changes")

        while True:
            choice = input("\nSelect an option (1-3): ").strip()

            if choice == "1":
                decision = ApprovalDecision.APPROVE
                break
            elif choice == "2":
                decision = ApprovalDecision.REJECT
                break
            elif choice == "3":
                decision = ApprovalDecision.REQUEST_CHANGE
                break
            else:
                print("Invalid choice. Please select 1, 2, or 3.")

        reason = input("Enter reason/context (optional): ").strip()

        success = approval_engine.process_approval(
            stage=stage,
            approver_id=approver,
            decision=decision,
            context=reason
        )

        if success:
            decision_text = decision.value
            print(f"\nContent at {stage} stage {decision_text.lower()} by {approver}")
            if reason:
                print(f"Reason: {reason}")
        else:
            print(f"Failed to process approval for {stage} stage")

        return success
    except KeyboardInterrupt:
        print("\nApproval cancelled by user")
        return False
    except Exception as e:
        logging.error(f"Error in interactive approval: {str(e)}")
        print(f"Error in interactive approval: {str(e)}")
        return False