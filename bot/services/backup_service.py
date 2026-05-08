import logging
import subprocess
from datetime import datetime
from pathlib import Path

from bot.config import settings
from bot.utils.file_manager import BACKUPS_DIR

logger = logging.getLogger(__name__)


class BackupService:
    @staticmethod
    def create_backup() -> Path | None:
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.sql"
        filepath = BACKUPS_DIR / filename

        try:
            cmd = [
                "pg_dump",
                "-h", settings.db_host,
                "-p", str(settings.db_port),
                "-U", settings.db_user,
                "-d", settings.db_name,
                "-F", "c",
                "-f", str(filepath),
            ]
            env = {"PGPASSWORD": settings.db_password}
            subprocess.run(cmd, env=env, check=True, capture_output=True, timeout=300)
            logger.info("Backup created: %s", filepath)
            return filepath
        except subprocess.CalledProcessError as e:
            logger.error("Backup failed: %s", e.stderr)
            return None
        except FileNotFoundError:
            logger.error("pg_dump not found")
            return None

    @staticmethod
    def restore_backup(filepath: Path) -> bool:
        try:
            cmd = [
                "pg_restore",
                "-h", settings.db_host,
                "-p", str(settings.db_port),
                "-U", settings.db_user,
                "-d", settings.db_name,
                "-c",
                str(filepath),
            ]
            env = {"PGPASSWORD": settings.db_password}
            subprocess.run(cmd, env=env, check=True, capture_output=True, timeout=600)
            logger.info("Restore completed from: %s", filepath)
            return True
        except Exception as e:
            logger.error("Restore failed: %s", e)
            return False

    @staticmethod
    def list_backups() -> list[dict]:
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        backups = []
        for f in sorted(BACKUPS_DIR.glob("backup_*.sql"), reverse=True):
            backups.append({
                "name": f.name,
                "path": str(f),
                "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                "created": datetime.fromtimestamp(f.stat().st_mtime),
            })
        return backups

    @staticmethod
    def cleanup_old_backups(keep: int = 10):
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        backups = sorted(BACKUPS_DIR.glob("backup_*.sql"), reverse=True)
        for old in backups[keep:]:
            old.unlink()
            logger.info("Deleted old backup: %s", old.name)
