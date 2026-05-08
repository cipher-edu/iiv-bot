from datetime import datetime
from typing import Optional

from sqlalchemy import String, BigInteger, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.models.base import Base
from bot.core.enums import (
    Role,
    UserStatus,
    RegistrationStep,
    OrganizationType,
    StaffRole,
)


class Organization(Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    org_type: Mapped[OrganizationType] = mapped_column(
        String(50), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("organizations.id"), nullable=True
    )

    parent: Mapped[Optional["Organization"]] = relationship(
        "Organization", remote_side="Organization.id", lazy="selectin"
    )
    users: Mapped[list["TelegramUser"]] = relationship(
        back_populates="organization", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name})>"


class TelegramUser(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_telegram_id", "telegram_id", unique=True),
        Index("ix_users_role", "role"),
        Index("ix_users_status", "status"),
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False
    )
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    position: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    staff_role: Mapped[Optional[StaffRole]] = mapped_column(
        String(50), nullable=True
    )
    language: Mapped[str] = mapped_column(String(5), default="uz")

    role: Mapped[Role] = mapped_column(
        String(20), default=Role.USER, nullable=False
    )
    status: Mapped[UserStatus] = mapped_column(
        String(20), default=UserStatus.PENDING, nullable=False
    )
    registration_step: Mapped[RegistrationStep] = mapped_column(
        String(30), default=RegistrationStep.PHONE, nullable=False
    )

    organization_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("organizations.id"), nullable=True
    )
    organization: Mapped[Optional[Organization]] = relationship(
        back_populates="users", lazy="selectin"
    )

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    blocked_until: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    block_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    last_activity: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    login_attempts: Mapped[int] = mapped_column(default=0)

    def __repr__(self) -> str:
        return f"<TelegramUser(id={self.id}, tg_id={self.telegram_id}, name={self.full_name})>"

    @property
    def is_admin(self) -> bool:
        return Role(self.role).has_permission(Role.ADMIN)

    @property
    def is_superadmin(self) -> bool:
        return self.role == Role.SUPERADMIN

    @property
    def is_moderator(self) -> bool:
        return Role(self.role).has_permission(Role.MODERATOR)

    @property
    def is_registered(self) -> bool:
        return self.registration_step == RegistrationStep.COMPLETED

    @property
    def display_name(self) -> str:
        return self.full_name or self.username or f"User #{self.telegram_id}"

    @property
    def expected_org_type(self) -> Optional[OrganizationType]:
        mapping = {
            StaffRole.WORKER: OrganizationType.DEPARTMENT,
            StaffRole.DECANATE: OrganizationType.FACULTY,
            StaffRole.PROFESSOR: OrganizationType.CHAIR,
        }
        return mapping.get(self.staff_role)
