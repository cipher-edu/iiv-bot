from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.suggestion import Suggestion
from bot.repositories.base import BaseRepository


class SuggestionRepository(BaseRepository[Suggestion]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Suggestion)

    async def list_by_status(
        self,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[Suggestion]:
        stmt = (
            select(Suggestion)
            .where(Suggestion.is_deleted == False)
            .order_by(Suggestion.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if status:
            stmt = stmt.where(Suggestion.status == status)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_new(self) -> int:
        stmt = select(func.count(Suggestion.id)).where(
            Suggestion.status == "new",
            Suggestion.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def respond(
        self, suggestion_id: int, response: str, by_user_id: int
    ) -> Optional[Suggestion]:
        return await self.update_by_id(
            suggestion_id,
            admin_response=response,
            status="responded",
            responded_at=datetime.utcnow(),
            responded_by=by_user_id,
        )

    async def mark_status(
        self, suggestion_id: int, status: str
    ) -> Optional[Suggestion]:
        return await self.update_by_id(suggestion_id, status=status)
