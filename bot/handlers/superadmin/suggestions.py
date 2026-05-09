from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.suggestion_repo import SuggestionRepository
from bot.repositories.user_repo import UserRepository

router = Router(name="sa_suggestions")


class SuggestionResponseState(StatesGroup):
    waiting_response = State()


@router.callback_query(F.data == "sa:suggestions")
async def list_suggestions(callback: CallbackQuery, session: AsyncSession):
    repo = SuggestionRepository(session)
    items = await repo.list_by_status(limit=20)
    new_count = await repo.count_new()

    text = (
        f"✉️ <b>Takliflar inbox</b>\n\n"
        f"Yangi: {new_count} | Ko'rilgan: {len(items)}"
    )

    builder = InlineKeyboardBuilder()
    for s in items:
        icon = {"new": "🆕", "responded": "✅", "closed": "📕"}.get(s.status, "❓")
        preview = (s.text[:40] + "…") if len(s.text) > 40 else s.text
        builder.button(
            text=f"{icon} {preview}", callback_data=f"sug:view:{s.id}"
        )
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:superadmin"))

    if callback.message:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("sug:view:"))
async def view_suggestion(callback: CallbackQuery, session: AsyncSession):
    sug_id = int(callback.data.split(":")[-1])
    repo = SuggestionRepository(session)
    s = await repo.get_by_id(sug_id)
    if not s:
        await callback.answer("Topilmadi.", show_alert=True)
        return

    user_label = "Anonim"
    if not s.is_anonymous and s.user_id:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_id(s.user_id)
        if user:
            user_label = f"{user.display_name} (ID: {user.telegram_id})"

    text = (
        f"✉️ <b>Taklif #{s.id}</b>\n\n"
        f"📅 {s.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"From: {user_label}\n"
        f"Status: {s.status}\n\n"
        f"<b>Matn:</b>\n{s.text}\n"
    )
    if s.admin_response:
        text += f"\n<b>Javob:</b>\n{s.admin_response}\n"

    builder = InlineKeyboardBuilder()
    if s.status == "new":
        builder.button(text="✍️ Javob yozish", callback_data=f"sug:reply:{s.id}")
        if not s.is_anonymous and s.user_id:
            pass
    builder.button(text="📕 Yopish", callback_data=f"sug:close:{s.id}")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="sa:suggestions"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("sug:reply:"))
async def reply_suggestion_start(
    callback: CallbackQuery, state: FSMContext
):
    sug_id = int(callback.data.split(":")[-1])
    await state.set_state(SuggestionResponseState.waiting_response)
    await state.update_data(sug_id=sug_id)
    await callback.message.answer("✍️ Javobingizni kiriting:")
    await callback.answer()


@router.message(SuggestionResponseState.waiting_response, F.text)
async def reply_suggestion_save(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
    bot: Bot,
):
    data = await state.get_data()
    sug_id = data["sug_id"]
    repo = SuggestionRepository(session)
    sug = await repo.respond(sug_id, message.text.strip(), db_user.id)
    await state.clear()

    if sug and not sug.is_anonymous and sug.user_id:
        user_repo = UserRepository(session)
        target = await user_repo.get_by_id(sug.user_id)
        if target:
            try:
                await bot.send_message(
                    target.telegram_id,
                    f"✉️ <b>Taklifingizga javob keldi (#{sug.id})</b>\n\n"
                    f"<i>{sug.text}</i>\n\n"
                    f"<b>Javob:</b>\n{message.text.strip()}",
                )
            except Exception:
                pass

    await message.answer("✅ Javob saqlandi.")


@router.callback_query(F.data.startswith("sug:close:"))
async def close_suggestion(callback: CallbackQuery, session: AsyncSession):
    sug_id = int(callback.data.split(":")[-1])
    repo = SuggestionRepository(session)
    await repo.mark_status(sug_id, "closed")
    await callback.answer("📕 Yopildi.")
    callback.data = "sa:suggestions"
    await list_suggestions(callback, session)
