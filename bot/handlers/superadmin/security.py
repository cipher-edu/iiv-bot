from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.audit_repo import AuditRepository, SecurityEventRepository
from bot.core.enums import AuditAction

router = Router(name="sa_security")


@router.callback_query(F.data == "sa:security")
async def security_dashboard(callback: CallbackQuery, session: AsyncSession):
    sec_repo = SecurityEventRepository(session)
    audit_repo = AuditRepository(session)

    unresolved = await sec_repo.get_unresolved(limit=10)
    failed_auths = await audit_repo.get_by_action(AuditAction.FAILED_AUTH, limit=10)

    text = "🔐 <b>Xavfsizlik paneli</b>\n\n"

    text += f"⚠️ <b>Hal qilinmagan hodisalar: {len(unresolved)}</b>\n"
    for event in unresolved:
        text += (
            f"  [{event.severity.upper()}] {event.event_type}\n"
            f"  {event.description[:80]}\n"
            f"  📅 {event.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        )

    if not unresolved:
        text += "  ✅ Hammasi yaxshi!\n\n"

    text += f"🔑 <b>Oxirgi noto'g'ri kirishlar: {len(failed_auths)}</b>\n"
    for fa in failed_auths[:5]:
        text += f"  TG ID: {fa.telegram_id} | {fa.created_at.strftime('%d.%m %H:%M')}\n"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    if unresolved:
        builder.button(text="✅ Barchasini hal qilish", callback_data="sa:sec:resolve_all")
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:superadmin"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "sa:sec:resolve_all")
async def resolve_all_events(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    repo = SecurityEventRepository(session)
    unresolved = await repo.get_unresolved(limit=100)

    for event in unresolved:
        await repo.resolve_event(event.id, resolved_by=db_user.id, note="Bulk resolve")

    await callback.answer(f"✅ {len(unresolved)} ta hodisa hal qilindi.", show_alert=True)


@router.callback_query(F.data == "sa:audit")
async def audit_log(callback: CallbackQuery, session: AsyncSession):
    repo = AuditRepository(session)
    logs = await repo.get_recent(limit=30)

    text = "📋 <b>Audit Log</b>\n\n"
    for log in logs:
        time_str = log.created_at.strftime("%d.%m %H:%M")
        details = ""
        if log.details:
            details = str(log.details)[:50]
        text += f"[{time_str}] <code>{log.action}</code> uid={log.user_id} {details}\n"

    if not logs:
        text += "Loglar bo'sh."

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:superadmin"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()
