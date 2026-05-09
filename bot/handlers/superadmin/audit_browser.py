from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.audit import AuditLog
from bot.models.user import TelegramUser

router = Router(name="sa_audit_browser")


PAGE_SIZE = 10


@router.callback_query(F.data == "sa:audit")
async def audit_main(callback: CallbackQuery, session: AsyncSession):
    await _show_page(callback, session, page=1, action_filter=None)


@router.callback_query(F.data.startswith("sa:audit:page:"))
async def audit_page(callback: CallbackQuery, session: AsyncSession):
    parts = callback.data.split(":")
    page = int(parts[3])
    action_filter = parts[4] if len(parts) > 4 else None
    await _show_page(callback, session, page=page, action_filter=action_filter)


@router.callback_query(F.data.startswith("sa:audit:filter:"))
async def audit_filter(callback: CallbackQuery, session: AsyncSession):
    action = callback.data.split(":")[-1]
    if action == "all":
        action = None
    await _show_page(callback, session, page=1, action_filter=action)


async def _show_page(
    callback: CallbackQuery,
    session: AsyncSession,
    page: int,
    action_filter: str | None,
):
    base_stmt = select(AuditLog).where(AuditLog.is_deleted == False)
    if action_filter:
        base_stmt = base_stmt.where(AuditLog.action == action_filter)

    count_stmt = select(func.count(AuditLog.id)).where(AuditLog.is_deleted == False)
    if action_filter:
        count_stmt = count_stmt.where(AuditLog.action == action_filter)
    total = (await session.execute(count_stmt)).scalar_one()

    offset = (page - 1) * PAGE_SIZE
    items_stmt = (
        base_stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(PAGE_SIZE)
    )
    items = (await session.execute(items_stmt)).scalars().all()

    text = (
        f"📋 <b>Audit log</b>\n"
        f"Filter: {action_filter or 'all'} | Jami: {total} | Sahifa: {page}\n\n"
    )

    user_cache: dict[int, str] = {}
    for log in items:
        actor = "—"
        if log.user_id:
            if log.user_id not in user_cache:
                u = (await session.execute(
                    select(TelegramUser).where(TelegramUser.id == log.user_id)
                )).scalar_one_or_none()
                user_cache[log.user_id] = u.display_name if u else f"#{log.user_id}"
            actor = user_cache[log.user_id]

        ts = log.created_at.strftime("%d.%m %H:%M")
        details_brief = ""
        if log.details:
            details_brief = " | " + ", ".join(
                f"{k}={v}" for k, v in list(log.details.items())[:2]
            )
        text += f"<b>{ts}</b> · {log.action} · {actor}{details_brief}\n"

    builder = InlineKeyboardBuilder()
    nav = []
    if page > 1:
        nav.append(
            InlineKeyboardButton(
                text="⬅️",
                callback_data=f"sa:audit:page:{page - 1}:{action_filter or ''}",
            )
        )
    nav.append(
        InlineKeyboardButton(
            text=f"{page}",
            callback_data="noop",
        )
    )
    if offset + PAGE_SIZE < total:
        nav.append(
            InlineKeyboardButton(
                text="➡️",
                callback_data=f"sa:audit:page:{page + 1}:{action_filter or ''}",
            )
        )
    builder.row(*nav)

    for action in ("all", "block", "unblock", "role_change", "broadcast", "login"):
        builder.button(
            text=f"⚙️ {action}", callback_data=f"sa:audit:filter:{action}"
        )
    builder.adjust(3)
    builder.row(
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:superadmin")
    )

    if callback.message:
        try:
            await callback.message.edit_text(text, reply_markup=builder.as_markup())
        except Exception:
            await callback.message.answer(text, reply_markup=builder.as_markup())
    await callback.answer()
