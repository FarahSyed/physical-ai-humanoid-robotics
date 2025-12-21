"""
Qdrant client module for handling vector database operations
"""
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import PointStruct, VectorParams
from src.utils.config_loader import config
from src.utils.logger import logger


class QdrantEmbeddingClient:
    """
    Client for interacting with Qdrant vector database to store and retrieve embeddings
    """

    def __init__(self):
        """
        Initialize the Qdrant client with configuration from environment variables
        """
        self.client = QdrantClient(
            url=config.qdrant_host,
            api_key=config.qdrant_api_key,
            # Set timeout and other parameters as needed
        )
        self.collection_name = config.qdrant_collection_name

    def create_collection_if_not_exists(
        self,
        vector_size: int = 1024,  # Default size for Cohere embeddings
        distance: str = "Cosine"
    ) -> bool:
        """
        Create the collection if it doesn't exist

        Args:
            vector_size: Size of the embedding vectors
            distance: Distance metric to use for similarity search

        Returns:
            True if collection was created or already exists
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_exists = any(col.name == self.collection_name for col in collections.collections)

            if not collection_exists:
                # Create collection with specified parameters
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=models.Distance[distance.upper()]
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Qdrant collection already exists: {self.collection_name}")

            return True
        except Exception as e:
            logger.error(f"Error creating Qdrant collection: {e}")
            return False

    def upsert_embeddings(
        self,
        embeddings: List[Dict[str, Any]],
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Upsert embeddings into the Qdrant collection

        Args:
            embeddings: List of embeddings with their metadata
                Each embedding should be a dict with:
                - 'id': unique identifier
                - 'vector': the embedding vector
                - 'payload': metadata dict with URL, title, etc.
            batch_size: Number of embeddings to process in each batch

        Returns:
            Dictionary with results of the upsert operation
        """
        try:
            points = []
            for embedding_data in embeddings:
                point = PointStruct(
                    id=embedding_data['id'],
                    vector=embedding_data['vector'],
                    payload=embedding_data.get('payload', {})
                )
                points.append(point)

            # Process in batches
            results = []
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                result = self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                results.append(result)

            logger.info(f"Upserted {len(points)} embeddings in {len(results)} batches")
            return {
                "status": "success",
                "upserted_count": len(points),
                "batch_count": len(results),
                "collection_name": self.collection_name
            }
        except Exception as e:
            logger.error(f"Error upserting embeddings: {e}")
            return {
                "status": "error",
                "error": str(e),
                "upserted_count": 0
            }

    def search_similar(
        self,
        query_vector: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings in the collection

        Args:
            query_vector: The query embedding vector
            top_k: Number of similar items to return
            filters: Optional filters to apply to the search

        Returns:
            List of similar items with their payload and similarity scores
        """
        try:
            # Convert filters to Qdrant's filter format if provided
            qdrant_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    conditions.append(models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value)
                    ))
                if conditions:
                    qdrant_filter = models.Filter(must=conditions)

            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=qdrant_filter
            )

            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                })

            logger.debug(f"Found {len(formatted_results)} similar items")
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching for similar embeddings: {e}")
            return []

    def delete_by_payload(
        self,
        payload_filter: Dict[str, Any]
    ) -> bool:
        """
        Delete embeddings from the collection based on payload filter

        Args:
            payload_filter: Dictionary with key-value pairs to match in payload

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Create Qdrant filter
            conditions = []
            for key, value in payload_filter.items():
                conditions.append(models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value)
                ))

            qdrant_filter = models.Filter(must=conditions)

            # Delete points matching the filter
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=qdrant_filter
            )

            logger.info(f"Deleted embeddings matching filter: {payload_filter}")
            return True
        except Exception as e:
            logger.error(f"Error deleting embeddings by payload: {e}")
            return False

    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the collection

        Returns:
            Dictionary with collection information
        """
        try:
            info = self.client.get_collection(collection_name=self.collection_name)
            return {
                "name": info.config.params.vectors.size,
                "vector_size": info.config.params.vectors.size,
                "distance": info.config.params.vectors.distance,
                "point_count": info.points_count,
                "config": info.config.dict()
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {"error": str(e)}

    def close(self):
        """
        Close the Qdrant client connection
        """
        try:
            if hasattr(self.client, '_client'):
                self.client.close()
        except Exception as e:
            logger.warning(f"Error closing Qdrant client: {e}")


# Global instance for easy access
qdrant_client = QdrantEmbeddingClient()