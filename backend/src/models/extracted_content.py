"""
Data models for extracted content in the RAG pipeline
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from src.utils.hash_utils import generate_content_hash


@dataclass
class ExtractedContent:
    """
    Represents the raw content extracted from the website with associated metadata.
    """
    id: str
    url: str
    title: str
    content: str
    module: Optional[str] = None
    section: Optional[str] = None
    version: Optional[str] = "1.0.0"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    content_type: str = "text"
    word_count: Optional[int] = None
    content_hash: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """
        Post-initialization processing to set default values
        """
        if self.created_at is None:
            self.created_at = datetime.utcnow()

        if self.updated_at is None:
            self.updated_at = self.created_at

        if self.word_count is None:
            self.word_count = len(self.content.split()) if self.content else 0

        if self.content_hash is None:
            self.content_hash = generate_content_hash(self.content)

        if self.metadata is None:
            self.metadata = {}

    def validate(self) -> bool:
        """
        Validate the extracted content object

        Returns:
            True if the object is valid, False otherwise
        """
        # Check that required fields are not empty
        if not self.url or not isinstance(self.url, str):
            return False

        if not self.title or not isinstance(self.title, str):
            return False

        if not isinstance(self.content, str):
            return False

        # Check that word_count is non-negative
        if self.word_count is not None and self.word_count < 0:
            return False

        # Check that content_hash is valid
        if self.content_hash and not isinstance(self.content_hash, str):
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the ExtractedContent object to a dictionary

        Returns:
            Dictionary representation of the object
        """
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "module": self.module,
            "section": self.section,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "content_type": self.content_type,
            "word_count": self.word_count,
            "content_hash": self.content_hash,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtractedContent':
        """
        Create an ExtractedContent object from a dictionary

        Args:
            data: Dictionary containing the extracted content data

        Returns:
            ExtractedContent object
        """
        from datetime import datetime

        # Handle datetime conversion
        created_at = None
        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))

        updated_at = None
        if data.get("updated_at"):
            updated_at = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))

        return cls(
            id=data["id"],
            url=data["url"],
            title=data["title"],
            content=data["content"],
            module=data.get("module"),
            section=data.get("section"),
            version=data.get("version", "1.0.0"),
            created_at=created_at,
            updated_at=updated_at,
            content_type=data.get("content_type", "text"),
            word_count=data.get("word_count"),
            content_hash=data.get("content_hash"),
            metadata=data.get("metadata", {})
        )

    def update_content(self, new_content: str):
        """
        Update the content and recalculate dependent fields

        Args:
            new_content: New content string
        """
        self.content = new_content
        self.updated_at = datetime.utcnow()
        self.word_count = len(new_content.split()) if new_content else 0
        self.content_hash = generate_content_hash(new_content)


@dataclass
class EmbeddingVector:
    """
    Represents the vector embedding of content stored in Qdrant.
    """
    id: str  # Should match the ExtractedContent.id
    vector: list  # The embedding vector from Cohere
    payload: Dict[str, Any]  # Metadata object containing URL, title, etc.

    def validate(self) -> bool:
        """
        Validate the embedding vector object

        Returns:
            True if the object is valid, False otherwise
        """
        # Check that required fields are not empty
        if not self.id or not isinstance(self.id, str):
            return False

        if not self.vector or not isinstance(self.vector, list):
            return False

        if not self.payload or not isinstance(self.payload, dict):
            return False

        # Check that vector has consistent dimensions
        if not all(isinstance(v, (int, float)) for v in self.vector):
            return False

        # Check that payload contains required fields
        required_payload_fields = ["url", "title", "content_hash"]
        for field in required_payload_fields:
            if field not in self.payload:
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the EmbeddingVector object to a dictionary

        Returns:
            Dictionary representation of the object
        """
        return {
            "id": self.id,
            "vector": self.vector,
            "payload": self.payload
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EmbeddingVector':
        """
        Create an EmbeddingVector object from a dictionary

        Args:
            data: Dictionary containing the embedding vector data

        Returns:
            EmbeddingVector object
        """
        return cls(
            id=data["id"],
            vector=data["vector"],
            payload=data["payload"]
        )


@dataclass
class ContentMetadata:
    """
    Contains information about the extracted content structure and quality.
    """
    content_id: str
    source_url: str
    module: Optional[str] = None
    section: Optional[str] = None
    version: Optional[str] = "1.0.0"
    extraction_date: Optional[datetime] = None
    quality_score: float = 0.0  # Quality assessment score (0.0-1.0)
    content_length: Optional[int] = None  # Length of extracted content in characters
    word_count: Optional[int] = None  # Number of words in content
    language: Optional[str] = "en"  # Detected language of content
    content_structure: Optional[Dict[str, Any]] = None  # Information about headings, code blocks, etc.
    content_hash: Optional[str] = None  # Hash of the content for deduplication purposes

    def __post_init__(self):
        """
        Post-initialization processing to set default values
        """
        if self.extraction_date is None:
            self.extraction_date = datetime.utcnow()

        if self.content_length is None and self.content_hash:
            # If content_hash is available, we can estimate content length
            # This is a placeholder - in a real implementation, you'd have access to the actual content
            pass

        if self.content_structure is None:
            self.content_structure = {}

    def validate(self) -> bool:
        """
        Validate the content metadata object

        Returns:
            True if the object is valid, False otherwise
        """
        # Check that required fields are not empty
        if not self.content_id or not isinstance(self.content_id, str):
            return False

        if not self.source_url or not isinstance(self.source_url, str):
            return False

        # Check that quality_score is between 0.0 and 1.0
        if not 0.0 <= self.quality_score <= 1.0:
            return False

        # Check that content_length is non-negative
        if self.content_length is not None and self.content_length < 0:
            return False

        # Check that word_count is non-negative
        if self.word_count is not None and self.word_count < 0:
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the ContentMetadata object to a dictionary

        Returns:
            Dictionary representation of the object
        """
        return {
            "content_id": self.content_id,
            "source_url": self.source_url,
            "module": self.module,
            "section": self.section,
            "version": self.version,
            "extraction_date": self.extraction_date.isoformat() if self.extraction_date else None,
            "quality_score": self.quality_score,
            "content_length": self.content_length,
            "word_count": self.word_count,
            "language": self.language,
            "content_structure": self.content_structure,
            "content_hash": self.content_hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentMetadata':
        """
        Create a ContentMetadata object from a dictionary

        Args:
            data: Dictionary containing the content metadata data

        Returns:
            ContentMetadata object
        """
        from datetime import datetime

        # Handle datetime conversion
        extraction_date = None
        if data.get("extraction_date"):
            extraction_date = datetime.fromisoformat(data["extraction_date"].replace("Z", "+00:00"))

        return cls(
            content_id=data["content_id"],
            source_url=data["source_url"],
            module=data.get("module"),
            section=data.get("section"),
            version=data.get("version", "1.0.0"),
            extraction_date=extraction_date,
            quality_score=data.get("quality_score", 0.0),
            content_length=data.get("content_length"),
            word_count=data.get("word_count"),
            language=data.get("language", "en"),
            content_structure=data.get("content_structure", {}),
            content_hash=data.get("content_hash")
        )