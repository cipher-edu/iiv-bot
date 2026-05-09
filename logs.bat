@echo off
title IIV EduBot - Bot loglari
chcp 65001 > nul
color 0A

cd /d "%~dp0"

echo.
echo ===============================================
echo   BOT LOGLARI (CTRL+C - chiqish)
echo ===============================================
echo.

docker logs -f --tail 50 iiv_bot
