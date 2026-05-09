from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser, Organization
from bot.models.rating import UserRating
from bot.repositories.user_repo import UserRepository, OrganizationRepository
from bot.repositories.audit_repo import AuditRepository
from bot.core.broadcast_queue import BroadcastJob, get_broadcast_queue
from bot.core.enums import Role, UserStatus, AuditAction, UserCategory

router = Router(name="admin_broadcast_segments")


class SegmentBroadcastState(StatesGroup):
    choosing_segment = State()
    waiting_message = State()


@router.callback_query(F.data == "admin:broadcast:segment")
async def start_segment_broadcast(callback: CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.button(text="🌐 Hammaga", callback_data="seg:all")
    builder.button(text="🧑‍💼 Faqat Hodimlar", callback_data="seg:hodim")
    builder.button(text="🧍 Faqat Fuqarolar", callback_data="seg:fuqaro")
    builder.button(text="🎭 Adminlar", callback_data="seg:admin")
    builder.button(text="🏢 Tashkilot bo'yicha", callback_data="seg:org_pick")
    builder.button(text="🏆 100+ ball egalari", callback_data="seg:high_score")
    builder.adjust(1)
    await callback.message.answer(
        "🎯 <b>Segment tanlang:</b>", reply_markup=builder.as_markup()
    )
    await state.set_state(SegmentBroadcastState.choosing_segment)
    await callback.answer()


@router.callback_query(SegmentBroadcastState.choosing_segment, F.data.startswith("seg:org_pick"))
async def pick_org(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    org_repo = OrganizationRepository(session)
    orgs = await org_repo.get_active_all()
    if not orgs:
        await callback.answer("Tashkilotlar yo'q.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    for o in orgs:
        builder.button(text=o.name, callback_data=f"seg:org:{o.id}")
    builder.adjust(1)
    await callback.message.answer("Tashkilot tanlang:", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(SegmentBroadcastState.choosing_segment, F.data.startswith("seg:"))
async def chose_segment(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    code = callback.data[len("seg:") :]
    if code == "org_pick":
        return  # handled above

    chat_ids = await _resolve_segment(session, code)
    if not chat_ids:
        await callback.answer("❌ Bu segmentda foydalanuvchi yo'q.", show_alert=True)
        return

    await state.update_data(chat_ids=chat_ids, segment=code)
    await state.set_state(SegmentBroadcastState.waiting_message)
    await callback.message.answer(
        f"📢 Topildi: {len(chat_ids)} ta foydalanuvchi.\n\n"
        f"Endi xabar matnini kiriting:"
    )
    await callback.answer()


async def _resolve_segment(session: AsyncSession, code: str) -> list[int]:
    base = select(TelegramUser.telegram_id).where(
        TelegramUser.is_deleted == False,
        TelegramUser.is_blocked == False,
        TelegramUser.status == UserStatus.ACTIVE,
    )

    if code == "all":
        stmt = base
    elif code == "hodim":
        stmt = base.where(TelegramUser.category == UserCategory.HODIM)
    elif code == "fuqaro":
        stmt = base.where(TelegramUser.category == UserCategory.FUQARO)
    elif code == "admin":
        stmt = base.where(
            TelegramUser.role.in_([Role.ADMIN, Role.SUPERADMIN, Role.MODERATOR])
        )
    elif code.startswith("org:"):
        org_id = int(code.split(":")[-1])
        stmt = base.where(TelegramUser.organization_id == org_id)
    elif code == "high_score":
        sub = select(UserRating.user_id).where(UserRating.total_points >= 100)
        stmt = base.where(TelegramUser.id.in_(sub))
    else:
        return []

    result = await session.execute(stmt)
    return [r for r in result.scalars().all()]


@router.message(SegmentBroadcastState.waiting_message, F.text)
async def send_segment_broadcast(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
    bot: Bot,
):
    data = await state.get_data()
    chat_ids = data["chat_ids"]
    text = message.text
    await state.clear()

    audit_repo = AuditRepository(session)
    await audit_repo.log_action(
        action=AuditAction.BROADCAST,
        user_id=db_user.id,
        telegram_id=db_user.telegram_id,
        details={"segment": data["segment"], "size": len(chat_ids)},
    )

    queue = get_broadcast_queue()
    queue.submit(
        BroadcastJob(
            job_id=0,
            chat_ids=chat_ids,
            text=f"📢 <b>Xabar</b>\n\n{text}",
        )
    )
    await message.answer(
        f"✅ Navbatga qo'shildi: {len(chat_ids)} ta foydalanuvchi."
    )
