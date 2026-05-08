from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.user_repo import UserRepository
from bot.repositories.audit_repo import AuditRepository
from bot.core.enums import Role, AuditAction

router = Router(name="sa_roles")


class AssignRoleState(StatesGroup):
    waiting_search = State()


@router.callback_query(F.data == "sa:roles")
async def roles_management(callback: CallbackQuery, session: AsyncSession):
    user_repo = UserRepository(session)
    admins = await user_repo.get_by_role(Role.ADMIN, limit=50)
    moderators = await user_repo.get_by_role(Role.MODERATOR, limit=50)

    text = "👥 <b>Rollar boshqaruvi</b>\n\n"

    text += f"🔴 <b>Adminlar ({len(admins)}):</b>\n"
    for a in admins:
        text += f"  👤 {a.display_name} (ID: {a.telegram_id})\n"

    text += f"\n🟡 <b>Moderatorlar ({len(moderators)}):</b>\n"
    for m in moderators:
        text += f"  👤 {m.display_name} (ID: {m.telegram_id})\n"

    if not admins and not moderators:
        text += "Hali admin/moderator tayinlanmagan.\n"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Admin tayinlash", callback_data="sa:roles:add_admin")
    builder.button(text="➕ Moderator tayinlash", callback_data="sa:roles:add_mod")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:superadmin"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("sa:roles:add_"))
async def start_role_assign(callback: CallbackQuery, state: FSMContext):
    role_type = callback.data.split("_")[-1]
    target_role = Role.ADMIN if role_type == "admin" else Role.MODERATOR
    await state.set_state(AssignRoleState.waiting_search)
    await state.update_data(target_role=target_role.value)
    await callback.message.answer("Foydalanuvchi ismini yoki Telegram ID kiriting:")
    await callback.answer()


@router.message(AssignRoleState.waiting_search, F.text)
async def search_for_role(
    message: Message, state: FSMContext, session: AsyncSession, db_user: TelegramUser
):
    user_repo = UserRepository(session)
    audit_repo = AuditRepository(session)

    try:
        tg_id = int(message.text)
        user = await user_repo.get_by_telegram_id(tg_id)
    except ValueError:
        users = await user_repo.search_users(message.text, limit=5)
        if not users:
            await message.answer("❌ Foydalanuvchi topilmadi.")
            return

        if len(users) == 1:
            user = users[0]
        else:
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            for u in users:
                builder.button(
                    text=u.display_name,
                    callback_data=f"sa:roles:select:{u.id}",
                )
            builder.adjust(1)
            await message.answer("Foydalanuvchini tanlang:", reply_markup=builder.as_markup())
            return

    if not user:
        await message.answer("❌ Foydalanuvchi topilmadi.")
        return

    data = await state.get_data()
    new_role = Role(data["target_role"])
    await user_repo.set_role(user.id, new_role)

    await audit_repo.log_action(
        action=AuditAction.ROLE_CHANGE,
        user_id=db_user.id,
        telegram_id=db_user.telegram_id,
        entity_type="user",
        entity_id=user.id,
        details={"new_role": new_role.value, "user_name": user.display_name},
    )

    await state.clear()
    await message.answer(
        f"✅ {user.display_name} ga {new_role.value} roli berildi."
    )


@router.callback_query(F.data.startswith("sa:roles:select:"))
async def select_user_for_role(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: TelegramUser
):
    user_id = int(callback.data.split(":")[-1])
    data = await state.get_data()
    new_role = Role(data["target_role"])

    user_repo = UserRepository(session)
    audit_repo = AuditRepository(session)

    user = await user_repo.get_by_id(user_id)
    if not user:
        await callback.answer("Foydalanuvchi topilmadi.", show_alert=True)
        return

    await user_repo.set_role(user.id, new_role)
    await audit_repo.log_action(
        action=AuditAction.ROLE_CHANGE,
        user_id=db_user.id,
        telegram_id=db_user.telegram_id,
        entity_type="user",
        entity_id=user.id,
        details={"new_role": new_role.value},
    )

    await state.clear()
    await callback.answer(
        f"✅ {user.display_name} → {new_role.value}", show_alert=True
    )
