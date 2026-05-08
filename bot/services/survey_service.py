from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.survey import Survey, SurveyResponse
from bot.repositories.survey_repo import SurveyRepository


class SurveyService:
    def __init__(self, session: AsyncSession):
        self.repo = SurveyRepository(session)

    async def get_active_surveys(
        self, offset: int = 0, limit: int = 10
    ) -> Sequence[Survey]:
        return await self.repo.get_active_surveys(offset=offset, limit=limit)

    async def get_survey_with_questions(self, survey_id: int) -> Optional[Survey]:
        return await self.repo.get_with_questions(survey_id)

    async def has_responded(self, survey_id: int, user_id: int) -> bool:
        return await self.repo.has_responded(survey_id, user_id)

    async def submit(
        self, survey_id: int, user_id: int | None, answers: dict,
    ) -> SurveyResponse:
        return await self.repo.submit_response(survey_id, user_id, answers)

    async def get_responses(
        self, survey_id: int, limit: int = 50,
    ) -> Sequence[SurveyResponse]:
        return await self.repo.get_responses(survey_id, limit=limit)

    async def get_response_count(self, survey_id: int) -> int:
        return await self.repo.get_response_count(survey_id)
