from typing import Optional

from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    Text,
    Boolean,
    JSON,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.models.base import Base


class FileCategory(Base):
    __tablename__ = "file_categories"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    icon: Mapped[str] = mapped_column(String(10), default="📁")
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("file_categories.id"), nullable=True
    )
    order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    files: Mapped[list["FileItem"]] = relationship(
        back_populates="category", lazy="noload"
    )


class FileItem(Base):
    __tablename__ = "file_items"
    __table_args__ = (
        Index("ix_file_category", "category_id"),
        Index("ix_file_type", "file_type"),
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("file_categories.id", ondelete="SET NULL"), nullable=True
    )
    uploaded_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    tags: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    category: Mapped[Optional[FileCategory]] = relationship(back_populates="files")


class Bookmark(Base):
    __tablename__ = "bookmarks"
    __table_args__ = (
        UniqueConstraint("user_id", "file_id", name="uq_bookmark"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    file_id: Mapped[int] = mapped_column(
        ForeignKey("file_items.id", ondelete="CASCADE"), nullable=False
    )
    note: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
