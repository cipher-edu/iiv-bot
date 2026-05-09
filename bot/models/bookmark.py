from typing import Optional

from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base


class SavedItem(Base):
    """User-saved reference to any entity (lesson, course, news).

    Distinct from `Bookmark` (which is library-files only).
    """

    __tablename__ = "saved_items"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "entity_type", "entity_id", name="uq_saved_item"
        ),
        Index("ix_saved_user", "user_id"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    title_cache: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
