import io
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.user_repo import UserRepository
from bot.utils.csv_export import users_to_csv, test_results_to_csv, ratings_to_csv


class ExportService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def export_users_csv(self) -> io.BytesIO:
        repo = UserRepository(self.session)
        users = await repo.get_all(limit=10000)
        return users_to_csv(users)

    async def export_test_results_csv(self) -> io.BytesIO:
        from bot.repositories.test_repo import TestResultRepository
        repo = TestResultRepository(self.session)
        results = await repo.get_all(limit=10000)
        return test_results_to_csv(results)

    async def export_ratings_csv(self) -> io.BytesIO:
        from bot.repositories.rating_repo import RatingRepository
        repo = RatingRepository(self.session)
        from sqlalchemy import select
        from bot.models.rating import UserRating
        stmt = select(UserRating).limit(10000)
        result = await self.session.execute(stmt)
        ratings = result.scalars().all()
        return ratings_to_csv(ratings)
