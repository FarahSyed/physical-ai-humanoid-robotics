"""
Main CLI interface for the pipeline verification system.

This module integrates all components into a cohesive CLI tool with commands for
starting the pipeline, checking status, resuming, validating, and more.
"""
import argparse
import sys
from typing import Optional
import logging

from src.pipeline.state_machine import PipelineState
from src.pipeline.state_persistence import StatePersistence, PipelineStateManager
from src.pipeline.approval_engine import ApprovalEngine
from src.pipeline.preview_service import PreviewService
from src.pipeline.resume_logic import ResumeLogic
from src.pipeline.verification_service import VerificationService
from src.cli.approval_cli import create_approval_parser, run_approval_cli, interactive_approve_content


def create_pipeline_parser():
    """Create the main argument parser for the pipeline CLI."""
    parser = argparse.ArgumentParser(
        description="Pipeline Verification System CLI - A comprehensive tool for managing content extraction, chunking, and embedding pipelines with human approval gates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s start --config pipeline_config.json
    Start a new pipeline with the specified configuration

  %(prog)s start --dry-run
    Run the pipeline in dry-run mode without making irreversible changes

  %(prog)s status
    Check the current status of the pipeline

  %(prog)s approval approve extraction --approver "user123" --reason "Content looks good"
    Approve the extracted content

  %(prog)s approval preview chunking --offset 0 --limit 500
    Preview the chunked output with first 500 characters

  %(prog)s resume
    Resume the pipeline from the last saved state

  %(prog)s resume --force-extraction
    Force the pipeline to restart from the beginning (IDLE state)

  %(prog)s validate
    Validate the current pipeline configuration and state

  %(prog)s approval reject chunking --approver "user123" --reason "Chunks need adjustment"
    Reject the chunked output and require changes
        """
    )

    # Global arguments
    parser.add_argument(
        "--state-file",
        default="pipeline_state.json",
        help="Path to the pipeline state file (default: pipeline_state.json)"
    )
    parser.add_argument(
        "--config",
        help="Path to the pipeline configuration file"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start the pipeline",
                                        description="Start a new pipeline execution. This command initializes the pipeline state and begins processing content according to the specified configuration.")
    start_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode without making irreversible changes"
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Get current pipeline status",
                                         description="Display the current status of the pipeline including state, approval status, and artifacts.")

    # Resume command
    resume_parser = subparsers.add_parser("resume", help="Resume the pipeline from last state",
                                        description="Resume the pipeline from the last saved state. This command will determine the appropriate state to resume from based on the current state and approval status.")
    resume_parser.add_argument(
        "--force-extraction",
        action="store_true",
        help="Force re-extraction even if already completed (resumes from IDLE state)"
    )
    resume_parser.add_argument(
        "--force-chunking",
        action="store_true",
        help="Force re-chunking even if already completed (resumes from EXTRACTION_APPROVED state)"
    )

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate pipeline configuration and state",
                                          description="Validate the current pipeline configuration and state for consistency and completeness. This command runs various checks to ensure the pipeline is ready for execution.")

    # Approval commands
    approval_parser = subparsers.add_parser("approval", parents=[create_approval_parser()], add_help=False,
                                          help="Handle approval workflows for pipeline stages",
                                          description="Manage approval workflows for pipeline stages. Use this command to approve, reject, or preview content at different stages of the pipeline.")

    return parser


def handle_start_command(args: argparse.Namespace) -> int:
    """
    Handle the start command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Initialize components
        state_persistence = StatePersistence(args.state_file)
        approval_engine = ApprovalEngine(state_persistence)
        preview_service = PreviewService()
        resume_logic = ResumeLogic(state_persistence)
        verification_service = VerificationService()

        # Enable dry-run if requested
        if args.dry_run:
            verification_service.enable_dry_run_mode()
            print("Running in DRY-RUN mode - no irreversible changes will be made")

        # Check if pipeline is already running
        current_state = state_persistence.get_current_state()
        if current_state and current_state != PipelineState.IDLE and current_state != PipelineState.FAILED and current_state != PipelineState.REJECTED:
            print(f"Pipeline is currently in state: {current_state.value}")
            print("Use 'resume' command to continue or 'status' to check status")
            return 1

        # Initialize pipeline
        state_manager = PipelineStateManager(args.state_file)
        config = None
        if args.config:
            from src.utils.file_utils import read_json_file
            config = read_json_file(args.config)
            if not config:
                print(f"Failed to read configuration from {args.config}")
                return 1

        if not state_manager.initialize_pipeline(config):
            print("Failed to initialize pipeline")
            return 1

        print("Pipeline initialized successfully")
        print(f"Current state: {state_manager.get_pipeline_state().value}")

        # In a real implementation, this would start the actual pipeline process
        # For now, we'll just show the starting state
        print("Pipeline started. Use 'status' to check progress or 'approval' commands for approval gates.")

        return 0
    except Exception as e:
        logging.error(f"Error in start command: {str(e)}")
        print(f"Error starting pipeline: {str(e)}")
        return 1


def handle_status_command(args: argparse.Namespace) -> int:
    """
    Handle the status command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        state_persistence = StatePersistence(args.state_file)
        current_state = state_persistence.get_current_state()

        if current_state is None:
            print("No pipeline state found. Use 'start' to begin a new pipeline.")
            return 0

        print(f"Current pipeline state: {current_state.value}")

        # Show additional status information
        state_data = state_persistence.read_state()
        if state_data:
            timestamp = state_data.get("timestamp", "unknown")
            print(f"State last updated: {timestamp}")

            # Show approval status if available
            approvals = state_data.get("approvals", {})
            if approvals:
                print("Approval status:")
                for stage, approval in approvals.items():
                    status = approval.get("status", "UNKNOWN")
                    approver = approval.get("approver", "N/A")
                    decision = approval.get("decision", "N/A")
                    print(f"  {stage}: {status} (approver: {approver}, decision: {decision})")

            # Show artifact paths if available
            artifact_paths = state_data.get("artifact_paths", {})
            if artifact_paths:
                print("Artifacts:")
                for name, path in artifact_paths.items():
                    print(f"  {name}: {path}")

        return 0
    except Exception as e:
        logging.error(f"Error in status command: {str(e)}")
        print(f"Error getting pipeline status: {str(e)}")
        return 1


def handle_resume_command(args: argparse.Namespace) -> int:
    """
    Handle the resume command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        state_persistence = StatePersistence(args.state_file)
        resume_logic = ResumeLogic(state_persistence)

        # Get resume recommendation
        recommendation = resume_logic.get_resume_recommendation()
        print(f"Current state: {recommendation['current_state']}")
        print(f"Recommended resume state: {recommendation['recommended_resume_state']}")
        print(f"Action: {recommendation['action']}")
        print(f"Message: {recommendation['message']}")
        print(f"Artifacts valid: {recommendation['artifacts_valid']}")

        if not recommendation['artifacts_valid']:
            print("WARNING: Some required artifacts may be missing!")
            response = input("Continue with resume? (y/N): ").strip().lower()
            if response != 'y':
                print("Resume cancelled by user")
                return 1

        # Perform resume
        resume_state = resume_logic.resume_from_state(
            force_extraction=args.force_extraction,
            force_chunking=args.force_chunking
        )

        if resume_state:
            print(f"Pipeline resumed successfully to state: {resume_state.value}")
            print("Use 'status' to check current status or continue processing.")
        else:
            print("Failed to resume pipeline")
            return 1

        return 0
    except Exception as e:
        logging.error(f"Error in resume command: {str(e)}")
        print(f"Error resuming pipeline: {str(e)}")
        return 1


def handle_validate_command(args: argparse.Namespace) -> int:
    """
    Handle the validate command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        verification_service = VerificationService()
        validation_report = verification_service.generate_validation_report()

        print("Pipeline Validation Report:")
        print(f"Generated at: {validation_report['timestamp']}")
        print(f"Validation type: {validation_report['validation_type']}")

        if 'error' in validation_report:
            print(f"Error: {validation_report['error']}")
            return 1

        print("\nValidation Checks:")
        for check_name, check_info in validation_report['checks'].items():
            status = check_info.get('status', 'unknown')
            print(f"  {check_name}: {status}")

        print(f"\nSummary: {validation_report['summary']['passed']} passed, "
              f"{validation_report['summary']['failed']} failed, "
              f"{validation_report['summary']['total']} total")

        return 0
    except Exception as e:
        logging.error(f"Error in validate command: {str(e)}")
        print(f"Error validating pipeline: {str(e)}")
        return 1


def handle_approval_command(args: argparse.Namespace) -> int:
    """
    Handle the approval command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        state_persistence = StatePersistence(args.state_file)
        approval_engine = ApprovalEngine(state_persistence)
        preview_service = PreviewService()

        # Create a temporary args object with the approval-specific command
        temp_args = argparse.Namespace(
            approval_command=args.approval_command,
            stage=getattr(args, 'stage', None),
            approver=getattr(args, 'approver', None),
            reason=getattr(args, 'reason', None),
            offset=getattr(args, 'offset', 0),
            limit=getattr(args, 'limit', None)
        )

        return run_approval_cli(temp_args, approval_engine, state_persistence, preview_service)
    except Exception as e:
        logging.error(f"Error in approval command: {str(e)}")
        print(f"Error in approval command: {str(e)}")
        return 1


def main():
    """
    Main entry point for the pipeline CLI.
    """
    parser = create_pipeline_parser()
    args = parser.parse_args()

    # If no command is provided, show help
    if not args.command:
        parser.print_help()
        return 0

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Route to appropriate handler
    if args.command == "start":
        return handle_start_command(args)
    elif args.command == "status":
        return handle_status_command(args)
    elif args.command == "resume":
        return handle_resume_command(args)
    elif args.command == "validate":
        return handle_validate_command(args)
    elif args.command == "approval":
        return handle_approval_command(args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())