from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.models.test import TestResult, TestSession
from bot.models.course import Enrollment
from bot.models.news import News
from bot.models.rating import PointTransaction


class AnalyticsService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_dashboard_stats(self) -> dict:
        total_users = await self._count(TelegramUser)
        active_users = await self._count(
            TelegramUser, TelegramUser.status == "active"
        )
        total_tests_taken = await self._count(TestSession)
        total_enrollments = await self._count(Enrollment)

        new_today = await self._count(
            TelegramUser,
            TelegramUser.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0),
        )

        return {
            "total_users": total_users,
            "active_users": active_users,
            "new_today": new_today,
            "total_tests_taken": total_tests_taken,
            "total_enrollments": total_enrollments,
        }

    async def get_weekly_activity(self) -> dict:
        week_ago = datetime.utcnow() - timedelta(days=7)

        new_users = await self._count(
            TelegramUser, TelegramUser.created_at >= week_ago,
        )
        tests_taken = await self._count(
            TestSession, TestSession.created_at >= week_ago,
        )
        points_earned = await self._sum(
            PointTransaction.points, PointTransaction.created_at >= week_ago,
        )

        return {
            "new_users": new_users,
            "tests_taken": tests_taken,
            "points_earned": points_earned or 0,
        }

    async def _count(self, model, *filters):
        stmt = select(func.count(model.id))
        for f in filters:
            stmt = stmt.where(f)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def _sum(self, column, *filters):
        stmt = select(func.coalesce(func.sum(column), 0))
        for f in filters:
            stmt = stmt.where(f)
        result = await self.session.execute(stmt)
        return result.scalar_one()
