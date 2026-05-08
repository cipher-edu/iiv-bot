from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.audit import AuditLog, SecurityEvent
from bot.repositories.base import BaseRepository
from bot.core.enums import AuditAction


class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, AuditLog)

    async def log_action(
        self,
        action: AuditAction,
        user_id: Optional[int] = None,
        telegram_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        details: Optional[dict] = None,
    ) -> AuditLog:
        return await self.create(
            user_id=user_id,
            telegram_id=telegram_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )

    async def get_user_actions(
        self, user_id: int, offset: int = 0, limit: int = 20
    ) -> Sequence[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_action(
        self, action: AuditAction, offset: int = 0, limit: int = 20
    ) -> Sequence[AuditLog]:
        stmt = (
            select(AuditLog)
            .where(AuditLog.action == action)
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_recent(self, limit: int = 50) -> Sequence[AuditLog]:
        stmt = (
            select(AuditLog)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class SecurityEventRepository(BaseRepository[SecurityEvent]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SecurityEvent)

    async def log_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        telegram_id: Optional[int] = None,
        details: Optional[dict] = None,
    ) -> SecurityEvent:
        return await self.create(
            event_type=event_type,
            severity=severity,
            description=description,
            telegram_id=telegram_id,
            details=details,
        )

    async def get_unresolved(
        self, offset: int = 0, limit: int = 20
    ) -> Sequence[SecurityEvent]:
        stmt = (
            select(SecurityEvent)
            .where(SecurityEvent.is_resolved == False)
            .order_by(SecurityEvent.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def resolve_event(
        self, event_id: int, resolved_by: int, note: Optional[str] = None
    ) -> Optional[SecurityEvent]:
        return await self.update_by_id(
            event_id,
            is_resolved=True,
            resolved_by=resolved_by,
            resolved_note=note,
        )
