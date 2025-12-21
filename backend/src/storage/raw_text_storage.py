"""
Raw text storage module for temporarily storing extracted content for review
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from src.models.extracted_content import ExtractedContent
from src.utils.logger import logger
from src.utils.hash_utils import generate_content_hash


class RawTextStorage:
    """
    Handles storage of raw extracted content to temporary files for review
    """

    def __init__(self, storage_dir: str = "data/raw_text"):
        """
        Initialize raw text storage

        Args:
            storage_dir: Directory to store raw text files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_content(self, extracted_content: ExtractedContent, filename: str = None) -> str:
        """
        Save a single extracted content item to a file

        Args:
            extracted_content: ExtractedContent object to save
            filename: Optional filename (will be generated if not provided)

        Returns:
            Path to the saved file
        """
        if not filename:
            # Create a safe filename from the URL
            safe_filename = "".join(c for c in extracted_content.url if c.isalnum() or c in ('-', '_', '.')).rstrip()
            if not safe_filename:
                safe_filename = extracted_content.id[:16]

            # Limit filename length
            if len(safe_filename) > 100:
                safe_filename = safe_filename[:100]

            # Add timestamp to avoid conflicts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_filename}_{timestamp}.json"

        filepath = self.storage_dir / filename

        # Prepare content data
        content_data = {
            "id": extracted_content.id,
            "url": extracted_content.url,
            "title": extracted_content.title,
            "content": extracted_content.content,
            "module": extracted_content.module,
            "section": extracted_content.section,
            "version": extracted_content.version,
            "created_at": extracted_content.created_at.isoformat() if extracted_content.created_at else None,
            "updated_at": extracted_content.updated_at.isoformat() if extracted_content.updated_at else None,
            "content_type": extracted_content.content_type,
            "word_count": extracted_content.word_count,
            "content_hash": extracted_content.content_hash,
            "metadata": extracted_content.metadata,
            "saved_at": datetime.now().isoformat()
        }

        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(content_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved raw content to {filepath}")
        return str(filepath)

    def save_multiple_content(self, extracted_contents: List[ExtractedContent]) -> List[str]:
        """
        Save multiple extracted content items to files

        Args:
            extracted_contents: List of ExtractedContent objects to save

        Returns:
            List of paths to the saved files
        """
        saved_paths = []
        for content in extracted_contents:
            try:
                filepath = self.save_content(content)
                saved_paths.append(filepath)
            except Exception as e:
                logger.error(f"Error saving content from {content.url}: {e}")
                continue

        logger.info(f"Saved {len(saved_paths)} content items to raw text storage")
        return saved_paths

    def load_content(self, filepath: str) -> Optional[ExtractedContent]:
        """
        Load a single extracted content item from a file

        Args:
            filepath: Path to the file to load

        Returns:
            ExtractedContent object or None if loading fails
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content_data = json.load(f)

            # Convert datetime strings back to datetime objects
            created_at = None
            if content_data.get("created_at"):
                created_at = datetime.fromisoformat(content_data["created_at"].replace("Z", "+00:00"))

            updated_at = None
            if content_data.get("updated_at"):
                updated_at = datetime.fromisoformat(content_data["updated_at"].replace("Z", "+00:00"))

            # Create ExtractedContent object
            extracted_content = ExtractedContent(
                id=content_data["id"],
                url=content_data["url"],
                title=content_data["title"],
                content=content_data["content"],
                module=content_data.get("module"),
                section=content_data.get("section"),
                version=content_data.get("version", "1.0.0"),
                created_at=created_at,
                updated_at=updated_at,
                content_type=content_data.get("content_type", "text"),
                word_count=content_data.get("word_count"),
                content_hash=content_data.get("content_hash"),
                metadata=content_data.get("metadata", {})
            )

            return extracted_content

        except Exception as e:
            logger.error(f"Error loading content from {filepath}: {e}")
            return None

    def load_all_content(self) -> List[ExtractedContent]:
        """
        Load all extracted content from storage directory

        Returns:
            List of ExtractedContent objects
        """
        all_content = []
        json_files = list(self.storage_dir.glob("*.json"))

        for filepath in json_files:
            content = self.load_content(str(filepath))
            if content:
                all_content.append(content)

        logger.info(f"Loaded {len(all_content)} content items from raw text storage")
        return all_content

    def get_content_list(self) -> List[Dict[str, Any]]:
        """
        Get a list of all stored content with basic information

        Returns:
            List of dictionaries with basic content information
        """
        content_list = []
        json_files = list(self.storage_dir.glob("*.json"))

        for filepath in json_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content_data = json.load(f)

                content_info = {
                    "id": content_data["id"],
                    "url": content_data["url"],
                    "title": content_data["title"],
                    "word_count": content_data.get("word_count", 0),
                    "content_hash": content_data.get("content_hash"),
                    "saved_at": content_data.get("saved_at"),
                    "file_path": str(filepath)
                }
                content_list.append(content_info)

            except Exception as e:
                logger.error(f"Error reading content info from {filepath}: {e}")
                continue

        return content_list

    def delete_content(self, filepath: str) -> bool:
        """
        Delete a content file from storage

        Args:
            filepath: Path to the file to delete

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            path = Path(filepath)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted content file: {filepath}")
                return True
            else:
                logger.warning(f"Content file does not exist: {filepath}")
                return False
        except Exception as e:
            logger.error(f"Error deleting content file {filepath}: {e}")
            return False

    def clear_storage(self) -> bool:
        """
        Clear all content from storage directory

        Returns:
            True if clearing was successful, False otherwise
        """
        try:
            json_files = list(self.storage_dir.glob("*.json"))
            deleted_count = 0

            for filepath in json_files:
                filepath.unlink()
                deleted_count += 1

            logger.info(f"Cleared {deleted_count} content files from storage")
            return True
        except Exception as e:
            logger.error(f"Error clearing storage: {e}")
            return False

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the storage

        Returns:
            Dictionary with storage statistics
        """
        json_files = list(self.storage_dir.glob("*.json"))
        total_files = len(json_files)

        total_content_length = 0
        total_word_count = 0

        for filepath in json_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content_data = json.load(f)
                    total_content_length += len(content_data.get("content", ""))
                    total_word_count += content_data.get("word_count", 0)
            except Exception:
                continue

        return {
            "total_files": total_files,
            "total_content_length": total_content_length,
            "total_word_count": total_word_count,
            "storage_path": str(self.storage_dir),
            "storage_size_mb": sum(f.stat().st_size for f in json_files) / (1024 * 1024) if json_files else 0
        }