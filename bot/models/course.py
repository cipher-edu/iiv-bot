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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.models.base import Base


class Course(Base):
    __tablename__ = "courses"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    min_points: Mapped[int] = mapped_column(Integer, default=50)
    order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    difficulty: Mapped[str] = mapped_column(String(20), default="beginner")
    estimated_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    modules: Mapped[list["CourseModule"]] = relationship(
        back_populates="course",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="CourseModule.order",
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(
        back_populates="course", lazy="noload"
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

    module: Mapped[CourseModule] = relationship(back_populates="lessons")


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
