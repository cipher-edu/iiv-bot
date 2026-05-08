import logging
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.audit import AuditLog, SecurityEvent
from bot.repositories.audit_repo import AuditRepository, SecurityEventRepository
from bot.core.enums import AuditAction

logger = logging.getLogger(__name__)


class SecurityService:
    def __init__(self, session: AsyncSession):
        self.audit_repo = AuditRepository(session)
        self.event_repo = SecurityEventRepository(session)

    async def log_action(
        self, user_id: int, action: AuditAction,
        entity_type: str = "", entity_id: int | None = None,
        details: dict | None = None,
    ) -> AuditLog:
        return await self.audit_repo.log_action(
            action=action,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details or {},
        )

    async def log_security_event(
        self, event_type: str, severity: str,
        user_id: int | None = None, details: dict | None = None,
    ) -> SecurityEvent:
        return await self.event_repo.log_event(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            details=details or {},
        )

    async def get_recent_events(
        self, limit: int = 20, severity: str | None = None,
    ) -> Sequence[SecurityEvent]:
        from sqlalchemy import select
        stmt = select(SecurityEvent).order_by(SecurityEvent.created_at.desc())
        if severity:
            stmt = stmt.where(SecurityEvent.severity == severity)
        stmt = stmt.limit(limit)
        result = await self.event_repo.session.execute(stmt)
        return result.scalars().all()

    async def get_unresolved_events(self) -> Sequence[SecurityEvent]:
        from sqlalchemy import select
        stmt = (
            select(SecurityEvent)
            .where(SecurityEvent.is_resolved == False)
            .order_by(SecurityEvent.created_at.desc())
        )
        result = await self.event_repo.session.execute(stmt)
        return result.scalars().all()

    async def resolve_event(self, event_id: int, resolved_by: int) -> SecurityEvent | None:
        return await self.event_repo.resolve_event(event_id, resolved_by)

    async def get_audit_log(
        self, user_id: int | None = None, action: str | None = None, limit: int = 50,
    ) -> Sequence[AuditLog]:
        if action:
            return await self.audit_repo.get_by_action(action, limit=limit)
        from sqlalchemy import select
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc())
        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
        stmt = stmt.limit(limit)
        result = await self.audit_repo.session.execute(stmt)
        return result.scalars().all()
