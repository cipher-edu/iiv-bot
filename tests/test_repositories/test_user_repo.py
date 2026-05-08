import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.user_repo import UserRepository
from bot.models.user import TelegramUser


class TestUserRepository:
    @pytest.mark.asyncio
    async def test_create_user(self, session: AsyncSession):
        repo = UserRepository(session)
        user = await repo.create_user(telegram_id=999999, username="testbot")
        assert user is not None
        assert user.telegram_id == 999999

    @pytest.mark.asyncio
    async def test_get_by_telegram_id(self, session: AsyncSession):
        repo = UserRepository(session)
        await repo.create_user(telegram_id=888888, username="findme")
        found = await repo.get_by_telegram_id(888888)
        assert found is not None
        assert found.username == "findme"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, session: AsyncSession):
        repo = UserRepository(session)
        found = await repo.get_by_telegram_id(111111)
        assert found is None
