import logging
from typing import Sequence

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.notification import Notification
from bot.repositories.notification_repo import NotificationRepository, NotificationPreferenceRepository
from bot.core.enums import NotificationType

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, session: AsyncSession, bot: Bot | None = None):
        self.repo = NotificationRepository(session)
        self.pref_repo = NotificationPreferenceRepository(session)
        self.bot = bot

    async def create_notification(
        self, user_id: int, title: str, message: str,
        notification_type: NotificationType = NotificationType.SYSTEM,
    ) -> Notification:
        return await self.repo.create(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type.value,
        )

    async def send_notification(
        self, user_id: int, telegram_id: int, title: str, message: str,
        notification_type: NotificationType = NotificationType.SYSTEM,
    ):
        notification = await self.create_notification(user_id, title, message, notification_type)

        if self.bot:
            try:
                text = f"🔔 <b>{title}</b>\n\n{message}"
                await self.bot.send_message(telegram_id, text)
            except Exception as e:
                logger.warning("Failed to send notification to %s: %s", telegram_id, e)

        return notification

    async def get_unread(self, user_id: int) -> Sequence[Notification]:
        return await self.repo.get_user_notifications(user_id, unread_only=True)

    async def get_unread_count(self, user_id: int) -> int:
        return await self.repo.count_unread(user_id)

    async def mark_all_read(self, user_id: int):
        await self.repo.mark_all_read(user_id)
