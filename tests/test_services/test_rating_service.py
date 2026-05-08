import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.services.rating_service import RatingService
from bot.core.enums import PointReason


class TestRatingService:
    @pytest.fixture
    def service(self):
        session = AsyncMock()
        return RatingService(session)

    @pytest.mark.asyncio
    async def test_add_points(self, service):
        service.rating_repo.add_points = AsyncMock()
        await service.add_points(1, 10, PointReason.TEST_EXCELLENT, "test")
        service.rating_repo.add_points.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_leaderboard(self, service):
        service.rating_repo.get_leaderboard = AsyncMock(return_value=[])
        result = await service.get_leaderboard("weekly", 10)
        assert result == []

    @pytest.mark.asyncio
    async def test_reset_weekly(self, service):
        service.rating_repo.reset_weekly = AsyncMock()
        await service.reset_weekly()
        service.rating_repo.reset_weekly.assert_called_once()
