@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 > nul
title IIV EduBot - Avtomatik O'rnatish va Ishga Tushirish
color 0B

cd /d "%~dp0"

echo.
echo ==================================================================
echo     IIV EDUBOT PLATFORM - AVTOMATIK SOZLASH VA ISHGA TUSHIRISH   
echo ==================================================================
echo.

REM --- 1. .env faylini tekshirish va avtomatik yaratish ---
echo [1/5] Konfiguratsiya (.env) tekshirilmoqda...
if not exist ".env" (
    if exist ".env.example" (
        echo     .env fayli topilmadi. .env.example dan avtomatik nusxalanmoqda...
        copy /y ".env.example" ".env" > nul
        echo     [OK] .env fayli yaratildi.
    ) else (
        echo     [XATO] .env yoki .env.example fayli topilmadi!
        pause
        exit /b 1
    )
) else (
    echo     [OK] .env fayli mavjud.
)

REM --- 2. Docker va Docker Compose mavjudligini tekshirish ---
echo [2/5] Docker muhiti tekshirilmoqda...
set "HAS_DOCKER=0"
where docker > nul 2>&1
if not errorlevel 1 (
    set "HAS_DOCKER=1"
)

if "%HAS_DOCKER%"=="1" (
    REM Docker daemon holatini tekshirish
    docker info > nul 2>&1
    if errorlevel 1 (
        echo     Docker daemon ishlamayapti. Docker Desktop ishga tushirilmoqda...
        set "DOCKER_EXE="
        if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" set "DOCKER_EXE=%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
        if not defined DOCKER_EXE if exist "%ProgramW6432%\Docker\Docker\Docker Desktop.exe" set "DOCKER_EXE=%ProgramW6432%\Docker\Docker\Docker Desktop.exe"
        if not defined DOCKER_EXE if exist "%LocalAppData%\Docker\Docker Desktop.exe" set "DOCKER_EXE=%LocalAppData%\Docker\Docker Desktop.exe"

        if defined DOCKER_EXE (
            start "" "%DOCKER_EXE%"
            echo     Docker daemon javob berishi kutilmoqda (60 soniyagacha)...
            set /a WAIT_COUNT=0
            :WAIT_DOCKER_LOOP
            timeout /t 3 /nobreak > nul
            set /a WAIT_COUNT=!WAIT_COUNT!+3
            docker info > nul 2>&1
            if not errorlevel 1 goto DOCKER_ACTIVE
            if !WAIT_COUNT! GEQ 60 goto DOCKER_FAILED
            echo     ... !WAIT_COUNT! soniya
            goto WAIT_DOCKER_LOOP
        ) else (
            echo     Docker Desktop fayli topilmadi.
            goto DOCKER_FAILED
        )
    )
    :DOCKER_ACTIVE
    echo     [OK] Docker daemon ishlamoqda.
    goto DOCKER_MODE
)

:DOCKER_FAILED
echo     [OGOHLANTIRISH] Docker topilmadi yoki ishga tushmadi.
echo     Mahalliy (Local Python + Node.js) rejimga o'tilmoqda...
goto LOCAL_MODE

REM ============================================================================
REM DOCKER REJIMI (Konteynerlar bilan ishga tushirish)
REM ============================================================================
:DOCKER_MODE
echo.
echo [3/5] DOCKER REJIMI: Konteynerlar qurilmoqda va ko'tarilmoqda...
echo.

docker compose -p iiv-bot up -d --build --remove-orphans
if errorlevel 1 (
    echo.
    echo [XATO] Docker Compose orqali konteynerlarni ko'tarib bo'lmadi.
    echo Mahalliy rejimni sinab ko'ramiz...
    goto LOCAL_MODE
)

echo.
echo [4/5] PostgreSQL ma'lumotlar bazasi tekshirilmoqda...
set /a DB_WAIT=0
:WAIT_DB_LOOP
timeout /t 3 /nobreak > nul
set /a DB_WAIT=!DB_WAIT!+3
docker compose -p iiv-bot exec -T postgres pg_isready -U iiv_admin -d iiv_bot > nul 2>&1
if not errorlevel 1 goto DB_READY
if !DB_WAIT! GEQ 45 goto DB_READY
goto WAIT_DB_LOOP

