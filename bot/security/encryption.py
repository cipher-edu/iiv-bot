import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from bot.config import settings


def _get_fernet() -> Fernet:
    if settings.encryption_key:
        key = settings.encryption_key.encode()
        if len(key) < 32:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"iiv-bot-salt",
                iterations=100_000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(key))
        return Fernet(key)
    key = Fernet.generate_key()
    return Fernet(key)


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
