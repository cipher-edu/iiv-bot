from typing import Optional, Sequence
from datetime import datetime

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser, Organization
from bot.repositories.base import BaseRepository
from bot.core.enums import Role, UserStatus, RegistrationStep, OrganizationType


class UserRepository(BaseRepository[TelegramUser]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, TelegramUser)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[TelegramUser]:
        stmt = select(TelegramUser).where(
            TelegramUser.telegram_id == telegram_id,
            TelegramUser.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, telegram_id: int, username: Optional[str] = None) -> TelegramUser:
        return await self.create(
            telegram_id=telegram_id,
            username=username,
            role=Role.USER,
            status=UserStatus.PENDING,
            registration_step=RegistrationStep.PHONE,
        )

    async def update_registration(
        self, user_id: int, step: RegistrationStep, **kwargs
    ) -> Optional[TelegramUser]:
        kwargs["registration_step"] = step
        if step == RegistrationStep.COMPLETED:
            kwargs["status"] = UserStatus.ACTIVE
            kwargs["is_verified"] = True
        return await self.update_by_id(user_id, **kwargs)

    async def get_active_users(
        self, offset: int = 0, limit: int = 10
    ) -> Sequence[TelegramUser]:
        stmt = (
            select(TelegramUser)
            .where(
                TelegramUser.status == UserStatus.ACTIVE,
                TelegramUser.is_deleted == False,
            )
            .order_by(TelegramUser.full_name)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_all_active_ids(self) -> Sequence[int]:
        stmt = select(TelegramUser.telegram_id).where(
            TelegramUser.status == UserStatus.ACTIVE,
            TelegramUser.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_role(
        self, role: Role, offset: int = 0, limit: int = 10
    ) -> Sequence[TelegramUser]:
        stmt = (
            select(TelegramUser)
            .where(
                TelegramUser.role == role,
                TelegramUser.is_deleted == False,
            )
            .order_by(TelegramUser.full_name)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search_users(
        self, query: str, offset: int = 0, limit: int = 10
    ) -> Sequence[TelegramUser]:
        pattern = f"%{query}%"
        stmt = (
            select(TelegramUser)
            .where(
                TelegramUser.is_deleted == False,
                (
                    TelegramUser.full_name.ilike(pattern)
                    | TelegramUser.username.ilike(pattern)
                    | TelegramUser.phone.ilike(pattern)
                ),
            )
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def block_user(
        self,
        user_id: int,
        reason: str,
        blocked_until: Optional[datetime] = None,
    ) -> Optional[TelegramUser]:
        return await self.update_by_id(
            user_id,
            is_blocked=True,
            status=UserStatus.BLOCKED,
            block_reason=reason,
            blocked_until=blocked_until,
        )

    async def unblock_user(self, user_id: int) -> Optional[TelegramUser]:
        return await self.update_by_id(
            user_id,
            is_blocked=False,
            status=UserStatus.ACTIVE,
            block_reason=None,
            blocked_until=None,
            login_attempts=0,
        )

    async def set_role(self, user_id: int, role: Role) -> Optional[TelegramUser]:
        return await self.update_by_id(user_id, role=role)

    async def update_activity(self, user_id: int) -> None:
        stmt = (
            update(TelegramUser)
            .where(TelegramUser.id == user_id)
            .values(last_activity=func.now())
        )
        await self.session.execute(stmt)

    async def increment_login_attempts(self, user_id: int) -> int:
        user = await self.get_by_id(user_id)
        if user:
            new_count = user.login_attempts + 1
            await self.update_by_id(user_id, login_attempts=new_count)
            return new_count
        return 0

    async def count_by_status(self) -> dict:
        stmt = (
            select(TelegramUser.status, func.count(TelegramUser.id))
            .where(TelegramUser.is_deleted == False)
            .group_by(TelegramUser.status)
        )
        result = await self.session.execute(stmt)
        return dict(result.all())

    async def get_by_organization(
        self, org_id: int, offset: int = 0, limit: int = 10
    ) -> Sequence[TelegramUser]:
        stmt = (
            select(TelegramUser)
            .where(
                TelegramUser.organization_id == org_id,
                TelegramUser.is_deleted == False,
            )
            .order_by(TelegramUser.full_name)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class OrganizationRepository(BaseRepository[Organization]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Organization)

    async def get_by_type(
        self, org_type: OrganizationType
    ) -> Sequence[Organization]:
        stmt = (
            select(Organization)
            .where(
                Organization.org_type == org_type,
                Organization.is_active == True,
                Organization.is_deleted == False,
            )
            .order_by(Organization.name)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_active_all(self) -> Sequence[Organization]:
        stmt = (
            select(Organization)
            .where(
                Organization.is_active == True,
                Organization.is_deleted == False,
            )
            .order_by(Organization.org_type, Organization.name)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
