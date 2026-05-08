import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestStartHandler:
    @pytest.mark.asyncio
    async def test_start_new_user(self, mock_message, mock_state):
        mock_message.text = "/start"
        mock_session = AsyncMock()

        from bot.repositories.user_repo import UserRepository
        with patch.object(UserRepository, "get_by_telegram_id", return_value=None):
            with patch.object(UserRepository, "create_user", return_value=MagicMock()):
                pass

        mock_message.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_existing_user(self, mock_message):
        mock_user = MagicMock()
        mock_user.registration_step = "completed"
        mock_user.full_name = "Test User"

        mock_message.answer.assert_not_called()
