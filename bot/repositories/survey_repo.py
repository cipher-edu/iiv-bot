from typing import Optional, Sequence
from datetime import datetime

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.survey import Survey, SurveyQuestion, SurveyResponse
from bot.repositories.base import BaseRepository


class SurveyRepository(BaseRepository[Survey]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Survey)

    async def get_active_surveys(
        self, offset: int = 0, limit: int = 10
    ) -> Sequence[Survey]:
        now = datetime.utcnow()
        stmt = (
            select(Survey)
            .where(
                Survey.is_active == True,
                Survey.is_deleted == False,
            )
            .order_by(Survey.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_with_questions(self, survey_id: int) -> Optional[Survey]:
        from sqlalchemy.orm import selectinload
        stmt = (
            select(Survey)
            .where(Survey.id == survey_id, Survey.is_deleted == False)
            .options(selectinload(Survey.questions))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_responded(self, survey_id: int, user_id: int) -> bool:
        stmt = select(func.count(SurveyResponse.id)).where(
            SurveyResponse.survey_id == survey_id,
            SurveyResponse.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    async def submit_response(
        self, survey_id: int, user_id: Optional[int], answers: dict
    ) -> SurveyResponse:
        response = SurveyResponse(
            survey_id=survey_id,
            user_id=user_id,
            answers=answers,
            submitted_at=datetime.utcnow(),
        )
        self.session.add(response)

        stmt = (
            update(Survey)
            .where(Survey.id == survey_id)
            .values(total_responses=Survey.total_responses + 1)
        )
        await self.session.execute(stmt)
        await self.session.flush()
        return response

    async def get_responses(
        self, survey_id: int, offset: int = 0, limit: int = 50
    ) -> Sequence[SurveyResponse]:
        stmt = (
            select(SurveyResponse)
            .where(SurveyResponse.survey_id == survey_id)
            .order_by(SurveyResponse.submitted_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_response_count(self, survey_id: int) -> int:
        stmt = select(func.count(SurveyResponse.id)).where(
            SurveyResponse.survey_id == survey_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
