"""
Embeddings module for the pipeline verification system.

This module implements embedding generation and persistence functionality
for approved content chunks, integrating with the existing pipeline architecture.
"""
from .config import EmbeddingConfig
from .provider import EmbeddingProvider, CohereEmbeddingProvider
from .batch_processor import EmbeddingTask, EmbeddingResult, EmbeddingQueue, BatchEmbeddingProcessor
from .security import APIKeyValidator, validate_and_secure_config
from .generator import EmbeddingGenerator
from .audit import EmbeddingAuditLogger, EmbeddingOperationRecord
from .qdrant_client import QdrantEmbeddingClient


__all__ = [
    'EmbeddingConfig',
    'EmbeddingProvider',
    'CohereEmbeddingProvider',
    'EmbeddingTask',
    'EmbeddingResult',
    'EmbeddingQueue',
    'BatchEmbeddingProcessor',
    'APIKeyValidator',
    'validate_and_secure_config',
    'EmbeddingGenerator',
    'EmbeddingAuditLogger',
    'EmbeddingOperationRecord',
    'QdrantEmbeddingClient'
]