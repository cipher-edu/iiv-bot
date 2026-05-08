from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.survey_repo import SurveyRepository
from bot.states.admin_states import SurveyCreateState
from bot.keyboards.user_reply import cancel_keyboard

router = Router(name="admin_surveys")


@router.callback_query(F.data == "admin:surveys")
async def admin_surveys(callback: CallbackQuery, session: AsyncSession):
    repo = SurveyRepository(session)
    surveys = await repo.get_all(limit=20)

    text = "📊 <b>So'rovnomalar boshqaruvi</b>\n\n"
    for s in surveys:
        status = "✅" if s.is_active else "❌"
        text += f"{status} {s.title} (👥 {s.total_responses} javob)\n"

    if not surveys:
        text += "Hozircha so'rovnomalar yo'q."

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Yangi so'rovnoma", callback_data="admin:surveys:create")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:menu"))

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "admin:surveys:create")
async def create_survey_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SurveyCreateState.waiting_title)
    await callback.message.answer(
        "📊 <b>Yangi so'rovnoma yaratish</b>\n\nSarlavha kiriting:",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(SurveyCreateState.waiting_title, F.text)
async def survey_title(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return
    await state.update_data(title=message.text, questions_data=[])
    await state.set_state(SurveyCreateState.waiting_question_text)
    await message.answer("❓ 1-savol matnini kiriting:")


@router.message(SurveyCreateState.waiting_question_text, F.text)
async def survey_question(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return

    await state.update_data(current_q_text=message.text)
    await state.set_state(SurveyCreateState.waiting_question_type)

    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Matnli javob"), KeyboardButton(text="📋 Tanlov")]
        ],
        resize_keyboard=True,
    )
    await message.answer("Savol turini tanlang:", reply_markup=kb)


@router.message(SurveyCreateState.waiting_question_type, F.text)
async def survey_q_type(message: Message, state: FSMContext):
    if message.text == "📝 Matnli javob":
        data = await state.get_data()
        questions = data.get("questions_data", [])
        questions.append({
            "text": data["current_q_text"],
            "type": "text",
            "options": None,
        })
        await state.update_data(questions_data=questions)
        await state.set_state(SurveyCreateState.confirm_add_more)
        await message.answer("✅ Savol qo'shildi! Yana savol qo'shasizmi? (ha/yo'q)")
    elif message.text == "📋 Tanlov":
        await state.set_state(SurveyCreateState.waiting_question_options)
        await message.answer(
            "Variantlarni vergul bilan kiriting:\n"
            "Masalan: Yaxshi, O'rtacha, Yomon",
            reply_markup=cancel_keyboard(),
        )


@router.message(SurveyCreateState.waiting_question_options, F.text)
async def survey_options(message: Message, state: FSMContext):
    options = [o.strip() for o in message.text.split(",") if o.strip()]
    if len(options) < 2:
        await message.answer("❌ Kamida 2 ta variant kerak. Qayta kiriting:")
        return

    data = await state.get_data()
    questions = data.get("questions_data", [])
    questions.append({
        "text": data["current_q_text"],
        "type": "choice",
        "options": options,
    })
    await state.update_data(questions_data=questions)
    await state.set_state(SurveyCreateState.confirm_add_more)
    await message.answer("✅ Savol qo'shildi! Yana savol qo'shasizmi? (ha/yo'q)")


@router.message(SurveyCreateState.confirm_add_more, F.text)
async def more_survey_questions(
    message: Message, state: FSMContext, session: AsyncSession, db_user: TelegramUser
):
    if message.text.lower() in ("ha", "yes", "da"):
        data = await state.get_data()
        count = len(data.get("questions_data", []))
        await state.set_state(SurveyCreateState.waiting_question_text)
        await message.answer(f"❓ {count + 1}-savol matnini kiriting:")
    else:
        data = await state.get_data()
        repo = SurveyRepository(session)
        survey = await repo.create(
            title=data["title"],
            created_by=db_user.id,
            is_anonymous=True,
        )

        from bot.models.survey import SurveyQuestion
        for idx, q in enumerate(data.get("questions_data", [])):
            sq = SurveyQuestion(
                survey_id=survey.id,
                text=q["text"],
                question_type=q["type"],
                options=q.get("options"),
                order=idx + 1,
            )
            session.add(sq)

        await state.clear()
        await message.answer(
            f"✅ So'rovnoma yaratildi!\n"
            f"📊 {data['title']}\n"
            f"❓ Savollar: {len(data.get('questions_data', []))}"
        )
