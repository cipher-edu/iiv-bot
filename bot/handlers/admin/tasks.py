from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.task_repo import TaskRepository, TaskAssignmentRepository
from bot.repositories.user_repo import UserRepository
from bot.states.admin_states import TaskCreateState
from bot.keyboards.user_reply import cancel_keyboard

router = Router(name="admin_tasks")


@router.callback_query(F.data == "admin:tasks")
async def admin_tasks(callback: CallbackQuery, session: AsyncSession):
    repo = TaskRepository(session)
    tasks = await repo.get_active_tasks(limit=20)

    text = "📋 <b>Vazifalar boshqaruvi</b>\n\n"
    for t in tasks:
        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(t.priority, "⚪")
        text += f"{priority_icon} {t.title} [{t.status}]\n"

    if not tasks:
        text += "Hozircha vazifa yo'q."

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Yangi vazifa", callback_data="admin:tasks:create")
    builder.button(text="⏰ Muddati o'tganlar", callback_data="admin:tasks:overdue")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:menu"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "admin:tasks:create")
async def create_task_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TaskCreateState.waiting_title)
    await callback.message.answer(
        "📋 <b>Yangi vazifa yaratish</b>\n\nVazifa nomini kiriting:",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(TaskCreateState.waiting_title, F.text)
async def task_title(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return
    await state.update_data(title=message.text)
    await state.set_state(TaskCreateState.waiting_description)
    await message.answer("📝 Vazifa tavsifini kiriting (yoki '-'):")


@router.message(TaskCreateState.waiting_description, F.text)
async def task_description(message: Message, state: FSMContext):
    desc = message.text if message.text != "-" else None
    await state.update_data(description=desc)
    await state.set_state(TaskCreateState.waiting_priority)

    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔴 Yuqori"), KeyboardButton(text="🟡 O'rta"), KeyboardButton(text="🟢 Past")]
        ],
        resize_keyboard=True,
    )
    await message.answer("⚡ Muhimlik darajasini tanlang:", reply_markup=kb)


@router.message(TaskCreateState.waiting_priority, F.text)
async def task_priority(
    message: Message, state: FSMContext, session: AsyncSession, db_user: TelegramUser
):
    priority_map = {"🔴 Yuqori": "high", "🟡 O'rta": "medium", "🟢 Past": "low"}
    priority = priority_map.get(message.text, "medium")

    data = await state.get_data()
    repo = TaskRepository(session)
    task = await repo.create(
        title=data["title"],
        description=data.get("description"),
        created_by=db_user.id,
        priority=priority,
    )

    await state.clear()
    await message.answer(
        f"✅ Vazifa yaratildi!\n\n"
        f"📋 {data['title']}\n"
        f"⚡ Muhimlik: {priority}\n\n"
        f"Xodimlarga tayinlash uchun admin panelga boring."
    )


@router.callback_query(F.data == "admin:tasks:overdue")
async def overdue_tasks(callback: CallbackQuery, session: AsyncSession):
    repo = TaskRepository(session)
    overdue = await repo.get_overdue_tasks()

    text = "⏰ <b>Muddati o'tgan vazifalar:</b>\n\n"
    for t in overdue:
        text += f"🔴 {t.title} | Muddat: {t.deadline.strftime('%d.%m.%Y')}\n"

    if not overdue:
        text += "Muddati o'tgan vazifa yo'q. ✅"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:tasks"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()
