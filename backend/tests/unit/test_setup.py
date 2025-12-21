"""
Unit tests for setup components
"""
import pytest
import os
from pathlib import Path


def test_backend_structure_exists():
    """Test that the required backend directories exist"""
    required_dirs = [
        "src",
        "data/raw_text",
        "config",
        "logs",
        "tests"
    ]

    for directory in required_dirs:
        path = Path("backend") / directory
        assert path.exists(), f"Directory {path} should exist"
        assert path.is_dir(), f"{path} should be a directory"


def test_requirements_file_exists():
    """Test that requirements.txt exists"""
    requirements_path = Path("backend") / "requirements.txt"
    assert requirements_path.exists(), "requirements.txt should exist"
    assert requirements_path.is_file(), "requirements.txt should be a file"


def test_env_example_file_exists():
    """Test that .env.example exists"""
    env_example_path = Path("backend") / ".env.example"
    assert env_example_path.exists(), ".env.example should exist"
    assert env_example_path.is_file(), ".env.example should be a file"


def test_readme_file_exists():
    """Test that README.md exists"""
    readme_path = Path("backend") / "README.md"
    assert readme_path.exists(), "README.md should exist"
    assert readme_path.is_file(), "README.md should be a file"


if __name__ == "__main__":
    pytest.main([__file__])