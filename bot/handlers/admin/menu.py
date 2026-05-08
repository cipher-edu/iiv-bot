from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from bot.models.user import TelegramUser
from bot.keyboards.inline import admin_main_keyboard, superadmin_keyboard

router = Router(name="admin_menu")


@router.message(F.text == "⚙️ Admin panel")
@router.message(Command("admin"))
async def admin_panel(message: Message, db_user: TelegramUser):
    await message.answer(
        "⚙️ <b>Admin panel</b>\n\n"
        "Bo'limni tanlang:",
        reply_markup=admin_main_keyboard(),
    )


@router.callback_query(F.data == "admin:menu")
async def admin_menu_callback(callback: CallbackQuery, db_user: TelegramUser):
    await callback.message.edit_text(
        "⚙️ <b>Admin panel</b>\n\nBo'limni tanlang:",
        reply_markup=admin_main_keyboard(),
    )
    await callback.answer()


@router.message(Command("superadmin"))
async def superadmin_panel(message: Message, db_user: TelegramUser):
    if not db_user.is_superadmin:
        await message.answer("❌ Sizda bu huquq yo'q.")
        return
    await message.answer(
        "🔐 <b>Superadmin panel</b>\n\nBo'limni tanlang:",
        reply_markup=superadmin_keyboard(),
    )


@router.callback_query(F.data == "admin:superadmin")
async def superadmin_callback(callback: CallbackQuery, db_user: TelegramUser):
    if not db_user.is_superadmin:
        await callback.answer("Sizda bu huquq yo'q.", show_alert=True)
        return
    await callback.message.edit_text(
        "🔐 <b>Superadmin panel</b>\n\nBo'limni tanlang:",
        reply_markup=superadmin_keyboard(),
    )
    await callback.answer()
