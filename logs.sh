#!/usr/bin/env bash
# ==============================================================================
# IIV EDUBOT PLATFORM - JONLI LOGLARNI KO'RISH (logs.sh)
# ==============================================================================

set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

COMPOSE_CMD=""
if command -v docker >/dev/null 2>&1; then
    if docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD="docker-compose"
    fi
fi

if [ -n "$COMPOSE_CMD" ] && docker info >/dev/null 2>&1; then
    echo "Bot konteyneri loglari (To'xtatish uchun CTRL+C bosing):"
    $COMPOSE_CMD -p iiv-bot logs -f --tail 100 bot
else
    echo "Docker ishlamayapti yoki topilmadi."
fi
