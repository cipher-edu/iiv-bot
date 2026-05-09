from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, ForeignKey, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base


class SpacedRepetition(Base):
    """Tracks when a lesson should be reviewed again.

    Simple SM-2-lite: each successful review pushes next_review further out.
    """

    __tablename__ = "spaced_repetition"
    __table_args__ = (
        Index("ix_spaced_user", "user_id"),
        Index("ix_spaced_next", "next_review_at"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False
    )
    interval_days: Mapped[int] = mapped_column(Integer, default=7)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    next_review_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sent_reminder: Mapped[bool] = mapped_column(Boolean, default=False)
