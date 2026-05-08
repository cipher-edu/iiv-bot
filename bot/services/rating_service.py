from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.rating_repo import RatingRepository, LeaderboardRepository
from bot.core.enums import PointReason


class RatingService:
    def __init__(self, session: AsyncSession):
        self.rating_repo = RatingRepository(session)
        self.leaderboard_repo = LeaderboardRepository(session)

    async def add_points(
        self, user_id: int, points: int, reason: PointReason, details: str = ""
    ):
        await self.rating_repo.add_points(user_id, points, reason.value, details)

    async def get_leaderboard(self, period: str = "total", limit: int = 10) -> Sequence:
        return await self.rating_repo.get_leaderboard(period=period, limit=limit)

    async def get_user_rank(self, user_id: int) -> dict:
        return await self.rating_repo.get_user_rank(user_id)

    async def reset_weekly(self):
        await self.rating_repo.reset_weekly()

    async def reset_monthly(self):
        await self.rating_repo.reset_monthly()
