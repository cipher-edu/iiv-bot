from aiogram.fsm.state import State, StatesGroup


class TestSessionState(StatesGroup):
    in_progress = State()
    waiting_answer = State()
    reviewing_results = State()
