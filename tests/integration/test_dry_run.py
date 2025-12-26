"""
Integration tests for dry-run functionality.
This test verifies that the dry-run execution works correctly with the full pipeline,
ensuring that no irreversible changes are made during dry-run mode.
"""
import os
import tempfile
import unittest
import json

from src.pipeline.state_machine import PipelineState
from src.pipeline.state_persistence import StatePersistence, PipelineStateManager
from src.pipeline.verification_service import VerificationService
from src.pipeline.approval_engine import ApprovalEngine
from src.pipeline.resume_logic import ResumeLogic


class TestDryRun(unittest.TestCase):
    """
    Integration tests for dry-run functionality.
    """

    def setUp(self):
        """
        Set up test fixtures before each test method.
        """
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.state_file = self.temp_file.name

        # Initialize components
        self.state_persistence = StatePersistence(self.state_file)
        self.state_manager = PipelineStateManager(self.state_file)
        self.verification_service = VerificationService()
        self.approval_engine = ApprovalEngine(self.state_persistence)
        self.resume_logic = ResumeLogic(self.state_persistence)

    def tearDown(self):
        """
        Clean up after each test method.
        """
        # Remove the temporary file
        if os.path.exists(self.state_file):
            os.remove(self.state_file)

    def test_dry_run_mode_enable_disable(self):
        """
        Test enabling and disabling dry-run mode in verification service.
        """
        # Initially should be disabled
        self.assertFalse(self.verification_service.is_dry_run_mode())

        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()
        self.assertTrue(self.verification_service.is_dry_run_mode())

        # Disable dry-run mode
        self.verification_service.disable_dry_run_mode()
        self.assertFalse(self.verification_service.is_dry_run_mode())

    def test_dry_run_extract_content_operation(self):
        """
        Test dry-run of extract content operation.
        """
        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()

        # Prepare parameters for extract content operation
        params = {
            "source_path": "/path/to/source/document.txt",
            "output_path": "/path/to/output/extracted_content.txt"
        }

        # Perform dry-run of extract content operation
        result = self.verification_service.perform_dry_run("extract_content", params)

        # Verify result structure
        self.assertIsNotNone(result)
        self.assertEqual(result["operation"], "extract_content")
        self.assertEqual(result["params"], params)
        self.assertTrue(result["dry_run"])
        self.assertTrue(result["would_perform"])
        self.assertEqual(result["impact"], "no_changes_made")

    def test_dry_run_chunk_content_operation(self):
        """
        Test dry-run of chunk content operation.
        """
        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()

        # Prepare parameters for chunk content operation
        params = {
            "content_path": "/path/to/content.txt",
            "chunk_size": 1000,
            "overlap": 100
        }

        # Perform dry-run of chunk content operation
        result = self.verification_service.perform_dry_run("chunk_content", params)

        # Verify result structure
        self.assertIsNotNone(result)
        self.assertEqual(result["operation"], "chunk_content")
        self.assertEqual(result["params"], params)
        self.assertTrue(result["dry_run"])
        self.assertTrue(result["would_perform"])
        self.assertEqual(result["impact"], "no_changes_made")

    def test_dry_run_approve_extraction_operation(self):
        """
        Test dry-run of approve extraction operation.
        """
        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()

        # Prepare parameters for approve extraction operation
        params = {
            "approver": "test_approver",
            "context": "Content looks good",
            "decision": "APPROVE"
        }

        # Perform dry-run of approve extraction operation
        result = self.verification_service.perform_dry_run("approve_extraction", params)

        # Verify result structure
        self.assertIsNotNone(result)
        self.assertEqual(result["operation"], "approve_extraction")
        self.assertEqual(result["params"], params)
        self.assertTrue(result["dry_run"])
        self.assertTrue(result["would_perform"])
        self.assertEqual(result["impact"], "no_changes_made")

    def test_dry_run_approve_chunking_operation(self):
        """
        Test dry-run of approve chunking operation.
        """
        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()

        # Prepare parameters for approve chunking operation
        params = {
            "approver": "test_approver",
            "context": "Chunks look good",
            "decision": "APPROVE"
        }

        # Perform dry-run of approve chunking operation
        result = self.verification_service.perform_dry_run("approve_chunking", params)

        # Verify result structure
        self.assertIsNotNone(result)
        self.assertEqual(result["operation"], "approve_chunking")
        self.assertEqual(result["params"], params)
        self.assertTrue(result["dry_run"])
        self.assertTrue(result["would_perform"])
        self.assertEqual(result["impact"], "no_changes_made")

    def test_dry_run_with_validation_errors(self):
        """
        Test dry-run with validation errors.
        """
        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()

        # Prepare parameters for extract content operation without required field
        params = {
            # Missing "source_path" which is required
            "output_path": "/path/to/output.txt"
        }

        # Perform dry-run of extract content operation (should have validation errors)
        result = self.verification_service.perform_dry_run("extract_content", params)

        # Verify validation failed
        self.assertIsNotNone(result)
        self.assertFalse(result["validation_passed"])
        self.assertTrue(len(result["warnings"]) > 0)

    def test_dry_run_with_pipeline_state_integration(self):
        """
        Test dry-run integration with pipeline state management.
        """
        # Initialize the pipeline
        self.state_manager.initialize_pipeline({"input_path": "test_input.txt"})

        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()

        # Check that we're in IDLE state initially
        initial_state = self.state_manager.get_pipeline_state()
        self.assertEqual(initial_state, PipelineState.IDLE)

        # Perform a dry-run operation
        params = {"source_path": "/path/to/source.txt"}
        result = self.verification_service.perform_dry_run("extract_content", params)

        # Verify the operation was dry-run and no state change occurred
        self.assertTrue(result["dry_run"])
        final_state = self.state_manager.get_pipeline_state()
        self.assertEqual(final_state, PipelineState.IDLE)  # Should still be in IDLE

    def test_dry_run_determinism_verification(self):
        """
        Test determinism verification in dry-run context.
        """
        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()

        # Test determinism calculation
        input_data = "test input for determinism"
        config = {"param1": "value1", "param2": "value2"}

        # Calculate deterministic hash
        hash_result = self.verification_service.calculate_deterministic_hash(input_data, config)
        self.assertIsNotNone(hash_result)
        self.assertEqual(len(hash_result), 64)  # SHA256 hash length

        # Verify determinism
        is_deterministic = self.verification_service.verify_determinism(input_data, config, hash_result)
        self.assertTrue(is_deterministic)

    def test_dry_run_configuration_validation(self):
        """
        Test configuration validation in dry-run context.
        """
        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()

        # Test valid configuration
        valid_config = {
            "input_path": "/valid/input/path",
            "output_path": "/valid/output/path"
        }
        result = self.verification_service.validate_configuration(valid_config)

        # Verify validation passed
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        self.assertIsNotNone(result["config_hash"])

        # Test invalid configuration
        invalid_config = {
            "input_path": "/valid/input/path"
            # Missing output_path
        }
        result = self.verification_service.validate_configuration(invalid_config)

        # Verify validation failed
        self.assertFalse(result["valid"])
        self.assertTrue(len(result["errors"]) > 0)

    def test_dry_run_with_artifact_validation(self):
        """
        Test dry-run with artifact validation.
        """
        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()

        # Create temporary files for testing
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("Test content for artifact validation.")
            content_file_path = content_file.name

        try:
            # Validate content before approval (extraction stage)
            result = self.verification_service.validate_before_approval("extraction", content_file_path)

            # Verify validation passed
            self.assertTrue(result["valid"])
            self.assertEqual(result["stage"], "extraction")
            self.assertTrue(result["preview_available"])

            # Validate content before approval (chunking stage with JSON)
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as chunk_file:
                json.dump(["chunk1", "chunk2", "chunk3"], chunk_file)
                chunk_file_path = chunk_file.name

            try:
                result = self.verification_service.validate_before_approval("chunking", chunk_file_path)

                # Verify validation passed
                self.assertTrue(result["valid"])
                self.assertEqual(result["stage"], "chunking")
                self.assertTrue(result["preview_available"])

            finally:
                # Clean up chunk file
                if os.path.exists(chunk_file_path):
                    os.remove(chunk_file_path)

        finally:
            # Clean up content file
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_dry_run_with_nonexistent_files(self):
        """
        Test dry-run with nonexistent files (should handle gracefully).
        """
        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()

        # Validate content before approval with nonexistent file
        result = self.verification_service.validate_before_approval("extraction", "/nonexistent/file.txt")

        # Verify validation failed gracefully
        self.assertFalse(result["valid"])
        self.assertFalse(result["preview_available"])
        self.assertTrue(len(result["errors"]) > 0)

    def test_dry_run_approve_operations_with_state_integration(self):
        """
        Test dry-run of approval operations with state integration.
        """
        # Initialize the pipeline
        self.state_manager.initialize_pipeline({"input_path": "test_input.txt"})

        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()

        # Set up extraction complete state
        self.state_manager.transition_to_extraction_in_progress()

        # Create extracted content file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as extract_file:
            extract_file.write("Extracted content for approval testing.")
            extract_file_path = extract_file.name

        try:
            # Complete extraction
            self.state_manager.transition_to_extraction_complete(extract_file_path)

            # Verify we're in EXTRACTION_COMPLETE
            current_state = self.state_manager.get_pipeline_state()
            self.assertEqual(current_state, PipelineState.EXTRACTION_COMPLETE)

            # Perform dry-run of approve extraction operation
            params = {
                "approver": "test_approver",
                "context": "Content approved in dry-run mode",
                "decision": "APPROVE"
            }
            result = self.verification_service.perform_dry_run("approve_extraction", params)

            # Verify dry-run was successful
            self.assertTrue(result["dry_run"])
            self.assertTrue(result["would_perform"])

            # Verify state did not change (still in EXTRACTION_COMPLETE)
            final_state = self.state_manager.get_pipeline_state()
            self.assertEqual(final_state, PipelineState.EXTRACTION_COMPLETE)

        finally:
            # Clean up temporary file
            if os.path.exists(extract_file_path):
                os.remove(extract_file_path)

    def test_dry_run_chunking_operations_with_state_integration(self):
        """
        Test dry-run of chunking operations with state integration.
        """
        # Initialize the pipeline
        self.state_manager.initialize_pipeline({"input_path": "test_input.txt"})

        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()

        # Go through extraction
        self.state_manager.transition_to_extraction_in_progress()

        # Create extracted content file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as extract_file:
            extract_file.write("Extracted content for chunking testing.")
            extract_file_path = extract_file.name

        try:
            # Complete extraction
            self.state_manager.transition_to_extraction_complete(extract_file_path)

            # Process extraction approval
            self.approval_engine.process_approval(
                stage="extraction",
                approver_id="test_approver",
                decision="APPROVE",
                context="Content approved"
            )

            # Start chunking
            self.state_manager.transition_to_chunking_in_progress()

            # Create chunked content file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as chunk_file:
                json.dump(["chunk1", "chunk2", "chunk3"], chunk_file)
                chunk_file_path = chunk_file.name

            try:
                # Complete chunking
                self.state_manager.transition_to_chunking_complete(chunk_file_path)

                # Verify we're in CHUNKING_COMPLETE
                current_state = self.state_manager.get_pipeline_state()
                self.assertEqual(current_state, PipelineState.CHUNKING_COMPLETE)

                # Perform dry-run of approve chunking operation
                params = {
                    "approver": "test_approver",
                    "context": "Chunks approved in dry-run mode",
                    "decision": "APPROVE"
                }
                result = self.verification_service.perform_dry_run("approve_chunking", params)

                # Verify dry-run was successful
                self.assertTrue(result["dry_run"])
                self.assertTrue(result["would_perform"])

                # Verify state did not change (still in CHUNKING_COMPLETE)
                final_state = self.state_manager.get_pipeline_state()
                self.assertEqual(final_state, PipelineState.CHUNKING_COMPLETE)

            finally:
                # Clean up chunk file
                if os.path.exists(chunk_file_path):
                    os.remove(chunk_file_path)

        finally:
            # Clean up extract file
            if os.path.exists(extract_file_path):
                os.remove(extract_file_path)

    def test_dry_run_processing_determinism(self):
        """
        Test processing determinism verification in dry-run mode.
        """
        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()

        # Create temporary content file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as content_file:
            content_file.write("Test content for processing determinism verification.")
            content_file_path = content_file.name

        try:
            config = {"param1": "value1", "param2": "value2"}

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

            # Verify with wrong hash
            is_deterministic = self.verification_service.verify_processing_determinism(
                content_file_path, config, "wrong_hash"
            )
            self.assertFalse(is_deterministic)

        finally:
            # Clean up temporary file
            if os.path.exists(content_file_path):
                os.remove(content_file_path)

    def test_dry_run_validation_report_generation(self):
        """
        Test validation report generation in dry-run mode.
        """
        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()

        # Generate validation report
        report = self.verification_service.generate_validation_report()

        # Verify report structure
        self.assertIsNotNone(report)
        self.assertIn("timestamp", report)
        self.assertIn("validation_type", report)
        self.assertIn("checks", report)
        self.assertIn("summary", report)

        # Verify checks structure
        checks = report["checks"]
        self.assertIn("determinism", checks)
        self.assertIn("config_consistency", checks)
        self.assertIn("dry_run_capability", checks)
        self.assertIn("artifact_integrity", checks)

    def test_dry_run_config_consistency_check(self):
        """
        Test configuration consistency check in dry-run mode.
        """
        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()

        # Test configuration consistency
        config = {
            "input_path": "/test/input",
            "output_path": "/test/output"
        }
        result = self.verification_service.validate_configuration(config)
        expected_hash = result["config_hash"]

        # Check consistency
        is_consistent = self.verification_service.check_config_consistency(config, expected_hash)
        self.assertTrue(is_consistent)

        # Check with wrong hash
        is_consistent = self.verification_service.check_config_consistency(config, "wrong_hash")
        self.assertFalse(is_consistent)

    def test_dry_run_with_pipeline_resumption(self):
        """
        Test dry-run functionality with pipeline resumption.
        """
        # Initialize the pipeline
        self.state_manager.initialize_pipeline({"input_path": "test_input.txt"})

        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()

        # Set up state
        self.state_manager.transition_to_extraction_in_progress()

        # Create extracted content file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as extract_file:
            extract_file.write("Extracted content for resumption testing.")
            extract_file_path = extract_file.name

        try:
            # Complete extraction
            self.state_manager.transition_to_extraction_complete(extract_file_path)

            # Process extraction approval
            self.approval_engine.process_approval(
                stage="extraction",
                approver_id="test_approver",
                decision="APPROVE",
                context="Content approved"
            )

            # Verify we're in EXTRACTION_APPROVED
            current_state = self.state_manager.get_pipeline_state()
            self.assertEqual(current_state, PipelineState.EXTRACTION_APPROVED)

            # Test resume logic in dry-run context
            resume_state = self.resume_logic.get_resume_state()
            self.assertEqual(resume_state, PipelineState.EXTRACTION_APPROVED)

            # Get resume recommendation
            recommendation = self.resume_logic.get_resume_recommendation()
            self.assertIsNotNone(recommendation)
            self.assertEqual(recommendation["current_state"], PipelineState.EXTRACTION_APPROVED.value)

            # Verify state remains unchanged after resume logic operations
            final_state = self.state_manager.get_pipeline_state()
            self.assertEqual(final_state, PipelineState.EXTRACTION_APPROVED)

        finally:
            # Clean up temporary file
            if os.path.exists(extract_file_path):
                os.remove(extract_file_path)

    def test_dry_run_validation_with_different_stages(self):
        """
        Test dry-run validation across different pipeline stages.
        """
        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()

        # Test extract content validation
        extract_params = {"source_path": "/path/to/source.txt"}
        extract_result = self.verification_service.perform_dry_run("extract_content", extract_params)
        self.assertEqual(extract_result["operation"], "extract_content")
        self.assertTrue(extract_result["dry_run"])

        # Test chunk content validation
        chunk_params = {"content_path": "/path/to/content.txt"}
        chunk_result = self.verification_service.perform_dry_run("chunk_content", chunk_params)
        self.assertEqual(chunk_result["operation"], "chunk_content")
        self.assertTrue(chunk_result["dry_run"])

        # Test approve extraction validation
        approve_extract_params = {"approver": "test_approver"}
        approve_extract_result = self.verification_service.perform_dry_run("approve_extraction", approve_extract_params)
        self.assertEqual(approve_extract_result["operation"], "approve_extraction")
        self.assertTrue(approve_extract_result["dry_run"])

        # Test approve chunking validation
        approve_chunk_params = {"approver": "test_approver"}
        approve_chunk_result = self.verification_service.perform_dry_run("approve_chunking", approve_chunk_params)
        self.assertEqual(approve_chunk_result["operation"], "approve_chunking")
        self.assertTrue(approve_chunk_result["dry_run"])

    def test_dry_run_error_handling(self):
        """
        Test error handling in dry-run mode.
        """
        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()

        # Test dry-run with operation that has validation errors
        params = {}  # Missing required parameters
        result = self.verification_service.perform_dry_run("extract_content", params)

        # Verify error handling worked properly
        self.assertIsNotNone(result)
        self.assertTrue(result["dry_run"])
        self.assertFalse(result["validation_passed"])
        self.assertEqual(result["impact"], "no_changes_made")

    def test_dry_run_mode_persistence(self):
        """
        Test that dry-run mode persists across different operations.
        """
        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()
        self.assertTrue(self.verification_service.is_dry_run_mode())

        # Perform multiple operations and verify dry-run mode stays enabled
        for operation in ["extract_content", "chunk_content", "approve_extraction", "approve_chunking"]:
            params = {"source_path": "/path/to/source.txt"} if operation == "extract_content" else {"approver": "test"}
            result = self.verification_service.perform_dry_run(operation, params)
            self.assertTrue(result["dry_run"])

        # Verify dry-run mode is still enabled after all operations
        self.assertTrue(self.verification_service.is_dry_run_mode())

    def test_dry_run_with_realistic_pipeline_scenario(self):
        """
        Test dry-run with a realistic pipeline scenario.
        """
        # Initialize the pipeline
        self.state_manager.initialize_pipeline({"input_path": "test_input.txt"})

        # Enable dry-run mode
        self.verification_service.enable_dry_run_mode()

        # Simulate a full pipeline execution in dry-run mode
        initial_state = self.state_manager.get_pipeline_state()
        self.assertEqual(initial_state, PipelineState.IDLE)

        # Attempt to transition to extraction in progress (in dry-run)
        extract_params = {"source_path": "/path/to/source.txt"}
        extract_result = self.verification_service.perform_dry_run("extract_content", extract_params)
        self.assertTrue(extract_result["dry_run"])

        # Verify state remains unchanged
        state_after_extract = self.state_manager.get_pipeline_state()
        self.assertEqual(state_after_extract, PipelineState.IDLE)

        # Attempt to transition to chunking (in dry-run)
        chunk_params = {"content_path": "/path/to/content.txt"}
        chunk_result = self.verification_service.perform_dry_run("chunk_content", chunk_params)
        self.assertTrue(chunk_result["dry_run"])

        # Verify state still remains unchanged
        state_after_chunk = self.state_manager.get_pipeline_state()
        self.assertEqual(state_after_chunk, PipelineState.IDLE)

        # Verify that no irreversible changes were made during the dry-run operations
        final_state = self.state_manager.get_pipeline_state()
        self.assertEqual(final_state, PipelineState.IDLE)


if __name__ == '__main__':
    unittest.main()