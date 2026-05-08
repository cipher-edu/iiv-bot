import re


def validate_phone(phone: str) -> bool:
    cleaned = re.sub(r"[\s\-\(\)]+", "", phone)
    return bool(re.match(r"^\+?998\d{9}$", cleaned))


def validate_name(name: str) -> bool:
    if not name or len(name) < 2 or len(name) > 100:
        return False
    return bool(re.match(r"^[A-Za-zА-Яа-яЁёЎўҚқҒғҲҳ\s'`.,-]+$", name))


def validate_file_extension(filename: str, allowed: list[str] | None = None) -> bool:
    if allowed is None:
        allowed = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".jpg", ".png", ".zip"]
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in allowed


def validate_file_size(size_bytes: int, max_mb: int = 50) -> bool:
    return 0 < size_bytes <= max_mb * 1024 * 1024


def sanitize_callback_data(data: str) -> str:
    return re.sub(r"[^a-zA-Z0-9:_\-]", "", data)[:64]


def validate_test_score(score: int) -> bool:
    return 0 <= score <= 100


def validate_priority(priority: str) -> bool:
    return priority in ("low", "medium", "high", "urgent")
