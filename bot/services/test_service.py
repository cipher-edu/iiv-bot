import random
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.test import Test, TestSession, TestResult
from bot.repositories.test_repo import TestRepository, TestSessionRepository, TestResultRepository
from bot.config import settings


class TestService:
    def __init__(self, session: AsyncSession):
        self.test_repo = TestRepository(session)
        self.session_repo = TestSessionRepository(session)
        self.result_repo = TestResultRepository(session)

    async def get_available_tests(self, offset: int = 0, limit: int = 10) -> Sequence[Test]:
        return await self.test_repo.get_active_tests(offset=offset, limit=limit)

    async def start_test(
        self, user_id: int, test_id: int
    ) -> Optional[TestSession]:
        test = await self.test_repo.get_with_questions(test_id)
        if not test or not test.questions:
            return None

        question_ids = [q.id for q in test.questions]
        random.shuffle(question_ids)

        return await self.session_repo.create_session(
            user_id=user_id,
            test_id=test_id,
            question_order=question_ids,
        )

    async def submit_answer(
        self, session_id: int, question_id: int, answer_id: int
    ) -> bool:
        return await self.session_repo.submit_answer(session_id, question_id, answer_id)

    async def finish_test(self, session_id: int) -> Optional[TestResult]:
        result = await self.session_repo.finish_session(session_id)
        if not result:
            return None

        score = result.get("score", 0)
        points = 0
        if score >= settings.score_excellent_threshold:
            points = settings.score_excellent
        elif score >= settings.score_good_threshold:
            points = settings.score_good
        elif score >= settings.score_satisfactory_threshold:
            points = settings.score_satisfactory
        else:
            points = settings.score_participation

        return result

    async def get_user_results(
        self, user_id: int, limit: int = 20
    ) -> Sequence[TestResult]:
        return await self.result_repo.get_by_user(user_id, limit=limit)
