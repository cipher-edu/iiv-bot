import re
import html


def sanitize_input(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    return text.strip()


def sanitize_sql_input(text: str) -> str:
    dangerous = ["--", ";", "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "EXEC", "UNION"]
    result = text
    for d in dangerous:
        result = re.sub(re.escape(d), "", result, flags=re.IGNORECASE)
    return result.strip()


def validate_phone(phone: str) -> bool:
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    return bool(re.match(r'^\+?\d{9,15}$', cleaned))


def validate_name(name: str) -> bool:
    if len(name) < 2 or len(name) > 255:
        return False
    return bool(re.match(r"^[\w\s'\-\.]+$", name, re.UNICODE))


def validate_file_extension(filename: str, allowed: list[str] = None) -> bool:
    if allowed is None:
        allowed = ["pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "jpg", "png", "mp4"]
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in allowed
