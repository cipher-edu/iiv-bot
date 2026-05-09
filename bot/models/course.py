from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    ForeignKey,
    Text,
    UniqueConstraint,
    Index,
    SmallInteger,
    Float,
    CheckConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.models.base import Base
from bot.core.enums import AttachmentType, AttachmentStorage, CourseStatus


class Course(Base):
    __tablename__ = "courses"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    min_points: Mapped[int] = mapped_column(Integer, default=50)
    order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[CourseStatus] = mapped_column(
        String(20), default=CourseStatus.PUBLISHED, nullable=False
    )
    difficulty: Mapped[str] = mapped_column(String(20), default="beginner")
    estimated_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    syllabus_file_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    syllabus_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    syllabus_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    syllabus_type: Mapped[Optional[AttachmentType]] = mapped_column(
        String(20), nullable=True
    )

    modules: Mapped[list["CourseModule"]] = relationship(
        back_populates="course",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="CourseModule.order",
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="course", lazy="noload"
    )
    prerequisites: Mapped[list["CoursePrerequisite"]] = relationship(
        foreign_keys="CoursePrerequisite.course_id",
        back_populates="course",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    @property
    def total_lessons(self) -> int:
        return sum(len(m.lessons) for m in self.modules)


class CourseModule(Base):
    __tablename__ = "course_modules"

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)

    course: Mapped[Course] = relationship(back_populates="modules")
    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="module",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="Lesson.order",
    )


class Lesson(Base):
    __tablename__ = "lessons"

    module_id: Mapped[int] = mapped_column(
        ForeignKey("course_modules.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    require_rating: Mapped[bool] = mapped_column(Boolean, default=True)

    module: Mapped[CourseModule] = relationship(back_populates="lessons")
    attachments: Mapped[list["LessonAttachment"]] = relationship(
        back_populates="lesson",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="LessonAttachment.order",
    )
    ratings: Mapped[list["LessonRating"]] = relationship(
        back_populates="lesson", lazy="noload", cascade="all, delete-orphan"
    )


class LessonAttachment(Base):
    __tablename__ = "lesson_attachments"
    __table_args__ = (Index("ix_attachment_lesson", "lesson_id"),)

    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_type: Mapped[AttachmentType] = mapped_column(String(20), nullable=False)
    storage: Mapped[AttachmentStorage] = mapped_column(String(20), nullable=False)
    file_id: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    minio_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)

    lesson: Mapped[Lesson] = relationship(back_populates="attachments")


class LessonRating(Base):
    __tablename__ = "lesson_ratings"
    __table_args__ = (
        UniqueConstraint("lesson_id", "user_id", name="uq_lesson_rating"),
        CheckConstraint("stars >= 1 AND stars <= 5", name="ck_lesson_rating_stars"),
        Index("ix_lesson_rating_lesson", "lesson_id"),
    )

    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    stars: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    lesson: Mapped[Lesson] = relationship(back_populates="ratings")


class CoursePrerequisite(Base):
    __tablename__ = "course_prerequisites"
    __table_args__ = (
        UniqueConstraint(
            "course_id", "required_course_id", name="uq_course_prereq"
        ),
    )

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    required_course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )

    course: Mapped[Course] = relationship(
        foreign_keys=[course_id], back_populates="prerequisites"
    )
    required_course: Mapped[Course] = relationship(foreign_keys=[required_course_id])


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_enrollment"),
        Index("ix_enrollment_user", "user_id"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    course: Mapped[Course] = relationship(back_populates="enrollments", lazy="selectin")
    progress: Mapped[list["LessonProgress"]] = relationship(
        back_populates="enrollment", lazy="selectin", cascade="all, delete-orphan"
    )

    def get_progress_percent(self) -> int:
        total = self.course.total_lessons
        if total == 0:
            return 0
        completed = len(self.progress)
        return int((completed / total) * 100)


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (
        UniqueConstraint(
            "enrollment_id", "lesson_id", name="uq_lesson_progress"
        ),
    )

    enrollment_id: Mapped[int] = mapped_column(
        ForeignKey("enrollments.id", ondelete="CASCADE"), nullable=False
    )
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )

    enrollment: Mapped[Enrollment] = relationship(back_populates="progress")
