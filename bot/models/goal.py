from datetime import date
from typing import Optional

from sqlalchemy import String, Integer, ForeignKey, Date, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base


class UserGoal(Base):
    __tablename__ = "user_goals"
    __table_args__ = (Index("ix_goal_user", "user_id"),)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    goal_type: Mapped[str] = mapped_column(String(30), nullable=False)
    target: Mapped[int] = mapped_column(Integer, nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    period: Mapped[str] = mapped_column(String(20), default="month")
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
