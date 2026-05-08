import random
from math import ceil

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.filters.registered import IsRegisteredFilter
from bot.repositories.test_repo import TestRepository, TestSessionRepository, TestResultRepository
from bot.repositories.rating_repo import RatingRepository
from bot.keyboards.inline import paginated_keyboard, test_options_keyboard
from bot.keyboards.user_reply import back_keyboard, main_menu_keyboard
from bot.states.test_session import TestSessionState
from bot.core.enums import PointReason
from bot.config import settings

router = Router(name="tests")
router.message.filter(IsRegisteredFilter())


@router.message(F.text == "📝 Testlar")
async def show_tests(
    message: Message,
    session: AsyncSession,
    db_user: TelegramUser,
):
    repo = TestRepository(session)
    tests = await repo.get_available_for_user(
        db_user.id, db_user.organization_id
    )

    if not tests:
        await message.answer("Hozircha testlar mavjud emas.", reply_markup=back_keyboard())
        return

    items = [
        (f"📝 {t.title} ({t.question_count} savol)", f"test:start:{t.id}")
        for t in tests
    ]
    total_pages = ceil(len(items) / settings.pagination_size)
    page_items = items[: settings.pagination_size]

    await message.answer(
        "📝 <b>Mavjud testlar:</b>\n\nTestni tanlang:",
        reply_markup=paginated_keyboard(
            page_items, page=1, total_pages=total_pages, prefix="tests"
        ),
    )


@router.callback_query(F.data.startswith("test:start:"))
async def start_test(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
):
    test_id = int(callback.data.split(":")[-1])
    test_repo = TestRepository(session)
    test = await test_repo.get_with_questions(test_id)

    if not test or not test.questions:
        await callback.answer("Test topilmadi yoki savollar yo'q.", show_alert=True)
        return

    session_repo = TestSessionRepository(session)

    active = await session_repo.get_user_active_session(db_user.id)
    if active:
        await callback.answer("Sizda tugallanmagan test bor!", show_alert=True)
        return

    if test.max_attempts > 0:
        attempts = await session_repo.get_user_attempts(db_user.id, test_id)
        if attempts >= test.max_attempts:
            await callback.answer(
                f"Siz bu testni {test.max_attempts} marta topshirgansiz.", show_alert=True
            )
            return

    question_ids = [q.id for q in test.questions if q.is_active]
    if test.randomize_questions:
        random.shuffle(question_ids)

    test_session = await session_repo.create_session(
        user_id=db_user.id, test_id=test.id, question_order=question_ids
    )

    await state.set_state(TestSessionState.in_progress)
    await state.update_data(
        session_id=test_session.id,
        test_id=test.id,
        question_index=0,
    )

    await callback.answer()
    await send_question(callback.message, state, session, test_session, test, 0)


async def send_question(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    test_session,
    test,
    index: int,
):
    if index >= len(test_session.question_order):
        await finish_test(message, state, session, test_session)
        return

    question_id = test_session.question_order[index]
    question = next((q for q in test.questions if q.id == question_id), None)

    if not question:
        await state.update_data(question_index=index + 1)
        await send_question(message, state, session, test_session, test, index + 1)
        return

    options = list(question.options)
    if test.randomize_options:
        random.shuffle(options)

    option_items = [(o.id, o.text) for o in options]
    total = len(test_session.question_order)

    text = (
        f"📝 <b>Savol {index + 1}/{total}</b>\n"
        f"⏱ Vaqt: {test.time_per_question} soniya\n\n"
        f"{question.text}"
    )

    await message.answer(
        text, reply_markup=test_options_keyboard(option_items, test_session.id)
    )


@router.callback_query(TestSessionState.in_progress, F.data.startswith("test:answer:"))
async def process_answer(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
):
    parts = callback.data.split(":")
    session_id = int(parts[2])
    option_id = int(parts[3])

    data = await state.get_data()
    index = data.get("question_index", 0)
    test_id = data["test_id"]

    session_repo = TestSessionRepository(session)
    test_repo = TestRepository(session)

    test_session = await session_repo.get_by_id(session_id)
    test = await test_repo.get_with_questions(test_id)

    if not test_session or not test:
        await callback.answer("Sessiya topilmadi.", show_alert=True)
        return

    question_id = test_session.question_order[index]
    await session_repo.submit_answer(session_id, question_id, option_id)
    await session_repo.update_by_id(session_id, current_question_index=index + 1)

    next_index = index + 1
    await state.update_data(question_index=next_index)

    await callback.answer()

    try:
        await callback.message.delete()
    except Exception:
        pass

    await send_question(callback.message, state, session, test_session, test, next_index)


async def finish_test(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    test_session,
):
    data = await state.get_data()
    test_id = data["test_id"]

    session_repo = TestSessionRepository(session)
    test_repo = TestRepository(session)
    result_repo = TestResultRepository(session)
    rating_repo = RatingRepository(session)

    test = await test_repo.get_with_questions(test_id)
    await session_repo.finish_session(test_session.id)

    test_session = await session_repo.get_by_id(test_session.id)
    answers = test_session.answers

    correct = sum(1 for a in answers if a.is_correct)
    timeout = sum(1 for a in answers if a.is_timeout)
    total = len(test_session.question_order)
    wrong = total - correct - timeout
    score = int((correct / total) * 100) if total > 0 else 0
    is_passed = score >= test.passing_score

    if score >= settings.score_excellent_threshold:
        points = settings.score_excellent
        reason = PointReason.TEST_EXCELLENT
    elif score >= settings.score_good_threshold:
        points = settings.score_good
        reason = PointReason.TEST_GOOD
    elif score >= settings.score_satisfactory_threshold:
        points = settings.score_satisfactory
        reason = PointReason.TEST_SATISFACTORY
    else:
        points = settings.score_participation
        reason = PointReason.TEST_PARTICIPATION

    await result_repo.create_result(
        session_id=test_session.id,
        user_id=test_session.user_id,
        test_id=test_id,
        correct=correct,
        wrong=wrong,
        timeout=timeout,
        total=total,
        score=score,
        is_passed=is_passed,
        points=points,
    )

    await rating_repo.add_points(
        test_session.user_id, points, reason,
        description=f"Test: {test.title}",
        reference_id=test_session.id,
    )
    await rating_repo.increment_tests(test_session.user_id, passed=is_passed)

    status = "✅ O'tdingiz!" if is_passed else "❌ O'ta olmadingiz"
    text = (
        f"📊 <b>Test natijalari</b>\n\n"
        f"📝 {test.title}\n"
        f"{'─' * 25}\n"
        f"✅ To'g'ri: {correct}/{total}\n"
        f"❌ Noto'g'ri: {wrong}/{total}\n"
        f"⏱ Vaqt tugadi: {timeout}/{total}\n"
        f"{'─' * 25}\n"
        f"📈 Ball: {score}%\n"
        f"🏅 {status}\n"
        f"💰 +{points} ball\n"
    )

    await state.clear()
    await message.answer(text, reply_markup=main_menu_keyboard())
