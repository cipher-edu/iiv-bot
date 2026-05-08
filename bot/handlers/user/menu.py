from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.models.user import TelegramUser
from bot.filters.registered import IsRegisteredFilter
from bot.keyboards.user_reply import main_menu_keyboard

router = Router(name="menu")
router.message.filter(IsRegisteredFilter())


@router.message(F.text == "⬅️ Orqaga")
async def back_to_menu(message: Message, state: FSMContext, db_user: TelegramUser):
    await state.clear()
    await message.answer(
        "Asosiy menyu:",
        reply_markup=main_menu_keyboard(is_admin=db_user.is_admin),
    )
