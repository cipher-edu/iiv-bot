#!/usr/bin/env bash
# ==============================================================================
# IIV EDUBOT PLATFORM - AVTOMATIK O'RNATISH VA ISHGA TUSHIRISH (start.sh)
# Ushbu skript yangi kompyuterda barcha bog'liqliklarni o'rnatib, loyihani
# to'liq avtonom tarzda ishga tushirish uchun mo'ljallangan.
# ==============================================================================

set -o pipefail

# Ranglar va formatlash
if [ -t 1 ]; then
    C_RESET='\033[0m'
    C_BOLD='\033[1m'
    C_GREEN='\033[32m'
    C_BLUE='\033[34m'
    C_CYAN='\033[36m'
    C_YELLOW='\033[33m'
    C_RED='\033[31m'
else
    C_RESET=''
    C_BOLD=''
    C_GREEN=''
    C_BLUE=''
    C_CYAN=''
    C_YELLOW=''
    C_RED=''
fi

log_info() { echo -e "${C_CYAN}[MA'LUMOT]${C_RESET} $*"; }
log_ok() { echo -e "${C_GREEN}[BAJARILDI]${C_RESET} $*"; }
log_warn() { echo -e "${C_YELLOW}[OGOHLANTIRISH]${C_RESET} $*"; }
log_err() { echo -e "${C_RED}[XATOLIK]${C_RESET} $*"; }
log_step() { echo -e "\n${C_BOLD}${C_BLUE}===> $*${C_RESET}"; }

# Loyihaning asosiy papkasiga o'tish
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || { log_err "Loyiha katalogiga o'tib bo'lmadi: $SCRIPT_DIR"; exit 1; }

echo -e "${C_BOLD}${C_BLUE}"
echo "=================================================================="
echo "    IIV EDUBOT PLATFORM - AVTOMATIK SOZLASH VA ISHGA TUSHIRISH    "
echo "=================================================================="
echo -e "${C_RESET}"

# ------------------------------------------------------------------------------
# 1-QADAM: Tizim muhitini aniqlash (OS & Platform)
# ------------------------------------------------------------------------------
log_step "[1/6] Operatsion tizim va muhit aniqlanmoqda..."

OS_TYPE="unknown"
case "$(uname -s)" in
    Linux*)     OS_TYPE="Linux";;
    Darwin*)    OS_TYPE="macOS";;
    CYGWIN*|MINGW*|MSYS*) OS_TYPE="Windows";;
    *)          OS_TYPE="Boshqa";;
esac
log_info "Operatsion tizim: ${C_BOLD}$OS_TYPE${C_RESET} ($(uname -s) $(uname -m))"
log_info "Loyiha katalogi: $SCRIPT_DIR"

# ------------------------------------------------------------------------------
# 2-QADAM: .env konfiguratsiya faylini tekshirish va avtomatik yaratish
# ------------------------------------------------------------------------------
log_step "[2/6] Konfiguratsiya (.env) tekshirilmoqda..."

generate_random_hex() {
    local len="${1:-32}"
    if command -v openssl >/dev/null 2>&1; then
        openssl rand -hex "$len" 2>/dev/null
    elif [ -r /dev/urandom ]; then
        LC_ALL=C tr -dc 'a-f0-9' < /dev/urandom | head -c "$((len * 2))"
    else
        echo "iiv_secret_$(date +%s%N 2>/dev/null || date +%s)_token"
    fi
}

generate_random_base64() {
    local len="${1:-32}"
    if command -v openssl >/dev/null 2>&1; then
        openssl rand -base64 "$len" 2>/dev/null
    else
        echo "aWl2X3NlY3VyZV9lbmNyeXB0aW9uX2tleV8yMDI0IQ=="
    fi
}

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        log_info ".env fayli topilmadi. .env.example dan yangi .env yaratilmoqda..."
        cp .env.example .env
        
        # Xavfsizlik kalitlarini avtomatik generatsiya qilish
        NEW_SECRET="$(generate_random_hex 32)"
        NEW_ENC_KEY="$(generate_random_base64 32)"
        NEW_SALT="$(generate_random_hex 16)"
        NEW_JWT="$(generate_random_hex 32)"
        
        # Kalitlarni almashtirish
        if [ "$OS_TYPE" = "macOS" ]; then
            sed -i '' "s|SECRET_KEY=.*|SECRET_KEY=${NEW_SECRET}|" .env
            sed -i '' "s|ENCRYPTION_KEY=.*|ENCRYPTION_KEY=${NEW_ENC_KEY}|" .env
            sed -i '' "s|ENCRYPTION_SALT=.*|ENCRYPTION_SALT=${NEW_SALT}|" .env
            sed -i '' "s|JWT_SECRET=.*|JWT_SECRET=${NEW_JWT}|" .env
        else
            sed -i "s|SECRET_KEY=.*|SECRET_KEY=${NEW_SECRET}|" .env 2>/dev/null || true
            sed -i "s|ENCRYPTION_KEY=.*|ENCRYPTION_KEY=${NEW_ENC_KEY}|" .env 2>/dev/null || true
            sed -i "s|ENCRYPTION_SALT=.*|ENCRYPTION_SALT=${NEW_SALT}|" .env 2>/dev/null || true
            sed -i "s|JWT_SECRET=.*|JWT_SECRET=${NEW_JWT}|" .env 2>/dev/null || true
        fi
        log_ok ".env fayli yaratildi va maxfiy xavfsizlik kalitlari avtomatik to'ldirildi."
    else
        log_err ".env va .env.example fayllari topilmadi!"
        exit 1
    fi
