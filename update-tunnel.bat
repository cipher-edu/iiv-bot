@echo off
chcp 65001 > nul
title IIV EduBot - Yangi Telegram Web App tunnel
rem Yangi trycloudflare manzil oladi, .env ga yozadi va botni qayta ishga tushiradi
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0update-tunnel.ps1" %*
pause
