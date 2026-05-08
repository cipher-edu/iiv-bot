class BotException(Exception):
    def __init__(self, message: str = "Ichki xatolik yuz berdi"):
        self.message = message
        super().__init__(self.message)


class AccessDeniedError(BotException):
    def __init__(self, message: str = "Sizda bu amalni bajarish huquqi yo'q"):
        super().__init__(message)


class NotFoundError(BotException):
    def __init__(self, entity: str = "Ma'lumot"):
        super().__init__(f"{entity} topilmadi")


class ValidationError(BotException):
    def __init__(self, message: str = "Noto'g'ri ma'lumot kiritildi"):
        super().__init__(message)


class RateLimitError(BotException):
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(
            f"Juda ko'p so'rov. {retry_after} soniyadan keyin urinib ko'ring"
        )


class BlockedUserError(BotException):
    def __init__(self):
        super().__init__("Sizning hisobingiz bloklangan. Admin bilan bog'laning")


class MaintenanceError(BotException):
    def __init__(self):
        super().__init__(
            "Tizimda texnik xizmat ko'rsatish ishlari olib borilmoqda. "
            "Iltimos, keyinroq urinib ko'ring"
        )


class SessionExpiredError(BotException):
    def __init__(self):
        super().__init__("Sessiya muddati tugadi. Qaytadan boshlang")


class FileUploadError(BotException):
    def __init__(self, message: str = "Fayl yuklashda xatolik"):
        super().__init__(message)


class AIServiceError(BotException):
    def __init__(self, message: str = "AI xizmati vaqtincha ishlamayapti"):
        super().__init__(message)