else
    log_ok ".env fayli mavjud."
fi

# Bot tokenni tekshirish
BOT_TOKEN_VAL=$(grep -E "^BOT_TOKEN=" .env | cut -d '=' -f2- | tr -d ' "\r')
if [ -z "$BOT_TOKEN_VAL" ] || [ "$BOT_TOKEN_VAL" = "your_bot_token_here" ]; then
    log_warn "DIQQAT: .env faylida BOT_TOKEN kiritilmagan yoki namuna qiymatda turibdi!"
    log_warn "Telegram bot ishlashi uchun @BotFather orqali token olib .env fayliga kiriting."
fi

# ------------------------------------------------------------------------------
# 3-QADAM: DOCKER muhitini aniqlash va tekshirish
# ------------------------------------------------------------------------------
log_step "[3/6] Ishga tushirish muhiti aniqlanmoqda (Docker vs Local)..."

HAS_DOCKER=false
COMPOSE_CMD=""

if command -v docker >/dev/null 2>&1; then
    if docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
        HAS_DOCKER=true
    elif command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD="docker-compose"
        HAS_DOCKER=true
    fi
fi

start_docker_daemon() {
    log_info "Docker daemon ishga tushirilmoqda..."
    if [ "$OS_TYPE" = "Linux" ]; then
        if command -v systemctl >/dev/null 2>&1; then
            sudo systemctl start docker 2>/dev/null || true
        elif command -v service >/dev/null 2>&1; then
            sudo service docker start 2>/dev/null || true
        fi
    elif [ "$OS_TYPE" = "macOS" ]; then
        open -a Docker 2>/dev/null || true
    elif [ "$OS_TYPE" = "Windows" ]; then
        DOCKER_WIN_PATHS=(
            "/c/Program Files/Docker/Docker/Docker Desktop.exe"
            "/mnt/c/Program Files/Docker/Docker/Docker Desktop.exe"
            "C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe"
            "$LOCALAPPDATA/Docker/Docker Desktop.exe"
        )
        for dpath in "${DOCKER_WIN_PATHS[@]}"; do
            if [ -f "$dpath" ]; then
                log_info "Docker Desktop topildi: $dpath"
                cmd.exe /c start "" "$dpath" 2>/dev/null || "$dpath" &
                break
            fi
        done
    fi

    # Daemon tayyor bo'lishini kutish (60 soniyagacha)
    local wait_sec=0
    echo -n "Docker daemon javob berishi kutilmoqda"
    while [ $wait_sec -lt 60 ]; do
        if docker info >/dev/null 2>&1; then
            echo -e " ${C_GREEN}[TAYYOR]${C_RESET}"
            return 0
        fi
        echo -n "."
        sleep 3
        wait_sec=$((wait_sec + 3))
    done
    echo ""
    return 1
}

DOCKER_AVAILABLE=false
if [ "$HAS_DOCKER" = true ]; then
    log_info "Docker va Docker Compose topildi: OK"
    if docker info >/dev/null 2>&1; then
        DOCKER_AVAILABLE=true
        log_ok "Docker daemon ishlamoqda."
    else
        log_warn "Docker daemon o'chiq holatda. Avtomatik ishga tushirilmoqda..."
        if start_docker_daemon; then
            DOCKER_AVAILABLE=true
            log_ok "Docker daemon muvaffaqiyatli ishga tushdi."
        else
            log_warn "Docker daemon 60 soniyada javob bermadi."
        fi
    fi
fi

