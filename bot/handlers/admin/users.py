from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.user_repo import UserRepository
from bot.repositories.audit_repo import AuditRepository
from bot.states.admin_states import UserManageState
from bot.core.enums import Role, AuditAction
from bot.keyboards.inline import paginated_keyboard, confirmation_keyboard

router = Router(name="admin_users")


@router.callback_query(F.data == "admin:users")
async def admin_users(callback: CallbackQuery, session: AsyncSession):
    repo = UserRepository(session)
    users = await repo.get_active_users(limit=50)

    items = [
        (f"👤 {u.display_name}", f"admin:user:{u.id}")
        for u in users
    ]

    from math import ceil
    from bot.config import settings
    total_pages = ceil(len(items) / settings.pagination_size) or 1
    page_items = items[: settings.pagination_size]

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Qidirish", callback_data="admin:users:search")
    builder.adjust(1)

    await callback.message.edit_text(
        "👥 <b>Foydalanuvchilar boshqaruvi</b>\n\n"
        f"Jami: {len(items)} ta foydalanuvchi",
        reply_markup=paginated_keyboard(
            page_items,
            page=1,
            total_pages=total_pages,
            prefix="admin_users",
            back_button="admin:menu",
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:user:"))
async def view_user(callback: CallbackQuery, session: AsyncSession):
    user_id = int(callback.data.split(":")[-1])
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)

    if not user:
        await callback.answer("Foydalanuvchi topilmadi.", show_alert=True)
        return

    text = (
        f"👤 <b>{user.display_name}</b>\n\n"
        f"🆔 Telegram ID: {user.telegram_id}\n"
        f"📱 Telefon: {user.phone or '—'}\n"
        f"💼 Lavozim: {user.position or '—'}\n"
        f"🏢 Tashkilot: {user.organization.name if user.organization else '—'}\n"
        f"🎭 Rol: {user.role}\n"
        f"📊 Status: {user.status}\n"
        f"📅 Ro'yxatdan: {user.created_at.strftime('%d.%m.%Y')}\n"
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()

    if not user.is_blocked:
        builder.button(text="🚫 Bloklash", callback_data=f"admin:block:{user.id}")
    else:
        builder.button(text="✅ Blokdan chiqarish", callback_data=f"admin:unblock:{user.id}")

    builder.button(text="🎭 Rol o'zgartirish", callback_data=f"admin:role:{user.id}")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:users"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("admin:block:"))
async def block_user_start(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession
):
    user_id = int(callback.data.split(":")[-1])
    await state.set_state(UserManageState.waiting_block_reason)
    await state.update_data(target_user_id=user_id)
    await callback.message.answer("🚫 Bloklash sababini kiriting:")
    await callback.answer()


@router.message(UserManageState.waiting_block_reason, F.text)
async def block_user_confirm(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
):
    data = await state.get_data()
    target_id = data["target_user_id"]
    reason = message.text

    repo = UserRepository(session)
    audit_repo = AuditRepository(session)

    await repo.block_user(target_id, reason=reason)
    await audit_repo.log_action(
        action=AuditAction.BLOCK,
        user_id=db_user.id,
        telegram_id=db_user.telegram_id,
        entity_type="user",
        entity_id=target_id,
        details={"reason": reason},
    )

    await state.clear()
    await message.answer(f"✅ Foydalanuvchi bloklandi.\nSabab: {reason}")


@router.callback_query(F.data.startswith("admin:unblock:"))
async def unblock_user(
    callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser
):
    user_id = int(callback.data.split(":")[-1])
    repo = UserRepository(session)
    audit_repo = AuditRepository(session)

    await repo.unblock_user(user_id)
    await audit_repo.log_action(
        action=AuditAction.UNBLOCK,
        user_id=db_user.id,
        telegram_id=db_user.telegram_id,
        entity_type="user",
        entity_id=user_id,
    )

    await callback.answer("✅ Foydalanuvchi blokdan chiqarildi.", show_alert=True)
    await view_user(callback, session)


@router.callback_query(F.data.startswith("admin:role:"))
async def change_role(callback: CallbackQuery, session: AsyncSession):
    user_id = int(callback.data.split(":")[-1])

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for role in [Role.USER, Role.MODERATOR, Role.ADMIN]:
        builder.button(
            text=f"🎭 {role.value.capitalize()}",
            callback_data=f"admin:setrole:{user_id}:{role.value}",
        )
    builder.adjust(1)

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
