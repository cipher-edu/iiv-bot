from datetime import date, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.gamification import UserStreak
from bot.repositories.rating_repo import RatingRepository
from bot.core.enums import PointReason
from bot.config import settings


class StreakService:
    """Tracks consecutive-day activity. A day counts if user did anything."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _get_or_create(self, user_id: int) -> UserStreak:
        stmt = select(UserStreak).where(UserStreak.user_id == user_id)
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing
        streak = UserStreak(
            user_id=user_id,
            current_streak=0,
            longest_streak=0,
        )
        self.session.add(streak)
        await self.session.flush()
        return streak

    async def get(self, user_id: int) -> UserStreak:
        return await self._get_or_create(user_id)

    async def record_activity(self, user_id: int) -> tuple[UserStreak, bool]:
        """Record today's activity. Returns (streak, increased_today).

        - If last_activity == today: nothing happens.
        - If last_activity == yesterday: streak += 1.
        - Otherwise: streak resets to 1.
        """
        today = date.today()
        streak = await self._get_or_create(user_id)

        if streak.last_activity_date == today:
            return streak, False

        if streak.last_activity_date == today - timedelta(days=1):
            streak.current_streak += 1
        else:
            streak.current_streak = 1
            streak.streak_start_date = today

        streak.last_activity_date = today
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak

        # Bonus every 7 days
        if streak.current_streak > 0 and streak.current_streak % 7 == 0:
            rating_repo = RatingRepository(self.session)
            await rating_repo.add_points(
                user_id,
                settings.score_streak_bonus,
                PointReason.STREAK_BONUS,
                description=f"{streak.current_streak} kunlik streak",
            )

        await self.session.flush()
        return streak, True