# ------------------------------------------------------------------------------
# 4-QADAM: DOCKER REJIMI (Agar Docker tayyor bo'lsa)
# ------------------------------------------------------------------------------
if [ "$DOCKER_AVAILABLE" = true ]; then
    log_step "[4/6] DOCKER REJIMI: Konteynerlar qurilmoqda va ko'tarilmoqda..."
    log_info "Buyruq: $COMPOSE_CMD -p iiv-bot up -d --build --remove-orphans"
    
    $COMPOSE_CMD -p iiv-bot up -d --build --remove-orphans
    if [ $? -ne 0 ]; then
        log_err "Docker konteynerlarini ko'tarishda xatolik yuz berdi!"
        log_warn "Mahalliy (Local) rejimga o'tish tekshirilmoqda..."
        DOCKER_AVAILABLE=false
    else
        log_ok "Konteynerlar fon rejimida ko'tarildi."

        # Database (PostgreSQL) tayyor bo'lishini kutish
        log_step "[5/6] PostgreSQL ma'lumotlar bazasi tekshirilmoqda..."
        local_db_wait=0
        echo -n "PostgreSQL tayyor bo'lishi kutilmoqda"
        while [ $local_db_wait -lt 60 ]; do
            if $COMPOSE_CMD -p iiv-bot exec -T postgres pg_isready -U iiv_admin -d iiv_bot >/dev/null 2>&1; then
                echo -e " ${C_GREEN}[TAYYOR]${C_RESET}"
                break
            fi
            echo -n "."
            sleep 3
            local_db_wait=$((local_db_wait + 3))
        done

        # Database migratsiyalarini qo'llash
        log_info "Alembic migratsiyalari va jadvallar tekshirilmoqda..."
        $COMPOSE_CMD -p iiv-bot exec -T bot alembic upgrade head >/dev/null 2>&1 || true

        # Demo ma'lumotlarni tekshirish va yuklash (idempotent)
        log_info "Boshlang'ich va demo ma'lumotlar yuklanmoqda (seed_demo.py)..."
        $COMPOSE_CMD -p iiv-bot exec -T bot python scripts/seed_demo.py >/dev/null 2>&1 || true

        # Konteynerlar yakuniy holati
        log_step "[6/6] TIZIM TAYYOR VA ISHGA TUSHIRILDI!"
        echo -e "${C_BOLD}${C_GREEN}"
        echo "=================================================================="
        echo "       IIV EDUBOT PLATFORMASI MUVAFFAQIYATLI ISHGA TUSHDI!        "
        echo "=================================================================="
        echo -e "${C_RESET}"
        
        $COMPOSE_CMD -p iiv-bot ps

        echo ""
        echo -e "${C_BOLD}XIZMATLAR VA MANZILLAR:${C_RESET}"
        echo -e "  • ${C_CYAN}Telegram Bot:${C_RESET}         @ijaransubot (yoki .env dagi botingiz)"
        echo -e "  • ${C_CYAN}Web App (User):${C_RESET}       http://localhost:3000"
        echo -e "  • ${C_CYAN}Admin Dashboard:${C_RESET}      http://localhost:3000/admin"
        echo -e "  • ${C_CYAN}Web API Server:${C_RESET}       http://localhost:8081"
        echo -e "  • ${C_CYAN}Grafana Monitoring:${C_RESET}   http://localhost:3001"
        echo -e "  • ${C_CYAN}pgAdmin:${C_RESET}              http://localhost:5050"
        echo -e "  • ${C_CYAN}MinIO Fayl Saqlash:${C_RESET}  http://localhost:9001"
        echo -e "  • ${C_CYAN}Prometheus:${C_RESET}           http://localhost:9090"
        echo -e "  • ${C_CYAN}Nginx Proxy:${C_RESET}          http://localhost:8080"
        echo ""
        echo -e "${C_BOLD}BOSHQARUV BUYRUQLARI:${C_RESET}"
        echo -e "  • Jonli loglarni ko'rish:  ${C_YELLOW}./logs.sh${C_RESET}  (yoki: $COMPOSE_CMD -p iiv-bot logs -f bot)"
        echo -e "  • Loyihani to'xtatish:    ${C_YELLOW}./stop.sh${C_RESET}  (yoki: $COMPOSE_CMD -p iiv-bot stop)"
        echo -e "  • Barcha servislarni:     ${C_YELLOW}$COMPOSE_CMD -p iiv-bot restart${C_RESET}"
        echo "=================================================================="
        exit 0
    fi
fi

# ------------------------------------------------------------------------------
# 5-QADAM: MAHALLIY (LOCAL / STANDALONE) REJIM
# (Agar Docker o'rnatilmagan yoki ishga tushirib bo'lmagan bo'lsa)
# ------------------------------------------------------------------------------
log_step "[4/6] MAHALLIY REJIM (Local Python & Node.js)..."
log_warn "Docker topilmadi yoki ishlamadi. Mahalliy muhit avtomatik sozlanmoqda..."

