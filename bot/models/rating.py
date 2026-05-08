from datetime import date
from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    JSON,
    Boolean,
    Date,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.models.base import Base
from bot.core.enums import PointReason


class UserRating(Base):
    __tablename__ = "user_ratings"
    __table_args__ = (
        Index("ix_rating_total", "total_points"),
        Index("ix_rating_weekly", "weekly_points"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    weekly_points: Mapped[int] = mapped_column(Integer, default=0)
    monthly_points: Mapped[int] = mapped_column(Integer, default=0)
    tests_taken: Mapped[int] = mapped_column(Integer, default=0)
    tests_passed: Mapped[int] = mapped_column(Integer, default=0)
    courses_completed: Mapped[int] = mapped_column(Integer, default=0)
    current_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    transactions: Mapped[list["PointTransaction"]] = relationship(
        back_populates="rating", lazy="noload"
    )


class PointTransaction(Base):
    __tablename__ = "point_transactions"
    __table_args__ = (
        Index("ix_transaction_user", "user_id"),
        Index("ix_transaction_reason", "reason"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    rating_id: Mapped[int] = mapped_column(
        ForeignKey("user_ratings.id", ondelete="CASCADE"), nullable=False
    )
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[PointReason] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    rating: Mapped[UserRating] = relationship(back_populates="transactions")


class WeeklyLeaderboard(Base):
    __tablename__ = "weekly_leaderboards"
    __table_args__ = (
        UniqueConstraint("week_start", "week_end", name="uq_week_period"),
    )

    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    week_end: Mapped[date] = mapped_column(Date, nullable=False)
    rankings: Mapped[list] = mapped_column(JSON, default=list)
    is_announced: Mapped[bool] = mapped_column(Boolean, default=False)
    total_participants: Mapped[int] = mapped_column(Integer, default=0)
