import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from bot.services.user_service import UserService
from bot.core.enums import Role


class TestUserService:
    @pytest.fixture
    def service(self):
        session = AsyncMock()
        return UserService(session)

    @pytest.mark.asyncio
    async def test_get_or_create_existing(self, service):
        mock_user = MagicMock()
        mock_user.telegram_id = 123
        service.repo.get_by_telegram_id = AsyncMock(return_value=mock_user)

        user = await service.get_or_create_user(123, "test")
        assert user.telegram_id == 123
        service.repo.create_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_create_new(self, service):
        service.repo.get_by_telegram_id = AsyncMock(return_value=None)
        mock_new = MagicMock()
        mock_new.telegram_id = 456
        service.repo.create_user = AsyncMock(return_value=mock_new)

        user = await service.get_or_create_user(456, "newuser")
        assert user.telegram_id == 456
        service.repo.create_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_block_user(self, service):
        service.repo.block_user = AsyncMock(return_value=MagicMock())
        result = await service.block_user(1, "spam")
        service.repo.block_user.assert_called_once_with(1, "spam")

    @pytest.mark.asyncio
    async def test_set_role(self, service):
        service.repo.set_role = AsyncMock(return_value=MagicMock())
        await service.set_role(1, Role.ADMIN)
        service.repo.set_role.assert_called_once_with(1, Role.ADMIN)