:DB_READY
echo     [OK] Ma'lumotlar bazasi tayyor.
echo     Migratsiyalar va demo ma'lumotlar tekshirilmoqda...
docker compose -p iiv-bot exec -T bot alembic upgrade head > nul 2>&1
docker compose -p iiv-bot exec -T bot python scripts/seed_demo.py > nul 2>&1

echo.
echo [5/5] TIZIM TAYYOR VA ISHGA TUSHIRILDI!
echo ==================================================================
echo       IIV EDUBOT PLATFORMASI MUVAFFAQIYATLI ISHGA TUSHDI!         
echo ==================================================================
docker compose -p iiv-bot ps
echo.
echo MANZILLAR:
echo   • Telegram Bot:         @ijaransubot
echo   • Web App (User):       http://localhost:3000
echo   • Admin Dashboard:      http://localhost:3000/admin
echo   • Web API Server:       http://localhost:8081
echo   • Grafana Monitoring:   http://localhost:3001
echo   • pgAdmin:              http://localhost:5050
echo   • MinIO Fayl Saqlash:  http://localhost:9001
echo   • Prometheus:           http://localhost:9090
echo   • Nginx Proxy:          http://localhost:8080
echo.
echo BOSHQARUV:
echo   • Jonli loglar:  logs.bat
echo   • To'xtatish:    stop.bat
echo ==================================================================
echo.
pause
exit /b 0

REM ============================================================================
REM MAHALLIY (LOCAL) REJIM (Agar Docker bo'lmasa)
REM ============================================================================
:LOCAL_MODE
echo.
echo [3/5] MAHALLIY REJIM: Python va Node.js tekshirilmoqda...

set "PY_CMD="
where python > nul 2>&1
if not errorlevel 1 set "PY_CMD=python"
if not defined PY_CMD (
    where py > nul 2>&1
    if not errorlevel 1 set "PY_CMD=py"
)

if not defined PY_CMD (
    echo.
    echo [XATO] Python topilmadi!
    echo Iltimos, Python 3.11+ ni o'rnating: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo     [OK] Python topildi: %PY_CMD%

REM Virtual muhitni tekshirish
if not exist "venv" (
    echo     Virtual muhit (venv) yaratilmoqda...
    %PY_CMD% -m venv venv
    if errorlevel 1 (
        echo [XATO] Virtual muhit yaratib bo'lmadi.
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat 2> nul || goto VENV_FAIL
goto VENV_OK

:VENV_FAIL
echo     [OGOHLANTIRISH] venv aktivlashtirib bo'lmadi, asosiy python ishlatiladi.
set "ACT_PY=%PY_CMD%"
goto PIP_INSTALL

:VENV_OK
set "ACT_PY=python"

:PIP_INSTALL
echo     Kutubxonalar tekshirilmoqda (requirements.txt)...
%ACT_PY% -m pip install -r requirements.txt > nul 2>&1

REM Node.js va WebApp
where node > nul 2>&1
if not errorlevel 1 (
    if exist "webapp" (
        if not exist "webapp\node_modules" (
            echo     Web App paketlari o'rnatilmoqda (npm install)...
            pushd webapp
            call npm install > nul 2>&1
            popd
        )
    )
)

echo.
echo [4/5] Docker bazasi (agar mavjud bo'lsa) ko'tarilmoqda...
if "%HAS_DOCKER%"=="1" (
    docker compose -p iiv-bot up -d postgres redis > nul 2>&1
)

echo.
echo [5/5] Xizmatlar ishga tushirilmoqda...
echo.
echo ==================================================================
echo   BARCHA XIZMATLAR ISHGA TUSHIRILMOQDA!
echo   - Web App:      http://localhost:3000
echo   - Admin Panel:  http://localhost:3000/admin
echo   - Web API:      http://localhost:8081
echo ==================================================================
echo.

start "IIV Web API" cmd /k "cd /d %~dp0 && %ACT_PY% -m bot.api.server"
timeout /t 2 /nobreak > nul

where node > nul 2>&1
if not errorlevel 1 (
    if exist "webapp" (
        start "IIV Web App (Port 3000)" cmd /k "cd /d %~dp0\webapp && npm run dev"
        timeout /t 2 /nobreak > nul
    )
)

start "IIV Telegram Bot" cmd /k "cd /d %~dp0 && %ACT_PY% run_bot.py"

echo Barcha oynalar alohida ochildi. Ushbu oynani yopishingiz mumkin.
pause
exit /b 0
