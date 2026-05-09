from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.models.learning_path import LearningPath, PathCourse, UserPathEnrollment
from bot.models.course import Course
from bot.repositories.base import BaseRepository


class LearningPathRepository(BaseRepository[LearningPath]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, LearningPath)

    async def get_active(self, limit: int = 50) -> Sequence[LearningPath]:
        stmt = (
            select(LearningPath)
            .where(
                LearningPath.is_active == True,
                LearningPath.is_deleted == False,
            )
            .options(selectinload(LearningPath.courses))
            .order_by(LearningPath.id.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_with_courses(self, path_id: int) -> Optional[LearningPath]:
        stmt = (
            select(LearningPath)
            .where(LearningPath.id == path_id, LearningPath.is_deleted == False)
            .options(selectinload(LearningPath.courses))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_course(
        self, path_id: int, course_id: int, order: int = 0, required: bool = True
    ) -> PathCourse:
        pc = PathCourse(
            path_id=path_id,
            course_id=course_id,
            order=order,
            is_required=required,
        )
        self.session.add(pc)
        await self.session.flush()
        return pc

    async def get_user_enrollment(
        self, user_id: int, path_id: int
    ) -> Optional[UserPathEnrollment]:
        stmt = select(UserPathEnrollment).where(
            UserPathEnrollment.user_id == user_id,
            UserPathEnrollment.path_id == path_id,
            UserPathEnrollment.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def enroll_user(
        self, user_id: int, path_id: int
    ) -> UserPathEnrollment:
        existing = await self.get_user_enrollment(user_id, path_id)
        if existing:
            return existing
        ue = UserPathEnrollment(user_id=user_id, path_id=path_id)
        self.session.add(ue)
        await self.session.flush()
        return ue

    async def get_courses_titles(self, path_id: int) -> Sequence[Course]:
        stmt = (
            select(Course)
            .join(PathCourse, PathCourse.course_id == Course.id)
            .where(PathCourse.path_id == path_id)
            .order_by(PathCourse.order)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
