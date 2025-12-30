"""
Qdrant client for embedding persistence.

This module implements persistence of embeddings to Qdrant vector database
with specific payload schema and ID strategy.
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional, Union
from uuid import uuid4
import numpy as np

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import Distance, VectorParams, PointStruct
except ImportError:
    raise ImportError(
        "qdrant-client is required for Qdrant persistence. "
        "Install it with: pip install qdrant-client"
    )

from .config import EmbeddingConfig


class QdrantEmbeddingClient:
    """
    Client for storing and retrieving embeddings from Qdrant vector database.
    """

    def __init__(self, config: EmbeddingConfig, collection_name: str = None):
        """
        Initialize the Qdrant client.

        Args:
            config: Embedding configuration containing Qdrant connection details
            collection_name: Name of the Qdrant collection to use (default: comes from config)
        """
        self.config = config
        # Use the collection name from config if not provided explicitly
        self.collection_name = collection_name or config.qdrant_collection_name
        self.client = None
        self.logger = logging.getLogger(__name__)
        self._vector_size = None  # Will be determined from first embedding

    def connect(self, **kwargs) -> 'QdrantEmbeddingClient':
        """
        Connect to Qdrant instance.

        Args:
            **kwargs: Additional connection parameters (host, port, etc.)

        Returns:
            Self instance for method chaining
        """
        # Use configuration values from the embedding config, with kwargs override capability
        host = kwargs.get('host', self.config.qdrant_host)
        port = kwargs.get('port', self.config.qdrant_port)
        https = kwargs.get('https', self.config.qdrant_https)
        prefix = kwargs.get('prefix', '')
        timeout = kwargs.get('timeout', self.config.qdrant_timeout)
        api_key = kwargs.get('api_key', self.config.qdrant_api_key)

        # Check if host contains protocol (for cloud instances)
        if host.startswith(('http://', 'https://')):
            # For cloud instances, use url parameter instead of host/port
            connection_params = {
                'url': host,
                'timeout': timeout,
                **{k: v for k, v in kwargs.items() if k not in ['host', 'port', 'https', 'prefix', 'timeout', 'api_key']}
            }
        else:
            # For local instances, use host/port parameters
            connection_params = {
                'host': host,
                'port': port,
                'https': https,
                'timeout': timeout,
                **{k: v for k, v in kwargs.items() if k not in ['host', 'port', 'https', 'prefix', 'timeout', 'api_key']}
            }

        # Add API key if provided
        if api_key:
            connection_params['api_key'] = api_key

        self.client = QdrantClient(**connection_params)

        # Ensure collection exists - run this synchronously instead of asyncio.run
        self._ensure_collection_exists_sync()

        # Create payload index for chunk_id field to enable efficient filtering
        self._create_payload_index_sync()

        return self

    def _ensure_collection_exists_sync(self) -> None:
        """
        Synchronous version of _ensure_collection_exists to avoid asyncio.run issues.
        """
        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name not in collection_names:
                # Create collection with appropriate vector parameters
                # Vector size will be determined from first embedding
                # For now, we'll use a default size that's common for embeddings
                vector_size = 384  # Default size for many embedding models

                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                self.logger.info(f"Created new collection: {self.collection_name}")
            else:
                # Get existing collection info to determine vector size
                collection_info = self.client.get_collection(self.collection_name)
                # Note: Accessing vector size from collection config may vary depending on Qdrant version
                self.logger.info(f"Using existing collection: {self.collection_name}")
        except Exception as e:
            self.logger.error(f"Error ensuring collection exists: {str(e)}")
            raise

    def _create_payload_index_sync(self) -> None:
        """
        Create payload index for chunk_id field to enable efficient filtering.
        """
        try:
            # Create index for chunk_id field to allow efficient filtering
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="chunk_id",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            self.logger.info(f"Created payload index for chunk_id in collection: {self.collection_name}")
        except Exception as e:
            # Index might already exist, which is fine
            self.logger.info(f"Payload index for chunk_id may already exist or error occurred: {str(e)}")

    async def _ensure_collection_exists(self) -> None:
        """
        Ensure the target collection exists in Qdrant.
        """
        try:
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if self.collection_name not in collection_names:
                # Create collection with appropriate vector parameters
                # Vector size will be determined from first embedding
                # For now, we'll use a default size that's common for embeddings
                vector_size = 384  # Default size for many embedding models

                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                self.logger.info(f"Created new collection: {self.collection_name}")
            else:
                # Get existing collection info to determine vector size
                collection_info = self.client.get_collection(self.collection_name)
                self.logger.info(f"Using existing collection: {self.collection_name}")
        except Exception as e:
            self.logger.error(f"Error ensuring collection exists: {str(e)}")
            raise

    def _generate_point_id(self, chunk_id: str) -> str:
        """
        Generate a unique point ID for Qdrant.

        Args:
            chunk_id: The original chunk ID

        Returns:
            Unique ID for the Qdrant point
        """
        # Use UUID for point ID to ensure compatibility with Qdrant cloud
        return str(uuid4())

    def _prepare_payload(
        self,
        chunk_id: str,
        pipeline_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare payload for Qdrant storage.

        Args:
            chunk_id: ID of the content chunk
            pipeline_id: ID of the pipeline
            content: The original content (or summary)
            metadata: Additional metadata

        Returns:
            Payload dictionary for Qdrant
        """
        payload = {
            "chunk_id": chunk_id,
            "pipeline_id": pipeline_id,
            "content_preview": content[:200] if content else "",  # Store a preview, not full content
            "timestamp": self._get_current_timestamp(),
            "embedding_model": self.config.model,
            "embedding_provider": self.config.provider
        }

        # Add any additional metadata
        payload.update(metadata)

        return payload

    def _get_current_timestamp(self) -> str:
        """
        Get current timestamp in ISO format.

        Returns:
            Current timestamp as ISO string
        """
        from datetime import datetime
        return datetime.utcnow().isoformat()

    def store_embeddings(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        pipeline_ids: List[str],
        contents: List[str],
        metadata_list: List[Dict[str, Any]]
    ) -> bool:
        """
        Store embeddings to Qdrant collection.

        Args:
            chunk_ids: List of chunk IDs
            embeddings: List of embedding vectors
            pipeline_ids: List of pipeline IDs
            contents: List of content strings
            metadata_list: List of metadata dictionaries

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            raise RuntimeError("Qdrant client not connected. Call connect() first.")

        if not (len(chunk_ids) == len(embeddings) == len(pipeline_ids) == len(contents) == len(metadata_list)):
            raise ValueError("All input lists must have the same length")

        # Prepare points for insertion
        points = []
        for i in range(len(chunk_ids)):
            point_id = self._generate_point_id(chunk_ids[i])
            payload = self._prepare_payload(
                chunk_ids[i],
                pipeline_ids[i],
                contents[i],
                metadata_list[i]
            )

            # Ensure embedding is a list of floats
            embedding_vector = [float(x) for x in embeddings[i]]

            point = PointStruct(
                id=point_id,
                vector=embedding_vector,
                payload=payload
            )
            points.append(point)

        try:
            # Upsert the points to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            self.logger.info(f"Successfully stored {len(points)} embeddings to Qdrant")
            return True
        except Exception as e:
            self.logger.error(f"Error storing embeddings to Qdrant: {str(e)}")
            return False

    def retrieve_embedding(self, point_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single embedding by its point ID.

        Args:
            point_id: ID of the point to retrieve

        Returns:
            Dictionary containing embedding and metadata, or None if not found
        """
        if not self.client:
            raise RuntimeError("Qdrant client not connected. Call connect() first.")

        try:
            records = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[point_id]
            )

            if records:
                record = records[0]
                return {
                    'id': record.id,
                    'vector': record.vector,
                    'payload': record.payload
                }
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving embedding from Qdrant: {str(e)}")
            return None

    def retrieve_embeddings_by_chunk_id(self, chunk_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve embeddings by chunk ID (using payload filtering).

        Args:
            chunk_id: The chunk ID to search for

        Returns:
            List of matching embedding records
        """
        if not self.client:
            raise RuntimeError("Qdrant client not connected. Call connect() first.")

        try:
            # Search by payload filter
            response = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="chunk_id",
                            match=models.MatchValue(value=chunk_id)
                        )
                    ]
                ),
                limit=100  # Limit to prevent excessive results
            )

            # The scroll method returns a tuple (records, next_page_offset) in newer versions
            # Handle both possible return formats
            if isinstance(response, tuple):
                records, _ = response
            else:
                records = response

            results = []
            for record in records:
                results.append({
                    'id': record.id,
                    'vector': record.vector,
                    'payload': record.payload
                })

            return results
        except Exception as e:
            self.logger.error(f"Error retrieving embeddings by chunk ID from Qdrant: {str(e)}")
            return []

    def search_similar(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings.

        Args:
            query_embedding: The embedding vector to search for similarity
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold

        Returns:
            List of similar embedding records with similarity scores
        """
        if not self.client:
            raise RuntimeError("Qdrant client not connected. Call connect() first.")

        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=threshold
            )

            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': result.id,
                    'vector': result.vector,
                    'payload': result.payload,
                    'score': result.score
                })

            return formatted_results
        except Exception as e:
            self.logger.error(f"Error searching for similar embeddings in Qdrant: {str(e)}")
            return []

    def delete_embedding(self, point_id: str) -> bool:
        """
        Delete an embedding by its point ID.

        Args:
            point_id: ID of the point to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            raise RuntimeError("Qdrant client not connected. Call connect() first.")

        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[point_id]
            )
            self.logger.info(f"Successfully deleted embedding with ID: {point_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting embedding from Qdrant: {str(e)}")
            return False

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.

        Returns:
            Dictionary with collection statistics
        """
        if not self.client:
            raise RuntimeError("Qdrant client not connected. Call connect() first.")

        try:
            collection_info = self.client.get_collection(self.collection_name)
            return {
                "collection_name": self.collection_name,
                "vector_count": collection_info.points_count,
                "config": collection_info.config.dict() if hasattr(collection_info.config, 'dict') else str(collection_info.config)
            }
        except Exception as e:
            self.logger.error(f"Error getting collection stats: {str(e)}")
            return {}

    async def verify_embeddings_exist(self, chunk_ids: List[str]) -> Dict[str, bool]:
        """
        Verify that embeddings exist in Qdrant for the given chunk IDs.

        Args:
            chunk_ids: List of chunk IDs to verify

        Returns:
            Dictionary mapping chunk IDs to boolean indicating existence
        """
        if not self.client:
            raise RuntimeError("Qdrant client not connected. Call connect() first.")

        verification_results = {}

        for chunk_id in chunk_ids:
            try:
                # Search for embeddings with this chunk ID in the payload
                response = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="chunk_id",
                                match=models.MatchValue(value=chunk_id)
                            )
                        ]
                    ),
                    limit=100  # Limit to prevent excessive results
                )

                # The scroll method returns a tuple (records, next_page_offset) in newer versions
                # Handle both possible return formats
                if isinstance(response, tuple):
                    records_list, _ = response
                else:
                    records_list = response

                exists = len(records_list) > 0
                verification_results[chunk_id] = exists

                if exists:
                    self.logger.info(f"Verified embedding exists for chunk ID: {chunk_id}")
                else:
                    self.logger.warning(f"Embedding NOT found for chunk ID: {chunk_id}")

            except Exception as e:
                self.logger.error(f"Error verifying embedding for chunk ID {chunk_id}: {str(e)}")
                verification_results[chunk_id] = False

        return verification_results

    def retrieve_embedding_by_chunk_id(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an embedding by its chunk ID.

        Args:
            chunk_id: The chunk ID to search for

        Returns:
            Dictionary containing embedding data if found, None otherwise
        """
        if not self.client:
            raise RuntimeError("Qdrant client not connected. Call connect() first.")

        try:
            # Search by payload filter
            response = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="chunk_id",
                            match=models.MatchValue(value=chunk_id)
                        )
                    ]
                ),
                limit=1  # We only need the first match
            )

            # The scroll method returns a tuple (records, next_page_offset) in newer versions
            # Handle both possible return formats
            if isinstance(response, tuple):
                records, _ = response
            else:
                records = response

            if records:
                record = records[0]
                return {
                    'id': record.id,
                    'vector': record.vector,
                    'payload': record.payload
                }
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving embedding by chunk ID from Qdrant: {str(e)}")
            return None

    def confirm_vector_validity(self, chunk_id: str) -> bool:
        """
        Confirm that the vector exists and is valid for the given chunk ID.

        Args:
            chunk_id: The chunk ID to verify

        Returns:
            True if vector exists and is valid, False otherwise
        """
        try:
            embedding_data = self.retrieve_embedding_by_chunk_id(chunk_id)

            if embedding_data is None:
                self.logger.warning(f"No embedding found for chunk ID: {chunk_id}")
                return False

            # Check that the vector exists and has valid values
            vector = embedding_data.get('vector')
            if vector is None:
                self.logger.warning(f"Vector is None for chunk ID: {chunk_id}")
                return False

            # Check that vector is a list/array with numeric values
            if not isinstance(vector, (list, tuple)) or len(vector) == 0:
                self.logger.warning(f"Vector is invalid format for chunk ID: {chunk_id}")
                return False

            # Check that all values in the vector are numeric
            if not all(isinstance(val, (int, float)) for val in vector):
                self.logger.warning(f"Vector contains non-numeric values for chunk ID: {chunk_id}")
                return False

            self.logger.info(f"Confirmed valid vector for chunk ID: {chunk_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error confirming vector validity for chunk ID {chunk_id}: {str(e)}")
            return False