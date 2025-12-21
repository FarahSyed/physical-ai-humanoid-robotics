"""
Unit tests for the logging infrastructure
"""
import logging
import os
import tempfile
from pathlib import Path
import pytest
from src.utils.logger import setup_logger


class TestLogger:
    """Test cases for logger module"""

    def test_setup_logger_returns_logger_instance(self):
        """Test that setup_logger returns a logger instance"""
        logger = setup_logger("test_logger")
        assert isinstance(logger, logging.Logger)

    def test_logger_has_correct_name(self):
        """Test that logger has the specified name"""
        logger = setup_logger("test_logger")
        assert logger.name == "test_logger"

    def test_logger_has_console_handler(self):
        """Test that logger has a console handler"""
        logger = setup_logger("test_logger")
        console_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) > 0

    def test_logger_creates_file_handler_with_default_path(self):
        """Test that logger creates a file handler with default path"""
        logger = setup_logger("test_logger_default_file")
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0

    def test_logger_with_custom_file_path(self):
        """Test that logger can be configured with a custom file path"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            logger = setup_logger("test_logger_custom_file", log_file=temp_file_path)
            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) > 0
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    def test_logger_logs_message(self):
        """Test that logger can log a message"""
        logger = setup_logger("test_logger_log_message")
        # This should not raise an exception
        logger.info("Test log message")

    def test_logger_level_configurable(self):
        """Test that logger level can be configured"""
        logger = setup_logger("test_logger_level", level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_logger_format_configurable(self):
        """Test that logger format can be configured"""
        custom_format = "%(levelname)s - %(message)s"
        logger = setup_logger("test_logger_format", log_format=custom_format)
        # Check that the format was applied by inspecting the handlers
        for handler in logger.handlers:
            if hasattr(handler, 'formatter') and handler.formatter:
                # If formatter exists, format string should be set
                assert handler.formatter._fmt == custom_format
                break

    def test_logger_creates_logs_directory(self):
        """Test that logger creates logs directory when using default path"""
        # Remove logs directory if it exists to test creation
        logs_dir = Path("logs")
        if logs_dir.exists():
            logs_dir.rmdir()

        logger = setup_logger("test_logger_create_dir")
        file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
        assert len(file_handlers) > 0
        # The logs directory should now exist
        assert logs_dir.exists()

    def test_logger_avoids_duplicate_handlers(self):
        """Test that calling setup_logger multiple times doesn't add duplicate handlers"""
        logger = setup_logger("test_logger_unique", level=logging.INFO)
        initial_handler_count = len(logger.handlers)

        # Call setup_logger again with the same name
        logger2 = setup_logger("test_logger_unique", level=logging.INFO)
        final_handler_count = len(logger2.handlers)

        # The handler count should not have increased
        assert initial_handler_count == final_handler_count


if __name__ == "__main__":
    pytest.main([__file__])