from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.api.service import account_on_start, finish_with_category, is_staff_role
from bot.keyboards.user_reply import main_menu_keyboard

router = Router(name="start")


def _category_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="🧑‍💼 Hodim", callback_data="cat:hodim"),
            InlineKeyboardButton(text="🧍 Fuqaro", callback_data="cat:fuqaro"),
        ]]
    )


def _telegram_payload(tg) -> dict:
    return {
        "id": tg.id,
        "first_name": tg.first_name or "",
        "last_name": tg.last_name or "",
        "username": tg.username,
    }


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
):
    tg = message.from_user
    if tg is None:
        return
    db_user, mode = await account_on_start(session, _telegram_payload(tg))
    await state.clear()
    if mode == "choose":
        await message.answer(
            f"Assalomu alaykum, {db_user.display_name}! 👋\n\n"
            "Davom etish uchun toifangizni tanlang:\n"
            "🧑‍💼 <b>Hodim</b> — tashkilot xodimi\n"
            "🧍 <b>Fuqaro</b> — oddiy foydalanuvchi",
            reply_markup=_category_keyboard(),
        )
        return
    staff = is_staff_role(str(db_user.role))
    title = "To'liq administrator" if staff else ("Hodim" if str(db_user.category) == "hodim" else "Fuqaro")
    await message.answer(
        f"Assalomu alaykum, {db_user.display_name}! 👋\n\n"
        f"Hisobingiz ochiq: <b>{title}</b>.\n"
        "Asosiy menyudan kerakli bo'limni tanlang:",
        reply_markup=main_menu_keyboard(is_admin=staff),
    )


@router.callback_query(F.data.in_({"cat:hodim", "cat:fuqaro"}))
async def choose_category(query: CallbackQuery, session: AsyncSession):
    tg = query.from_user
    category = (query.data or "cat:fuqaro").split(":", 1)[1]
    db_user, _mode = await account_on_start(session, _telegram_payload(tg))
    db_user = await finish_with_category(session, db_user, category)
    saved = str(db_user.category) if db_user.category else category
    label = "Hodim" if saved == "hodim" else "Fuqaro"
    await query.answer("Saqlandi")
    if query.message:
        await query.message.answer(
            f"Siz <b>{label}</b> sifatida ro'yxatdan o'tdingiz.",
            reply_markup=main_menu_keyboard(is_admin=is_staff_role(str(db_user.role))),
        )
