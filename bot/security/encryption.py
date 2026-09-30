import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from bot.config import settings


def _get_fernet() -> Fernet:
    if not settings.encryption_key:
        raise RuntimeError(
            "ENCRYPTION_KEY .env'da bo'sh. Shifrlash uchun barqaror kalit kerak; "
            "aks holda restart'dan keyin eski ma'lumotni o'qib bo'lmaydi."
        )

    salt_source = settings.encryption_salt or settings.secret_key
    if not salt_source:
        raise RuntimeError(
            "ENCRYPTION_SALT yoki SECRET_KEY .env'da o'rnatilishi shart."
        )
    salt = salt_source.encode()[:32].ljust(16, b"_")

    key = settings.encryption_key.encode()
    if len(key) < 32 or not _is_urlsafe_b64_32(settings.encryption_key):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=200_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(key))
    return Fernet(key)


def _is_urlsafe_b64_32(s: str) -> bool:
    try:
        return len(base64.urlsafe_b64decode(s.encode())) == 32
    except Exception:
        return False


_fernet = None


def _get_instance() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = _get_fernet()
    return _fernet


def encrypt_data(data: str) -> str:
    f = _get_instance()
    return f.encrypt(data.encode()).decode()


def decrypt_data(encrypted: str) -> str:
    f = _get_instance()
    return f.decrypt(encrypted.encode()).decode()
