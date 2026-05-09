from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.user_repo import UserRepository
from bot.repositories.audit_repo import AuditRepository
from bot.states.admin_states import BroadcastState
from bot.core.enums import AuditAction
from bot.core.broadcast_queue import (
    BroadcastJob,
    get_broadcast_queue,
)
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
    all_ids = list(await user_repo.get_all_active_ids())

    status_message = await callback.message.edit_text(
        f"📢 Navbatga qo'shildi: {len(all_ids)} ta foydalanuvchi.\n"
        "Yuborish fonda davom etmoqda..."
    )

    chat_id_for_status = callback.from_user.id

    async def on_progress(job: BroadcastJob) -> None:
        done = job.sent + job.failed + job.blocked
        try:
            await bot.edit_message_text(
                f"📢 Yuborilmoqda... {done}/{len(job.chat_ids)}\n"
                f"✅ {job.sent} | 🚫 {job.blocked} | ❌ {job.failed}",
                chat_id=chat_id_for_status,
                message_id=status_message.message_id,
            )
        except Exception:
            pass

    async def on_done(job: BroadcastJob) -> None:
        try:
            await audit_repo.log_action(
                action=AuditAction.BROADCAST,
                user_id=db_user.id,
                telegram_id=db_user.telegram_id,
                details={
                    "sent": job.sent,
                    "failed": job.failed,
                    "blocked": job.blocked,
                    "total": len(job.chat_ids),
                },
            )
            await session.commit()
        except Exception:
            pass
        try:
            await bot.send_message(
                chat_id_for_status,
                f"✅ <b>Broadcast tugadi!</b>\n\n"
                f"📤 Yuborildi: {job.sent}\n"
                f"🚫 Bloklagan: {job.blocked}\n"
                f"❌ Xato: {job.failed}\n"
                f"📊 Jami: {len(job.chat_ids)}",
            )
        except Exception:
            pass

    queue = get_broadcast_queue()
    queue.submit(
        BroadcastJob(
            job_id=0,
            chat_ids=all_ids,
            text=f"📢 <b>Xabar</b>\n\n{text}",
            on_progress=on_progress,
            on_done=on_done,
        )
    )

    await callback.answer("✅ Navbatga qo'shildi.", show_alert=False)


@router.callback_query(BroadcastState.confirmation, F.data == "broadcast:cancel")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Broadcast bekor qilindi.")
    await callback.answer()
