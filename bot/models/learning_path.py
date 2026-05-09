from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    Text,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.models.base import Base


class LearningPath(Base):
    __tablename__ = "learning_paths"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[str] = mapped_column(String(10), default="🎯")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    courses: Mapped[list["PathCourse"]] = relationship(
        back_populates="path",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="PathCourse.order",
    )


class PathCourse(Base):
    __tablename__ = "path_courses"
    __table_args__ = (
        UniqueConstraint("path_id", "course_id", name="uq_path_course"),
        Index("ix_path_course_path", "path_id"),
    )

    path_id: Mapped[int] = mapped_column(
        ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    order: Mapped[int] = mapped_column(Integer, default=0)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)

    path: Mapped[LearningPath] = relationship(back_populates="courses")


class UserPathEnrollment(Base):
    __tablename__ = "user_path_enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "path_id", name="uq_user_path"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    path_id: Mapped[int] = mapped_column(
        ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False
    )
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
