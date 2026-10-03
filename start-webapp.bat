@echo off
chcp 65001 > nul
title IIV EduBot - Next.js Web App Server
color 0A

cd /d "%~dp0\webapp"

echo.
echo =======================================================
echo   IIV EDUBOT v2.0 - TELEGRAM WEB APP ^& ADMIN PLATFORM
echo =======================================================
echo.

where node > nul 2>&1
if errorlevel 1 (
    echo [XATO] Node.js o'rnatilmagan!
    echo Iltimos, https://nodejs.org saytidan Node.js ni o'rnating.
    pause
    exit /b 1
)

echo [1/3] Server muhiti tekshirildi: Node.js OK

if not exist "node_modules" (
    echo [MA'LUMOT] Web App paketlari - node_modules topilmadi.
    echo O'rnatilmoqda - npm install...
    call npm install
    if errorlevel 1 (
        echo [XATO] npm install muvaffaqiyatsiz tugadi!
        pause
        exit /b 1
    )
    echo [OK] Paketlar muvaffaqiyatli o'rnatildi.
)

set "PY_CMD=python"
if exist "%~dp0venv\Scripts\python.exe" set "PY_CMD=%~dp0venv\Scripts\python.exe"

echo [2/3] Web API (port 8081) yangi oynada ochilmoqda...
start "IIV Web API" cmd /k "cd /d %~dp0 && %PY_CMD% -m bot.api.server"
echo [3/3] Next.js Web App ishga tushirilmoqda...
echo.
echo =======================================================
echo   MANZILLAR:
echo   - Foydalanuvchi Mini App:   http://localhost:3000
echo   - Administrator Paneli:    http://localhost:3000/admin
echo.
echo   Telegramda ochish uchun:
echo   npx cloudflared tunnel --url http://localhost:3000
echo =======================================================
echo.

npm run dev

