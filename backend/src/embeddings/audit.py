"""
Audit logging for embedding operations.

This module implements audit logging for embedding operations
with hybrid approach (summary and detail records).
"""
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class EmbeddingOperationRecord:
    """
    Record of a single embedding operation for audit logging.
    """
    chunk_id: str
    pipeline_id: str
    success: bool
    model: str
    provider: str
    timestamp: datetime
    error: Optional[str] = None
    embedding_length: Optional[int] = None


class EmbeddingAuditLogger:
    """
    Logger for embedding operations with hybrid audit approach.

    Implements both summary and detail record logging as specified
    in the requirements.
    """

    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize the audit logger.

        Args:
            log_dir: Directory to store audit logs (defaults to ./logs/embedding-audit/)
        """
        self.log_dir = Path(log_dir or "./logs/embedding-audit/")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Set up detailed operation logger
        self.detail_logger = logging.getLogger("embedding.detail.audit")
        detail_handler = logging.FileHandler(self.log_dir / "detail-operations.log")
        detail_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        ))
        self.detail_logger.addHandler(detail_handler)
        self.detail_logger.setLevel(logging.INFO)

        # Set up summary logger
        self.summary_logger = logging.getLogger("embedding.summary.audit")
        summary_handler = logging.FileHandler(self.log_dir / "summary-operations.log")
        summary_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        ))
        self.summary_logger.addHandler(summary_handler)
        self.summary_logger.setLevel(logging.INFO)

    def log_operation(self, record: EmbeddingOperationRecord) -> None:
        """
        Log a single embedding operation with both detail and summary records.

        Args:
            record: The embedding operation record to log
        """
        # Log detailed record
        detail_msg = (
            f"Embedding operation - "
            f"chunk_id: {record.chunk_id}, "
            f"pipeline_id: {record.pipeline_id}, "
            f"model: {record.model}, "
            f"provider: {record.provider}, "
            f"success: {record.success}, "
            f"timestamp: {record.timestamp.isoformat()}"
        )

        if record.error:
            detail_msg += f", error: {record.error}"
        if record.embedding_length:
            detail_msg += f", embedding_length: {record.embedding_length}"

        if record.success:
            self.detail_logger.info(detail_msg)
        else:
            self.detail_logger.error(detail_msg)

        # Log summary record (aggregated information)
        summary_msg = (
            f"Embedding summary - "
            f"pipeline_id: {record.pipeline_id}, "
            f"operation: {'success' if record.success else 'failure'}, "
            f"chunk_id: {record.chunk_id}, "
            f"timestamp: {record.timestamp.isoformat()}"
        )

        if record.success:
            self.summary_logger.info(summary_msg)
        else:
            self.summary_logger.warning(summary_msg)

    def log_batch_summary(
        self,
        pipeline_id: str,
        total_operations: int,
        successful_operations: int,
        failed_operations: int,
        start_time: datetime,
        end_time: datetime
    ) -> None:
        """
        Log a summary of a batch of embedding operations.

        Args:
            pipeline_id: ID of the pipeline
            total_operations: Total number of operations in the batch
            successful_operations: Number of successful operations
            failed_operations: Number of failed operations
            start_time: When the batch started
            end_time: When the batch ended
        """
        duration = end_time - start_time
        success_rate = (successful_operations / total_operations * 100) if total_operations > 0 else 0

        summary_msg = (
            f"Batch embedding summary - "
            f"pipeline_id: {pipeline_id}, "
            f"total_operations: {total_operations}, "
            f"successful: {successful_operations}, "
            f"failed: {failed_operations}, "
            f"success_rate: {success_rate:.2f}%, "
            f"duration: {duration.total_seconds():.2f}s"
        )

        self.summary_logger.info(summary_msg)

    def get_audit_records(
        self,
        pipeline_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        success_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieve audit records based on filters.

        Args:
            pipeline_id: Filter by pipeline ID
            start_date: Filter by start date
            end_date: Filter by end date
            success_only: Only return successful operations

        Returns:
            List of audit records matching the criteria
        """
        # In a real implementation, this would query a database or parse log files
        # For now, we'll return an empty list as this would require log parsing
        return []

    def export_audit_data(self, output_path: str, format: str = "json") -> None:
        """
        Export audit data to a file.

        Args:
            output_path: Path to export the data
            format: Format to export in (json, csv)
        """
        # Implementation would depend on storage method
        pass