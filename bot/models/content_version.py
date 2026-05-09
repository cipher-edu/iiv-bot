from typing import Optional

from sqlalchemy import String, Text, Integer, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base


class LessonHistory(Base):
    """Snapshot of a lesson taken whenever it is updated."""

    __tablename__ = "lesson_history"
    __table_args__ = (
        Index("ix_lesson_history_lesson", "lesson_id"),
        Index("ix_lesson_history_version", "lesson_id", "version"),
    )

    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    changed_by_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    change_note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
