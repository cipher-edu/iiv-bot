import os
import logging
from pathlib import Path

from bot.config import settings

logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
UPLOADS_DIR = DATA_DIR / "uploads"
CERTIFICATES_DIR = DATA_DIR / "certificates"
BACKUPS_DIR = DATA_DIR / "backups"
TEMP_DIR = DATA_DIR / "temp"


def ensure_dirs():
    for d in [DATA_DIR, UPLOADS_DIR, CERTIFICATES_DIR, BACKUPS_DIR, TEMP_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def get_upload_path(category: str, filename: str) -> Path:
    target = UPLOADS_DIR / category
    target.mkdir(parents=True, exist_ok=True)
    return target / filename


def get_certificate_path(cert_number: str) -> Path:
    CERTIFICATES_DIR.mkdir(parents=True, exist_ok=True)
    return CERTIFICATES_DIR / f"{cert_number}.pdf"


def get_backup_path(filename: str) -> Path:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    return BACKUPS_DIR / filename


def cleanup_temp():
    if TEMP_DIR.exists():
        for f in TEMP_DIR.iterdir():
            try:
                if f.is_file():
                    f.unlink()
            except Exception as e:
                logger.warning("Failed to delete temp file %s: %s", f, e)


def get_file_size_mb(path: Path) -> float:
    if path.exists():
        return path.stat().st_size / (1024 * 1024)
    return 0.0


def is_allowed_size(size_bytes: int) -> bool:
    return size_bytes <= settings.max_file_size_mb * 1024 * 1024
