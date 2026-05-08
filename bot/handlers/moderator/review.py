from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.task_repo import TaskAssignmentRepository

router = Router(name="moderator_review")


class ReviewState(StatesGroup):
    waiting_note = State()


@router.callback_query(F.data == "mod:tasks")
async def pending_tasks(callback: CallbackQuery, session: AsyncSession):
    repo = TaskAssignmentRepository(session)
    from sqlalchemy import select
    from bot.models.task import TaskAssignment
    stmt = (
        select(TaskAssignment)
        .where(TaskAssignment.status == "submitted", TaskAssignment.is_deleted == False)
        .order_by(TaskAssignment.completed_at.desc())
        .limit(20)
    )
    result = await session.execute(stmt)
    assignments = result.scalars().all()

    if not assignments:
        await callback.answer("Tekshirish kutayotgan vazifalar yo'q.", show_alert=True)
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for a in assignments:
        builder.button(
            text=f"📤 Vazifa #{a.task_id} (user:{a.user_id})",
            callback_data=f"mod:review:{a.id}",
        )
    builder.adjust(1)

    await callback.message.edit_text(
        "📋 <b>Tekshirish kutayotgan vazifalar:</b>",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("mod:review:"))
async def review_assignment(callback: CallbackQuery, session: AsyncSession):
    assignment_id = int(callback.data.split(":")[-1])
    repo = TaskAssignmentRepository(session)
    assignment = await repo.get_by_id(assignment_id)

    if not assignment:
        await callback.answer("Vazifa topilmadi.", show_alert=True)
        return

    text = (
        f"📋 <b>Vazifa #{assignment.task_id}</b>\n\n"
        f"👤 Foydalanuvchi: {assignment.user_id}\n"
        f"📤 Hisobot:\n{assignment.report or 'Bo`sh'}\n"
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Qabul qilish", callback_data=f"mod:approve:{assignment.id}")
    builder.button(text="❌ Rad etish", callback_data=f"mod:reject:{assignment.id}")
    builder.adjust(2)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("mod:approve:"))
async def approve_assignment(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    assignment_id = int(callback.data.split(":")[-1])
    repo = TaskAssignmentRepository(session)
    await repo.review_assignment(
        assignment_id, reviewed_by=db_user.id,
        review_status="approved", review_note="Qabul qilindi",
    )
    await callback.message.edit_text("✅ Vazifa qabul qilindi!")
    await callback.answer()


@router.callback_query(F.data.startswith("mod:reject:"))
async def reject_start(callback: CallbackQuery, state: FSMContext):
    assignment_id = int(callback.data.split(":")[-1])
    await state.set_state(ReviewState.waiting_note)
    await state.update_data(reject_assignment_id=assignment_id)
    await callback.message.answer("❌ Rad etish sababini yozing:")
    await callback.answer()


@router.message(ReviewState.waiting_note, F.text)
async def reject_complete(
    message: Message, state: FSMContext, session: AsyncSession, db_user: TelegramUser
):
    data = await state.get_data()
    repo = TaskAssignmentRepository(session)
    await repo.review_assignment(
        data["reject_assignment_id"], reviewed_by=db_user.id,
        review_status="rejected", review_note=message.text,
    )
    await state.clear()
    await message.answer("❌ Vazifa rad etildi.")