# 1. Python mavjudligini tekshirish
PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    log_err "Python topilmadi! Iltimos, Python 3.11+ o'rnating:"
    if [ "$OS_TYPE" = "Linux" ]; then
        echo "  Ubuntu/Debian: sudo apt update && sudo apt install -y python3 python3-venv python3-pip"
    elif [ "$OS_TYPE" = "macOS" ]; then
        echo "  macOS (Brew): brew install python"
    else
        echo "  Windows: https://www.python.org/downloads/ dan yuklab oling."
    fi
    exit 1
fi

PY_VER=$($PYTHON_BIN -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
log_info "Python aniqlandi: $PYTHON_BIN (versiya $PY_VER)"

# 2. Virtual muhit (venv) tekshirish va yaratish
if [ ! -d "venv" ]; then
    log_info "Python virtual muhiti (venv) yaratilmoqda..."
    $PYTHON_BIN -m venv venv || {
        log_err "Virtual muhit yaratishda xatolik. python3-venv o'rnatilganini tekshiring."
        exit 1
    }
    log_ok "Virtual muhit yaratildi (venv)."
fi

# Virtual muhitni faollashtirish
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
fi

# 3. Pip kutubxonalarini o'rnatish
log_info "Python kutubxonalari tekshirilmoqda va o'rnatilmoqda (requirements.txt)..."
pip install --upgrade pip >/dev/null 2>&1 || true
pip install -r requirements.txt
log_ok "Python kutubxonalari o'rnatildi."

# 4. Node.js va WebApp tekshirish
HAS_NODE=false
if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    HAS_NODE=true
    NODE_VER=$(node -v)
    log_info "Node.js aniqlandi: $NODE_VER"
    
    if [ -d "webapp" ]; then
        if [ ! -d "webapp/node_modules" ]; then
            log_info "Web App bog'liqliklari o'rnatilmoqda (npm install in webapp)..."
            (cd webapp && npm install)
            log_ok "Web App paketlari o'rnatildi."
        else
            log_ok "Web App paketlari (node_modules) mavjud."
        fi
    fi
else
    log_warn "Node.js topilmadi. Web App UI alohida ishga tushirish uchun https://nodejs.org dan o'rnating."
fi

# 5. Database tekshirish yoki ishga tushirish
log_step "[5/6] Ma'lumotlar bazasi va xizmatlar tayyorlanmoqda..."
if [ "$HAS_DOCKER" = true ]; then
    # Agar docker CLI boru, lekin to'liq stack ishlamagan bo'lsa, hech bo'lmasa postgres/redis ni ko'tarish
    log_info "Docker orqali faqat PostgreSQL va Redis konteynerlari ko'tarilmoqda..."
    $COMPOSE_CMD -p iiv-bot up -d postgres redis >/dev/null 2>&1 || true
fi

# 6. Mahalliy xizmatlarni parallel ishga tushirish
log_step "[6/6] Barcha xizmatlar ishga tushirilmoqda..."

LOCAL_PIDS=()

cleanup() {
    echo ""
    log_warn "Xizmatlar to'xtatilmoqda..."
    for pid in "${LOCAL_PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    log_ok "Barcha xizmatlar to'xtatildi."
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Web API serverini ishga tushirish
log_info "1. Web API server (port 8081) ishga tushirilmoqda..."
python -m bot.api.server > /dev/null 2>&1 &
LOCAL_PIDS+=($!)
sleep 2

# Web App serverini ishga tushirish
if [ "$HAS_NODE" = true ] && [ -d "webapp" ]; then
    log_info "2. Next.js Web App (port 3000) ishga tushirilmoqda..."
    (cd webapp && npm run dev > /dev/null 2>&1) &
    LOCAL_PIDS+=($!)
    sleep 2
fi

# Telegram Bot ishga tushirish
log_info "3. Telegram Bot ishga tushirilmoqda..."
echo -e "${C_BOLD}${C_GREEN}"
echo "=================================================================="
echo "    BARCHA TIZIMLAR ISHGA TUSHIRILDI (Mahalliy rejim)!            "
echo "  • Web App:      http://localhost:3000                          "
echo "  • Admin Panel:  http://localhost:3000/admin                    "
echo "  • Web API:      http://localhost:8081                          "
echo "  • To'xtatish:   CTRL+C bosing                                  "
echo "=================================================================="
echo -e "${C_RESET}"

# Botni asosiy oqimda ishlatish (loglar to'g'ridan-to'g'ri terminalda ko'rinadi)
python run_bot.py
