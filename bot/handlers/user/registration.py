from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
)
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.user_repo import UserRepository, OrganizationRepository
from bot.keyboards.user_reply import (
    main_menu_keyboard,
    cancel_keyboard,
)
from bot.states.registration import RegistrationState
from bot.core.enums import RegistrationStep, UserCategory

router = Router(name="registration")


CATEGORY_HODIM_TEXT = "🧑‍💼 Hodim"
CATEGORY_FUQARO_TEXT = "🧍 Fuqaro"
SKIP_TEXT = "⏭ O'tkazib yuborish"


def category_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=CATEGORY_HODIM_TEXT)],
            [KeyboardButton(text=CATEGORY_FUQARO_TEXT)],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def skip_or_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=SKIP_TEXT)],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
    )


async def _finish_registration(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
):
    await state.clear()
    repo = UserRepository(session)
    user = await repo.get_by_id(db_user.id)
    is_admin = bool(user and user.is_admin)
    await message.answer(
        "🎉 <b>Tabriklaymiz!</b>\n\n"
        "Siz muvaffaqiyatli ro'yxatdan o'tdingiz.\n"
        "Endi platformaning barcha imkoniyatlaridan foydalanishingiz mumkin!",
        reply_markup=main_menu_keyboard(is_admin=is_admin),
    )


@router.message(RegistrationState.waiting_phone, F.contact)
async def process_phone_contact(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
):
    phone = message.contact.phone_number
    repo = UserRepository(session)
    await repo.update_registration(db_user.id, RegistrationStep.FULL_NAME, phone=phone)

    await state.set_state(RegistrationState.waiting_full_name)
    await message.answer(
        "✅ Telefon raqam qabul qilindi!\n\n"
        "👤 To'liq ismingizni kiriting (F.I.O):",
        reply_markup=cancel_keyboard(),
    )


@router.message(RegistrationState.waiting_phone, F.text)
async def process_phone_text(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
):
    phone = message.text.strip()
    if not phone.replace("+", "").replace(" ", "").isdigit() or len(phone) < 9:
        await message.answer("❌ Noto'g'ri format. Telefon raqamni to'g'ri kiriting.")
        return

    repo = UserRepository(session)
    await repo.update_registration(db_user.id, RegistrationStep.FULL_NAME, phone=phone)

    await state.set_state(RegistrationState.waiting_full_name)
    await message.answer(
        "✅ Telefon raqam qabul qilindi!\n\n"
        "👤 To'liq ismingizni kiriting (F.I.O):",
        reply_markup=cancel_keyboard(),
    )


@router.message(RegistrationState.waiting_full_name, F.text)
async def process_full_name(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Ro'yxatdan o'tish bekor qilindi. /start bosing.")
        return

    full_name = message.text.strip()
    if len(full_name) < 3:
        await message.answer("❌ Ism juda qisqa. To'liq F.I.O kiriting.")
        return

    repo = UserRepository(session)
    await repo.update_registration(
        db_user.id, RegistrationStep.CATEGORY, full_name=full_name
    )
    await state.update_data(full_name=full_name)
    await state.set_state(RegistrationState.waiting_category)

    await message.answer(
        "🧭 <b>Toifani tanlang:</b>\n\n"
        "🧑‍💼 <b>Hodim</b> — tashkilotda ishlovchi (lavozim ko'rsatiladi)\n"
        "🧍 <b>Fuqaro</b> — oddiy foydalanuvchi (faqat F.I.O)",
        reply_markup=category_keyboard(),
    )


@router.message(RegistrationState.waiting_category, F.text)
async def process_category(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
):
    text = message.text.strip()
    if text == CATEGORY_FUQARO_TEXT:
        repo = UserRepository(session)
        await repo.update_registration(
            db_user.id,
            RegistrationStep.COMPLETED,
            category=UserCategory.FUQARO,
            staff_role=None,
            organization_id=None,
            position=None,
        )
        await _finish_registration(message, state, session, db_user)
        return

    if text != CATEGORY_HODIM_TEXT:
        await message.answer("❌ Iltimos, tugmalardan birini tanlang.")
        return

    repo = UserRepository(session)
    await repo.update_registration(
        db_user.id, RegistrationStep.ORGANIZATION, category=UserCategory.HODIM
    )
    await state.update_data(category=UserCategory.HODIM.value)

    org_repo = OrganizationRepository(session)
    organizations = await org_repo.get_active_all()

    if not organizations:
        await state.set_state(RegistrationState.waiting_position)
        await message.answer(
            "🏢 Hozircha tashkilotlar ro'yxati bo'sh.\n\n"
            "💼 Lavozimingizni kiriting (yoki o'tkazib yuboring):",
            reply_markup=skip_or_cancel_keyboard(),
        )
        return

    builder = InlineKeyboardBuilder()
    for org in organizations:
        builder.button(text=org.name, callback_data=f"reg:org:{org.id}")
    builder.button(text=SKIP_TEXT, callback_data="reg:org:skip")
    builder.adjust(1)

    await state.set_state(RegistrationState.waiting_organization)
    await message.answer(
        "🏢 Tashkilotingizni tanlang (ixtiyoriy):",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(
    RegistrationState.waiting_organization, F.data.startswith("reg:org:")
)
async def process_organization(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
):
    suffix = callback.data.split(":")[-1]
    repo = UserRepository(session)

    if suffix == "skip":
        await repo.update_registration(db_user.id, RegistrationStep.POSITION)
    else:
        org_id = int(suffix)
        await repo.update_registration(
            db_user.id, RegistrationStep.POSITION, organization_id=org_id
        )

    await state.set_state(RegistrationState.waiting_position)
    await callback.message.answer(
        "💼 Lavozimingizni kiriting (yoki o'tkazib yuboring):",
        reply_markup=skip_or_cancel_keyboard(),
    )
    await callback.answer()


@router.message(RegistrationState.waiting_position, F.text)
async def process_position(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Ro'yxatdan o'tish bekor qilindi. /start bosing.")
        return

    repo = UserRepository(session)

    if message.text == SKIP_TEXT:
        await repo.update_registration(db_user.id, RegistrationStep.COMPLETED)
    else:
        position = message.text.strip()
        await repo.update_registration(
            db_user.id, RegistrationStep.COMPLETED, position=position
        )

    await _finish_registration(message, state, session, db_user)


@router.message(F.text == "❌ Bekor qilish")
async def cancel_registration(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state and current_state.startswith("RegistrationState"):
        await state.clear()
        await message.answer(
            "Ro'yxatdan o'tish bekor qilindi.\n"
            "Qaytadan boshlash uchun /start bosing."
        )
