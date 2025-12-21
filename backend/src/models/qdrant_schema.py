"""
Qdrant schema and ID strategy definitions for the embedding storage
"""
from typing import Dict, Any, Optional
from enum import Enum
import uuid
from datetime import datetime


class ContentType(Enum):
    """
    Enum for different types of content that can be stored
    """
    TEXT = "text"
    CODE = "code"
    DOCUMENTATION = "documentation"
    ARTICLE = "article"
    TUTORIAL = "tutorial"


class QdrantSchema:
    """
    Defines the schema for storing embeddings in Qdrant
    """

    @staticmethod
    def get_embedding_payload_schema() -> Dict[str, Any]:
        """
        Get the schema definition for embedding payloads

        Returns:
            Dictionary representing the payload schema
        """
        return {
            "url": "string",  # Source URL of the content
            "title": "string",  # Page title
            "module": "string",  # Module name (e.g., "Module 1: The Robotic Nervous System")
            "section": "string",  # Section name (e.g., "Week 3-5", "ROS 2 Nodes, Topics, and Services")
            "version": "string",  # Version identifier for the content
            "content_type": "string",  # Type of content (text, code, documentation, etc.)
            "word_count": "integer",  # Number of words in the content
            "content_hash": "string",  # Hash of the content for deduplication
            "created_at": "string",  # Timestamp when content was extracted
            "updated_at": "string",  # Timestamp when content was last updated
            "quality_score": "float",  # Quality assessment score (0.0-1.0)
            "chunk_index": "integer",  # Index of the content chunk if content was split
            "total_chunks": "integer",  # Total number of chunks for this content
            "language": "string",  # Detected language of content
            "metadata": "object"  # Additional metadata as key-value pairs
        }

    @staticmethod
    def create_payload(
        url: str,
        title: str,
        content: str = "",
        module: Optional[str] = None,
        section: Optional[str] = None,
        version: Optional[str] = "1.0.0",
        content_type: ContentType = ContentType.TEXT,
        word_count: Optional[int] = None,
        content_hash: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        quality_score: Optional[float] = None,
        chunk_index: Optional[int] = 0,
        total_chunks: Optional[int] = 1,
        language: Optional[str] = "en",
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a properly formatted payload for Qdrant embedding storage

        Args:
            url: Source URL of the content
            title: Page title
            content: The content text (used to calculate word count if not provided)
            module: Module name
            section: Section name
            version: Version identifier
            content_type: Type of content
            word_count: Number of words in the content
            content_hash: Hash of the content for deduplication
            created_at: Timestamp when content was extracted
            updated_at: Timestamp when content was last updated
            quality_score: Quality assessment score
            chunk_index: Index of the content chunk if content was split
            total_chunks: Total number of chunks for this content
            language: Detected language of content
            additional_metadata: Additional metadata as key-value pairs

        Returns:
            Dictionary formatted for Qdrant payload
        """
        if created_at is None:
            created_at = datetime.utcnow()

        if updated_at is None:
            updated_at = created_at

        # Calculate word count if not provided
        if word_count is None and content:
            word_count = len(content.split())

        payload = {
            "url": url,
            "title": title,
            "module": module or "",
            "section": section or "",
            "version": version,
            "content_type": content_type.value,
            "word_count": word_count or 0,
            "content_hash": content_hash or "",
            "created_at": created_at.isoformat(),
            "updated_at": updated_at.isoformat(),
            "quality_score": quality_score or 0.0,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "language": language or "en",
            "metadata": additional_metadata or {}
        }

        return payload

    @staticmethod
    def generate_embedding_id() -> str:
        """
        Generate a unique ID for an embedding

        Returns:
            UUID string for the embedding
        """
        return str(uuid.uuid4())

    @staticmethod
    def validate_payload(payload: Dict[str, Any]) -> bool:
        """
        Validate that a payload has the required fields for Qdrant storage

        Args:
            payload: The payload to validate

        Returns:
            True if payload is valid, False otherwise
        """
        required_fields = ["url", "title", "content_type", "content_hash"]
        for field in required_fields:
            if field not in payload:
                return False
            if payload[field] is None:
                return False

        # Validate content_type is valid
        try:
            ContentType(payload["content_type"])
        except ValueError:
            return False

        return True

    @staticmethod
    def get_search_filters(
        module: Optional[str] = None,
        section: Optional[str] = None,
        content_type: Optional[ContentType] = None,
        min_quality_score: Optional[float] = None,
        url_pattern: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create filters for searching embeddings in Qdrant

        Args:
            module: Filter by module name
            section: Filter by section name
            content_type: Filter by content type
            min_quality_score: Filter by minimum quality score
            url_pattern: Filter by URL pattern

        Returns:
            Dictionary of filters for Qdrant search
        """
        filters = {}

        if module:
            filters["module"] = module
        if section:
            filters["section"] = section
        if content_type:
            filters["content_type"] = content_type.value
        if min_quality_score is not None:
            filters["quality_score"] = {"$gte": min_quality_score}
        if url_pattern:
            filters["url"] = {"$regex": url_pattern}

        return filters


# Singleton instance for easy access
qdrant_schema = QdrantSchema()