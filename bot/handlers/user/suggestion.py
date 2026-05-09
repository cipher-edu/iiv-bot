from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.filters.registered import IsRegisteredFilter
from bot.models.user import TelegramUser
from bot.repositories.suggestion_repo import SuggestionRepository
from bot.keyboards.user_reply import cancel_keyboard

router = Router(name="suggestion")
router.message.filter(IsRegisteredFilter())


class SuggestionState(StatesGroup):
    waiting_anonymous_choice = State()
    waiting_text = State()


@router.message(F.text == "✉️ Taklif")
async def suggestion_start(message: Message, state: FSMContext):
    await state.set_state(SuggestionState.waiting_anonymous_choice)
    builder = InlineKeyboardBuilder()
    builder.button(text="🕵️ Anonim yuborish", callback_data="sug:mode:anon")
    builder.button(text="👤 Ism bilan", callback_data="sug:mode:named")
    builder.adjust(1)
    await message.answer(
        "✉️ <b>Taklif / shikoyat</b>\n\n"
        "Sizning fikringiz super adminga yuboriladi.\n"
        "Qanday yuborasiz?",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(SuggestionState.waiting_anonymous_choice, F.data.startswith("sug:mode:"))
async def suggestion_mode(callback: CallbackQuery, state: FSMContext):
    is_anon = callback.data.endswith(":anon")
    await state.update_data(is_anonymous=is_anon)
    await state.set_state(SuggestionState.waiting_text)
    await callback.message.answer(
        "📝 Endi taklifingizni yozing:", reply_markup=cancel_keyboard()
    )
    await callback.answer()


@router.message(SuggestionState.waiting_text, F.text)
async def suggestion_save(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
    bot: Bot,
):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return

    text = message.text.strip()
    if len(text) < 5:
        await message.answer("❌ Taklif juda qisqa.")
        return

    data = await state.get_data()
    is_anon = data.get("is_anonymous", True)

    repo = SuggestionRepository(session)
    suggestion = await repo.create(
        user_id=None if is_anon else db_user.id,
        is_anonymous=is_anon,
        text=text,
    )
    await session.flush()

    sender = "Anonim" if is_anon else db_user.display_name
    notify_text = (
        f"✉️ <b>Yangi taklif (#{suggestion.id})</b>\n\n"
        f"From: {sender}\n\n{text}"
    )
    for sa_id in settings.bot_superadmin_ids:
        try:
            await bot.send_message(sa_id, notify_text)
        except Exception:
            pass

    await state.clear()
    await message.answer(
        "✅ Rahmat! Taklifingiz qabul qilindi va super adminga yuborildi."
    )
