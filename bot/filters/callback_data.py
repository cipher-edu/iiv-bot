from aiogram.filters.callback_data import CallbackData


class AdminCallback(CallbackData, prefix="admin"):
    action: str
    id: int | None = None


class TestCallback(CallbackData, prefix="test"):
    action: str
    id: int | None = None
    page: int = 1


class CourseCallback(CallbackData, prefix="course"):
    action: str
    id: int | None = None
    page: int = 1


class LibraryCallback(CallbackData, prefix="lib"):
    action: str
    id: int | None = None
    page: int = 1


class TaskCallback(CallbackData, prefix="task"):
    action: str
    id: int | None = None


class SurveyCallback(CallbackData, prefix="survey"):
    action: str
    id: int | None = None
    index: int = 0


class PaginationCallback(CallbackData, prefix="page"):
    prefix: str
    page: int
