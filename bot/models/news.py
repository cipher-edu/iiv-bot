from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, ForeignKey, Text, Integer, BigInteger, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.models.base import Base


class News(Base):
    __tablename__ = "news"
    __table_args__ = (
        Index("ix_news_active_created", "is_active", "created_at"),
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_broadcast: Mapped[bool] = mapped_column(Boolean, default=False)
    broadcast_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    author_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    target_organizations: Mapped[Optional[list]] = mapped_column(
        JSON, default=list, nullable=True
    )

    broadcast_logs: Mapped[list["BroadcastLog"]] = relationship(
        back_populates="news", lazy="noload", cascade="all, delete-orphan"
    )


class BroadcastLog(Base):
    __tablename__ = "broadcast_logs"
    __table_args__ = (
        Index("ix_broadcast_news", "news_id"),
    )

    news_id: Mapped[int] = mapped_column(
        ForeignKey("news.id", ondelete="CASCADE"), nullable=False
    )
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    error: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    news: Mapped[News] = relationship(back_populates="broadcast_logs")
