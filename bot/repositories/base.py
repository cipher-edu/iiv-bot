from typing import Generic, TypeVar, Optional, Sequence

from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    def __init__(self, session: AsyncSession, model: type[T]):
        self.session = session
        self.model = model

    async def get_by_id(self, entity_id: int) -> Optional[T]:
        stmt = select(self.model).where(
            self.model.id == entity_id,
            self.model.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 10,
        order_by=None,
    ) -> Sequence[T]:
        stmt = select(self.model).where(self.model.is_deleted == False)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        else:
            stmt = stmt.order_by(self.model.id.desc())
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, **filters) -> int:
        stmt = select(func.count(self.model.id)).where(
            self.model.is_deleted == False
        )
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def create(self, **kwargs) -> T:
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update_by_id(self, entity_id: int, **kwargs) -> Optional[T]:
        stmt = (
            update(self.model)
            .where(self.model.id == entity_id)
            .values(**kwargs)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        instance = result.scalar_one_or_none()
        if instance:
            await self.session.refresh(instance)
        return instance

    async def soft_delete(self, entity_id: int) -> bool:
        stmt = (
            update(self.model)
            .where(self.model.id == entity_id)
            .values(is_deleted=True)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def hard_delete(self, entity_id: int) -> bool:
        stmt = delete(self.model).where(self.model.id == entity_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0

    async def exists(self, **filters) -> bool:
        stmt = select(func.count(self.model.id)).where(
            self.model.is_deleted == False
        )
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    async def get_by_filters(
        self,
        offset: int = 0,
        limit: int = 10,
        order_by=None,
        **filters,
    ) -> Sequence[T]:
        stmt = select(self.model).where(self.model.is_deleted == False)
        for key, value in filters.items():
            if hasattr(self.model, key):
                if isinstance(value, list):
                    stmt = stmt.where(getattr(self.model, key).in_(value))
                else:
                    stmt = stmt.where(getattr(self.model, key) == value)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        else:
            stmt = stmt.order_by(self.model.id.desc())
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
