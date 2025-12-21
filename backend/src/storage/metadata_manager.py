"""
Metadata manager module for handling content metadata and quality metrics
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from src.models.extracted_content import ContentMetadata, ExtractedContent
from src.utils.logger import logger
from src.utils.hash_utils import generate_content_hash


class MetadataManager:
    """
    Manages metadata for extracted content including quality metrics and tracking
    """

    def __init__(self, metadata_dir: str = "data/metadata"):
        """
        Initialize metadata manager

        Args:
            metadata_dir: Directory to store metadata files
        """
        self.metadata_dir = Path(metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.metadata_dir / "content_metadata.json"

    def save_metadata(self, metadata: ContentMetadata) -> bool:
        """
        Save content metadata to storage

        Args:
            metadata: ContentMetadata object to save

        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Load existing metadata
            all_metadata = self.load_all_metadata()

            # Add or update the metadata
            all_metadata[metadata.content_id] = metadata.to_dict()

            # Save all metadata to file
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(all_metadata, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"Saved metadata for content: {metadata.content_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving metadata for content {metadata.content_id}: {e}")
            return False

    def save_multiple_metadata(self, metadata_list: List[ContentMetadata]) -> int:
        """
        Save multiple metadata objects to storage

        Args:
            metadata_list: List of ContentMetadata objects to save

        Returns:
            Number of metadata objects successfully saved
        """
        saved_count = 0
        for metadata in metadata_list:
            if self.save_metadata(metadata):
                saved_count += 1

        logger.info(f"Saved {saved_count} metadata objects")
        return saved_count

    def load_metadata(self, content_id: str) -> Optional[ContentMetadata]:
        """
        Load content metadata by content ID

        Args:
            content_id: ID of the content to load metadata for

        Returns:
            ContentMetadata object or None if not found
        """
        try:
            all_metadata = self.load_all_metadata()
            metadata_dict = all_metadata.get(content_id)

            if metadata_dict:
                return ContentMetadata.from_dict(metadata_dict)
            else:
                logger.info(f"Metadata not found for content: {content_id}")
                return None

        except Exception as e:
            logger.error(f"Error loading metadata for content {content_id}: {e}")
            return None

    def load_all_metadata(self) -> Dict[str, Any]:
        """
        Load all metadata from storage

        Returns:
            Dictionary of all metadata objects indexed by content ID
        """
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logger.error(f"Error loading all metadata: {e}")
            return {}

    def update_metadata(self, content_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update specific fields in content metadata

        Args:
            content_id: ID of the content to update
            updates: Dictionary of fields to update

        Returns:
            True if update was successful, False otherwise
        """
        try:
            all_metadata = self.load_all_metadata()
            metadata_dict = all_metadata.get(content_id)

            if metadata_dict:
                # Update the metadata fields
                for key, value in updates.items():
                    metadata_dict[key] = value

                # Save back to storage
                all_metadata[content_id] = metadata_dict
                with open(self.metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(all_metadata, f, ensure_ascii=False, indent=2, default=str)

                logger.info(f"Updated metadata for content: {content_id}")
                return True
            else:
                logger.warning(f"Metadata not found for content: {content_id}")
                return False

        except Exception as e:
            logger.error(f"Error updating metadata for content {content_id}: {e}")
            return False

    def delete_metadata(self, content_id: str) -> bool:
        """
        Delete content metadata

        Args:
            content_id: ID of the content to delete metadata for

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            all_metadata = self.load_all_metadata()

            if content_id in all_metadata:
                del all_metadata[content_id]

                # Save back to storage
                with open(self.metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(all_metadata, f, ensure_ascii=False, indent=2, default=str)

                logger.info(f"Deleted metadata for content: {content_id}")
                return True
            else:
                logger.info(f"Metadata not found for content: {content_id}")
                return False

        except Exception as e:
            logger.error(f"Error deleting metadata for content {content_id}: {e}")
            return False

    def get_quality_report(self) -> Dict[str, Any]:
        """
        Generate a quality report for all stored content

        Returns:
            Dictionary with quality metrics and statistics
        """
        all_metadata = self.load_all_metadata()
        if not all_metadata:
            return {"message": "No metadata available"}

        quality_scores = [meta.get('quality_score', 0) for meta in all_metadata.values()]
        content_lengths = [meta.get('content_length', 0) for meta in all_metadata.values()]
        word_counts = [meta.get('word_count', 0) for meta in all_metadata.values()]

        # Calculate statistics
        total_content = len(all_metadata)
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        avg_content_length = sum(content_lengths) / len(content_lengths) if content_lengths else 0
        avg_word_count = sum(word_counts) / len(word_counts) if word_counts else 0
        high_quality_count = sum(1 for score in quality_scores if score >= 0.7)
        low_quality_count = sum(1 for score in quality_scores if score < 0.3)

        return {
            "total_content": total_content,
            "average_quality_score": avg_quality,
            "average_content_length": avg_content_length,
            "average_word_count": avg_word_count,
            "high_quality_content": high_quality_count,
            "low_quality_content": low_quality_count,
            "quality_distribution": {
                "excellent": sum(1 for score in quality_scores if score >= 0.9),
                "good": sum(1 for score in quality_scores if 0.7 <= score < 0.9),
                "fair": sum(1 for score in quality_scores if 0.3 <= score < 0.7),
                "poor": sum(1 for score in quality_scores if score < 0.3)
            }
        }

    def validate_content_before_storage(self, extracted_content: ExtractedContent) -> Dict[str, Any]:
        """
        Validate content before storage and generate quality metrics

        Args:
            extracted_content: ExtractedContent object to validate

        Returns:
            Dictionary with validation results and quality metrics
        """
        results = {
            "valid": True,
            "quality_score": 0.0,
            "issues": [],
            "suggestions": []
        }

        # Content length check
        content_length = len(extracted_content.content) if extracted_content.content else 0
        if content_length < 50:
            results["valid"] = False
            results["issues"].append("Content too short")
            results["suggestions"].append("Ensure the page contains substantial content")
        elif content_length < 200:
            results["quality_score"] += 0.2
        elif content_length < 500:
            results["quality_score"] += 0.4
        else:
            results["quality_score"] += 0.6

        # Title quality
        if extracted_content.title and len(extracted_content.title.strip()) > 3:
            results["quality_score"] += 0.2

        # URL validity
        if extracted_content.url:
            results["quality_score"] += 0.1

        # Content uniqueness (based on hash)
        if extracted_content.content_hash:
            # In a real implementation, you'd check against existing hashes
            results["quality_score"] += 0.1

        # Ensure quality score is between 0 and 1
        results["quality_score"] = min(1.0, results["quality_score"])

        return results

    def create_metadata_from_extracted_content(self, extracted_content: ExtractedContent) -> ContentMetadata:
        """
        Create ContentMetadata object from ExtractedContent

        Args:
            extracted_content: ExtractedContent object to create metadata from

        Returns:
            ContentMetadata object
        """
        # Validate content and get quality metrics
        validation_results = self.validate_content_before_storage(extracted_content)

        # Extract content structure information from metadata if available
        content_structure = {}
        if extracted_content.metadata and isinstance(extracted_content.metadata, dict):
            content_structure = extracted_content.metadata.get('headings', {})

        metadata = ContentMetadata(
            content_id=extracted_content.id,
            source_url=extracted_content.url,
            module=extracted_content.module,
            section=extracted_content.section,
            version=extracted_content.version,
            quality_score=validation_results["quality_score"],
            content_length=len(extracted_content.content) if extracted_content.content else 0,
            word_count=extracted_content.word_count,
            content_structure=content_structure,
            content_hash=extracted_content.content_hash
        )

        return metadata

    def get_content_status(self, content_id: str) -> str:
        """
        Get the processing status of content

        Args:
            content_id: ID of the content to check

        Returns:
            Status string (e.g., "extracted", "reviewed", "embedded", "rejected")
        """
        metadata = self.load_metadata(content_id)
        if metadata:
            # In a real implementation, you'd have status tracking in the metadata
            # For now, return a default status
            return "extracted"
        else:
            return "not_found"

    def mark_content_as_reviewed(self, content_id: str, approved: bool = True) -> bool:
        """
        Mark content as reviewed (approved or rejected)

        Args:
            content_id: ID of the content to mark
            approved: Whether the content was approved during review

        Returns:
            True if marking was successful, False otherwise
        """
        # In a real implementation, you'd add a review status field to the metadata
        # For now, we'll just update the quality score based on approval
        if approved:
            return self.update_metadata(content_id, {"review_status": "approved"})
        else:
            return self.update_metadata(content_id, {"review_status": "rejected"})


class ContentValidator:
    """
    Validates content quality and completeness before storage
    """

    def __init__(self):
        pass

    def validate_content(self, extracted_content: ExtractedContent) -> Dict[str, Any]:
        """
        Validate extracted content and return quality metrics

        Args:
            extracted_content: ExtractedContent object to validate

        Returns:
            Dictionary with validation results and quality metrics
        """
        results = {
            'valid': True,
            'quality_score': 0.0,
            'issues': [],
            'suggestions': []
        }

        # Check content length
        content_length = len(extracted_content.content) if extracted_content.content else 0
        if content_length < 50:
            results['valid'] = False
            results['issues'].append('Content too short')
            results['suggestions'].append('Ensure the page contains substantial content')
        elif content_length < 200:
            results['quality_score'] += 0.3
            results['suggestions'].append('Content is quite short, consider if more content is available')
        else:
            results['quality_score'] += 0.5

        # Check title
        if not extracted_content.title or len(extracted_content.title.strip()) < 3:
            results['valid'] = False
            results['issues'].append('Title too short or missing')
        else:
            results['quality_score'] += 0.2

        # Check URL
        if not extracted_content.url:
            results['valid'] = False
            results['issues'].append('URL missing')
        else:
            results['quality_score'] += 0.1

        # Check for common issues
        if extracted_content.content and '404' in extracted_content.content:
            results['issues'].append('Possible 404 error page detected')
            results['valid'] = False

        if extracted_content.content and 'access denied' in extracted_content.content.lower():
            results['issues'].append('Access denied page detected')
            results['valid'] = False

        # Ensure quality score is between 0 and 1
        results['quality_score'] = min(1.0, results['quality_score'])

        return results

    def filter_content(self, extracted_contents: List[ExtractedContent]) -> List[ExtractedContent]:
        """
        Filter out low-quality content

        Args:
            extracted_contents: List of ExtractedContent objects

        Returns:
            Filtered list of ExtractedContent objects
        """
        filtered_contents = []

        for content in extracted_contents:
            validation = self.validate_content(content)
            if validation['valid'] and validation['quality_score'] >= 0.5:  # Only keep content with 50%+ quality
                filtered_contents.append(content)
            else:
                logger.info(f"Filtered out low-quality content from {content.url}: {validation['issues']}")

        return filtered_contents