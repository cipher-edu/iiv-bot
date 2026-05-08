from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.gamification import Badge, UserBadge, UserStreak
from bot.repositories.gamification_repo import (
    BadgeRepository,
    StreakRepository,
    LevelRepository,
    ChallengeRepository,
)
from bot.core.enums import BadgeType


class GamificationService:
    def __init__(self, session: AsyncSession):
        self.badge_repo = BadgeRepository(session)
        self.streak_repo = StreakRepository(session)
        self.level_repo = LevelRepository(session)
        self.challenge_repo = ChallengeRepository(session)

    async def award_badge(
        self, user_id: int, badge_type: BadgeType,
    ) -> UserBadge | None:
        return await self.badge_repo.award_badge(user_id, badge_type)

    async def get_user_badges(self, user_id: int) -> Sequence[UserBadge]:
        from sqlalchemy import select
        from bot.models.gamification import UserBadge as UB
        stmt = select(UB).where(UB.user_id == user_id).order_by(UB.earned_at.desc())
        result = await self.badge_repo.session.execute(stmt)
        return result.scalars().all()

    async def update_streak(self, user_id: int) -> UserStreak:
        return await self.streak_repo.update_streak(user_id)

    async def get_streak(self, user_id: int) -> UserStreak | None:
        from sqlalchemy import select
        from bot.models.gamification import UserStreak as US
        stmt = select(US).where(US.user_id == user_id)
        result = await self.streak_repo.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_challenges(self) -> Sequence:
        return await self.challenge_repo.get_active_challenges()

    async def check_level_up(self, user_id: int, total_points: int) -> dict | None:
        return await self.level_repo.check_and_update(user_id, total_points)
