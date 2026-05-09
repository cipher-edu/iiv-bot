import asyncio
import logging
from typing import Any, Optional

from aiogram.client.session.middlewares.base import (
    BaseRequestMiddleware,
    NextRequestMiddlewareType,
)
from aiogram.exceptions import (
    TelegramRetryAfter,
    TelegramServerError,
    TelegramNetworkError,
)
from aiogram.methods import Response, TelegramMethod
from aiogram.methods.base import TelegramType
from aiogram import Bot

from bot.core.rate_limiter import telegram_rate_limiter

logger = logging.getLogger(__name__)


def _extract_chat_id(method: TelegramMethod[Any]) -> Optional[int]:
    chat_id = getattr(method, "chat_id", None)
    if chat_id is None:
        return None
    if isinstance(chat_id, int):
        return chat_id
    return None


class RetryRequestMiddleware(BaseRequestMiddleware):
    """Outgoing-request middleware that:
    - applies a global+per-chat token bucket (Telegram limits),
    - retries on TelegramRetryAfter (sleeps the requested duration),
    - retries with exponential backoff on transient network/server errors.
    """

    def __init__(
        self,
        max_retries: int = 5,
        backoff_initial: float = 1.0,
        backoff_max: float = 30.0,
    ):
        self.max_retries = max_retries
        self.backoff_initial = backoff_initial
        self.backoff_max = backoff_max

    async def __call__(
        self,
        make_request: NextRequestMiddlewareType[TelegramType],
        bot: Bot,
        method: TelegramMethod[TelegramType],
    ) -> Response[TelegramType]:
        chat_id = _extract_chat_id(method)
        attempt = 0

        while True:
            attempt += 1
            async with telegram_rate_limiter.slot(chat_id):
                try:
                    return await make_request(bot, method)
                except TelegramRetryAfter as e:
                    delay = float(e.retry_after) + 0.5
                    logger.warning(
                        "Telegram RetryAfter %.1fs (method=%s, attempt=%s)",
                        delay,
                        method.__class__.__name__,
                        attempt,
                    )
                    if attempt >= self.max_retries:
                        raise
                    await asyncio.sleep(delay)
                except (TelegramServerError, TelegramNetworkError) as e:
                    if attempt >= self.max_retries:
                        raise
                    delay = min(
                        self.backoff_max,
                        self.backoff_initial * (2 ** (attempt - 1)),
                    )
                    logger.warning(
                        "Telegram transient error (%s), retry in %.1fs (attempt=%s)",
                        e.__class__.__name__,
                        delay,
                        attempt,
                    )
                    await asyncio.sleep(delay)
