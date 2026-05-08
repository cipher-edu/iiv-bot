#!/bin/bash
set -euo pipefail

BACKUP_DIR="/app/data/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="backup_${TIMESTAMP}.sql"
KEEP_DAYS=30

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..."

pg_dump \
  -h "${DB_HOST:-postgres}" \
  -p "${DB_PORT:-5432}" \
  -U "${DB_USER:-iiv_admin}" \
  -d "${DB_NAME:-iiv_bot}" \
  -F c \
  -f "${BACKUP_DIR}/${FILENAME}"

echo "[$(date)] Backup created: ${FILENAME}"

find "$BACKUP_DIR" -name "backup_*.sql" -mtime +${KEEP_DAYS} -delete
echo "[$(date)] Old backups cleaned up (keeping ${KEEP_DAYS} days)"

echo "[$(date)] Backup completed successfully"
