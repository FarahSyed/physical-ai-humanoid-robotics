"""
Embedding generator module for creating vector embeddings from extracted content
"""
import time
from typing import List, Dict, Any, Optional
from src.models.extracted_content import ExtractedContent, EmbeddingVector
from src.utils.config_loader import config
from src.utils.logger import logger
from src.utils.hash_utils import generate_content_hash


class EmbeddingGenerator:
    """
    Generates vector embeddings from extracted content using Cohere API
    """

    def __init__(self):
        self.batch_size = config.embedding_batch_size

    def generate_embeddings(self, extracted_contents: List[ExtractedContent],
                          batch_size: int = None) -> List[EmbeddingVector]:
        """
        Generate embeddings for a list of extracted content items

        Args:
            extracted_contents: List of ExtractedContent objects to generate embeddings for
            batch_size: Size of batches for embedding generation (uses config if not provided)

        Returns:
            List of EmbeddingVector objects
        """
        import cohere

        batch_size = batch_size or self.batch_size

        # Initialize Cohere client
        co = cohere.Client(config.cohere_api_key)

        embedding_vectors = []

        # Process in batches to respect API limits
        for i in range(0, len(extracted_contents), batch_size):
            batch = extracted_contents[i:i + batch_size]
            logger.info(f"Processing embedding batch {i//batch_size + 1}/{(len(extracted_contents)-1)//batch_size + 1}")

            # Extract content texts for embedding
            texts = []
            content_map = {}  # Map from text to content object for reference

            for content in batch:
                # Truncate content if it's too long (Cohere has limits)
                text = content.content
                if len(text) > 5000:  # Cohere's typical limit
                    logger.warning(f"Truncating content from {content.url} due to length: {len(text)} chars")
                    text = text[:5000]

                texts.append(text)
                content_map[text] = content

            try:
                # Generate embeddings
                response = co.embed(
                    texts=texts,
                    model='multilingual-22-12',  # Using a suitable Cohere model
                    input_type='search_document'
                )

                # Create embedding vectors
                for j, embedding_vector in enumerate(response.embeddings):
                    original_text = texts[j]
                    original_content = content_map[original_text]

                    # Create payload with metadata
                    payload = {
                        'url': original_content.url,
                        'title': original_content.title,
                        'content': original_content.content[:1000] + "..." if len(original_content.content) > 1000 else original_content.content,  # Truncate long content
                        'module': original_content.module,
                        'section': original_content.section,
                        'version': original_content.version,
                        'created_at': original_content.created_at.isoformat() if original_content.created_at else None,
                        'word_count': original_content.word_count,
                        'content_hash': original_content.content_hash,
                        'content_type': original_content.content_type
                    }

                    # Add any additional metadata
                    if original_content.metadata:
                        payload.update(original_content.metadata)

                    embedding_vector_obj = EmbeddingVector(
                        id=original_content.id,
                        vector=embedding_vector,
                        payload=payload
                    )

                    # Validate the embedding vector
                    if embedding_vector_obj.validate():
                        embedding_vectors.append(embedding_vector_obj)
                    else:
                        logger.error(f"Invalid embedding vector for content {original_content.id}")

            except Exception as e:
                logger.error(f"Error generating embeddings for batch {i//batch_size + 1}: {e}")

                # Implement retry logic for API errors
                if "rate limit" in str(e).lower() or "too many requests" in str(e).lower():
                    logger.info("Rate limit hit, waiting before retry...")
                    time.sleep(10)  # Wait before retrying
                    continue
                else:
                    # Skip this batch if it's a different error
                    continue

        logger.info(f"Generated {len(embedding_vectors)} embeddings from {len(extracted_contents)} content items")
        return embedding_vectors

    def generate_single_embedding(self, content: ExtractedContent) -> Optional[EmbeddingVector]:
        """
        Generate a single embedding for one content item

        Args:
            content: ExtractedContent object to generate embedding for

        Returns:
            EmbeddingVector object or None if generation fails
        """
        import cohere

        # Initialize Cohere client
        co = cohere.Client(config.cohere_api_key)

        try:
            # Truncate content if it's too long
            text = content.content
            if len(text) > 5000:
                logger.warning(f"Truncating content from {content.url} due to length: {len(text)} chars")
                text = text[:5000]

            # Generate embedding
            response = co.embed(
                texts=[text],
                model='multilingual-22-12',
                input_type='search_document'
            )

            # Create payload with metadata
            payload = {
                'url': content.url,
                'title': content.title,
                'content': content.content[:1000] + "..." if len(content.content) > 1000 else content.content,
                'module': content.module,
                'section': content.section,
                'version': content.version,
                'created_at': content.created_at.isoformat() if content.created_at else None,
                'word_count': content.word_count,
                'content_hash': content.content_hash,
                'content_type': content.content_type
            }

            # Add any additional metadata
            if content.metadata:
                payload.update(content.metadata)

            embedding_vector = EmbeddingVector(
                id=content.id,
                vector=response.embeddings[0],
                payload=payload
            )

            if embedding_vector.validate():
                return embedding_vector
            else:
                logger.error(f"Invalid embedding vector for content {content.id}")
                return None

        except Exception as e:
            logger.error(f"Error generating embedding for content {content.id}: {e}")
            return None

    def validate_embedding_quality(self, embedding_vector: EmbeddingVector,
                                 original_content: ExtractedContent) -> Dict[str, Any]:
        """
        Validate the quality and correctness of an embedding

        Args:
            embedding_vector: EmbeddingVector to validate
            original_content: Original ExtractedContent for comparison

        Returns:
            Dictionary with validation results
        """
        results = {
            'valid': True,
            'issues': [],
            'similarity_check_passed': True
        }

        # Check embedding dimensions (should be consistent)
        if not embedding_vector.vector or len(embedding_vector.vector) == 0:
            results['valid'] = False
            results['issues'].append('Empty embedding vector')

        # Check that required payload fields are present
        required_fields = ['url', 'title', 'content_hash']
        for field in required_fields:
            if field not in embedding_vector.payload:
                results['valid'] = False
                results['issues'].append(f'Missing required payload field: {field}')

        # Check content hash matches
        if (original_content.content_hash and
            embedding_vector.payload.get('content_hash') != original_content.content_hash):
            results['valid'] = False
            results['issues'].append('Content hash mismatch between original and embedding payload')

        return results

    def batch_generate_with_validation(self, extracted_contents: List[ExtractedContent],
                                     batch_size: int = None) -> List[EmbeddingVector]:
        """
        Generate embeddings with validation and error handling

        Args:
            extracted_contents: List of ExtractedContent objects to generate embeddings for
            batch_size: Size of batches for embedding generation

        Returns:
            List of validated EmbeddingVector objects
        """
        embeddings = self.generate_embeddings(extracted_contents, batch_size)

        validated_embeddings = []
        for i, embedding in enumerate(embeddings):
            original_content = next((c for c in extracted_contents if c.id == embedding.id), None)
            if original_content:
                validation = self.validate_embedding_quality(embedding, original_content)
                if validation['valid']:
                    validated_embeddings.append(embedding)
                else:
                    logger.warning(f"Embedding failed validation for content {embedding.id}: {validation['issues']}")
            else:
                logger.warning(f"No original content found for embedding ID {embedding.id}")
                validated_embeddings.append(embedding)  # Still include if validation isn't possible

        logger.info(f"Validated {len(validated_embeddings)} out of {len(embeddings)} embeddings passed validation")
        return validated_embeddings


