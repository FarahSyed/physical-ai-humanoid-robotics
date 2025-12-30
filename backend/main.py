"""
Main entry point for the backend pipeline verification system.
"""
import sys
import os
# Add the backend src to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.cli.pipeline_cli import main as cli_main


def main():
    """Main entry point for the backend application."""
    print("Starting backend pipeline verification system...")
    # Delegate to the CLI main function
    return cli_main()


if __name__ == "__main__":
    sys.exit(main())
