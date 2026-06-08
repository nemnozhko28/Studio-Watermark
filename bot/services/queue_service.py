"""
Async task queue with a bounded worker pool.
Workers process video watermarking jobs sequentially per slot.
"""
import asyncio
import logging
import os
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Optional

from bot.config import config

logger = logging.getLogger(__name__)


@dataclass
class Task:
    task_id: str
    coro_factory: Callable[[], Coroutine]
    user_id: int
    job_id: int


class TaskQueue:
    def __init__(self, max_workers: int = 2):
        self._queue: asyncio.Queue[Task] = asyncio.Queue()
        self._max_workers = max_workers
        self._semaphore = asyncio.Semaphore(max_workers)
        self._workers: list[asyncio.Task] = []
        self._running = False

    def start(self) -> None:
        """Start the worker pool."""
        self._running = True
        for i in range(self._max_workers):
            worker = asyncio.create_task(self._worker(i), name=f"worker-{i}")
            self._workers.append(worker)
        logger.info(f"Task queue started with {self._max_workers} workers")

    async def stop(self) -> None:
        """Gracefully stop all workers."""
        self._running = False
        for _ in self._workers:
            await self._queue.put(None)  # type: ignore[arg-type] — sentinel
        await asyncio.gather(*self._workers, return_exceptions=True)
        logger.info("Task queue stopped")

    async def enqueue(self, coro_factory: Callable[[], Coroutine], user_id: int, job_id: int) -> str:
        """Add a task to the queue. Returns the task_id."""
        task_id = str(uuid.uuid4())[:8]
        task = Task(task_id=task_id, coro_factory=coro_factory, user_id=user_id, job_id=job_id)
        await self._queue.put(task)
        qsize = self._queue.qsize()
        logger.info(f"Enqueued task {task_id} for user {user_id}; queue size: {qsize}")
        return task_id

    async def _worker(self, worker_id: int) -> None:
        logger.debug(f"Worker {worker_id} started")
        while self._running:
            item = await self._queue.get()
            if item is None:  # Sentinel — shut down
                self._queue.task_done()
                break
            task: Task = item
            logger.info(f"Worker {worker_id} processing task {task.task_id} (job {task.job_id})")
            try:
                await task.coro_factory()
            except Exception as e:
                logger.error(
                    f"Worker {worker_id} task {task.task_id} failed: {e}",
                    exc_info=True,
                )
            finally:
                self._queue.task_done()
                logger.info(f"Worker {worker_id} finished task {task.task_id}")

    @property
    def pending_count(self) -> int:
        return self._queue.qsize()


# Global queue instance
task_queue = TaskQueue(max_workers=config.max_workers)
