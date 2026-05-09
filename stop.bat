@echo off
setlocal EnableExtensions
title IIV EduBot - To'xtatish
chcp 65001 > nul
color 0E

cd /d "%~dp0"

echo.
echo ===============================================
echo   IIV EDUBOT PLATFORM - TO'XTATISH
echo ===============================================
echo.

docker info > nul 2>&1
if errorlevel 1 (
    echo Docker daemon ishlamayapti - hech narsa to'xtatishga yo'q.
    pause
    exit /b 0
)

echo Konteynerlar to'xtatilmoqda...
docker compose -p iiv-bot stop
if errorlevel 1 (
    echo [XATO] Konteynerlarni to'xtatib bo'lmadi.
    pause
    exit /b 1
)

echo.
echo ===============================================
echo   TO'XTATILDI
echo ===============================================
echo.
echo Ma'lumotlar saqlangan (volumes), keyingi safar:
echo   start.bat
echo bilan davom etadi.
echo.
pause
