import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import TelegramObject, Message, CallbackQuery

from bot.core.exceptions import (
    BotException,
    AccessDeniedError,
    NotFoundError,
    RateLimitError,
    BlockedUserError,
    MaintenanceError,
)

logger = logging.getLogger(__name__)


_BENIGN_BAD_REQUEST_SUBSTRINGS = (
    "message is not modified",
    "message to edit not found",
    "message to delete not found",
    "message can't be edited",
    "query is too old",
    "query id is invalid",
    "response timeout expired",
)


def _is_benign_bad_request(exc: TelegramBadRequest) -> bool:
    msg = (exc.message or "").lower()
    return any(s in msg for s in _BENIGN_BAD_REQUEST_SUBSTRINGS)


class ErrorHandlerMiddleware(BaseMiddleware):
    ERROR_MESSAGES = {
        AccessDeniedError: "🚫 Sizda bu amalni bajarish uchun ruxsat yo'q.",
        NotFoundError: "❌ So'ralgan ma'lumot topilmadi.",
        RateLimitError: "⏳ Juda ko'p so'rov yubordingiz. Biroz kuting.",
        BlockedUserError: "🚫 Sizning hisobingiz bloklangan.",
        MaintenanceError: "🔧 Tizim texnik xizmat rejimida.",
    }

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except BotException as e:
            error_text = self.ERROR_MESSAGES.get(type(e), f"⚠️ Xato: {e}")
            await self._send_error(event, str(error_text))
        except TelegramBadRequest as e:
            if _is_benign_bad_request(e):
                if isinstance(event, CallbackQuery):
                    try:
                        await event.answer()
                    except Exception:
                        pass
                logger.debug("Benign Telegram BadRequest ignored: %s", e.message)
                return
            logger.exception("Telegram BadRequest in handler: %s", e)
            await self._send_error(event, "⚠️ Kutilmagan xato yuz berdi. Iltimos, keyinroq urinib ko'ring.")
        except Exception as e:
            logger.exception("Unhandled error in handler: %s", e)
            await self._send_error(event, "⚠️ Kutilmagan xato yuz berdi. Iltimos, keyinroq urinib ko'ring.")

    @staticmethod
    async def _send_error(event: TelegramObject, text: str):
        try:
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
        except Exception:
            pass
