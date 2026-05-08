from typing import Optional, Sequence
from datetime import datetime

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.notification import Notification, NotificationPreference
from bot.repositories.base import BaseRepository
from bot.core.enums import NotificationType


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Notification)

    async def get_user_notifications(
        self, user_id: int, unread_only: bool = False, offset: int = 0, limit: int = 10
    ) -> Sequence[Notification]:
        stmt = (
            select(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_deleted == False,
            )
        )
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)
        stmt = stmt.order_by(Notification.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_unread(self, user_id: int) -> int:
        stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read == False,
            Notification.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def mark_as_read(self, notification_id: int) -> None:
        await self.update_by_id(
            notification_id,
            is_read=True,
            read_at=datetime.utcnow(),
        )

    async def mark_all_read(self, user_id: int) -> None:
        stmt = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read == False,
            )
            .values(is_read=True, read_at=datetime.utcnow())
        )
        await self.session.execute(stmt)

    async def create_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        metadata: Optional[dict] = None,
    ) -> Notification:
        return await self.create(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            metadata=metadata,
        )

    async def get_pending_notifications(self, limit: int = 50) -> Sequence[Notification]:
        stmt = (
            select(Notification)
            .where(
                Notification.is_sent == False,
                Notification.is_deleted == False,
            )
            .order_by(Notification.created_at)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_sent(self, notification_id: int) -> None:
        await self.update_by_id(
            notification_id,
            is_sent=True,
            sent_at=datetime.utcnow(),
        )


class NotificationPreferenceRepository(BaseRepository[NotificationPreference]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, NotificationPreference)

    async def get_user_prefs(self, user_id: int) -> Optional[NotificationPreference]:
        stmt = select(NotificationPreference).where(
            NotificationPreference.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: int) -> NotificationPreference:
        prefs = await self.get_user_prefs(user_id)
        if not prefs:
            prefs = await self.create(user_id=user_id)
        return prefs
