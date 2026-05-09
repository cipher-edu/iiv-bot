from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    Text,
    Integer,
    ForeignKey,
    Boolean,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.models.base import Base


class LessonQuestion(Base):
    __tablename__ = "lesson_questions"
    __table_args__ = (Index("ix_lq_lesson", "lesson_id"),)

    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    upvotes: Mapped[int] = mapped_column(Integer, default=0)

    answers: Mapped[list["LessonAnswer"]] = relationship(
        back_populates="question",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="LessonAnswer.created_at",
    )


class LessonAnswer(Base):
    __tablename__ = "lesson_answers"

    question_id: Mapped[int] = mapped_column(
        ForeignKey("lesson_questions.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)
    upvotes: Mapped[int] = mapped_column(Integer, default=0)

    question: Mapped[LessonQuestion] = relationship(back_populates="answers")


class QAUpvote(Base):
    __tablename__ = "qa_upvotes"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "entity_type", "entity_id", name="uq_qa_upvote"
        ),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
