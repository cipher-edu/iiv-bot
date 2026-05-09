from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Integer, ForeignKey, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base


class Suggestion(Base):
    """Anonymous suggestion / complaint sent to super admin."""

    __tablename__ = "suggestions"
    __table_args__ = (
        Index("ix_suggestion_status", "status"),
        Index("ix_suggestion_created", "created_at"),
    )

    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="other")
    status: Mapped[str] = mapped_column(String(20), default="new")
    admin_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    responded_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    responded_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
