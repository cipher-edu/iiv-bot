from typing import Optional, Sequence

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.models.qa import LessonQuestion, LessonAnswer, QAUpvote
from bot.repositories.base import BaseRepository


class QARepository(BaseRepository[LessonQuestion]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, LessonQuestion)

    async def list_for_lesson(
        self, lesson_id: int, limit: int = 50
    ) -> Sequence[LessonQuestion]:
        stmt = (
            select(LessonQuestion)
            .where(
                LessonQuestion.lesson_id == lesson_id,
                LessonQuestion.is_deleted == False,
            )
            .options(selectinload(LessonQuestion.answers))
            .order_by(LessonQuestion.upvotes.desc(), LessonQuestion.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def ask_question(
        self, lesson_id: int, user_id: int, question: str
    ) -> LessonQuestion:
        q = LessonQuestion(
            lesson_id=lesson_id, user_id=user_id, question=question
        )
        self.session.add(q)
        await self.session.flush()
        return q

    async def add_answer(
        self,
        question_id: int,
        user_id: int,
        answer: str,
        is_official: bool = False,
    ) -> LessonAnswer:
        a = LessonAnswer(
            question_id=question_id,
            user_id=user_id,
            answer=answer,
            is_official=is_official,
        )
        self.session.add(a)
        if is_official:
            await self.update_by_id(question_id, is_resolved=True)
        await self.session.flush()
        return a

    async def toggle_upvote(
        self, user_id: int, entity_type: str, entity_id: int
    ) -> bool:
        """Returns True if vote added, False if removed."""
        stmt = select(QAUpvote).where(
            QAUpvote.user_id == user_id,
            QAUpvote.entity_type == entity_type,
            QAUpvote.entity_id == entity_id,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        target_table = LessonQuestion if entity_type == "question" else LessonAnswer

        if existing:
            await self.session.execute(
                delete(QAUpvote).where(QAUpvote.id == existing.id)
            )
            target = await self.session.get(target_table, entity_id)
            if target and target.upvotes > 0:
                target.upvotes -= 1
            await self.session.flush()
            return False

        upvote = QAUpvote(
            user_id=user_id, entity_type=entity_type, entity_id=entity_id
        )
        self.session.add(upvote)
        target = await self.session.get(target_table, entity_id)
        if target:
            target.upvotes += 1
        await self.session.flush()
        return True

    async def get_question(self, question_id: int) -> Optional[LessonQuestion]:
        stmt = (
            select(LessonQuestion)
            .where(LessonQuestion.id == question_id)
            .options(selectinload(LessonQuestion.answers))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
