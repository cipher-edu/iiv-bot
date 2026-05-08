from typing import Optional, Sequence
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.models.test import (
    Test,
    Question,
    AnswerOption,
    TestSession,
    UserAnswer,
    TestResult,
)
from bot.repositories.base import BaseRepository
from bot.core.enums import TestSessionStatus


class TestRepository(BaseRepository[Test]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Test)

    async def get_active_tests(
        self, offset: int = 0, limit: int = 10
    ) -> Sequence[Test]:
        stmt = (
            select(Test)
            .where(Test.is_active == True, Test.is_deleted == False)
            .options(selectinload(Test.questions).selectinload(Question.options))
            .order_by(Test.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def get_with_questions(self, test_id: int) -> Optional[Test]:
        stmt = (
            select(Test)
            .where(Test.id == test_id, Test.is_deleted == False)
            .options(selectinload(Test.questions).selectinload(Question.options))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_available_for_user(
        self, user_id: int, org_id: Optional[int] = None
    ) -> Sequence[Test]:
        stmt = (
            select(Test)
            .where(Test.is_active == True, Test.is_deleted == False)
            .options(selectinload(Test.questions))
            .order_by(Test.created_at.desc())
        )
        result = await self.session.execute(stmt)
        tests = result.scalars().unique().all()
        if org_id:
            return [
                t for t in tests
                if not t.target_organizations or org_id in t.target_organizations
            ]
        return tests

    async def create_question(
        self, test_id: int, text: str, order: int = 0, image_url: Optional[str] = None
    ) -> Question:
        question = Question(
            test_id=test_id, text=text, order=order, image_url=image_url
        )
        self.session.add(question)
        await self.session.flush()
        await self.session.refresh(question)
        return question

    async def create_option(
        self, question_id: int, text: str, is_correct: bool = False, order: int = 0
    ) -> AnswerOption:
        option = AnswerOption(
            question_id=question_id, text=text, is_correct=is_correct, order=order
        )
        self.session.add(option)
        await self.session.flush()
        return option


class TestSessionRepository(BaseRepository[TestSession]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, TestSession)

    async def get_active_session(
        self, user_id: int, test_id: int
    ) -> Optional[TestSession]:
        stmt = select(TestSession).where(
            TestSession.user_id == user_id,
            TestSession.test_id == test_id,
            TestSession.status == TestSessionStatus.ACTIVE,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_active_session(self, user_id: int) -> Optional[TestSession]:
        stmt = (
            select(TestSession)
            .where(
                TestSession.user_id == user_id,
                TestSession.status == TestSessionStatus.ACTIVE,
            )
            .options(selectinload(TestSession.test))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_session(
        self, user_id: int, test_id: int, question_order: list
    ) -> TestSession:
        session = TestSession(
            user_id=user_id,
            test_id=test_id,
            status=TestSessionStatus.ACTIVE,
            question_order=question_order,
            started_at=datetime.utcnow(),
            current_question_index=0,
        )
        self.session.add(session)
        await self.session.flush()
        await self.session.refresh(session)
        return session

    async def submit_answer(
        self,
        session_id: int,
        question_id: int,
        option_id: Optional[int] = None,
        is_timeout: bool = False,
    ) -> UserAnswer:
        answer = UserAnswer(
            session_id=session_id,
            question_id=question_id,
            selected_option_id=option_id,
            is_timeout=is_timeout,
            answered_at=datetime.utcnow(),
        )
        self.session.add(answer)
        await self.session.flush()
        return answer

    async def finish_session(self, session_id: int) -> Optional[TestSession]:
        return await self.update_by_id(
            session_id,
            status=TestSessionStatus.FINISHED,
            finished_at=datetime.utcnow(),
        )

    async def expire_session(self, session_id: int) -> None:
        await self.update_by_id(
            session_id,
            status=TestSessionStatus.EXPIRED,
            finished_at=datetime.utcnow(),
        )

    async def get_user_attempts(self, user_id: int, test_id: int) -> int:
        stmt = select(func.count(TestSession.id)).where(
            TestSession.user_id == user_id,
            TestSession.test_id == test_id,
            TestSession.status.in_([
                TestSessionStatus.FINISHED,
                TestSessionStatus.EXPIRED,
            ]),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()


class TestResultRepository(BaseRepository[TestResult]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, TestResult)

    async def create_result(
        self,
        session_id: int,
        user_id: int,
        test_id: int,
        correct: int,
        wrong: int,
        timeout: int,
        total: int,
        score: int,
        is_passed: bool,
        points: int,
    ) -> TestResult:
        return await self.create(
            session_id=session_id,
            user_id=user_id,
            test_id=test_id,
            correct_count=correct,
            wrong_count=wrong,
            timeout_count=timeout,
            total_questions=total,
            score_percent=score,
            is_passed=is_passed,
            points_awarded=points,
        )

    async def get_user_results(
        self, user_id: int, offset: int = 0, limit: int = 10
    ) -> Sequence[TestResult]:
        stmt = (
            select(TestResult)
            .where(TestResult.user_id == user_id)
            .order_by(TestResult.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_best_result(self, user_id: int, test_id: int) -> Optional[TestResult]:
        stmt = (
            select(TestResult)
            .where(
                TestResult.user_id == user_id,
                TestResult.test_id == test_id,
            )
            .order_by(TestResult.score_percent.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
