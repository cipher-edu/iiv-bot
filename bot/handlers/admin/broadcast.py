import asyncio

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.user_repo import UserRepository
from bot.repositories.news_repo import NewsRepository
from bot.repositories.audit_repo import AuditRepository
from bot.states.admin_states import BroadcastState
from bot.core.enums import AuditAction
from bot.keyboards.user_reply import cancel_keyboard
from bot.keyboards.inline import confirmation_keyboard

router = Router(name="admin_broadcast")


@router.callback_query(F.data == "admin:broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BroadcastState.waiting_message)
    await callback.message.answer(
        "📢 <b>Broadcast xabar</b>\n\n"
        "Barcha faol foydalanuvchilarga yuboriladigan xabarni kiriting:",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(BroadcastState.waiting_message, F.text)
async def broadcast_message_text(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Broadcast bekor qilindi.")
        return

    await state.update_data(broadcast_text=message.text)
    await state.set_state(BroadcastState.confirmation)
    await message.answer(
        f"📢 <b>Xabar ko'rinishi:</b>\n\n{message.text}\n\n"
        "Yuborishni tasdiqlaysizmi?",
        reply_markup=confirmation_keyboard("broadcast:confirm", "broadcast:cancel"),
    )


@router.callback_query(BroadcastState.confirmation, F.data == "broadcast:confirm")
async def confirm_broadcast(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
    bot: Bot,
):
    data = await state.get_data()
    text = data["broadcast_text"]
    await state.clear()

    user_repo = UserRepository(session)
    audit_repo = AuditRepository(session)
    all_ids = await user_repo.get_all_active_ids()

    await callback.message.edit_text(
        f"📢 Yuborilmoqda... (0/{len(all_ids)})"
    )

    sent = 0
    failed = 0
    for tg_id in all_ids:
        try:
            await bot.send_message(tg_id, f"📢 <b>Xabar</b>\n\n{text}")
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await audit_repo.log_action(
        action=AuditAction.BROADCAST,
        user_id=db_user.id,
        telegram_id=db_user.telegram_id,
        details={"sent": sent, "failed": failed, "total": len(all_ids)},
    )

    await callback.message.edit_text(
        f"✅ <b>Broadcast tugadi!</b>\n\n"
        f"📤 Yuborildi: {sent}\n"
        f"❌ Xatolik: {failed}\n"
        f"📊 Jami: {len(all_ids)}"
    )
    await callback.answer()


@router.callback_query(BroadcastState.confirmation, F.data == "broadcast:cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Broadcast bekor qilindi.")
    await callback.answer()
