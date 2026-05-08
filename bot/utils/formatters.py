from datetime import datetime, date


def format_datetime(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y %H:%M")


def format_date(d: date) -> str:
    return d.strftime("%d.%m.%Y")


def format_phone(phone: str) -> str:
    if phone.startswith("+"):
        phone = phone[1:]
    if len(phone) == 12 and phone.startswith("998"):
        return f"+{phone[:3]} ({phone[3:5]}) {phone[5:8]}-{phone[8:10]}-{phone[10:]}"
    return phone


def truncate(text: str, max_length: int = 100) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def progress_bar(percent: int, length: int = 10) -> str:
    filled = int(length * percent / 100)
    empty = length - filled
    return f"{'█' * filled}{'░' * empty} {percent}%"


def format_number(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def ordinal_uz(n: int) -> str:
    return f"{n}-o'rin"
