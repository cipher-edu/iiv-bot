from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.course import Course, Enrollment
from bot.repositories.course_repo import CourseRepository, EnrollmentRepository


class CourseService:
    def __init__(self, session: AsyncSession):
        self.course_repo = CourseRepository(session)
        self.enrollment_repo = EnrollmentRepository(session)

    async def get_available_courses(
        self, offset: int = 0, limit: int = 10
    ) -> Sequence[Course]:
        return await self.course_repo.get_all(
            offset=offset, limit=limit
        )

    async def enroll_user(self, user_id: int, course_id: int) -> Enrollment:
        return await self.enrollment_repo.enroll(user_id, course_id)

    async def complete_lesson(
        self, user_id: int, course_id: int, lesson_id: int
    ) -> dict:
        await self.enrollment_repo.complete_lesson(user_id, lesson_id)
        enrollment = await self.enrollment_repo.get_by_filters(
            user_id=user_id, course_id=course_id
        )

        if enrollment:
            e = enrollment[0] if isinstance(enrollment, (list, tuple)) else enrollment
            progress = e.get_progress_percent() if hasattr(e, "get_progress_percent") else 0
            return {"progress": progress, "completed": progress >= 100}

        return {"progress": 0, "completed": False}

    async def get_user_enrollments(
        self, user_id: int, limit: int = 20
    ) -> Sequence[Enrollment]:
        return await self.enrollment_repo.get_by_filters(user_id=user_id)
