from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from bot.models.task import TaskAssignment
from bot.models.user import TelegramUser

router = Router(name="moderator_reports")


@router.message(F.text == "/modpanel")
async def mod_panel(message: Message):
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Tekshirish kutayotganlar", callback_data="mod:tasks")
    builder.button(text="📊 Statistika", callback_data="mod:stats")
    builder.adjust(1)
    await message.answer(
        "👮 <b>Moderator paneli</b>",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "mod:stats")
async def mod_stats(callback: CallbackQuery, session: AsyncSession):
    submitted = await session.execute(
        select(func.count(TaskAssignment.id)).where(TaskAssignment.status == "submitted")
    )
    reviewed = await session.execute(
        select(func.count(TaskAssignment.id)).where(TaskAssignment.status == "reviewed")
    )

    text = (
        "📊 <b>Moderator statistikasi</b>\n\n"
        f"📤 Tekshirish kutayotgan: {submitted.scalar_one()}\n"
        f"✅ Tekshirilgan: {reviewed.scalar_one()}\n"
    )
    await callback.message.edit_text(text)
    await callback.answer()
