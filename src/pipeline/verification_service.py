"""
Verification service for the pipeline verification system.

This module implements determinism guarantees, validation paths, and dry-run execution
for the pipeline system.
"""
from typing import Dict, Any, Optional, List
import hashlib
import json
from datetime import datetime
import logging

from src.utils.validation_utils import calculate_config_hash, validate_config_hash


class VerificationService:
    """
    Service for handling verification, determinism checks, and dry-run execution.
    """
    def __init__(self):
        """
        Initialize the verification service.
        """
        self.dry_run_mode = False

    def enable_dry_run_mode(self):
        """
        Enable dry-run mode where no irreversible changes are made.
        """
        self.dry_run_mode = True
        logging.info("Dry-run mode enabled - no irreversible operations will be performed")

    def disable_dry_run_mode(self):
        """
        Disable dry-run mode.
        """
        self.dry_run_mode = False
        logging.info("Dry-run mode disabled")

    def is_dry_run_mode(self) -> bool:
        """
        Check if dry-run mode is enabled.

        Returns:
            True if dry-run mode is enabled, False otherwise
        """
        return self.dry_run_mode

    def calculate_deterministic_hash(self, input_data: Any, config: Optional[Dict[str, Any]] = None) -> str:
        """
        Calculate a deterministic hash for the input data and configuration.

        Args:
            input_data: Input data to hash
            config: Optional configuration to include in hash

        Returns:
            SHA256 hash string
        """
        try:
            # Convert input data to string representation
            input_str = str(input_data)

            # If config is provided, include it in the hash
            if config is not None:
                config_str = str(sorted(config.items()))
                combined_str = input_str + config_str
            else:
                combined_str = input_str

            # Calculate SHA256 hash
            return hashlib.sha256(combined_str.encode()).hexdigest()
        except Exception as e:
            logging.error(f"Error calculating deterministic hash: {str(e)}")
            return ""

    def verify_determinism(self, input_data: Any, config: Dict[str, Any],
                          expected_hash: str) -> bool:
        """
        Verify that the operation produces deterministic results.

        Args:
            input_data: Input data to verify
            config: Configuration used for the operation
            expected_hash: Expected hash to compare against

        Returns:
            True if operation is deterministic, False otherwise
        """
        try:
            actual_hash = self.calculate_deterministic_hash(input_data, config)
            is_deterministic = actual_hash == expected_hash

            if is_deterministic:
                logging.debug("Determinism verification passed")
            else:
                logging.warning(f"Determinism verification failed: expected {expected_hash}, got {actual_hash}")

            return is_deterministic
        except Exception as e:
            logging.error(f"Error verifying determinism: {str(e)}")
            return False

    def perform_dry_run(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a dry-run of an operation without making irreversible changes.

        Args:
            operation: Type of operation to perform dry-run for
            params: Parameters for the operation

        Returns:
            Dictionary with dry-run results
        """
        try:
            logging.info(f"Performing dry-run for operation: {operation}")

            # Log what would happen without doing it
            result = {
                "operation": operation,
                "params": params,
                "dry_run": True,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "would_perform": True,
                "impact": "no_changes_made",
                "validation_passed": True,
                "warnings": []
            }

            # Perform validation checks that would be done during real operation
            validation_result = self._validate_operation(operation, params)
            result["validation_passed"] = validation_result["valid"]
            if not validation_result["valid"]:
                result["warnings"].extend(validation_result.get("errors", []))

            logging.info(f"Dry-run completed for operation: {operation}")
            return result
        except Exception as e:
            logging.error(f"Error performing dry-run for {operation}: {str(e)}")
            return {
                "operation": operation,
                "params": params,
                "dry_run": True,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "would_perform": False,
                "impact": "error_occurred",
                "validation_passed": False,
                "errors": [str(e)],
                "warnings": []
            }

    def _validate_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate an operation without performing it.

        Args:
            operation: Type of operation to validate
            params: Parameters for the operation

        Returns:
            Dictionary with validation results
        """
        try:
            result = {
                "valid": True,
                "errors": [],
                "warnings": []
            }

            # Basic validation based on operation type
            if operation == "extract_content":
                if "source_path" not in params:
                    result["valid"] = False
                    result["errors"].append("Missing source_path parameter")
                elif not params["source_path"]:
                    result["valid"] = False
                    result["errors"].append("Empty source_path parameter")

            elif operation == "chunk_content":
                if "content_path" not in params:
                    result["valid"] = False
                    result["errors"].append("Missing content_path parameter")
                elif not params["content_path"]:
                    result["valid"] = False
                    result["errors"].append("Empty content_path parameter")

            elif operation == "approve_extraction":
                if "approver" not in params:
                    result["valid"] = False
                    result["errors"].append("Missing approver parameter")

            elif operation == "approve_chunking":
                if "approver" not in params:
                    result["valid"] = False
                    result["errors"].append("Missing approver parameter")

            return result
        except Exception as e:
            logging.error(f"Error validating operation {operation}: {str(e)}")
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": []
            }

    def validate_configuration(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate pipeline configuration for correctness.

        Args:
            config: Configuration to validate

        Returns:
            Dictionary with validation results
        """
        try:
            result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "config_hash": calculate_config_hash(config)
            }

            # Validate required configuration keys
            required_keys = ["input_path", "output_path"]
            for key in required_keys:
                if key not in config:
                    result["valid"] = False
                    result["errors"].append(f"Missing required configuration key: {key}")
                elif not config[key]:
                    result["valid"] = False
                    result["errors"].append(f"Configuration key '{key}' cannot be empty")
                elif not isinstance(config[key], str):
                    result["valid"] = False
                    result["errors"].append(f"Configuration key '{key}' must be a string")

            # Validate configuration values
            if "input_path" in config and isinstance(config["input_path"], str):
                if not config["input_path"].strip():
                    result["valid"] = False
                    result["errors"].append("input_path cannot be empty or whitespace")
                # Check for potentially dangerous paths
                elif ".." in config["input_path"]:
                    result["valid"] = False
                    result["warnings"].append("input_path contains '..' which may be unsafe - verify path is intended")

            if "output_path" in config and isinstance(config["output_path"], str):
                if not config["output_path"].strip():
                    result["valid"] = False
                    result["errors"].append("output_path cannot be empty or whitespace")
                # Check for potentially dangerous paths
                elif ".." in config["output_path"]:
                    result["valid"] = False
                    result["warnings"].append("output_path contains '..' which may be unsafe - verify path is intended")

            # Check for deprecated or invalid keys
            deprecated_keys = ["old_setting", "deprecated_option"]
            for key in deprecated_keys:
                if key in config:
                    result["warnings"].append(f"Deprecated configuration key found: {key}")

            return result
        except Exception as e:
            logging.error(f"Error validating configuration: {str(e)}")
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": [],
                "config_hash": ""
            }

    def check_config_consistency(self, config: Dict[str, Any], expected_hash: str) -> bool:
        """
        Check if the current configuration is consistent with the expected hash.

        Args:
            config: Current configuration
            expected_hash: Expected configuration hash

        Returns:
            True if configuration is consistent, False otherwise
        """
        try:
            return validate_config_hash(config, expected_hash)
        except Exception as e:
            logging.error(f"Error checking config consistency: {str(e)}")
            return False

    def verify_processing_determinism(self, input_path: str, config: Dict[str, Any],
                                     expected_output_hash: str) -> bool:
        """
        Verify that processing the same input with the same config produces the same output.

        Args:
            input_path: Path to input data
            config: Processing configuration
            expected_output_hash: Expected hash of the output

        Returns:
            True if processing is deterministic, False otherwise
        """
        try:
            # In a real implementation, this would process the input and compare the output
            # For now, we'll simulate the process by calculating a hash of the inputs
            with open(input_path, 'r', encoding='utf-8') as f:
                input_content = f.read()

            # Create a deterministic hash based on input and config
            input_config_str = input_content + str(sorted(config.items()))
            actual_output_hash = hashlib.sha256(input_config_str.encode()).hexdigest()

            is_deterministic = actual_output_hash == expected_output_hash
            if is_deterministic:
                logging.debug("Processing determinism verification passed")
            else:
                logging.warning(f"Processing determinism verification failed: expected {expected_output_hash}, got {actual_output_hash}")

            return is_deterministic
        except Exception as e:
            logging.error(f"Error verifying processing determinism: {str(e)}")
            return False

    def validate_before_approval(self, stage: str, content_path: str) -> Dict[str, Any]:
        """
        Perform validation before approval for a specific stage.

        Args:
            stage: Stage to validate ("extraction" or "chunking")
            content_path: Path to content being validated

        Returns:
            Dictionary with validation results
        """
        try:
            result = {
                "stage": stage,
                "content_path": content_path,
                "valid": True,
                "errors": [],
                "warnings": [],
                "size": 0,
                "preview_available": True
            }

            # Check if file exists
            import os
            if not os.path.exists(content_path):
                result["valid"] = False
                result["errors"].append(f"Content file does not exist: {content_path}")
                result["preview_available"] = False
                return result

            # Get file size
            size = os.path.getsize(content_path)
            result["size"] = size

            # Check if file is too large
            max_size = 100 * 1024 * 1024  # 100MB
            if size > max_size:
                result["warnings"].append(f"Content file is large ({size} bytes), may impact preview performance")

            # Validate content based on stage
            if stage == "extraction":
                # For extraction, validate that it's a text file
                try:
                    with open(content_path, 'r', encoding='utf-8') as f:
                        content = f.read(1000)  # Read first 1000 chars to validate
                    # Basic validation - content should be readable text
                    if not isinstance(content, str):
                        result["valid"] = False
                        result["errors"].append("Extraction output is not valid text")
                except UnicodeDecodeError:
                    result["valid"] = False
                    result["errors"].append("Extraction output is not valid UTF-8 text")
            elif stage == "chunking":
                # For chunking, validate that it's a JSON array of chunks
                try:
                    with open(content_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    data = json.loads(content)
                    if not isinstance(data, list):
                        result["valid"] = False
                        result["errors"].append("Chunking output is not a JSON array")
                except json.JSONDecodeError:
                    result["valid"] = False
                    result["errors"].append("Chunking output is not valid JSON")
            else:
                result["valid"] = False
                result["errors"].append(f"Unknown stage: {stage}")

            return result
        except Exception as e:
            logging.error(f"Error validating content before approval: {str(e)}")
            return {
                "stage": stage,
                "content_path": content_path,
                "valid": False,
                "errors": [str(e)],
                "warnings": [],
                "size": 0,
                "preview_available": False
            }

    def generate_validation_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive validation report for the pipeline.

        Returns:
            Dictionary with validation report
        """
        try:
            report = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "validation_type": "comprehensive",
                "checks": {
                    "determinism": {
                        "enabled": True,
                        "last_check": None,
                        "status": "pending"
                    },
                    "config_consistency": {
                        "enabled": True,
                        "last_check": None,
                        "status": "pending"
                    },
                    "dry_run_capability": {
                        "enabled": True,
                        "status": "ready"
                    },
                    "artifact_integrity": {
                        "enabled": True,
                        "last_check": None,
                        "status": "pending"
                    }
                },
                "summary": {
                    "passed": 0,
                    "failed": 0,
                    "total": 4
                }
            }

            # Update status based on current validation state
            for check_name, check_info in report["checks"].items():
                if check_info["status"] == "passed":
                    report["summary"]["passed"] += 1
                elif check_info["status"] == "failed":
                    report["summary"]["failed"] += 1

            return report
        except Exception as e:
            logging.error(f"Error generating validation report: {str(e)}")
            return {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "validation_type": "error",
                "checks": {},
                "summary": {
                    "passed": 0,
                    "failed": 1,
                    "total": 1
                },
                "error": str(e)
            }