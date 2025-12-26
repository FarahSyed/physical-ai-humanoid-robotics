"""
File utility functions for safe file operations in the pipeline verification system.

This module provides safe file operations for the pipeline system including
reading, writing, and validation of files.
"""
import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
import logging


def safe_read_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    Safely read a file with error handling.

    Args:
        file_path: Path to the file to read
        encoding: File encoding (default: utf-8)

    Returns:
        File content as string or None if error occurs
    """
    try:
        path = Path(file_path)
        if not path.exists():
            logging.warning(f"File does not exist: {file_path}")
            return None

        with open(path, 'r', encoding=encoding) as f:
            content = f.read()
        return content
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {str(e)}")
        return None


def safe_write_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """
    Safely write content to a file with error handling.

    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        encoding: File encoding (default: utf-8)

    Returns:
        True if successful, False otherwise
    """
    try:
        path = Path(file_path)
        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        logging.error(f"Error writing file {file_path}: {str(e)}")
        return False


def read_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Safely read a JSON file with error handling.

    Args:
        file_path: Path to the JSON file to read

    Returns:
        Parsed JSON data as dictionary or None if error occurs
    """
    try:
        content = safe_read_file(file_path)
        if content is None:
            return None

        data = json.loads(content)
        return data
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in file {file_path}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error reading JSON file {file_path}: {str(e)}")
        return None


def write_json_file(file_path: str, data: Dict[str, Any], indent: int = 2) -> bool:
    """
    Safely write data to a JSON file with error handling.

    Args:
        file_path: Path to the JSON file to write
        data: Data to write to the file
        indent: JSON indentation (default: 2)

    Returns:
        True if successful, False otherwise
    """
    try:
        json_content = json.dumps(data, indent=indent, ensure_ascii=False, sort_keys=True)
        return safe_write_file(file_path, json_content)
    except Exception as e:
        logging.error(f"Error writing JSON file {file_path}: {str(e)}")
        return False


def read_yaml_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Safely read a YAML file with error handling.

    Args:
        file_path: Path to the YAML file to read

    Returns:
        Parsed YAML data as dictionary or None if error occurs
    """
    try:
        content = safe_read_file(file_path)
        if content is None:
            return None

        data = yaml.safe_load(content)
        return data
    except yaml.YAMLError as e:
        logging.error(f"Invalid YAML in file {file_path}: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Error reading YAML file {file_path}: {str(e)}")
        return None


def write_yaml_file(file_path: str, data: Dict[str, Any], indent: int = 2) -> bool:
    """
    Safely write data to a YAML file with error handling.

    Args:
        file_path: Path to the YAML file to write
        data: Data to write to the file
        indent: YAML indentation (default: 2)

    Returns:
        True if successful, False otherwise
    """
    try:
        yaml_content = yaml.dump(data, default_flow_style=False, indent=indent, allow_unicode=True)
        return safe_write_file(file_path, yaml_content)
    except Exception as e:
        logging.error(f"Error writing YAML file {file_path}: {str(e)}")
        return False


def file_exists(file_path: str) -> bool:
    """
    Check if a file exists.

    Args:
        file_path: Path to the file to check

    Returns:
        True if file exists, False otherwise
    """
    try:
        path = Path(file_path)
        return path.exists() and path.is_file()
    except Exception:
        return False


def directory_exists(dir_path: str) -> bool:
    """
    Check if a directory exists.

    Args:
        dir_path: Path to the directory to check

    Returns:
        True if directory exists, False otherwise
    """
    try:
        path = Path(dir_path)
        return path.exists() and path.is_dir()
    except Exception:
        return False


def create_directory(dir_path: str) -> bool:
    """
    Create a directory if it doesn't exist.

    Args:
        dir_path: Path to the directory to create

    Returns:
        True if successful, False otherwise
    """
    try:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Error creating directory {dir_path}: {str(e)}")
        return False