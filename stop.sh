#!/usr/bin/env bash
# ==============================================================================
# IIV EDUBOT PLATFORM - TO'XTATISH (stop.sh)
# ==============================================================================

set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

if [ -t 1 ]; then
    C_RESET='\033[0m'
    C_BOLD='\033[1m'
    C_GREEN='\033[32m'
    C_YELLOW='\033[33m'
else
    C_RESET=''
    C_BOLD=''
    C_GREEN=''
    C_YELLOW=''
fi

echo -e "${C_BOLD}${C_YELLOW}"
echo "=================================================================="
echo "          IIV EDUBOT PLATFORMASI - XIZMATLARNI TO'XTATISH         "
echo "=================================================================="
echo -e "${C_RESET}"

# Docker mavjudligini tekshirish
COMPOSE_CMD=""
if command -v docker >/dev/null 2>&1; then
    if docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD="docker-compose"
    fi
fi

if [ -n "$COMPOSE_CMD" ] && docker info >/dev/null 2>&1; then
    echo "Docker konteynerlari to'xtatilmoqda..."
    $COMPOSE_CMD -p iiv-bot stop
    echo -e "${C_GREEN}[BAJARILDI] Barcha Docker konteynerlari to'xtatildi.${C_RESET}"
fi

# Mahalliy jarayonlarni to'xtatish (agar local python/node ishlagan bo'lsa)
pkill -f "python.*run_bot.py" 2>/dev/null || true
pkill -f "python.*bot.api.server" 2>/dev/null || true
pkill -f "python -m bot.main" 2>/dev/null || true
pkill -f "next-dev" 2>/dev/null || true

echo ""
echo "Ma'lumotlar saqlangan (database volumes)."
echo "Qayta ishga tushirish uchun: ./start.sh"
echo "=================================================================="
