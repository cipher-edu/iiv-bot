from typing import Optional, Sequence
from datetime import date

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.rating import UserRating, PointTransaction, WeeklyLeaderboard
from bot.repositories.base import BaseRepository
from bot.core.enums import PointReason


class RatingRepository(BaseRepository[UserRating]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserRating)

    async def get_by_user_id(self, user_id: int) -> Optional[UserRating]:
        stmt = select(UserRating).where(UserRating.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: int) -> UserRating:
        rating = await self.get_by_user_id(user_id)
        if not rating:
            rating = await self.create(user_id=user_id)
        return rating

    async def add_points(
        self,
        user_id: int,
        points: int,
        reason: PointReason,
        description: Optional[str] = None,
        reference_id: Optional[int] = None,
    ) -> PointTransaction:
        rating = await self.get_or_create(user_id)

        stmt = (
            update(UserRating)
            .where(UserRating.id == rating.id)
            .values(
                total_points=UserRating.total_points + points,
                weekly_points=UserRating.weekly_points + points,
                monthly_points=UserRating.monthly_points + points,
            )
        )
        await self.session.execute(stmt)

        transaction = PointTransaction(
            user_id=user_id,
            rating_id=rating.id,
            points=points,
            reason=reason,
            description=description,
            reference_id=reference_id,
        )
        self.session.add(transaction)
        await self.session.flush()
        return transaction

    async def get_leaderboard(
        self, offset: int = 0, limit: int = 10
    ) -> Sequence[UserRating]:
        stmt = (
            select(UserRating)
            .order_by(UserRating.total_points.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_weekly_leaderboard(
        self, offset: int = 0, limit: int = 10
    ) -> Sequence[UserRating]:
        stmt = (
            select(UserRating)
            .where(UserRating.weekly_points > 0)
            .order_by(UserRating.weekly_points.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def reset_weekly_points(self) -> None:
        stmt = update(UserRating).values(weekly_points=0)
        await self.session.execute(stmt)

    async def reset_monthly_points(self) -> None:
        stmt = update(UserRating).values(monthly_points=0)
        await self.session.execute(stmt)

    async def increment_tests(
        self, user_id: int, passed: bool = False
    ) -> None:
        rating = await self.get_or_create(user_id)
        values = {"tests_taken": UserRating.tests_taken + 1}
        if passed:
            values["tests_passed"] = UserRating.tests_passed + 1
        stmt = update(UserRating).where(UserRating.id == rating.id).values(**values)
        await self.session.execute(stmt)

    async def get_user_rank(self, user_id: int) -> Optional[int]:
        rating = await self.get_by_user_id(user_id)
        if not rating:
            return None
        stmt = select(func.count(UserRating.id)).where(
            UserRating.total_points > rating.total_points
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() + 1

    async def get_user_transactions(
        self, user_id: int, offset: int = 0, limit: int = 20
    ) -> Sequence[PointTransaction]:
        stmt = (
            select(PointTransaction)
            .where(PointTransaction.user_id == user_id)
            .order_by(PointTransaction.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class LeaderboardRepository(BaseRepository[WeeklyLeaderboard]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, WeeklyLeaderboard)

    async def save_weekly(
        self,
        week_start: date,
        week_end: date,
        rankings: list,
        total_participants: int,
    ) -> WeeklyLeaderboard:
        return await self.create(
            week_start=week_start,
            week_end=week_end,
            rankings=rankings,
            total_participants=total_participants,
        )

    async def get_latest(self) -> Optional[WeeklyLeaderboard]:
        stmt = (
            select(WeeklyLeaderboard)
            .order_by(WeeklyLeaderboard.week_end.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
