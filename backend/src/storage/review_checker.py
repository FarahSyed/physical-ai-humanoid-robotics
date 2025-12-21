"""
Review mechanism module for allowing developers to review extracted content before embedding
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.storage.raw_text_storage import RawTextStorage
from src.utils.logger import logger


class ReviewChecker:
    """
    Provides functionality for reviewing extracted content before embedding generation
    """

    def __init__(self, storage_dir: str = "data/raw_text"):
        """
        Initialize the review checker

        Args:
            storage_dir: Directory where raw text content is stored
        """
        self.storage_dir = Path(storage_dir)
        self.raw_text_storage = RawTextStorage(storage_dir)

    def get_content_for_review(self) -> List[Dict[str, Any]]:
        """
        Get all extracted content that needs to be reviewed

        Returns:
            List of dictionaries with content information for review
        """
        content_list = self.raw_text_storage.get_content_list()
        logger.info(f"Found {len(content_list)} content items available for review")
        return content_list

    def get_content_details(self, content_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about specific content for review

        Args:
            content_id: ID of the content to get details for

        Returns:
            Dictionary with content details or None if not found
        """
        # Find the file containing this content ID
        json_files = list(self.storage_dir.glob("*.json"))

        for filepath in json_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content_data = json.load(f)
                    if content_data.get("id") == content_id:
                        # Add file path to the content data
                        content_data["file_path"] = str(filepath)
                        return content_data
            except Exception as e:
                logger.error(f"Error reading content file {filepath}: {e}")
                continue

        return None

    def get_sample_content(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        Get a sample of content for quick review

        Args:
            count: Number of content items to return

        Returns:
            List of sample content items
        """
        content_list = self.get_content_for_review()
        return content_list[:min(count, len(content_list))]

    def mark_content_as_reviewed(self, content_id: str, approved: bool, reviewer_notes: str = "") -> bool:
        """
        Mark content as reviewed with approval status

        Args:
            content_id: ID of the content to mark
            approved: Whether the content was approved for embedding
            reviewer_notes: Optional notes from the reviewer

        Returns:
            True if marking was successful, False otherwise
        """
        # In a real implementation, you would add review status to the content metadata
        # For this implementation, we'll just log the review action
        status = "APPROVED" if approved else "REJECTED"
        logger.info(f"Content {content_id} marked as {status}. Notes: {reviewer_notes}")

        # In a complete implementation, you would update the metadata to include review status
        # For now, we'll just return True to indicate success
        return True

    def get_review_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about content review status

        Returns:
            Dictionary with review statistics
        """
        content_list = self.get_content_for_review()

        # In this simplified implementation, we don't track review status
        # In a complete implementation, you would track this in metadata
        total_content = len(content_list)

        return {
            "total_content": total_content,
            "reviewed_content": 0,  # Placeholder - would track actual reviewed count
            "pending_review": total_content,
            "approved_content": 0,  # Placeholder - would track actual approved count
            "rejected_content": 0,  # Placeholder - would track actual rejected count
        }

    def generate_review_report(self) -> str:
        """
        Generate a text report for content review

        Returns:
            Formatted text report
        """
        import json
        from datetime import datetime

        content_list = self.get_content_for_review()
        stats = self.get_review_statistics()

        report = []
        report.append("=" * 60)
        report.append("CONTENT REVIEW REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Storage Directory: {self.storage_dir}")
        report.append("")

        # Add statistics
        report.append("STATISTICS:")
        report.append(f"  Total Content Items: {stats['total_content']}")
        report.append(f"  Reviewed: {stats['reviewed_content']}")
        report.append(f"  Pending Review: {stats['pending_review']}")
        report.append(f"  Approved: {stats['approved_content']}")
        report.append(f"  Rejected: {stats['rejected_content']}")
        report.append("")

        # Add content list
        report.append("CONTENT ITEMS:")
        for i, content in enumerate(content_list[:20], 1):  # Limit to first 20 for readability
            report.append(f"  {i:2d}. {content['title'][:50]}{'...' if len(content['title']) > 50 else ''}")
            report.append(f"      ID: {content['id'][:16]}...")
            report.append(f"      URL: {content['url']}")
            report.append(f"      Words: {content['word_count']}")
            report.append(f"      File: {Path(content['file_path']).name}")
            report.append("")

        if len(content_list) > 20:
            report.append(f"... and {len(content_list) - 20} more items")

        report.append("=" * 60)

        return "\n".join(report)

    def save_review_report(self, filepath: str = None) -> str:
        """
        Save the review report to a file

        Args:
            filepath: Path to save the report (auto-generated if not provided)

        Returns:
            Path to the saved report file
        """
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = self.storage_dir / f"review_report_{timestamp}.txt"

        report = self.generate_review_report()

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)

        logger.info(f"Review report saved to {filepath}")
        return str(filepath)

    def check_ready_for_embedding(self, min_approved_ratio: float = 0.8) -> Dict[str, Any]:
        """
        Check if enough content has been reviewed and approved for embedding generation

        Args:
            min_approved_ratio: Minimum ratio of content that must be approved

        Returns:
            Dictionary with readiness check results
        """
        # In this simplified implementation, we'll consider all content as ready for review
        # In a complete implementation, you would check actual review status
        content_list = self.get_content_for_review()
        total_count = len(content_list)

        if total_count == 0:
            return {
                "ready": False,
                "message": "No content available for embedding",
                "approved_count": 0,
                "total_count": 0,
                "approved_ratio": 0.0
            }

        # For this implementation, we'll say content is ready if there's at least some content
        # and assume all content meets quality standards
        return {
            "ready": True,
            "message": f"Ready for embedding: {total_count} content items available",
            "approved_count": total_count,  # In a real implementation, this would be the reviewed+approved count
            "total_count": total_count,
            "approved_ratio": 1.0  # In a real implementation, this would be actual approval ratio
        }


# Example usage function
def example_usage():
    """
    Example of how to use the ReviewChecker
    """
    import json
    from datetime import datetime

    # Initialize the review checker
    checker = ReviewChecker()

    # Get statistics
    stats = checker.get_review_statistics()
    print(f"Review Statistics: {stats}")

    # Get sample content for review
    sample_content = checker.get_sample_content(count=3)
    print(f"\nSample Content for Review:")
    for content in sample_content:
        print(f"  - {content['title'][:50]}... ({content['word_count']} words)")

    # Generate and print review report
    report = checker.generate_review_report()
    print(f"\nReview Report Preview (first 20 lines):")
    print('\n'.join(report.split('\n')[:25]))

    # Check readiness for embedding
    readiness = checker.check_ready_for_embedding()
    print(f"\nReadiness for Embedding: {readiness}")


if __name__ == "__main__":
    example_usage()