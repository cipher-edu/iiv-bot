from typing import Optional, Sequence

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.library import FileItem, FileCategory, Bookmark
from bot.repositories.base import BaseRepository


class FileCategoryRepository(BaseRepository[FileCategory]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, FileCategory)

    async def get_active_categories(self) -> Sequence[FileCategory]:
        stmt = (
            select(FileCategory)
            .where(FileCategory.is_active == True, FileCategory.is_deleted == False)
            .order_by(FileCategory.order, FileCategory.name)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_root_categories(self) -> Sequence[FileCategory]:
        stmt = (
            select(FileCategory)
            .where(
                FileCategory.parent_id == None,
                FileCategory.is_active == True,
                FileCategory.is_deleted == False,
            )
            .order_by(FileCategory.order)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class FileItemRepository(BaseRepository[FileItem]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, FileItem)

    async def get_by_category(
        self, category_id: int, offset: int = 0, limit: int = 10
    ) -> Sequence[FileItem]:
        stmt = (
            select(FileItem)
            .where(
                FileItem.category_id == category_id,
                FileItem.is_active == True,
                FileItem.is_deleted == False,
            )
            .order_by(FileItem.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search_files(
        self, query: str, offset: int = 0, limit: int = 10
    ) -> Sequence[FileItem]:
        pattern = f"%{query}%"
        stmt = (
            select(FileItem)
            .where(
                FileItem.is_active == True,
                FileItem.is_deleted == False,
                (
                    FileItem.title.ilike(pattern)
                    | FileItem.description.ilike(pattern)
                ),
            )
            .order_by(FileItem.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def increment_download(self, file_id: int) -> None:
        stmt = (
            update(FileItem)
            .where(FileItem.id == file_id)
            .values(download_count=FileItem.download_count + 1)
        )
        await self.session.execute(stmt)


class BookmarkRepository(BaseRepository[Bookmark]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Bookmark)

    async def get_user_bookmarks(
        self, user_id: int, offset: int = 0, limit: int = 10
    ) -> Sequence[Bookmark]:
        stmt = (
            select(Bookmark)
            .where(Bookmark.user_id == user_id, Bookmark.is_deleted == False)
            .order_by(Bookmark.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def toggle_bookmark(self, user_id: int, file_id: int) -> bool:
        stmt = select(Bookmark).where(
            Bookmark.user_id == user_id, Bookmark.file_id == file_id
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            await self.hard_delete(existing.id)
            return False
        else:
            await self.create(user_id=user_id, file_id=file_id)
            return True