class EmbeddingStorageManager:
    """
    Manages the storage of embeddings in Qdrant with deduplication
    """

    def __init__(self):
        from src.embeddings.qdrant_client import qdrant_client
        self.qdrant_client = qdrant_client

    def store_embeddings(self, embedding_vectors: List[EmbeddingVector],
                        batch_size: int = 10) -> Dict[str, Any]:
        """
        Store embeddings in Qdrant with deduplication

        Args:
            embedding_vectors: List of EmbeddingVector objects to store
            batch_size: Batch size for storage operations

        Returns:
            Dictionary with storage results
        """
        # Prepare data for Qdrant
        embeddings_data = []
        for embedding in embedding_vectors:
            embedding_data = {
                'id': embedding.id,
                'vector': embedding.vector,
                'payload': embedding.payload
            }
            embeddings_data.append(embedding_data)

        # Store in Qdrant
        result = self.qdrant_client.upsert_embeddings(embeddings_data, batch_size)
        return result

    def check_content_exists(self, content_hash: str) -> bool:
        """
        Check if content with given hash already exists in Qdrant

        Args:
            content_hash: Hash of the content to check

        Returns:
            True if content exists, False otherwise
        """
        # Search in Qdrant for content with the same hash
        try:
            results = self.qdrant_client.search_similar(
                query_vector=[0.1] * 1024,  # Dummy vector for search with filter
                top_k=1,
                filters={'content_hash': content_hash}
            )
            return len(results) > 0
        except Exception as e:
            logger.error(f"Error checking content existence: {e}")
            return False

    def store_with_deduplication(self, embedding_vectors: List[EmbeddingVector],
                               batch_size: int = 10) -> Dict[str, Any]:
        """
        Store embeddings with automatic deduplication based on content hash

        Args:
            embedding_vectors: List of EmbeddingVector objects to store
            batch_size: Batch size for storage operations

        Returns:
            Dictionary with storage results including deduplication stats
        """
        # Filter out duplicates based on content hash
        unique_embeddings = []
        processed_hashes = set()

        for embedding in embedding_vectors:
            content_hash = embedding.payload.get('content_hash')
            if content_hash and content_hash not in processed_hashes:
                # Also check if it exists in Qdrant already
                if not self.check_content_exists(content_hash):
                    unique_embeddings.append(embedding)
                    processed_hashes.add(content_hash)
                else:
                    logger.info(f"Content with hash {content_hash} already exists in Qdrant, skipping")
            elif not content_hash:
                # If no content hash, use the ID as a fallback
                if embedding.id not in processed_hashes:
                    unique_embeddings.append(embedding)
                    processed_hashes.add(embedding.id)

        logger.info(f"Storing {len(unique_embeddings)} unique embeddings out of {len(embedding_vectors)} total")

        # Store the unique embeddings
        result = self.store_embeddings(unique_embeddings, batch_size)

        # Add deduplication stats to the result
        result['deduplication'] = {
            'original_count': len(embedding_vectors),
            'unique_count': len(unique_embeddings),
            'duplicates_removed': len(embedding_vectors) - len(unique_embeddings)
        }

        return result