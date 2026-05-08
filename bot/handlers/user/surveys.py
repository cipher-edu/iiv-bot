from math import ceil

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.filters.registered import IsRegisteredFilter
from bot.repositories.survey_repo import SurveyRepository
from bot.keyboards.inline import paginated_keyboard
from bot.keyboards.user_reply import back_keyboard
from bot.config import settings

router = Router(name="user_surveys")
router.message.filter(IsRegisteredFilter())


class SurveyFillState(StatesGroup):
    answering = State()


@router.message(F.text == "📊 So'rovnomalar")
async def show_surveys(message: Message, session: AsyncSession, db_user: TelegramUser):
    repo = SurveyRepository(session)
    surveys = await repo.get_active_surveys(limit=20)

    if not surveys:
        await message.answer("Hozircha faol so'rovnomalar yo'q.", reply_markup=back_keyboard())
        return

    items = []
    for s in surveys:
        responded = await repo.has_responded(s.id, db_user.id)
        icon = "✅" if responded else "📊"
        items.append((f"{icon} {s.title}", f"survey:view:{s.id}"))

    total_pages = ceil(len(items) / settings.pagination_size) or 1

    await message.answer(
        "📊 <b>So'rovnomalar:</b>",
        reply_markup=paginated_keyboard(
            items[: settings.pagination_size], page=1,
            total_pages=total_pages, prefix="surveys",
        ),
    )


@router.callback_query(F.data.startswith("survey:view:"))
async def view_survey(callback: CallbackQuery, session: AsyncSession, db_user: TelegramUser):
    survey_id = int(callback.data.split(":")[-1])
    repo = SurveyRepository(session)
    survey = await repo.get_with_questions(survey_id)

    if not survey:
        await callback.answer("So'rovnoma topilmadi.", show_alert=True)
        return

    responded = await repo.has_responded(survey_id, db_user.id)

    text = (
        f"📊 <b>{survey.title}</b>\n\n"
        f"{survey.description or ''}\n\n"
        f"❓ Savollar: {len(survey.questions)}\n"
        f"👥 Javoblar: {survey.total_responses}\n"
        f"{'🔒 Anonim' if survey.is_anonymous else '👤 Ochiq'}\n"
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()

    if responded:
        text += "\n✅ Siz allaqachon javob bergansiz."
    else:
        builder.button(text="📝 Javob berish", callback_data=f"survey:start:{survey.id}")

    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="survey:list"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("survey:start:"))
async def start_survey(
    callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: TelegramUser
):
    survey_id = int(callback.data.split(":")[-1])
    repo = SurveyRepository(session)
    survey = await repo.get_with_questions(survey_id)

    if not survey or not survey.questions:
        await callback.answer("So'rovnoma topilmadi.", show_alert=True)
        return

    await state.set_state(SurveyFillState.answering)
    await state.update_data(
        survey_id=survey.id,
        question_index=0,
        answers={},
        questions=[{"id": q.id, "text": q.text, "type": q.question_type, "options": q.options} for q in survey.questions],
    )

    await callback.answer()
    await send_survey_question(callback.message, state, 0)


async def send_survey_question(message: Message, state: FSMContext, index: int):
    data = await state.get_data()
    questions = data["questions"]

    if index >= len(questions):
        from bot.models.base import async_session_factory
        async with async_session_factory() as session:
            async with session.begin():
                repo = SurveyRepository(session)
                user_id = data.get("user_id")
                await repo.submit_response(data["survey_id"], user_id, data["answers"])
                await session.commit()

        await state.clear()
        await message.answer("✅ Javoblaringiz qabul qilindi! Rahmat.", reply_markup=back_keyboard())
        return

    q = questions[index]
    text = f"❓ <b>Savol {index + 1}/{len(questions)}</b>\n\n{q['text']}"

    if q["type"] == "choice" and q.get("options"):
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        for opt in q["options"]:
            builder.button(text=opt, callback_data=f"survey:ans:{index}:{opt[:30]}")
        builder.adjust(1)
        await message.answer(text, reply_markup=builder.as_markup())
    else:
        await message.answer(text)


@router.callback_query(SurveyFillState.answering, F.data.startswith("survey:ans:"))
async def process_choice_answer(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":", 3)
    index = int(parts[2])
    answer = parts[3]

    data = await state.get_data()
    answers = data["answers"]
    answers[str(data["questions"][index]["id"])] = answer
    await state.update_data(answers=answers, question_index=index + 1)

    await callback.answer()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await send_survey_question(callback.message, state, index + 1)


@router.message(SurveyFillState.answering, F.text)
async def process_text_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    index = data["question_index"]
    answers = data["answers"]
    answers[str(data["questions"][index]["id"])] = message.text
    await state.update_data(answers=answers, question_index=index + 1)

    await send_survey_question(message, state, index + 1)
