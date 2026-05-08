from typing import Optional, Sequence
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.task import Task, TaskAssignment
from bot.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Task)

    async def get_active_tasks(
        self, offset: int = 0, limit: int = 10
    ) -> Sequence[Task]:
        stmt = (
            select(Task)
            .where(Task.is_active == True, Task.is_deleted == False)
            .order_by(Task.deadline.asc().nullslast(), Task.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_overdue_tasks(self) -> Sequence[Task]:
        now = datetime.utcnow()
        stmt = (
            select(Task)
            .where(
                Task.is_active == True,
                Task.is_deleted == False,
                Task.deadline < now,
                Task.status != "completed",
            )
            .order_by(Task.deadline)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class TaskAssignmentRepository(BaseRepository[TaskAssignment]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, TaskAssignment)

    async def get_user_assignments(
        self, user_id: int, status: Optional[str] = None, offset: int = 0, limit: int = 10
    ) -> Sequence[TaskAssignment]:
        stmt = (
            select(TaskAssignment)
            .where(TaskAssignment.user_id == user_id, TaskAssignment.is_deleted == False)
        )
        if status:
            stmt = stmt.where(TaskAssignment.status == status)
        stmt = stmt.order_by(TaskAssignment.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def submit_report(
        self, assignment_id: int, report: str
    ) -> Optional[TaskAssignment]:
        return await self.update_by_id(
            assignment_id,
            report=report,
            status="submitted",
            completed_at=datetime.utcnow(),
        )

    async def review_assignment(
        self,
        assignment_id: int,
        reviewed_by: int,
        review_status: str,
        review_note: Optional[str] = None,
    ) -> Optional[TaskAssignment]:
        return await self.update_by_id(
            assignment_id,
            reviewed_by=reviewed_by,
            review_status=review_status,
            review_note=review_note,
            status="reviewed",
        )

    async def count_by_status(self, user_id: int) -> dict:
        stmt = (
            select(TaskAssignment.status, func.count(TaskAssignment.id))
            .where(TaskAssignment.user_id == user_id, TaskAssignment.is_deleted == False)
            .group_by(TaskAssignment.status)
        )
        result = await self.session.execute(stmt)
        return dict(result.all())
