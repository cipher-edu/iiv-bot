from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import TelegramUser
from bot.repositories.user_repo import UserRepository, OrganizationRepository
from bot.keyboards.user_reply import (
    main_menu_keyboard,
    cancel_keyboard,
    confirm_keyboard,
)
from bot.keyboards.inline import paginated_keyboard
from bot.states.registration import RegistrationState
from bot.core.enums import RegistrationStep, StaffRole, OrganizationType

router = Router(name="registration")


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
    full_name = message.text.strip()
    if len(full_name) < 3:
        await message.answer("❌ Ism juda qisqa. To'liq F.I.O kiriting.")
        return

    repo = UserRepository(session)
    await repo.update_registration(
        db_user.id, RegistrationStep.ROLE, full_name=full_name
    )
    await state.update_data(full_name=full_name)
    await state.set_state(RegistrationState.waiting_staff_role)

    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👷 Ishchi xodim")],
            [KeyboardButton(text="🏛 Dekanat")],
            [KeyboardButton(text="👨‍🏫 Professor / O'qituvchi")],
        ],
        resize_keyboard=True,
    )
    await message.answer("🎭 Lavozim turini tanlang:", reply_markup=kb)


@router.message(RegistrationState.waiting_staff_role, F.text)
async def process_staff_role(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
):
    role_map = {
        "👷 Ishchi xodim": StaffRole.WORKER,
        "🏛 Dekanat": StaffRole.DECANATE,
        "👨‍🏫 Professor / O'qituvchi": StaffRole.PROFESSOR,
    }
    staff_role = role_map.get(message.text)
    if not staff_role:
        await message.answer("❌ Iltimos, tugmalardan birini tanlang.")
        return

    repo = UserRepository(session)
    await repo.update_registration(
        db_user.id, RegistrationStep.ORGANIZATION, staff_role=staff_role
    )
    await state.update_data(staff_role=staff_role.value)

    org_type_map = {
        StaffRole.WORKER: OrganizationType.DEPARTMENT,
        StaffRole.DECANATE: OrganizationType.FACULTY,
        StaffRole.PROFESSOR: OrganizationType.CHAIR,
    }
    org_type = org_type_map[staff_role]

    org_repo = OrganizationRepository(session)
    organizations = await org_repo.get_by_type(org_type)

    if not organizations:
        await state.set_state(RegistrationState.waiting_position)
        await message.answer(
            "🏢 Hozircha tashkilotlar ro'yxati bo'sh.\n\n"
            "💼 Lavozimingizni kiriting:",
            reply_markup=cancel_keyboard(),
        )
        return

    items = [(org.name, f"reg:org:{org.id}") for org in organizations]
    kb = paginated_keyboard(items, page=1, total_pages=1, prefix="reg_org")

    await state.set_state(RegistrationState.waiting_organization)
    await message.answer("🏢 Tashkilotingizni tanlang:", reply_markup=kb)


@router.callback_query(RegistrationState.waiting_organization, F.data.startswith("reg:org:"))
async def process_organization(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    db_user: TelegramUser,
):
    org_id = int(callback.data.split(":")[-1])
    repo = UserRepository(session)
    await repo.update_registration(
        db_user.id, RegistrationStep.POSITION, organization_id=org_id
    )
    await state.update_data(organization_id=org_id)

    await state.set_state(RegistrationState.waiting_position)
    await callback.message.answer(
        "💼 Lavozimingizni kiriting:", reply_markup=cancel_keyboard()
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

    position = message.text.strip()
    repo = UserRepository(session)
    await repo.update_registration(
        db_user.id, RegistrationStep.COMPLETED, position=position
    )

    await state.clear()
    await message.answer(
        "🎉 <b>Tabriklaymiz!</b>\n\n"
        "Siz muvaffaqiyatli ro'yxatdan o'tdingiz.\n"
        "Endi platformaning barcha imkoniyatlaridan foydalanishingiz mumkin!",
        reply_markup=main_menu_keyboard(is_admin=db_user.is_admin),
    )


@router.message(F.text == "❌ Bekor qilish")
async def cancel_registration(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state and current_state.startswith("RegistrationState"):
        await state.clear()
        await message.answer(
            "Ro'yxatdan o'tish bekor qilindi.\n"
            "Qaytadan boshlash uchun /start bosing."
        )
