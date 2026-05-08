from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    ForeignKey,
    Text,
    Date,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.models.base import Base
from bot.core.enums import BadgeType


class Badge(Base):
    __tablename__ = "badges"

    badge_type: Mapped[BadgeType] = mapped_column(
        String(50), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    icon: Mapped[str] = mapped_column(String(10), default="🏅")
    points_reward: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserBadge(Base):
    __tablename__ = "user_badges"
    __table_args__ = (
        UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    badge_id: Mapped[int] = mapped_column(
        ForeignKey("badges.id", ondelete="CASCADE"), nullable=False
    )
    earned_at: Mapped[datetime] = mapped_column(nullable=False)

    badge: Mapped[Badge] = relationship(lazy="selectin")


class UserStreak(Base):
    __tablename__ = "user_streaks"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_activity_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    streak_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


class UserLevel(Base):
    __tablename__ = "user_levels"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    level: Mapped[int] = mapped_column(Integer, default=1)
    level_name: Mapped[str] = mapped_column(String(100), default="Yangi xodim")
    experience: Mapped[int] = mapped_column(Integer, default=0)


class Challenge(Base):
    __tablename__ = "challenges"
    __table_args__ = (
        Index("ix_challenge_active", "is_active", "end_date"),
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    challenge_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_value: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_points: Mapped[int] = mapped_column(Integer, default=3)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    participations: Mapped[list["ChallengeParticipation"]] = relationship(
        back_populates="challenge", lazy="noload"
    )


class ChallengeParticipation(Base):
    __tablename__ = "challenge_participations"
    __table_args__ = (
        UniqueConstraint("user_id", "challenge_id", name="uq_challenge_user"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    challenge_id: Mapped[int] = mapped_column(
        ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False
    )
    current_value: Mapped[int] = mapped_column(Integer, default=0)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    challenge: Mapped[Challenge] = relationship(back_populates="participations")
