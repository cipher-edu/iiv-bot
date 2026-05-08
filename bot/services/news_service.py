from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.news import News
from bot.repositories.news_repo import NewsRepository


class NewsService:
    def __init__(self, session: AsyncSession):
        self.repo = NewsRepository(session)

    async def get_latest_news(
        self, offset: int = 0, limit: int = 10
    ) -> Sequence[News]:
        return await self.repo.get_all(offset=offset, limit=limit)

    async def view_news(self, news_id: int) -> News | None:
        news = await self.repo.get_by_id(news_id)
        if news:
            await self.repo.increment_views(news_id)
        return news

    async def get_unbroadcast(self) -> Sequence[News]:
        return await self.repo.get_unbroadcast()

    async def mark_broadcast(self, news_id: int):
        await self.repo.mark_broadcast(news_id)
