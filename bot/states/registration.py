from aiogram.fsm.state import State, StatesGroup


class RegistrationState(StatesGroup):
    waiting_phone = State()
    waiting_full_name = State()
    waiting_staff_role = State()
    waiting_organization = State()
    waiting_position = State()
    confirmation = State()
