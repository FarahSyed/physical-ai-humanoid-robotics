"""
Preview service for the pipeline verification system.

This module implements content preview mechanisms for extracted text and chunks
with safety measures for large content, including sampling, paging, and memory safety.
"""
from typing import Optional, Dict, Any, List
import logging
from pathlib import Path

from src.utils.validation_utils import validate_content_length, validate_preview_params, sanitize_content


class PreviewService:
    """
    Service for generating previews of content for approval workflows.

    This service provides safe and efficient ways to preview extracted content and chunked output
    with safety measures for large content, including sampling, pagination, and content sanitization.
    """

    def __init__(self, max_preview_length: int = 10000, default_sample_size: int = 1000):
        """
        Initialize the preview service.

        Args:
            max_preview_length: Maximum length of preview content (default: 10000 chars)
            default_sample_size: Default sample size for content preview (default: 1000 chars)
        """
        self.max_preview_length = max_preview_length
        self.default_sample_size = default_sample_size

    def preview_extracted_content(self, content_path: str, offset: int = 0,
                                 limit: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Generate a preview of extracted content.

        Args:
            content_path: Path to the extracted content file
            offset: Starting position for preview (default: 0)
            limit: Number of characters to include in preview (default: use default_sample_size)

        Returns:
            Dictionary with preview information or None if error
        """
        try:
            # Use default limit if not provided
            if limit is None:
                limit = self.default_sample_size

            # Validate inputs
            if not Path(content_path).exists():
                logging.error(f"Content file does not exist: {content_path}")
                return None

            # Read content
            with open(content_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Validate content length
            if not validate_content_length(content, self.max_preview_length):
                logging.error(f"Content exceeds maximum length: {content_path}")
                return None

            # Validate preview parameters
            if not validate_preview_params(offset, limit, len(content)):
                logging.error(f"Invalid preview parameters for content: offset={offset}, limit={limit}, length={len(content)}")
                return None

            # Generate preview
            preview_content = content[offset:offset + limit]
            preview_content = sanitize_content(preview_content, self.max_preview_length)

            return {
                "preview_type": "extracted_content",
                "source_path": content_path,
                "offset": offset,
                "limit": limit,
                "total_length": len(content),
                "preview_content": preview_content,
                "preview_length": len(preview_content)
            }
        except Exception as e:
            logging.error(f"Error previewing extracted content from {content_path}: {str(e)}")
            return None

    def preview_chunked_output(self, chunks_path: str, chunk_index: Optional[int] = None,
                              offset: int = 0, limit: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Generate a preview of chunked output.

        Args:
            chunks_path: Path to the chunked output file
            chunk_index: Specific chunk index to preview (default: preview first few chunks)
            offset: Starting position for preview (default: 0)
            limit: Number of characters to include in preview (default: use default_sample_size)

        Returns:
            Dictionary with preview information or None if error
        """
        try:
            # Use default limit if not provided
            if limit is None:
                limit = self.default_sample_size

            # Validate inputs
            if not Path(chunks_path).exists():
                logging.error(f"Chunks file does not exist: {chunks_path}")
                return None

            # Read chunked content
            with open(chunks_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Validate content length
            if not validate_content_length(content, self.max_preview_length):
                logging.error(f"Chunked content exceeds maximum length: {chunks_path}")
                return None

            # If chunk_index is specified, try to parse and extract that specific chunk
            if chunk_index is not None:
                chunks = self._parse_chunks(content)
                if chunk_index >= len(chunks):
                    logging.error(f"Chunk index {chunk_index} out of range, only {len(chunks)} chunks available")
                    return None

                chunk_content = chunks[chunk_index]
                # Apply offset and limit to the specific chunk
                if not validate_preview_params(offset, limit, len(chunk_content)):
                    logging.error(f"Invalid preview parameters for chunk {chunk_index}: offset={offset}, limit={limit}, length={len(chunk_content)}")
                    return None

                preview_content = chunk_content[offset:offset + limit]
                preview_content = sanitize_content(preview_content, self.max_preview_length)

                return {
                    "preview_type": "chunked_output",
                    "source_path": chunks_path,
                    "chunk_index": chunk_index,
                    "chunk_total": len(chunks),
                    "offset": offset,
                    "limit": limit,
                    "total_length": len(chunk_content),
                    "preview_content": preview_content,
                    "preview_length": len(preview_content)
                }
            else:
                # Preview the first few chunks or a sample of the content
                if not validate_preview_params(offset, limit, len(content)):
                    logging.error(f"Invalid preview parameters for content: offset={offset}, limit={limit}, length={len(content)}")
                    return None

                preview_content = content[offset:offset + limit]
                preview_content = sanitize_content(preview_content, self.max_preview_length)

                chunks = self._parse_chunks(content)
                return {
                    "preview_type": "chunked_output",
                    "source_path": chunks_path,
                    "chunk_index": chunk_index,  # None means previewing overall content
                    "chunk_total": len(chunks),
                    "offset": offset,
                    "limit": limit,
                    "total_length": len(content),
                    "preview_content": preview_content,
                    "preview_length": len(preview_content)
                }
        except Exception as e:
            logging.error(f"Error previewing chunked output from {chunks_path}: {str(e)}")
            return None

    def _parse_chunks(self, content: str) -> List[str]:
        """
        Parse chunked content from a file into a list of chunks.

        Args:
            content: The content to parse

        Returns:
            List of chunks
        """
        try:
            # For this implementation, we'll assume chunks are separated by a special marker
            # In a real implementation, this would depend on the actual chunk format
            import json
            try:
                # Try to parse as JSON array of chunks
                data = json.loads(content)
                if isinstance(data, list):
                    return [str(item) for item in data]
            except json.JSONDecodeError:
                pass

            # If not JSON, split by common separators
            # This is a simplified approach - real implementation would depend on actual format
            return [content[i:i+1000] for i in range(0, len(content), 1000)]  # Simple 1000 char chunks
        except Exception as e:
            logging.error(f"Error parsing chunks: {str(e)}")
            # Return the entire content as a single chunk if parsing fails
            return [content]

    def generate_content_sample(self, content_path: str, sample_size: Optional[int] = None) -> Optional[str]:
        """
        Generate a sample of content for quick preview.

        Args:
            content_path: Path to the content file
            sample_size: Size of the sample to generate (default: use default_sample_size)

        Returns:
            Sample content string or None if error
        """
        try:
            if sample_size is None:
                sample_size = self.default_sample_size

            # Validate inputs
            if not Path(content_path).exists():
                logging.error(f"Content file does not exist: {content_path}")
                return None

            # Read content
            with open(content_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Validate content length
            if not validate_content_length(content, self.max_preview_length):
                logging.error(f"Content exceeds maximum length: {content_path}")
                return None

            # Generate sample
            sample = content[:sample_size]
            sample = sanitize_content(sample, self.max_preview_length)

            return sample
        except Exception as e:
            logging.error(f"Error generating content sample from {content_path}: {str(e)}")
            return None

    def preview_large_content_with_pagination(self, content_path: str, page: int = 1,
                                           page_size: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Preview large content with pagination to avoid memory issues.

        Args:
            content_path: Path to the content file
            page: Page number to preview (default: 1)
            page_size: Size of each page (default: use default_sample_size)

        Returns:
            Dictionary with paginated preview information or None if error
        """
        try:
            if page_size is None:
                page_size = self.default_sample_size

            if page < 1:
                page = 1

            # Validate inputs
            if not Path(content_path).exists():
                logging.error(f"Content file does not exist: {content_path}")
                return None

            # Read content
            with open(content_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Validate content length
            if not validate_content_length(content, self.max_preview_length):
                logging.error(f"Content exceeds maximum length: {content_path}")
                return None

            # Calculate offset based on page
            offset = (page - 1) * page_size

            # Validate preview parameters
            if not validate_preview_params(offset, page_size, len(content)):
                # If the calculated offset is beyond content length, return the last page
                if offset >= len(content):
                    offset = ((len(content) - 1) // page_size) * page_size
                    if offset < 0:
                        offset = 0

            # Generate preview
            preview_content = content[offset:offset + page_size]
            preview_content = sanitize_content(preview_content, self.max_preview_length)

            total_pages = (len(content) + page_size - 1) // page_size  # Ceiling division

            return {
                "preview_type": "paginated_content",
                "source_path": content_path,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "total_length": len(content),
                "preview_content": preview_content,
                "preview_length": len(preview_content),
                "offset": offset
            }
        except Exception as e:
            logging.error(f"Error previewing content with pagination from {content_path}: {str(e)}")
            return None

    def validate_preview_safety(self, content: str) -> bool:
        """
        Validate that the preview content is safe to display.

        Args:
            content: Content to validate

        Returns:
            True if content is safe for preview, False otherwise
        """
        try:
            # Check for potentially harmful content
            # This is a basic implementation - real implementation would have more checks
            harmful_patterns = [
                "<script", "javascript:", "vbscript:", "onerror=", "onload=",
                "eval(", "exec(", "__import__"
            ]

            content_lower = content.lower()
            for pattern in harmful_patterns:
                if pattern in content_lower:
                    logging.warning(f"Potentially harmful content detected in preview: {pattern}")
                    return False

            return True
        except Exception as e:
            logging.error(f"Error validating preview safety: {str(e)}")
            return False

    def sanitize_preview_content(self, content: str) -> str:
        """
        Sanitize preview content to remove potentially harmful elements.

        Args:
            content: Content to sanitize

        Returns:
            Sanitized content string
        """
        try:
            # Basic sanitization - remove potentially harmful HTML/script tags
            sanitized = content.replace("<script", "&lt;script").replace("</script>", "&lt;/script>")
            sanitized = sanitized.replace("javascript:", "javascript_").replace("vbscript:", "vbscript_")
            return sanitized
        except Exception as e:
            logging.error(f"Error sanitizing preview content: {str(e)}")
            return content  # Return original if sanitization fails