from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.user_repo import UserRepository
from bot.keyboards.user_reply import main_menu_keyboard, phone_request_keyboard
from bot.states.registration import RegistrationState

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser | None = None,
):
    if db_user and db_user.is_registered:
        await state.clear()
        await message.answer(
            f"Assalomu alaykum, {db_user.display_name}! 👋\n\n"
            "Asosiy menyudan kerakli bo'limni tanlang:",
            reply_markup=main_menu_keyboard(is_admin=db_user.is_admin),
        )
        return

    if not db_user:
        repo = UserRepository(session)
        db_user = await repo.create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
        )

    await state.set_state(RegistrationState.waiting_phone)
    await message.answer(
        "🎓 <b>IIV Ta'lim platformasiga xush kelibsiz!</b>\n\n"
        "Tizimdan foydalanish uchun ro'yxatdan o'ting.\n\n"
        "📱 Telefon raqamingizni yuboring:",
        reply_markup=phone_request_keyboard(),
    )
