import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)

logger = logging.getLogger(__name__)


@dataclass
class BroadcastJob:
    job_id: int
    chat_ids: list[int]
    text: Optional[str] = None
    photo_file_id: Optional[str] = None
    document_file_id: Optional[str] = None
    caption: Optional[str] = None
    sent: int = 0
    failed: int = 0
    blocked: int = 0
    finished: bool = False
    on_progress: Optional[callable] = None
    on_done: Optional[callable] = None
    extra: dict = field(default_factory=dict)


class BroadcastQueue:
    """Single async worker draining broadcast jobs.

    Heavy lifting (sending to thousands of users) runs here so handlers stay
    responsive. The Bot's outbound RetryRequestMiddleware enforces rate limits.
    """

    def __init__(self, bot: Bot):
        self.bot = bot
        self._queue: asyncio.Queue[BroadcastJob] = asyncio.Queue()
        self._worker: Optional[asyncio.Task] = None
        self._jobs: dict[int, BroadcastJob] = {}
        self._next_job_id = 1
        self._stopping = False

    def start(self) -> None:
        if self._worker is None or self._worker.done():
            self._stopping = False
            self._worker = asyncio.create_task(self._run(), name="broadcast-worker")
            logger.info("Broadcast worker ishga tushdi")

    async def stop(self) -> None:
        self._stopping = True
        if self._worker:
            await self._queue.put(None)  # type: ignore[arg-type]
            try:
                await asyncio.wait_for(self._worker, timeout=10)
            except asyncio.TimeoutError:
                self._worker.cancel()
            self._worker = None

    def submit(self, job: BroadcastJob) -> int:
        if job.job_id == 0:
            job.job_id = self._next_job_id
            self._next_job_id += 1
        self._jobs[job.job_id] = job
        self._queue.put_nowait(job)
        return job.job_id

    def get_job(self, job_id: int) -> Optional[BroadcastJob]:
        return self._jobs.get(job_id)

    async def _run(self) -> None:
        while not self._stopping:
            job = await self._queue.get()
            if job is None:
                break
            try:
                await self._process(job)
            except Exception:
                logger.exception("Broadcast job %s failed", job.job_id)
            finally:
                self._queue.task_done()

    async def _process(self, job: BroadcastJob) -> None:
        for idx, chat_id in enumerate(job.chat_ids, start=1):
            try:
                if job.photo_file_id:
                    await self.bot.send_photo(
                        chat_id, job.photo_file_id, caption=job.caption
                    )
                elif job.document_file_id:
                    await self.bot.send_document(
                        chat_id, job.document_file_id, caption=job.caption
                    )
                else:
                    await self.bot.send_message(chat_id, job.text or "")
                job.sent += 1
            except (TelegramForbiddenError, TelegramBadRequest):
                job.blocked += 1
            except TelegramRetryAfter:
                # the request middleware should already retry; keep counter for
                # visibility if it ever propagates
                job.failed += 1
            except Exception:
                job.failed += 1

            if job.on_progress and idx % 50 == 0:
                try:
                    await job.on_progress(job)
                except Exception:
                    pass

        job.finished = True
        if job.on_done:
            try:
                await job.on_done(job)
            except Exception:
                logger.exception("Broadcast on_done callback failed")


broadcast_queue: Optional[BroadcastQueue] = None


def get_broadcast_queue() -> BroadcastQueue:
    if broadcast_queue is None:
        raise RuntimeError("Broadcast queue is not initialized")
    return broadcast_queue


def init_broadcast_queue(bot: Bot) -> BroadcastQueue:
    global broadcast_queue
    broadcast_queue = BroadcastQueue(bot)
    broadcast_queue.start()
    return broadcast_queue
