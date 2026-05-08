#!/bin/bash
set -euo pipefail

BACKUP_DIR="/app/data/backups"

if [ $# -eq 0 ]; then
    LATEST=$(ls -t "${BACKUP_DIR}"/backup_*.sql 2>/dev/null | head -1)
    if [ -z "$LATEST" ]; then
        echo "No backup files found in ${BACKUP_DIR}"
        exit 1
    fi
    BACKUP_FILE="$LATEST"
else
    BACKUP_FILE="$1"
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

echo "[$(date)] Restoring from: ${BACKUP_FILE}"
echo "WARNING: This will overwrite the current database!"
echo "Press Ctrl+C to cancel, or wait 5 seconds..."
sleep 5

pg_restore \
  -h "${DB_HOST:-postgres}" \
  -p "${DB_PORT:-5432}" \
  -U "${DB_USER:-iiv_admin}" \
  -d "${DB_NAME:-iiv_bot}" \
  -c \
  --if-exists \
  "${BACKUP_FILE}"

echo "[$(date)] Restore completed successfully"
