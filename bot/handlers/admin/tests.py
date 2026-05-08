from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.test_repo import TestRepository
from bot.states.admin_states import TestCreateState
from bot.keyboards.user_reply import cancel_keyboard

router = Router(name="admin_tests")


@router.callback_query(F.data == "admin:tests")
async def admin_tests(callback: CallbackQuery, session: AsyncSession):
    repo = TestRepository(session)
    tests = await repo.get_all(limit=50)

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Yangi test", callback_data="admin:tests:create")
    builder.adjust(1)

    text = "📝 <b>Testlar boshqaruvi</b>\n\n"
    for t in tests:
        status = "✅" if t.is_active else "❌"
        text += f"{status} {t.title} ({t.question_count} savol)\n"

    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:menu"))
    await callback.message.edit_text(text or "Testlar yo'q.", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "admin:tests:create")
async def create_test_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TestCreateState.waiting_title)
    await callback.message.answer(
        "📝 <b>Yangi test yaratish</b>\n\n"
        "Test nomini kiriting:",
        reply_markup=cancel_keyboard(),
    )
    await callback.answer()


@router.message(TestCreateState.waiting_title, F.text)
async def create_test_title(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return

    await state.update_data(title=message.text)
    await state.set_state(TestCreateState.waiting_description)
    await message.answer("📋 Test tavsifini kiriting (yoki '-' bosing):")


@router.message(TestCreateState.waiting_description, F.text)
async def create_test_description(message: Message, state: FSMContext):
    desc = message.text if message.text != "-" else None
    await state.update_data(description=desc)
    await state.set_state(TestCreateState.waiting_time_per_question)
    await message.answer("⏱ Har bir savol uchun vaqt (soniyalarda, masalan: 30):")


@router.message(TestCreateState.waiting_time_per_question, F.text)
async def create_test_time(message: Message, state: FSMContext):
    try:
        time_val = int(message.text)
        if time_val < 5:
            await message.answer("❌ Minimal 5 soniya. Qayta kiriting:")
            return
    except ValueError:
        await message.answer("❌ Raqam kiriting:")
        return

    await state.update_data(time_per_question=time_val)
    await state.set_state(TestCreateState.waiting_passing_score)
    await message.answer("📊 O'tish balli (foizda, masalan: 70):")


@router.message(TestCreateState.waiting_passing_score, F.text)
async def create_test_score(message: Message, state: FSMContext, session: AsyncSession):
    try:
        score = int(message.text)
        if not 0 <= score <= 100:
            await message.answer("❌ 0 dan 100 gacha bo'lishi kerak:")
            return
    except ValueError:
        await message.answer("❌ Raqam kiriting:")
        return

    data = await state.get_data()
    repo = TestRepository(session)
    test = await repo.create(
        title=data["title"],
        description=data.get("description"),
        time_per_question=data["time_per_question"],
        passing_score=score,
    )

    await state.update_data(test_id=test.id, passing_score=score)
    await state.set_state(TestCreateState.waiting_question_text)
    await message.answer(
        f"✅ Test yaratildi: <b>{data['title']}</b>\n\n"
        f"Endi savollarni qo'shing.\n"
        f"1-savol matnini kiriting:"
    )


@router.message(TestCreateState.waiting_question_text, F.text)
async def add_question_text(message: Message, state: FSMContext, session: AsyncSession):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("✅ Test saqlandi.")
        return

    data = await state.get_data()
    repo = TestRepository(session)
    question_count = data.get("question_count", 0)

    question = await repo.create_question(
        test_id=data["test_id"],
        text=message.text,
        order=question_count + 1,
    )

    await state.update_data(
        current_question_id=question.id,
        question_count=question_count + 1,
        options_count=0,
    )
    await state.set_state(TestCreateState.waiting_options)
    await message.answer(
        "Javob variantlarini kiriting.\n"
        "Har bir variantni alohida xabarda yuboring.\n"
        "To'g'ri javobni * bilan belgilang (masalan: *Toshkent)\n\n"
        "Tayyor bo'lgach 'tayyor' deb yozing."
    )


@router.message(TestCreateState.waiting_options, F.text)
async def add_option(message: Message, state: FSMContext, session: AsyncSession):
    if message.text.lower() == "tayyor":
        data = await state.get_data()
        if data.get("options_count", 0) < 2:
            await message.answer("❌ Kamida 2 ta variant kerak.")
            return
        await state.set_state(TestCreateState.confirm_add_more)
        await message.answer(
            "✅ Savol saqlandi!\n\n"
            "Yana savol qo'shasizmi? (ha/yo'q)"
        )
        return

    data = await state.get_data()
    repo = TestRepository(session)

    text = message.text
    is_correct = text.startswith("*")
    if is_correct:
        text = text[1:].strip()

    options_count = data.get("options_count", 0)
    await repo.create_option(
        question_id=data["current_question_id"],
        text=text,
        is_correct=is_correct,
        order=options_count + 1,
    )
    await state.update_data(options_count=options_count + 1)

    mark = "✅ (to'g'ri)" if is_correct else ""
    await message.answer(f"Variant qo'shildi: {text} {mark}")


@router.message(TestCreateState.confirm_add_more, F.text)
async def confirm_more_questions(message: Message, state: FSMContext):
    if message.text.lower() in ("ha", "yes", "da"):
        data = await state.get_data()
        count = data.get("question_count", 0)
        await state.set_state(TestCreateState.waiting_question_text)
        await message.answer(f"{count + 1}-savol matnini kiriting:")
    else:
        data = await state.get_data()
        await state.clear()
        await message.answer(
            f"✅ Test muvaffaqiyatli yaratildi!\n"
            f"📝 {data.get('title')}\n"
            f"❓ Savollar soni: {data.get('question_count', 0)}"
        )
