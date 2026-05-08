from typing import Optional, Sequence
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.models.course import Course, CourseModule, Lesson, Enrollment, LessonProgress
from bot.repositories.base import BaseRepository


class CourseRepository(BaseRepository[Course]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Course)

    async def get_active_courses(
        self, offset: int = 0, limit: int = 10
    ) -> Sequence[Course]:
        stmt = (
            select(Course)
            .where(Course.is_active == True, Course.is_deleted == False)
            .options(
                selectinload(Course.modules).selectinload(CourseModule.lessons)
            )
            .order_by(Course.order)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def get_with_modules(self, course_id: int) -> Optional[Course]:
        stmt = (
            select(Course)
            .where(Course.id == course_id, Course.is_deleted == False)
            .options(
                selectinload(Course.modules).selectinload(CourseModule.lessons)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_module(
        self, course_id: int, title: str, order: int = 0
    ) -> CourseModule:
        module = CourseModule(course_id=course_id, title=title, order=order)
        self.session.add(module)
        await self.session.flush()
        await self.session.refresh(module)
        return module

    async def create_lesson(
        self,
        module_id: int,
        title: str,
        content: Optional[str] = None,
        order: int = 0,
        video_url: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> Lesson:
        lesson = Lesson(
            module_id=module_id,
            title=title,
            content=content,
            order=order,
            video_url=video_url,
            image_url=image_url,
        )
        self.session.add(lesson)
        await self.session.flush()
        await self.session.refresh(lesson)
        return lesson


class EnrollmentRepository(BaseRepository[Enrollment]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Enrollment)

    async def get_user_enrollment(
        self, user_id: int, course_id: int
    ) -> Optional[Enrollment]:
        stmt = (
            select(Enrollment)
            .where(
                Enrollment.user_id == user_id,
                Enrollment.course_id == course_id,
                Enrollment.is_deleted == False,
            )
            .options(
                selectinload(Enrollment.course)
                .selectinload(Course.modules)
                .selectinload(CourseModule.lessons),
                selectinload(Enrollment.progress),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_enrollments(
        self, user_id: int, offset: int = 0, limit: int = 10
    ) -> Sequence[Enrollment]:
        stmt = (
            select(Enrollment)
            .where(
                Enrollment.user_id == user_id,
                Enrollment.is_deleted == False,
            )
            .options(selectinload(Enrollment.course))
            .order_by(Enrollment.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def enroll_user(self, user_id: int, course_id: int) -> Enrollment:
        return await self.create(user_id=user_id, course_id=course_id)

    async def complete_lesson(
        self, enrollment_id: int, lesson_id: int
    ) -> LessonProgress:
        progress = LessonProgress(
            enrollment_id=enrollment_id, lesson_id=lesson_id
        )
        self.session.add(progress)
        await self.session.flush()
        return progress

    async def is_lesson_completed(
        self, enrollment_id: int, lesson_id: int
    ) -> bool:
        stmt = select(func.count(LessonProgress.id)).where(
            LessonProgress.enrollment_id == enrollment_id,
            LessonProgress.lesson_id == lesson_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    async def mark_completed(self, enrollment_id: int) -> Optional[Enrollment]:
        return await self.update_by_id(
            enrollment_id,
            is_completed=True,
            completed_at=datetime.utcnow(),
        )

    async def count_completed(self, user_id: int) -> int:
        stmt = select(func.count(Enrollment.id)).where(
            Enrollment.user_id == user_id,
            Enrollment.is_completed == True,
            Enrollment.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
