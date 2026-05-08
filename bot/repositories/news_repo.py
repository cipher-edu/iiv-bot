from typing import Optional, Sequence
from datetime import datetime

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.news import News, BroadcastLog
from bot.repositories.base import BaseRepository


class NewsRepository(BaseRepository[News]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, News)

    async def get_active_news(
        self, offset: int = 0, limit: int = 10
    ) -> Sequence[News]:
        stmt = (
            select(News)
            .where(News.is_active == True, News.is_deleted == False)
            .order_by(News.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_unbroadcast(self) -> Sequence[News]:
        stmt = (
            select(News)
            .where(
                News.is_active == True,
                News.is_broadcast == False,
                News.is_deleted == False,
            )
            .order_by(News.created_at)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_broadcast(self, news_id: int) -> None:
        await self.update_by_id(
            news_id,
            is_broadcast=True,
            broadcast_at=datetime.utcnow(),
        )

    async def increment_views(self, news_id: int) -> None:
        stmt = (
            update(News)
            .where(News.id == news_id)
            .values(views_count=News.views_count + 1)
        )
        await self.session.execute(stmt)

    async def create_broadcast_log(
        self, news_id: int, telegram_id: int, is_delivered: bool, error: Optional[str] = None
    ) -> BroadcastLog:
        log = BroadcastLog(
            news_id=news_id,
            telegram_id=telegram_id,
            is_delivered=is_delivered,
            delivered_at=datetime.utcnow() if is_delivered else None,
            error=error,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_broadcast_stats(self, news_id: int) -> dict:
        delivered = await self.session.execute(
            select(func.count(BroadcastLog.id)).where(
                BroadcastLog.news_id == news_id,
                BroadcastLog.is_delivered == True,
            )
        )
        failed = await self.session.execute(
            select(func.count(BroadcastLog.id)).where(
                BroadcastLog.news_id == news_id,
                BroadcastLog.is_delivered == False,
            )
        )
        return {
            "delivered": delivered.scalar_one(),
            "failed": failed.scalar_one(),
        }
