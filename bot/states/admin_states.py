from aiogram.fsm.state import State, StatesGroup


class TestCreateState(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_time_per_question = State()
    waiting_passing_score = State()
    waiting_question_text = State()
    waiting_question_image = State()
    waiting_options = State()
    waiting_correct_option = State()
    confirm_add_more = State()


class CourseCreateState(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_difficulty = State()
    waiting_module_title = State()
    waiting_lesson_title = State()
    waiting_lesson_content = State()
    waiting_lesson_media = State()
    confirm_add_more_lessons = State()
    confirm_add_more_modules = State()


class NewsCreateState(StatesGroup):
    waiting_title = State()
    waiting_content = State()
    waiting_image = State()
    waiting_target = State()
    confirmation = State()


class BroadcastState(StatesGroup):
    waiting_message = State()
    waiting_media = State()
    waiting_target = State()
    confirmation = State()


class UserManageState(StatesGroup):
    waiting_search = State()
    waiting_block_reason = State()
    waiting_block_duration = State()
    waiting_role_selection = State()


class TaskCreateState(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_priority = State()
    waiting_deadline = State()
    waiting_assignees = State()
    confirmation = State()


class SurveyCreateState(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_question_text = State()
    waiting_question_type = State()
    waiting_question_options = State()
    confirm_add_more = State()
    waiting_target = State()
    confirmation = State()
