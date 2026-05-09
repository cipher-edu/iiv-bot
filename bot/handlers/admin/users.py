from datetime import datetime, timedelta, timezone
from math import ceil

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.models.user import TelegramUser
from bot.repositories.user_repo import UserRepository
from bot.repositories.audit_repo import AuditRepository
from bot.states.admin_states import UserManageState
from bot.core.enums import Role, AuditAction, UserStatus
from bot.keyboards.inline import paginated_keyboard

router = Router(name="admin_users")


BLOCK_DURATIONS = {
    "1h": ("1 soat", timedelta(hours=1)),
    "1d": ("1 kun", timedelta(days=1)),
    "7d": ("7 kun", timedelta(days=7)),
    "30d": ("30 kun", timedelta(days=30)),
    "perm": ("Muddatsiz", None),
}


@router.callback_query(F.data == "admin:users")
async def admin_users(callback: CallbackQuery, session: AsyncSession):
    repo = UserRepository(session)
    users = await repo.get_active_users(limit=settings.pagination_size)
    blocked_count = await repo.count_blocked()
    active_count = await repo.count(status=UserStatus.ACTIVE)

    builder = InlineKeyboardBuilder()
    for u in users:
        builder.button(
            text=f"👤 {u.display_name}", callback_data=f"admin:user:{u.id}"
        )
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="🔍 Qidirish", callback_data="admin:users:search"),
        InlineKeyboardButton(
            text=f"🚫 Bloklanganlar ({blocked_count})",
            callback_data="admin:users:blocked",
        ),
    )
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:menu"))

    await callback.message.edit_text(
        "👥 <b>Foydalanuvchilar boshqaruvi</b>\n\n"
        f"Faol: {active_count} | Bloklangan: {blocked_count}",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:users:blocked")
async def list_blocked_users(callback: CallbackQuery, session: AsyncSession):
    repo = UserRepository(session)
    users = await repo.get_blocked_users(limit=50)

    if not users:
        builder = InlineKeyboardBuilder()
        builder.button(text="⬅️ Orqaga", callback_data="admin:users")
        await callback.message.edit_text(
            "🚫 <b>Bloklangan foydalanuvchilar</b>\n\nHech kim bloklanmagan.",
            reply_markup=builder.as_markup(),
        )
        await callback.answer()
        return

    text = "🚫 <b>Bloklangan foydalanuvchilar</b>\n\n"
    builder = InlineKeyboardBuilder()
    for u in users:
        until = (
            u.blocked_until.strftime("%d.%m.%Y %H:%M")
            if u.blocked_until
            else "muddatsiz"
        )
        text += f"• {u.display_name} — {until}\n"
        builder.button(
            text=f"👤 {u.display_name}", callback_data=f"admin:user:{u.id}"
        )
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:users"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "admin:users:search")
async def start_user_search(callback: CallbackQuery, state: FSMContext):
    await state.set_state(UserManageState.waiting_search)
    await callback.message.answer(
        "🔍 Foydalanuvchi ismini, telefon yoki Telegram ID kiriting:"
    )
    await callback.answer()


@router.message(UserManageState.waiting_search, F.text)
async def search_users(
    message: Message, state: FSMContext, session: AsyncSession
):
    repo = UserRepository(session)
    query = message.text.strip()

    user = None
    try:
        tg_id = int(query)
        user = await repo.get_by_telegram_id(tg_id)
    except ValueError:
        pass

    users = []
    if user:
        users = [user]
    else:
        users = list(await repo.search_users(query, limit=20))

    if not users:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return

    await state.clear()
    builder = InlineKeyboardBuilder()
    for u in users:
        builder.button(text=f"👤 {u.display_name}", callback_data=f"admin:user:{u.id}")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:users"))

    await message.answer(
        f"Topildi: {len(users)} ta", reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("admin:user:"))
async def view_user(callback: CallbackQuery, session: AsyncSession):
    user_id = int(callback.data.split(":")[-1])
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)

    if not user:
        await callback.answer("Foydalanuvchi topilmadi.", show_alert=True)
        return

    blocked_info = ""
    if user.is_blocked:
        until = (
            user.blocked_until.strftime("%d.%m.%Y %H:%M")
            if user.blocked_until
            else "muddatsiz"
        )
        blocked_info = (
            f"\n🚫 <b>Bloklangan</b>\n"
            f"Sabab: {user.block_reason or '—'}\n"
            f"Muddati: {until}\n"
        )

    text = (
        f"👤 <b>{user.display_name}</b>\n\n"
        f"🆔 Telegram ID: <code>{user.telegram_id}</code>\n"
        f"📱 Telefon: {user.phone or '—'}\n"
        f"🧭 Toifa: {user.category or '—'}\n"
        f"💼 Lavozim: {user.position or '—'}\n"
        f"🏢 Tashkilot: {user.organization.name if user.organization else '—'}\n"
        f"🎭 Rol: {user.role}\n"
        f"📊 Status: {user.status}\n"
        f"📅 Ro'yxatdan: {user.created_at.strftime('%d.%m.%Y')}"
        f"{blocked_info}"
    )

    builder = InlineKeyboardBuilder()
    if not user.is_blocked:
        builder.button(text="🚫 Bloklash", callback_data=f"admin:block:{user.id}")
    else:
        builder.button(
            text="✅ Blokdan chiqarish", callback_data=f"admin:unblock:{user.id}"
        )

    if user.role != Role.SUPERADMIN:
        builder.button(
            text="🎭 Rol o'zgartirish", callback_data=f"admin:role:{user.id}"
        )
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:users"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:block:"))
async def block_user_start(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    user_id = int(callback.data.split(":")[-1])
    repo = UserRepository(session)
    target = await repo.get_by_id(user_id)
    if not target:
        await callback.answer("Foydalanuvchi topilmadi.", show_alert=True)
        return
    if target.role == Role.SUPERADMIN:
        await callback.answer("Superadmin bloklanmaydi.", show_alert=True)
        return

    await state.set_state(UserManageState.waiting_block_reason)
    await state.update_data(target_user_id=user_id)
    await callback.message.answer("✍️ Bloklash sababini kiriting:")
    await callback.answer()


@router.message(UserManageState.waiting_block_reason, F.text)
async def block_user_reason(
    message: Message, state: FSMContext
):
    reason = message.text.strip()
    if len(reason) < 3:
        await message.answer("❌ Sabab juda qisqa.")
        return

    await state.update_data(block_reason=reason)
    await state.set_state(UserManageState.waiting_block_duration)

    builder = InlineKeyboardBuilder()
    for code, (label, _) in BLOCK_DURATIONS.items():
        builder.button(text=label, callback_data=f"admin:blockdur:{code}")
    builder.adjust(2)

    await message.answer(
        "⏱ Bloklash muddatini tanlang:", reply_markup=builder.as_markup()
    )


@router.callback_query(
    UserManageState.waiting_block_duration, F.data.startswith("admin:blockdur:")
)
async def block_user_finalize(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
    bot: Bot,
):
    code = callback.data.split(":")[-1]
    if code not in BLOCK_DURATIONS:
        await callback.answer("Noma'lum muddat.", show_alert=True)
        return

    label, delta = BLOCK_DURATIONS[code]
    blocked_until = datetime.now(timezone.utc) + delta if delta else None

    data = await state.get_data()
    target_id = data["target_user_id"]
    reason = data["block_reason"]

    repo = UserRepository(session)
    audit_repo = AuditRepository(session)
    target = await repo.get_by_id(target_id)
    if not target:
        await callback.answer("Foydalanuvchi topilmadi.", show_alert=True)
        await state.clear()
        return

    await repo.block_user(target_id, reason=reason, blocked_until=blocked_until)
    await audit_repo.log_action(
        action=AuditAction.BLOCK,
        user_id=db_user.id,
        telegram_id=db_user.telegram_id,
        entity_type="user",
        entity_id=target_id,
        details={"reason": reason, "duration": label},
    )

    try:
        until_text = (
            f"Muddati: {blocked_until.strftime('%d.%m.%Y %H:%M')}"
            if blocked_until
            else "Muddati: muddatsiz"
        )
        await bot.send_message(
            target.telegram_id,
            "🚫 <b>Sizning hisobingiz bloklandi</b>\n\n"
            f"Sabab: {reason}\n{until_text}",
        )
    except Exception:
        pass

    await state.clear()
    await callback.message.answer(
        f"✅ {target.display_name} bloklandi ({label}).\nSabab: {reason}"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:unblock:"))
async def unblock_user(
    callback: CallbackQuery,
    session: AsyncSession,
    db_user: TelegramUser,
    bot: Bot,
):
    user_id = int(callback.data.split(":")[-1])
    repo = UserRepository(session)
    audit_repo = AuditRepository(session)

    target = await repo.get_by_id(user_id)
    await repo.unblock_user(user_id)
    await audit_repo.log_action(
        action=AuditAction.UNBLOCK,
        user_id=db_user.id,
        telegram_id=db_user.telegram_id,
        entity_type="user",
        entity_id=user_id,
    )

    if target:
        try:
            await bot.send_message(
                target.telegram_id,
                "✅ Sizning hisobingiz blokdan chiqarildi. Bot bilan ishlashni davom ettirishingiz mumkin.",
            )
        except Exception:
            pass

    await callback.answer("✅ Foydalanuvchi blokdan chiqarildi.", show_alert=True)
    await view_user(callback, session)


@router.callback_query(F.data.startswith("admin:role:"))
async def change_role(callback: CallbackQuery, session: AsyncSession):
    user_id = int(callback.data.split(":")[-1])

    builder = InlineKeyboardBuilder()
    for role in [Role.USER, Role.MODERATOR, Role.ADMIN]:
        builder.button(
            text=f"🎭 {role.value.capitalize()}",
            callback_data=f"admin:setrole:{user_id}:{role.value}",
        )
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"admin:user:{user_id}")
    )

    await callback.message.edit_text(
        "🎭 Yangi rolni tanlang:", reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:setrole:"))
async def set_role(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    parts = callback.data.split(":")
    user_id = int(parts[2])
    new_role = Role(parts[3])

    repo = UserRepository(session)
    audit_repo = AuditRepository(session)

    target = await repo.get_by_id(user_id)
    if target and target.role == Role.SUPERADMIN:
        await callback.answer(
            "Superadmin rolini o'zgartirib bo'lmaydi.", show_alert=True
        )
        return

    await repo.set_role(user_id, new_role)
    await audit_repo.log_action(
        action=AuditAction.ROLE_CHANGE,
        user_id=db_user.id,
        telegram_id=db_user.telegram_id,
        entity_type="user",
        entity_id=user_id,
        details={"new_role": new_role.value},
    )

    await callback.answer(
        f"✅ Rol o'zgartirildi: {new_role.value}", show_alert=True
    )
