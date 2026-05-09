from typing import Optional, Sequence

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.bookmark import SavedItem
from bot.repositories.base import BaseRepository


class SavedItemRepository(BaseRepository[SavedItem]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SavedItem)

    async def list_for_user(
        self,
        user_id: int,
        entity_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[SavedItem]:
        stmt = (
            select(SavedItem)
            .where(SavedItem.user_id == user_id, SavedItem.is_deleted == False)
            .order_by(SavedItem.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if entity_type:
            stmt = stmt.where(SavedItem.entity_type == entity_type)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def is_saved(
        self, user_id: int, entity_type: str, entity_id: int
    ) -> bool:
        stmt = select(func.count(SavedItem.id)).where(
            SavedItem.user_id == user_id,
            SavedItem.entity_type == entity_type,
            SavedItem.entity_id == entity_id,
            SavedItem.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    async def toggle(
        self,
        user_id: int,
        entity_type: str,
        entity_id: int,
        title: Optional[str] = None,
    ) -> bool:
        """Returns True if saved (added), False if removed."""
        existing_stmt = select(SavedItem).where(
            SavedItem.user_id == user_id,
            SavedItem.entity_type == entity_type,
            SavedItem.entity_id == entity_id,
        )
        existing = (await self.session.execute(existing_stmt)).scalar_one_or_none()
        if existing:
            await self.session.execute(
                delete(SavedItem).where(SavedItem.id == existing.id)
            )
            await self.session.flush()
            return False

        item = SavedItem(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            title_cache=title,
        )
        self.session.add(item)
        await self.session.flush()
        return True

    async def count(self, user_id: int) -> int:
        stmt = select(func.count(SavedItem.id)).where(
            SavedItem.user_id == user_id,
            SavedItem.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
