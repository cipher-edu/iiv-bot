from typing import Optional, Sequence
from datetime import date, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.gamification import (
    Badge,
    UserBadge,
    UserStreak,
    UserLevel,
    Challenge,
    ChallengeParticipation,
)
from bot.repositories.base import BaseRepository
from bot.core.enums import BadgeType


class BadgeRepository(BaseRepository[Badge]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Badge)

    async def get_by_type(self, badge_type: BadgeType) -> Optional[Badge]:
        stmt = select(Badge).where(Badge.badge_type == badge_type)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_badges(self, user_id: int) -> Sequence[UserBadge]:
        stmt = (
            select(UserBadge)
            .where(UserBadge.user_id == user_id)
            .order_by(UserBadge.earned_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def has_badge(self, user_id: int, badge_type: BadgeType) -> bool:
        badge = await self.get_by_type(badge_type)
        if not badge:
            return False
        stmt = select(UserBadge).where(
            UserBadge.user_id == user_id,
            UserBadge.badge_id == badge.id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def award_badge(self, user_id: int, badge_type: BadgeType) -> Optional[UserBadge]:
        if await self.has_badge(user_id, badge_type):
            return None
        badge = await self.get_by_type(badge_type)
        if not badge:
            return None
        user_badge = UserBadge(
            user_id=user_id, badge_id=badge.id, earned_at=datetime.utcnow()
        )
        self.session.add(user_badge)
        await self.session.flush()
        await self.session.refresh(user_badge)
        return user_badge


class StreakRepository(BaseRepository[UserStreak]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserStreak)

    async def get_user_streak(self, user_id: int) -> Optional[UserStreak]:
        stmt = select(UserStreak).where(UserStreak.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_streak(self, user_id: int) -> UserStreak:
        streak = await self.get_user_streak(user_id)
        today = date.today()

        if not streak:
            streak = UserStreak(
                user_id=user_id,
                current_streak=1,
                longest_streak=1,
                last_activity_date=today,
                streak_start_date=today,
            )
            self.session.add(streak)
            await self.session.flush()
            await self.session.refresh(streak)
            return streak

        if streak.last_activity_date == today:
            return streak

        if streak.last_activity_date and (today - streak.last_activity_date).days == 1:
            new_streak = streak.current_streak + 1
            longest = max(streak.longest_streak, new_streak)
            stmt = (
                update(UserStreak)
                .where(UserStreak.id == streak.id)
                .values(
                    current_streak=new_streak,
                    longest_streak=longest,
                    last_activity_date=today,
                )
            )
        else:
            stmt = (
                update(UserStreak)
                .where(UserStreak.id == streak.id)
                .values(
                    current_streak=1,
                    last_activity_date=today,
                    streak_start_date=today,
                )
            )

        await self.session.execute(stmt)
        await self.session.refresh(streak)
        return streak


class LevelRepository(BaseRepository[UserLevel]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserLevel)

    async def get_user_level(self, user_id: int) -> Optional[UserLevel]:
        stmt = select(UserLevel).where(UserLevel.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: int) -> UserLevel:
        level = await self.get_user_level(user_id)
        if not level:
            level = UserLevel(user_id=user_id)
            self.session.add(level)
            await self.session.flush()
            await self.session.refresh(level)
        return level

    async def add_experience(self, user_id: int, xp: int) -> UserLevel:
        level = await self.get_or_create(user_id)
        stmt = (
            update(UserLevel)
            .where(UserLevel.id == level.id)
            .values(experience=UserLevel.experience + xp)
        )
        await self.session.execute(stmt)
        await self.session.refresh(level)
        return level


class ChallengeRepository(BaseRepository[Challenge]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Challenge)

    async def get_active_challenges(self) -> Sequence[Challenge]:
        today = date.today()
        stmt = (
            select(Challenge)
            .where(
                Challenge.is_active == True,
                Challenge.start_date <= today,
                Challenge.end_date >= today,
                Challenge.is_deleted == False,
            )
            .order_by(Challenge.end_date)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_participation(
        self, user_id: int, challenge_id: int
    ) -> Optional[ChallengeParticipation]:
        stmt = select(ChallengeParticipation).where(
            ChallengeParticipation.user_id == user_id,
            ChallengeParticipation.challenge_id == challenge_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def join_challenge(
        self, user_id: int, challenge_id: int
    ) -> ChallengeParticipation:
        participation = ChallengeParticipation(
            user_id=user_id, challenge_id=challenge_id
        )
        self.session.add(participation)
        await self.session.flush()
        return participation

    async def update_progress(
        self, user_id: int, challenge_id: int, increment: int = 1
    ) -> Optional[ChallengeParticipation]:
        participation = await self.get_participation(user_id, challenge_id)
        if not participation:
            return None
        stmt = (
            update(ChallengeParticipation)
            .where(ChallengeParticipation.id == participation.id)
            .values(
                current_value=ChallengeParticipation.current_value + increment
            )
        )
        await self.session.execute(stmt)
        await self.session.refresh(participation)
        return participation


GamificationRepository = BadgeRepository
