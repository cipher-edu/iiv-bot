from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.filters.registered import IsRegisteredFilter
from bot.repositories.task_repo import TaskAssignmentRepository
from bot.keyboards.user_reply import back_keyboard

router = Router(name="user_tasks")
router.message.filter(IsRegisteredFilter())


class TaskReportState(StatesGroup):
    waiting_report = State()


@router.message(F.text == "📋 Vazifalar")
async def show_tasks(message: Message, session: AsyncSession, db_user: TelegramUser):
    repo = TaskAssignmentRepository(session)
    assignments = await repo.get_user_assignments(db_user.id, limit=20)
    stats = await repo.count_by_status(db_user.id)

    text = (
        "📋 <b>Sizning vazifalaringiz</b>\n\n"
        f"📊 Jami: {sum(stats.values())} | "
        f"Kutilmoqda: {stats.get('assigned', 0)} | "
        f"Yuborilgan: {stats.get('submitted', 0)} | "
        f"Tekshirilgan: {stats.get('reviewed', 0)}\n\n"
    )

    if not assignments:
        text += "Hozircha vazifa yo'q."
        await message.answer(text, reply_markup=back_keyboard())
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    for a in assignments:
        status_icon = {"assigned": "📌", "submitted": "📤", "reviewed": "✅"}.get(a.status, "📋")
        builder.button(
            text=f"{status_icon} Vazifa #{a.task_id}",
            callback_data=f"task:view:{a.id}",
        )
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("task:view:"))
async def view_task(callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser):
    assignment_id = int(callback.data.split(":")[-1])

    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from bot.models.task import TaskAssignment as TA
    stmt = (
        select(TA)
        .where(TA.id == assignment_id, TA.is_deleted == False)
        .options(selectinload(TA.task))
    )
    result = await session.execute(stmt)
    assignment = result.scalar_one_or_none()

    if not assignment or assignment.user_id != db_user.id:
        await callback.answer("Vazifa topilmadi.", show_alert=True)
        return

    task = assignment.task
    status_text = {"assigned": "Kutilmoqda", "submitted": "Yuborilgan", "reviewed": "Tekshirilgan"}.get(assignment.status, assignment.status)

    text = (
        f"📋 <b>{task.title}</b>\n\n"
        f"{task.description or ''}\n\n"
        f"📊 Status: {status_text}\n"
        f"⚡ Muhimlik: {task.priority}\n"
    )
    if task.deadline:
        text += f"⏰ Muddat: {task.deadline.strftime('%d.%m.%Y %H:%M')}\n"
    if assignment.review_note:
        text += f"\n💬 Izoh: {assignment.review_note}\n"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()

    if assignment.status == "assigned":
        builder.button(text="📤 Hisobot yuborish", callback_data=f"task:report:{assignment.id}")
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="task:list"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("task:report:"))
async def start_report(callback: CallbackQuery, state: FSMContext):
    assignment_id = int(callback.data.split(":")[-1])
    await state.set_state(TaskReportState.waiting_report)
    await state.update_data(assignment_id=assignment_id)
    await callback.message.answer("📤 Hisobotingizni yozing:")
    await callback.answer()


@router.message(TaskReportState.waiting_report, F.text)
async def submit_report(
    message: Message, state: FSMContext, session: AsyncSession, db_user: TelegramUser
):
    data = await state.get_data()
    repo = TaskAssignmentRepository(session)
    await repo.submit_report(data["assignment_id"], message.text)
    await state.clear()
    await message.answer("✅ Hisobot yuborildi! Tekshirilishini kuting.", reply_markup=back_keyboard())
