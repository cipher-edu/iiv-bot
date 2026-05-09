from typing import Optional, Sequence
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.models.course import (
    Course,
    CourseModule,
    Lesson,
    Enrollment,
    LessonProgress,
    LessonAttachment,
    LessonRating,
    CoursePrerequisite,
)
from bot.repositories.base import BaseRepository
from bot.core.enums import AttachmentType, AttachmentStorage, CourseStatus


class CourseRepository(BaseRepository[Course]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Course)

    async def get_active_courses(
        self,
        offset: int = 0,
        limit: int = 10,
        status: Optional[CourseStatus] = CourseStatus.PUBLISHED,
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
        if status is not None:
            stmt = stmt.where(Course.status == status)
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def get_with_modules(self, course_id: int) -> Optional[Course]:
        stmt = (
            select(Course)
            .where(Course.id == course_id, Course.is_deleted == False)
            .options(
                selectinload(Course.modules)
                .selectinload(CourseModule.lessons)
                .selectinload(Lesson.attachments)
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
        require_rating: bool = True,
    ) -> Lesson:
        lesson = Lesson(
            module_id=module_id,
            title=title,
            content=content,
            order=order,
            video_url=video_url,
            image_url=image_url,
            require_rating=require_rating,
        )
        self.session.add(lesson)
        await self.session.flush()
        await self.session.refresh(lesson)
        return lesson

    async def update_lesson(
        self,
        lesson_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        changed_by_user_id: Optional[int] = None,
        change_note: Optional[str] = None,
    ) -> Optional[Lesson]:
        """Update lesson and snapshot the previous version into LessonHistory."""
        from bot.models.content_version import LessonHistory

        lesson = await self.get_lesson(lesson_id)
        if not lesson:
            return None

        count_stmt = select(func.count(LessonHistory.id)).where(
            LessonHistory.lesson_id == lesson_id
        )
        version = (await self.session.execute(count_stmt)).scalar_one() + 1

        history = LessonHistory(
            lesson_id=lesson_id,
            version=version,
            title=lesson.title,
            content=lesson.content,
            changed_by_user_id=changed_by_user_id,
            change_note=change_note,
        )
        self.session.add(history)

        if title is not None:
            lesson.title = title
        if content is not None:
            lesson.content = content
        await self.session.flush()
        return lesson

    async def get_lesson_history(self, lesson_id: int):
        from bot.models.content_version import LessonHistory
        stmt = (
            select(LessonHistory)
            .where(LessonHistory.lesson_id == lesson_id)
            .order_by(LessonHistory.version.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_lesson(self, lesson_id: int) -> Optional[Lesson]:
        stmt = (
            select(Lesson)
            .where(Lesson.id == lesson_id, Lesson.is_deleted == False)
            .options(selectinload(Lesson.attachments))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_attachment(
        self,
        lesson_id: int,
        file_type: AttachmentType,
        storage: AttachmentStorage,
        title: Optional[str] = None,
        file_id: Optional[str] = None,
        url: Optional[str] = None,
        minio_key: Optional[str] = None,
        mime_type: Optional[str] = None,
        size_bytes: Optional[int] = None,
    ) -> LessonAttachment:
        count_stmt = select(func.count(LessonAttachment.id)).where(
            LessonAttachment.lesson_id == lesson_id
        )
        order = (await self.session.execute(count_stmt)).scalar_one() or 0

        attachment = LessonAttachment(
            lesson_id=lesson_id,
            file_type=file_type,
            storage=storage,
            title=title,
            file_id=file_id,
            url=url,
            minio_key=minio_key,
            mime_type=mime_type,
            size_bytes=size_bytes,
            order=order,
        )
        self.session.add(attachment)
        await self.session.flush()
        await self.session.refresh(attachment)
        return attachment

    async def delete_attachment(self, attachment_id: int) -> bool:
        from sqlalchemy import delete
        stmt = delete(LessonAttachment).where(LessonAttachment.id == attachment_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def set_syllabus(
        self,
        course_id: int,
        title: str,
        file_type: AttachmentType,
        file_id: Optional[str] = None,
        url: Optional[str] = None,
    ) -> Optional[Course]:
        return await self.update_by_id(
            course_id,
            syllabus_title=title,
            syllabus_type=file_type,
            syllabus_file_id=file_id,
            syllabus_url=url,
        )

    async def set_status(
        self, course_id: int, status: CourseStatus
    ) -> Optional[Course]:
        return await self.update_by_id(course_id, status=status)

    async def add_prerequisite(
        self, course_id: int, required_course_id: int
    ) -> CoursePrerequisite:
        prereq = CoursePrerequisite(
            course_id=course_id, required_course_id=required_course_id
        )
        self.session.add(prereq)
        await self.session.flush()
        return prereq

    async def get_prerequisites(self, course_id: int) -> Sequence[CoursePrerequisite]:
        stmt = (
            select(CoursePrerequisite)
            .where(CoursePrerequisite.course_id == course_id)
            .options(selectinload(CoursePrerequisite.required_course))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


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


class LessonRatingRepository(BaseRepository[LessonRating]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, LessonRating)

    async def get_user_rating(
        self, lesson_id: int, user_id: int
    ) -> Optional[LessonRating]:
        stmt = select(LessonRating).where(
            LessonRating.lesson_id == lesson_id,
            LessonRating.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_rating(
        self,
        lesson_id: int,
        user_id: int,
        stars: int,
        comment: Optional[str] = None,
    ) -> LessonRating:
        existing = await self.get_user_rating(lesson_id, user_id)
        if existing:
            existing.stars = stars
            if comment is not None:
                existing.comment = comment
            await self.session.flush()
            return existing
        rating = LessonRating(
            lesson_id=lesson_id,
            user_id=user_id,
            stars=stars,
            comment=comment,
        )
        self.session.add(rating)
        await self.session.flush()
        return rating

    async def get_lesson_stats(self, lesson_id: int) -> tuple[float, int]:
        stmt = select(
            func.coalesce(func.avg(LessonRating.stars), 0.0),
            func.count(LessonRating.id),
        ).where(LessonRating.lesson_id == lesson_id)
        result = await self.session.execute(stmt)
        avg, count = result.one()
        return float(avg), int(count)
