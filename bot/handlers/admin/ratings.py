from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.rating_repo import RatingRepository
from bot.repositories.user_repo import UserRepository
from bot.core.enums import PointReason

router = Router(name="admin_ratings")


class ManualPointsState(StatesGroup):
    waiting_user_search = State()
    waiting_points = State()
    waiting_reason = State()


@router.callback_query(F.data == "admin:ratings")
async def admin_ratings(callback: CallbackQuery, session: AsyncSession):
    repo = RatingRepository(session)
    top = await repo.get_leaderboard(limit=10)
    user_repo = UserRepository(session)

    text = "🏆 <b>Reyting boshqaruvi</b>\n\n"
    for idx, r in enumerate(top):
        user = await user_repo.get_by_id(r.user_id)
        name = user.display_name if user else f"#{r.user_id}"
        text += f"{idx+1}. {name} — {r.total_points} ball\n"

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Qo'lda ball berish", callback_data="admin:ratings:manual")
    builder.button(text="🔄 Haftalik reset", callback_data="admin:ratings:reset_weekly")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:menu"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "admin:ratings:manual")
async def manual_points_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ManualPointsState.waiting_user_search)
    await callback.message.answer("Foydalanuvchi ismini yoki ID sini kiriting:")
    await callback.answer()


@router.message(ManualPointsState.waiting_user_search, F.text)
async def search_user_for_points(message: Message, state: FSMContext, session: AsyncSession):
    user_repo = UserRepository(session)
    users = await user_repo.search_users(message.text, limit=5)

    if not users:
        await message.answer("Foydalanuvchi topilmadi. Qayta kiriting:")
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for u in users:
        builder.button(text=u.display_name, callback_data=f"admin:pt_user:{u.id}")
    builder.adjust(1)
    await message.answer("Foydalanuvchini tanlang:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("admin:pt_user:"))
async def select_user_for_points(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split(":")[-1])
    await state.update_data(target_user_id=user_id)
    await state.set_state(ManualPointsState.waiting_points)
    await callback.message.answer("Ball sonini kiriting (masalan: 10 yoki -5):")
    await callback.answer()


@router.message(ManualPointsState.waiting_points, F.text)
async def enter_points(message: Message, state: FSMContext):
    try:
        points = int(message.text)
    except ValueError:
        await message.answer("❌ Raqam kiriting:")
        return

    await state.update_data(points=points)
    await state.set_state(ManualPointsState.waiting_reason)
    await message.answer("Sabab/izoh kiriting:")


@router.message(ManualPointsState.waiting_reason, F.text)
async def submit_manual_points(
    message: Message, state: FSMContext, session: AsyncSession, db_user: TelegramUser
):
    data = await state.get_data()
    repo = RatingRepository(session)

    await repo.add_points(
        user_id=data["target_user_id"],
        points=data["points"],
        reason=PointReason.ADMIN_BONUS,
        description=message.text,
    )

    await state.clear()
    sign = "+" if data["points"] > 0 else ""
    await message.answer(f"✅ {sign}{data['points']} ball berildi.\nIzoh: {message.text}")


@router.callback_query(F.data == "admin:ratings:reset_weekly")
async def reset_weekly(callback: CallbackQuery, session: AsyncSession):
    repo = RatingRepository(session)
    await repo.reset_weekly_points()
    await callback.answer("✅ Haftalik ballar tozalandi.", show_alert=True)
