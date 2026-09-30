@echo off
chcp 65001 > nul
title IIV EduBot - Barcha Xizmatlarni Ishga Tushirish
color 0B

echo ========================================================
echo   IIV EDUBOT v2.0 - BARCHA XIZMATLARNI ISHGA TUSHIRISH
echo ========================================================
echo.

echo [1/4] Web API (port 8081) yangi oynada ochilmoqda...
start "IIV Web API" cmd /k "cd /d %~dp0 && python -m bot.api.server"

timeout /t 2 /nobreak > nul

echo [2/4] Web App serveri yangi oynada ochilmoqda...
start "IIV Web App Server (Port 3000)" cmd /k "cd /d %~dp0\webapp && npm run dev"

timeout /t 3 /nobreak > nul

echo [3/4] Telegram uchun HTTPS tunnel (ixtiyoriy, telefon Mini App)...
start "IIV Telegram Tunnel" cmd /k "cd /d %~dp0 && tunnel.bat"

timeout /t 2 /nobreak > nul

echo [4/4] Telegram Bot ishga tushirilmoqda...
start "IIV Telegram Bot (@ijaransubot)" cmd /k "cd /d %~dp0 && python run_bot.py"

echo.
echo ========================================================
echo   BARCHA TIZIMLAR ISHGA TUSHIRILDI!
echo   - Web App server: http://localhost:3000
echo   - Telegram Bot: @ijaransubot
echo ========================================================
echo.
pause
