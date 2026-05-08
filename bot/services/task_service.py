from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.task import Task, TaskAssignment
from bot.repositories.task_repo import TaskRepository, TaskAssignmentRepository


class TaskService:
    def __init__(self, session: AsyncSession):
        self.task_repo = TaskRepository(session)
        self.assignment_repo = TaskAssignmentRepository(session)

    async def create_task(self, **kwargs) -> Task:
        return await self.task_repo.create(**kwargs)

    async def assign_task(self, task_id: int, user_id: int) -> TaskAssignment:
        return await self.assignment_repo.create(task_id=task_id, user_id=user_id)

    async def submit_report(self, assignment_id: int, report: str) -> Optional[TaskAssignment]:
        return await self.assignment_repo.submit_report(assignment_id, report)

    async def review(
        self, assignment_id: int, reviewer_id: int,
        status: str, note: str | None = None,
    ) -> Optional[TaskAssignment]:
        return await self.assignment_repo.review_assignment(
            assignment_id, reviewed_by=reviewer_id,
            review_status=status, review_note=note,
        )

    async def get_overdue(self) -> Sequence[Task]:
        return await self.task_repo.get_overdue_tasks()

    async def get_user_tasks(
        self, user_id: int, status: str | None = None, limit: int = 20,
    ) -> Sequence[TaskAssignment]:
        return await self.assignment_repo.get_user_assignments(
            user_id, status=status, limit=limit,
        )
