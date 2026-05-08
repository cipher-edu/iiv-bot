from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, ForeignKey, Integer, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base
from bot.core.enums import NotificationType


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notification_user_read", "user_id", "is_read"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[str] = mapped_column(String(2000), nullable=False)
    notification_type: Mapped[NotificationType] = mapped_column(
        String(20), default=NotificationType.INFO, nullable=False
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    action_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    news_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    test_reminders: Mapped[bool] = mapped_column(Boolean, default=True)
    course_reminders: Mapped[bool] = mapped_column(Boolean, default=True)
    rating_updates: Mapped[bool] = mapped_column(Boolean, default=True)
    achievement_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    quiet_start_hour: Mapped[int] = mapped_column(Integer, default=22)
    quiet_end_hour: Mapped[int] = mapped_column(Integer, default=7)
