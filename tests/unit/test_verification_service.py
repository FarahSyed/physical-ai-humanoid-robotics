"""
Unit tests for the verification service module.
"""
import os
import tempfile
import unittest
import json

from src.pipeline.verification_service import VerificationService


class TestVerificationService(unittest.TestCase):
    """
    Test cases for VerificationService functionality.
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        self.verification_service = VerificationService()

    def test_dry_run_mode_enable_disable(self):
        """
        Test enabling and disabling dry-run mode.
        """
        # Initially should be disabled
        self.assertFalse(self.verification_service.is_dry_run_mode())

        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()
        self.assertTrue(self.verification_service.is_dry_run_mode())

        # Disable dry-run mode
        self.verification_service.disable_dry_run_mode()
        self.assertFalse(self.verification_service.is_dry_run_mode())

    def test_calculate_deterministic_hash_with_data_only(self):
        """
        Test calculating deterministic hash with input data only.
        """
        input_data = "test input data"
        hash_result = self.verification_service.calculate_deterministic_hash(input_data)

        # Verify result is not empty and is a valid hash
        self.assertIsNotNone(hash_result)
        self.assertEqual(len(hash_result), 64)  # SHA256 hash is 64 characters
        self.assertTrue(isinstance(hash_result, str))

    def test_calculate_deterministic_hash_with_data_and_config(self):
        """
        Test calculating deterministic hash with input data and configuration.
        """
        input_data = "test input data"
        config = {"param1": "value1", "param2": "value2"}
        hash_result = self.verification_service.calculate_deterministic_hash(input_data, config)

        # Verify result is not empty and is a valid hash
        self.assertIsNotNone(hash_result)
        self.assertEqual(len(hash_result), 64)  # SHA256 hash is 64 characters
        self.assertTrue(isinstance(hash_result, str))

        # Same input should produce same hash
        hash_result2 = self.verification_service.calculate_deterministic_hash(input_data, config)
        self.assertEqual(hash_result, hash_result2)

        # Different input should produce different hash
        hash_result3 = self.verification_service.calculate_deterministic_hash("different input", config)
        self.assertNotEqual(hash_result, hash_result3)

    def test_verify_determinism_pass(self):
        """
        Test determinism verification that should pass.
        """
        input_data = "test input data"
        config = {"param1": "value1"}
        expected_hash = self.verification_service.calculate_deterministic_hash(input_data, config)

        # Verify determinism with correct hash
        is_deterministic = self.verification_service.verify_determinism(input_data, config, expected_hash)
        self.assertTrue(is_deterministic)

    def test_verify_determinism_fail(self):
        """
        Test determinism verification that should fail.
        """
        input_data = "test input data"
        config = {"param1": "value1"}
        wrong_hash = "wrong_hash_value"

        # Verify determinism with wrong hash
        is_deterministic = self.verification_service.verify_determinism(input_data, config, wrong_hash)
        self.assertFalse(is_deterministic)

    def test_perform_dry_run_extract_content(self):
        """
        Test performing dry-run for extract content operation.
        """
        params = {"source_path": "/path/to/source.txt"}
        result = self.verification_service.perform_dry_run("extract_content", params)

        # Verify result structure
        self.assertIsNotNone(result)
        self.assertEqual(result["operation"], "extract_content")
        self.assertEqual(result["params"], params)
        self.assertTrue(result["dry_run"])
        self.assertTrue(result["would_perform"])
        self.assertEqual(result["impact"], "no_changes_made")

    def test_perform_dry_run_chunk_content(self):
        """
        Test performing dry-run for chunk content operation.
        """
        params = {"content_path": "/path/to/content.txt"}
        result = self.verification_service.perform_dry_run("chunk_content", params)

        # Verify result structure
        self.assertIsNotNone(result)
        self.assertEqual(result["operation"], "chunk_content")
        self.assertEqual(result["params"], params)
        self.assertTrue(result["dry_run"])
        self.assertTrue(result["would_perform"])
        self.assertEqual(result["impact"], "no_changes_made")

    def test_perform_dry_run_with_validation_errors(self):
        """
        Test performing dry-run with validation errors.
        """
        # Missing required parameter should cause validation error
        params = {}  # Missing source_path
        result = self.verification_service.perform_dry_run("extract_content", params)

        # Verify validation failed
        self.assertIsNotNone(result)
        self.assertFalse(result["validation_passed"])
        self.assertTrue(len(result["warnings"]) > 0)

    def test_perform_dry_run_approve_extraction(self):
        """
        Test performing dry-run for approve extraction operation.
        """
        params = {"approver": "test_approver", "context": "test context"}
        result = self.verification_service.perform_dry_run("approve_extraction", params)

        # Verify result structure
        self.assertIsNotNone(result)
        self.assertEqual(result["operation"], "approve_extraction")
        self.assertEqual(result["params"], params)
        self.assertTrue(result["dry_run"])
        self.assertTrue(result["would_perform"])
        self.assertEqual(result["impact"], "no_changes_made")

    def test_perform_dry_run_approve_chunking(self):
        """
        Test performing dry-run for approve chunking operation.
        """
        params = {"approver": "test_approver", "context": "test context"}
        result = self.verification_service.perform_dry_run("approve_chunking", params)

        # Verify result structure
        self.assertIsNotNone(result)
        self.assertEqual(result["operation"], "approve_chunking")
        self.assertEqual(result["params"], params)
        self.assertTrue(result["dry_run"])
        self.assertTrue(result["would_perform"])
        self.assertEqual(result["impact"], "no_changes_made")

    def test_validate_operation_extract_content_valid(self):
        """
        Test validating extract content operation with valid parameters.
        """
        params = {"source_path": "/valid/path.txt"}
        result = self.verification_service._validate_operation("extract_content", params)

        # Verify validation passed
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)

    def test_validate_operation_extract_content_invalid(self):
        """
        Test validating extract content operation with invalid parameters.
        """
        # Missing source_path
        params = {}
        result = self.verification_service._validate_operation("extract_content", params)

        # Verify validation failed
        self.assertFalse(result["valid"])
        self.assertTrue(len(result["errors"]) > 0)

        # Empty source_path
        params = {"source_path": ""}
        result = self.verification_service._validate_operation("extract_content", params)

        # Verify validation failed
        self.assertFalse(result["valid"])
        self.assertTrue(len(result["errors"]) > 0)

    def test_validate_operation_chunk_content_valid(self):
        """
        Test validating chunk content operation with valid parameters.
        """
        params = {"content_path": "/valid/path.txt"}
        result = self.verification_service._validate_operation("chunk_content", params)

        # Verify validation passed
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)

    def test_validate_operation_chunk_content_invalid(self):
        """
        Test validating chunk content operation with invalid parameters.
        """
        # Missing content_path
        params = {}
        result = self.verification_service._validate_operation("chunk_content", params)

        # Verify validation failed
        self.assertFalse(result["valid"])
        self.assertTrue(len(result["errors"]) > 0)

        # Empty content_path
        params = {"content_path": ""}
        result = self.verification_service._validate_operation("chunk_content", params)

        # Verify validation failed
        self.assertFalse(result["valid"])
        self.assertTrue(len(result["errors"]) > 0)

    def test_validate_operation_approve_extraction_invalid(self):
        """
        Test validating approve extraction operation with invalid parameters.
        """
        # Missing approver
        params = {}
        result = self.verification_service._validate_operation("approve_extraction", params)

        # Verify validation failed
        self.assertFalse(result["valid"])
        self.assertTrue(len(result["errors"]) > 0)

    def test_validate_operation_approve_chunking_invalid(self):
        """
        Test validating approve chunking operation with invalid parameters.
        """
        # Missing approver
        params = {}
        result = self.verification_service._validate_operation("approve_chunking", params)

        # Verify validation failed
        self.assertFalse(result["valid"])
        self.assertTrue(len(result["errors"]) > 0)

    def test_validate_configuration_success(self):
        """
        Test validating configuration with all required parameters.
        """
        config = {
            "input_path": "/input/path",
            "output_path": "/output/path"
        }
        result = self.verification_service.validate_configuration(config)

        # Verify validation passed
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        self.assertIsNotNone(result["config_hash"])

    def test_validate_configuration_missing_required_keys(self):
        """
        Test validating configuration with missing required keys.
        """
        config = {
            "input_path": "/input/path"
            # Missing output_path
        }
        result = self.verification_service.validate_configuration(config)

        # Verify validation failed
        self.assertFalse(result["valid"])
        self.assertTrue(len(result["errors"]) > 0)

    def test_validate_configuration_empty_values(self):
        """
        Test validating configuration with empty values.
        """
        config = {
            "input_path": "",
            "output_path": "/output/path"
        }
        result = self.verification_service.validate_configuration(config)

        # Verify validation failed
        self.assertFalse(result["valid"])
        self.assertTrue(len(result["errors"]) > 0)

    def test_check_config_consistency(self):
        """
        Test checking configuration consistency with expected hash.
        """
        config = {
            "input_path": "/input/path",
            "output_path": "/output/path"
        }
        # Calculate expected hash
        result = self.verification_service.validate_configuration(config)
        expected_hash = result["config_hash"]

        # Check consistency
        is_consistent = self.verification_service.check_config_consistency(config, expected_hash)
        self.assertTrue(is_consistent)

        # Check with wrong hash
        is_consistent = self.verification_service.check_config_consistency(config, "wrong_hash")
        self.assertFalse(is_consistent)

    def test_verify_processing_determinism_success(self):
        """
        Test processing determinism verification that should pass.
        """
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("test content for determinism verification")
            content_file_path = content_file.name

        try:
            config = {"param1": "value1"}

            # Calculate expected hash by processing the content
            with open(content_file_path, 'r', encoding='utf-8') as f:
                input_content = f.read()
            input_config_str = input_content + str(sorted(config.items()))
            import hashlib
            expected_hash = hashlib.sha256(input_config_str.encode()).hexdigest()

            # Verify processing determinism
            is_deterministic = self.verification_service.verify_processing_determinism(
                content_file_path, config, expected_hash
            )
            self.assertTrue(is_deterministic)

        finally:
            # Clean up temporary file
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_verify_processing_determinism_failure(self):
        """
        Test processing determinism verification that should fail.
        """
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("test content for determinism verification")
            content_file_path = content_file.name

        try:
            config = {"param1": "value1"}
            wrong_hash = "wrong_hash_value"

            # Verify processing determinism with wrong hash
            is_deterministic = self.verification_service.verify_processing_determinism(
                content_file_path, config, wrong_hash
            )
            self.assertFalse(is_deterministic)

        finally:
            # Clean up temporary file
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_validate_before_approval_extraction_success(self):
        """
        Test validating content before extraction approval with valid content.
        """
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("Valid text content for extraction validation.")
            content_file_path = content_file.name

        try:
            # Validate content before approval
            result = self.verification_service.validate_before_approval("extraction", content_file_path)

            # Verify validation passed
            self.assertTrue(result["valid"])
            self.assertEqual(result["stage"], "extraction")
            self.assertEqual(result["content_path"], content_file_path)
            self.assertEqual(len(result["errors"]), 0)
            self.assertTrue(result["preview_available"])

        finally:
            # Clean up temporary file
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_validate_before_approval_extraction_invalid_file(self):
        """
        Test validating content before extraction approval with invalid file.
        """
        # Validate content before approval with non-existent file
        result = self.verification_service.validate_before_approval("extraction", "/nonexistent/file.txt")

        # Verify validation failed
        self.assertFalse(result["valid"])
        self.assertEqual(result["stage"], "extraction")
        self.assertFalse(result["preview_available"])
        self.assertTrue(len(result["errors"]) > 0)

    def test_validate_before_approval_chunking_success(self):
        """
        Test validating content before chunking approval with valid JSON content.
        """
        # Create a temporary JSON file for testing
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as content_file:
            json.dump(["chunk1", "chunk2", "chunk3"], content_file)
            content_file_path = content_file.name

        try:
            # Validate content before approval
            result = self.verification_service.validate_before_approval("chunking", content_file_path)

            # Verify validation passed
            self.assertTrue(result["valid"])
            self.assertEqual(result["stage"], "chunking")
            self.assertEqual(result["content_path"], content_file_path)
            self.assertEqual(len(result["errors"]), 0)
            self.assertTrue(result["preview_available"])

        finally:
            # Clean up temporary file
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_validate_before_approval_chunking_invalid_json(self):
        """
        Test validating content before chunking approval with invalid JSON content.
        """
        # Create a temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("Invalid JSON content for chunking validation.")
            content_file_path = content_file.name

        try:
            # Validate content before approval
            result = self.verification_service.validate_before_approval("chunking", content_file_path)

            # Verify validation failed
            self.assertFalse(result["valid"])
            self.assertEqual(result["stage"], "chunking")
            self.assertTrue(len(result["errors"]) > 0)

        finally:
            # Clean up temporary file
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_validate_before_approval_unknown_stage(self):
        """
        Test validating content before approval with unknown stage.
        """
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("test content")
            content_file_path = content_file.name

        try:
            # Validate content before approval with unknown stage
            result = self.verification_service.validate_before_approval("unknown_stage", content_file_path)

            # Verify validation failed
            self.assertFalse(result["valid"])
            self.assertEqual(result["stage"], "unknown_stage")
            self.assertTrue(len(result["errors"]) > 0)

        finally:
            # Clean up temporary file
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_generate_validation_report(self):
        """
        Test generating validation report.
        """
        # Generate validation report
        report = self.verification_service.generate_validation_report()

        # Verify report structure
        self.assertIsNotNone(report)
        self.assertIn("timestamp", report)
        self.assertIn("validation_type", report)
        self.assertIn("checks", report)
        self.assertIn("summary", report)
        self.assertEqual(report["validation_type"], "comprehensive")

        # Verify checks structure
        checks = report["checks"]
        self.assertIn("determinism", checks)
        self.assertIn("config_consistency", checks)
        self.assertIn("dry_run_capability", checks)
        self.assertIn("artifact_integrity", checks)

        # Verify summary structure
        summary = report["summary"]
        self.assertIn("passed", summary)
        self.assertIn("failed", summary)
        self.assertIn("total", summary)


if __name__ == '__main__':
    unittest.main()