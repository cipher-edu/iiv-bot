from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.library import FileCategory, FileItem
from bot.repositories.library_repo import (
    FileCategoryRepository,
    FileItemRepository,
    BookmarkRepository,
)


class LibraryService:
    def __init__(self, session: AsyncSession):
        self.cat_repo = FileCategoryRepository(session)
        self.file_repo = FileItemRepository(session)
        self.bookmark_repo = BookmarkRepository(session)

    async def get_root_categories(self) -> Sequence[FileCategory]:
        return await self.cat_repo.get_root_categories()

    async def get_files_by_category(
        self, category_id: int, limit: int = 20,
    ) -> Sequence[FileItem]:
        return await self.file_repo.get_by_category(category_id, limit=limit)

    async def search_files(
        self, query: str, limit: int = 20,
    ) -> Sequence[FileItem]:
        return await self.file_repo.search_files(query, limit=limit)

    async def download_file(self, file_id: int) -> Optional[FileItem]:
        file = await self.file_repo.get_by_id(file_id)
        if file:
            await self.file_repo.increment_download(file_id)
        return file

    async def toggle_bookmark(self, user_id: int, file_id: int) -> bool:
        return await self.bookmark_repo.toggle_bookmark(user_id, file_id)

    async def get_bookmarks(
        self, user_id: int, limit: int = 20,
    ) -> Sequence:
        return await self.bookmark_repo.get_user_bookmarks(user_id, limit=limit)
