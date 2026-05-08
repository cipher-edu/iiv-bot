from datetime import date
from typing import Optional

from sqlalchemy import String, Integer, ForeignKey, Text, Boolean, Date, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base


class CertificateTemplate(Base):
    __tablename__ = "certificate_templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    background_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    font_name: Mapped[str] = mapped_column(String(100), default="Helvetica")
    font_size_title: Mapped[int] = mapped_column(Integer, default=36)
    font_size_body: Mapped[int] = mapped_column(Integer, default=18)
    text_color: Mapped[str] = mapped_column(String(7), default="#000000")
    layout_config: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)


class Certificate(Base):
    __tablename__ = "certificates"
    __table_args__ = (
        Index("ix_cert_user", "user_id"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    course_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("courses.id", ondelete="SET NULL"), nullable=True
    )
    template_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("certificate_templates.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    certificate_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    issued_date: Mapped[date] = mapped_column(Date, nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    qr_code_data: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    score_percent: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
