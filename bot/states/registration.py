from aiogram.fsm.state import State, StatesGroup


class RegistrationState(StatesGroup):
    waiting_phone = State()
    waiting_full_name = State()
    waiting_category = State()
    waiting_organization = State()
    waiting_position = State()
    confirmation = State()
