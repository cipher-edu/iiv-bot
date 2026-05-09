import logging
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.base import async_session_factory
from bot.models.user import TelegramUser
from bot.core.enums import Role, UserStatus, RegistrationStep

logger = logging.getLogger(__name__)


async def sync_superadmins(superadmin_ids: Iterable[int]) -> None:
    """Ensure every telegram_id in BOT_SUPERADMIN_IDS exists in DB with SUPERADMIN role.

    Idempotent: safe to call on every startup. Creates missing rows, promotes
    existing rows whose role is below SUPERADMIN, never demotes anyone.
    """
    ids = [int(x) for x in superadmin_ids if x]
    if not ids:
        return

    async with async_session_factory() as session:  # type: AsyncSession
        stmt = select(TelegramUser).where(TelegramUser.telegram_id.in_(ids))
        existing = {u.telegram_id: u for u in (await session.execute(stmt)).scalars().all()}

        for tg_id in ids:
            user = existing.get(tg_id)
            if user is None:
                user = TelegramUser(
                    telegram_id=tg_id,
                    full_name=f"Superadmin {tg_id}",
                    role=Role.SUPERADMIN,
                    status=UserStatus.ACTIVE,
                    registration_step=RegistrationStep.COMPLETED,
                    is_verified=True,
                )
                session.add(user)
                logger.info("Superadmin %s DB ga qo'shildi", tg_id)
            else:
                changed = False
                if user.role != Role.SUPERADMIN:
                    user.role = Role.SUPERADMIN
                    changed = True
                if user.status != UserStatus.ACTIVE:
                    user.status = UserStatus.ACTIVE
                    changed = True
                if user.registration_step != RegistrationStep.COMPLETED:
                    user.registration_step = RegistrationStep.COMPLETED
                    changed = True
                if user.is_blocked:
                    user.is_blocked = False
                    user.blocked_until = None
                    user.block_reason = None
                    changed = True
                if not user.is_verified:
                    user.is_verified = True
                    changed = True
                if changed:
                    logger.info("Superadmin %s yangilandi", tg_id)

        await session.commit()
