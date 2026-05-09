from datetime import date, timedelta
from calendar import monthrange

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.filters.registered import IsRegisteredFilter
from bot.models.user import TelegramUser
from bot.models.goal import UserGoal

router = Router(name="goals")
router.message.filter(IsRegisteredFilter())


GOAL_TYPES = {
    "courses": "📚 Kurs tugatish",
    "tests": "📝 Test topshirish",
    "lessons": "📖 Dars o'qish",
    "points": "🏆 Ball to'plash",
}


PERIODS = {
    "week": ("Hafta", 7),
    "month": ("Oy", 30),
}


class GoalState(StatesGroup):
    waiting_target = State()


def _period_dates(period: str) -> tuple[date, date]:
    today = date.today()
    if period == "week":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
    else:
        start = today.replace(day=1)
        last_day = monthrange(today.year, today.month)[1]
        end = today.replace(day=last_day)
    return start, end


@router.message(F.text == "🎯 Maqsadlar")
async def goals_menu(
    message: Message, session: AsyncSession, db_user: TelegramUser
):
    today = date.today()
    stmt = select(UserGoal).where(
        UserGoal.user_id == db_user.id,
        UserGoal.is_deleted == False,
        UserGoal.period_end >= today,
    )
    goals = (await session.execute(stmt)).scalars().all()

    text = "🎯 <b>Sizning maqsadlaringiz</b>\n\n"
    if not goals:
        text += "Hozircha maqsad qo'ymagansiz."
    else:
        for g in goals:
            label = GOAL_TYPES.get(g.goal_type, g.goal_type)
            period_label = PERIODS.get(g.period, (g.period,))[0]
            done = "✅" if g.is_completed else "🔄"
            text += (
                f"{done} {label} ({period_label}): "
                f"{g.progress}/{g.target}\n"
            )

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Yangi maqsad", callback_data="goal:add")
    builder.adjust(1)

    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "goal:add")
async def add_goal_start(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    for code, label in GOAL_TYPES.items():
        builder.button(text=label, callback_data=f"goal:type:{code}")
    builder.adjust(1)
    await callback.message.answer(
        "🎯 Maqsad turini tanlang:", reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("goal:type:"))
async def goal_type_chosen(callback: CallbackQuery, state: FSMContext):
    goal_type = callback.data.split(":")[-1]
    await state.update_data(goal_type=goal_type)
    builder = InlineKeyboardBuilder()
    for code, (label, _) in PERIODS.items():
        builder.button(text=label, callback_data=f"goal:period:{code}")
    builder.adjust(1)
    await callback.message.answer(
        "📅 Qaysi davr uchun?", reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("goal:period:"))
async def goal_period_chosen(callback: CallbackQuery, state: FSMContext):
    period = callback.data.split(":")[-1]
    await state.update_data(period=period)
    await state.set_state(GoalState.waiting_target)
    await callback.message.answer("🔢 Maqsad miqdorini kiriting (raqam):")
    await callback.answer()


@router.message(GoalState.waiting_target, F.text)
async def goal_target_save(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
):
    try:
        target = int(message.text.strip())
        if target < 1 or target > 9999:
            raise ValueError
    except ValueError:
        await message.answer("❌ Iltimos, 1-9999 oralig'idagi raqam kiriting.")
        return

    data = await state.get_data()
    period = data["period"]
    start, end = _period_dates(period)

    goal = UserGoal(
        user_id=db_user.id,
        goal_type=data["goal_type"],
        target=target,
        period=period,
        period_start=start,
        period_end=end,
    )
    session.add(goal)
    await session.flush()
    await state.clear()

    label = GOAL_TYPES.get(data["goal_type"], data["goal_type"])
    period_label = PERIODS.get(period, (period,))[0]
    await message.answer(
        f"✅ Maqsad o'rnatildi!\n\n"
        f"{label} — {target} ta ({period_label})"
    )
