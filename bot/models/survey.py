from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    ForeignKey,
    Text,
    JSON,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.models.base import Base


class Survey(Base):
    __tablename__ = "surveys"

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    starts_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    ends_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    target_organizations: Mapped[Optional[list]] = mapped_column(
        JSON, default=list
    )
    total_responses: Mapped[int] = mapped_column(Integer, default=0)

    questions: Mapped[list["SurveyQuestion"]] = relationship(
        back_populates="survey",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="SurveyQuestion.order",
    )


class SurveyQuestion(Base):
    __tablename__ = "survey_questions"

    survey_id: Mapped[int] = mapped_column(
        ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(String(20), nullable=False)
    options: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    order: Mapped[int] = mapped_column(Integer, default=0)

    survey: Mapped[Survey] = relationship(back_populates="questions")


class SurveyResponse(Base):
    __tablename__ = "survey_responses"
    __table_args__ = (
        UniqueConstraint("survey_id", "user_id", name="uq_survey_response"),
        Index("ix_response_survey", "survey_id"),
    )

    survey_id: Mapped[int] = mapped_column(
        ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    answers: Mapped[dict] = mapped_column(JSON, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(nullable=False)
