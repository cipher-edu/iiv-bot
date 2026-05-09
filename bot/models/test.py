from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    ForeignKey,
    Text,
    JSON,
    Index,
    UniqueConstraint,
    CheckConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.models.base import Base
from bot.core.enums import TestSessionStatus


class Test(Base):
    __tablename__ = "tests"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_per_question: Mapped[int] = mapped_column(
        Integer, default=30, nullable=False
    )
    passing_score: Mapped[int] = mapped_column(Integer, default=70, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    randomize_questions: Mapped[bool] = mapped_column(Boolean, default=True)
    randomize_options: Mapped[bool] = mapped_column(Boolean, default=True)
    max_attempts: Mapped[int] = mapped_column(Integer, default=0)
    show_correct_answers: Mapped[bool] = mapped_column(Boolean, default=False)
    target_organizations: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    questions: Mapped[list["Question"]] = relationship(
        back_populates="test", lazy="selectin", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["TestSession"]] = relationship(
        back_populates="test", lazy="noload"
    )

    __table_args__ = (
        CheckConstraint("time_per_question >= 5", name="ck_time_min"),
        CheckConstraint(
            "passing_score >= 0 AND passing_score <= 100", name="ck_score_range"
        ),
    )

    @property
    def question_count(self) -> int:
        return len(self.questions) if self.questions else 0


class Question(Base):
    __tablename__ = "questions"

    test_id: Mapped[int] = mapped_column(
        ForeignKey("tests.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    test: Mapped[Test] = relationship(back_populates="questions")
    options: Mapped[list["AnswerOption"]] = relationship(
        back_populates="question", lazy="selectin", cascade="all, delete-orphan"
    )

    @property
    def correct_option(self) -> Optional["AnswerOption"]:
        for opt in self.options:
            if opt.is_correct:
                return opt
        return None

    @property
    def has_correct_option(self) -> bool:
        return any(opt.is_correct for opt in self.options)


class AnswerOption(Base):
    __tablename__ = "answer_options"

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    order: Mapped[int] = mapped_column(Integer, default=0)

    question: Mapped[Question] = relationship(back_populates="options")


class TestSession(Base):
    __tablename__ = "test_sessions"
    __table_args__ = (
        Index(
            "uq_active_session",
            "user_id",
            "test_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
        Index("ix_session_user_status", "user_id", "status"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    test_id: Mapped[int] = mapped_column(
        ForeignKey("tests.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[TestSessionStatus] = mapped_column(
        String(20), default=TestSessionStatus.ACTIVE, nullable=False
    )
    current_question_index: Mapped[int] = mapped_column(Integer, default=0)
    question_order: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    message_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timeout_task_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    test: Mapped[Test] = relationship(back_populates="sessions", lazy="selectin")
    answers: Mapped[list["UserAnswer"]] = relationship(
        back_populates="session", lazy="selectin", cascade="all, delete-orphan"
    )
    result: Mapped[Optional["TestResult"]] = relationship(
        back_populates="session", lazy="selectin", uselist=False
    )


class UserAnswer(Base):
    __tablename__ = "user_answers"

    session_id: Mapped[int] = mapped_column(
        ForeignKey("test_sessions.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    selected_option_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("answer_options.id", ondelete="SET NULL"), nullable=True
    )
    is_timeout: Mapped[bool] = mapped_column(Boolean, default=False)
    answered_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    session: Mapped[TestSession] = relationship(back_populates="answers")
    question: Mapped[Question] = relationship(lazy="selectin")
    selected_option: Mapped[Optional[AnswerOption]] = relationship(lazy="selectin")

    @property
    def is_correct(self) -> bool:
        if self.is_timeout or not self.selected_option:
            return False
        return self.selected_option.is_correct


class TestResult(Base):
    __tablename__ = "test_results"
    __table_args__ = (
        Index("ix_result_user", "user_id"),
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey("test_sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    test_id: Mapped[int] = mapped_column(
        ForeignKey("tests.id", ondelete="CASCADE"), nullable=False
    )
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0)
    timeout_count: Mapped[int] = mapped_column(Integer, default=0)
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    score_percent: Mapped[int] = mapped_column(Integer, default=0)
    is_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    points_awarded: Mapped[int] = mapped_column(Integer, default=0)

    session: Mapped[TestSession] = relationship(back_populates="result")
