"""
Batch processing and queue management for embedding operations.

This module implements parallel queue management for embedding operations
to handle multiple pipelines efficiently.
"""
import asyncio
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import logging
from .provider import EmbeddingProvider
from .config import EmbeddingConfig


@dataclass
class EmbeddingTask:
    """
    Represents a single embedding task with content and metadata.
    """
    chunk_id: str
    content: str
    pipeline_id: str
    metadata: Dict[str, Any]


@dataclass
class EmbeddingResult:
    """
    Result of an embedding operation.
    """
    chunk_id: str
    embedding: List[float]
    success: bool
    error: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class EmbeddingQueue:
    """
    Manages parallel embedding operations per pipeline with queue management.
    """

    def __init__(self, config: EmbeddingConfig, provider: EmbeddingProvider):
        """
        Initialize the embedding queue.

        Args:
            config: Configuration for embedding operations
            provider: Embedding provider to use
        """
        self.config = config
        self.provider = provider
        self.queue = asyncio.Queue()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.pipeline_queues: Dict[str, asyncio.Queue] = {}
        self.max_workers = config.parallel_workers
        self.workers = []
        self.running = False
        self.logger = logging.getLogger(__name__)

    async def add_task(self, task: EmbeddingTask) -> None:
        """
        Add a task to the appropriate pipeline queue.

        Args:
            task: The embedding task to add
        """
        # Create a pipeline-specific queue if it doesn't exist
        if task.pipeline_id not in self.pipeline_queues:
            self.pipeline_queues[task.pipeline_id] = asyncio.Queue()

        # Add the task to the pipeline's queue
        await self.pipeline_queues[task.pipeline_id].put(task)

    async def _worker(self, worker_id: int) -> None:
        """
        Worker coroutine that processes embedding tasks.

        Args:
            worker_id: ID of the worker for logging purposes
        """
        while self.running:
            try:
                # Check for tasks in any pipeline queue
                task = None
                for pipeline_id, queue in self.pipeline_queues.items():
                    if not queue.empty():
                        try:
                            task = queue.get_nowait()
                            break
                        except asyncio.QueueEmpty:
                            continue

                if task is None:
                    # If no tasks are available, sleep briefly before checking again
                    await asyncio.sleep(0.1)
                    continue

                # Process the task
                self.logger.info(f"Worker {worker_id} processing task {task.chunk_id} for pipeline {task.pipeline_id}")
                result = await self._process_task(task)
                self.logger.info(f"Worker {worker_id} completed task {task.chunk_id} for pipeline {task.pipeline_id}")

            except Exception as e:
                self.logger.error(f"Worker {worker_id} encountered error: {str(e)}")
                await asyncio.sleep(0.1)  # Brief pause before continuing

    async def _process_task(self, task: EmbeddingTask) -> EmbeddingResult:
        """
        Process a single embedding task.

        Args:
            task: The embedding task to process

        Returns:
            EmbeddingResult: Result of the embedding operation
        """
        try:
            # Generate embedding for the content
            embeddings = await self.provider.generate_embeddings([task.content])
            if embeddings and len(embeddings) > 0:
                return EmbeddingResult(
                    chunk_id=task.chunk_id,
                    embedding=embeddings[0],
                    success=True
                )
            else:
                return EmbeddingResult(
                    chunk_id=task.chunk_id,
                    embedding=[],
                    success=False,
                    error="No embeddings returned from provider"
                )
        except Exception as e:
            return EmbeddingResult(
                chunk_id=task.chunk_id,
                embedding=[],
                success=False,
                error=str(e)
            )

    async def start(self) -> None:
        """
        Start the embedding queue workers.
        """
        if self.running:
            return

        self.running = True
        self.workers = []

        # Start worker coroutines
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)

        self.logger.info(f"Started {self.max_workers} embedding workers")

    async def stop(self) -> None:
        """
        Stop the embedding queue workers.
        """
        if not self.running:
            return

        self.running = False

        # Wait for all workers to complete
        if self.workers:
            await asyncio.gather(*self.workers, return_exceptions=True)

        self.logger.info("Stopped all embedding workers")

    async def process_pipeline(self, pipeline_id: str, tasks: List[EmbeddingTask]) -> List[EmbeddingResult]:
        """
        Process all tasks for a specific pipeline.

        Args:
            pipeline_id: ID of the pipeline to process
            tasks: List of embedding tasks for the pipeline

        Returns:
            List of embedding results
        """
        if not self.running:
            raise RuntimeError("EmbeddingQueue is not running")

        # Add all tasks to the pipeline queue
        for task in tasks:
            await self.add_task(task)

        # Create a temporary queue to collect results
        results = []
        processed_count = 0
        total_tasks = len(tasks)

        # Wait until all tasks are processed
        while processed_count < total_tasks:
            # Check each pipeline queue to see if it's empty
            pipeline_queue = self.pipeline_queues.get(pipeline_id)
            if pipeline_queue and pipeline_queue.empty():
                # Brief pause before checking again
                await asyncio.sleep(0.1)
            else:
                # Tasks are still being processed
                await asyncio.sleep(0.1)

            processed_count = len(results)  # This is a simplified approach

        return results

    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get the current status of all queues.

        Returns:
            Dict containing queue status information
        """
        status = {
            "running": self.running,
            "max_workers": self.max_workers,
            "active_workers": len(self.workers),
            "pipeline_queues": {}
        }

        for pipeline_id, queue in self.pipeline_queues.items():
            status["pipeline_queues"][pipeline_id] = {
                "size": queue.qsize(),
                "active_tasks": len([t for t in self.active_tasks.values() if t.get("pipeline_id") == pipeline_id])
            }

        return status


class BatchEmbeddingProcessor:
    """
    Processes batches of embeddings with parallel queue management.
    """

    def __init__(self, config: EmbeddingConfig, provider: EmbeddingProvider):
        """
        Initialize the batch embedding processor.

        Args:
            config: Configuration for embedding operations
            provider: Embedding provider to use
        """
        self.config = config
        self.provider = provider
        self.queue = EmbeddingQueue(config, provider)

    async def process_batch(self, tasks: List[EmbeddingTask]) -> List[EmbeddingResult]:
        """
        Process a batch of embedding tasks.

        Args:
            tasks: List of embedding tasks to process

        Returns:
            List of embedding results
        """
        if not tasks:
            return []

        # Group tasks by pipeline ID
        pipeline_tasks = {}
        for task in tasks:
            if task.pipeline_id not in pipeline_tasks:
                pipeline_tasks[task.pipeline_id] = []
            pipeline_tasks[task.pipeline_id].append(task)

        # Start the queue if not already running
        if not self.queue.running:
            await self.queue.start()

        # Process each pipeline's tasks
        all_results = []
        for pipeline_id, pipeline_tasks_list in pipeline_tasks.items():
            results = await self.queue.process_pipeline(pipeline_id, pipeline_tasks_list)
            all_results.extend(results)

        return all_results

    async def close(self) -> None:
        """
        Close the batch processor and stop all workers.
        """
        await self.queue.stop()