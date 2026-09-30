@echo off
chcp 65001 > nul
title IIV EduBot - Telegram Web App HTTPS Tunnel
color 0B

echo ========================================================
echo   IIV EDUBOT - TELEGRAM UCHUN HTTPS TUNNEL
echo ========================================================
echo.
echo [1/3] HTTPS Tunnel (localhost.run) faollashtirilmoqda...
echo.

ssh -o StrictHostKeyChecking=no -R 80:localhost:3000 nokey@localhost.run
if errorlevel 1 (
    echo.
    echo [2/3] Pinggy Tunnel sinab ko'rilmoqda...
    ssh -p 443 -o StrictHostKeyChecking=no -R0:localhost:3000 a.pinggy.io
    if errorlevel 1 (
        echo.
        echo [3/3] Cloudflare Tunnel ishga tushirilmoqda...
        cloudflared tunnel --edge-ip-version 4 --url http://localhost:3000
    )
)

pause
