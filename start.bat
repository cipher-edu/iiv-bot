@echo off
chcp 65001 > nul
title IIV EduBot - Ishga tushirish
color 0B

cd /d "%~dp0"

echo.
echo ===============================================
echo   IIV EDUBOT PLATFORM - AVTO ISHGA TUSHIRISH
echo ===============================================
echo.

REM --- 1. Docker mavjudligini tekshirish ---
where docker > nul 2>&1
if errorlevel 1 goto NO_DOCKER
echo [1/5] Docker o'rnatilgan: OK

REM --- 2. Docker daemon holatini tekshirish ---
docker info > nul 2>&1
if not errorlevel 1 goto DOCKER_READY

echo [2/5] Docker Desktop ishga tushirilmoqda...

set "DOCKER_EXE="
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" set "DOCKER_EXE=%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
if not defined DOCKER_EXE if exist "%ProgramW6432%\Docker\Docker\Docker Desktop.exe" set "DOCKER_EXE=%ProgramW6432%\Docker\Docker\Docker Desktop.exe"
if not defined DOCKER_EXE if exist "%LocalAppData%\Docker\Docker Desktop.exe" set "DOCKER_EXE=%LocalAppData%\Docker\Docker Desktop.exe"

if not defined DOCKER_EXE goto NO_DOCKER_DESKTOP

start "" "%DOCKER_EXE%"

echo     Docker daemon javob berishi kutilmoqda (90 soniyagacha)...
set /a WAIT=0
:WAIT_DOCKER
timeout /t 3 /nobreak > nul
set /a WAIT=%WAIT%+3
docker info > nul 2>&1
if not errorlevel 1 goto DOCKER_STARTED
if %WAIT% GEQ 90 goto DOCKER_TIMEOUT
echo     ... %WAIT% soniya
goto WAIT_DOCKER

:DOCKER_STARTED
echo [2/5] Docker daemon: OK
goto CHECK_ENV

:DOCKER_READY
echo [2/5] Docker daemon allaqachon ishlamoqda: OK

:CHECK_ENV
REM --- 3. .env fayli ---
if not exist ".env" goto NO_ENV
echo [3/5] .env fayli: OK

REM --- 4. docker-compose.yml ---
if not exist "docker-compose.yml" goto NO_COMPOSE
echo [4/5] docker-compose.yml: OK

REM --- 5. Konteynerlar ---
echo.
echo [5/5] Konteynerlar ko'tarilmoqda... (birinchi marta 1-2 daqiqa olishi mumkin)
echo.

docker compose -p iiv-bot up -d --remove-orphans
if errorlevel 1 goto COMPOSE_FAIL

echo.
echo ===============================================
echo   KONTEYNERLAR HOLATI
echo ===============================================
docker compose -p iiv-bot ps

echo.
echo ===============================================
echo   LOYIHA TAYYOR!
echo ===============================================
echo.
echo Bot:           Telegram @nsusupportbot
echo Grafana:       http://localhost:3000
echo pgAdmin:       http://localhost:5050
echo MinIO konsoli: http://localhost:9001
echo Prometheus:    http://localhost:9090
echo Nginx:         http://localhost:8080
echo.
echo Bot loglari:   logs.bat
echo To'xtatish:    stop.bat
echo.
pause
exit /b 0

:NO_DOCKER
echo.
echo [XATO] Docker o'rnatilmagan!
echo Docker Desktop ni shu yerdan yuklab oling:
echo   https://www.docker.com/products/docker-desktop
echo.
pause
exit /b 1

:NO_DOCKER_DESKTOP
echo.
echo [XATO] Docker Desktop topilmadi (Program Files yoki LocalAppData ichida).
echo Iltimos, Docker Desktop ni qo'lda ishga tushiring va yana urinib ko'ring.
echo.
pause
exit /b 1

:DOCKER_TIMEOUT
echo.
echo [XATO] Docker daemon 90 soniyada javob bermadi.
echo Docker Desktop oynasida tray belgisini tekshiring.
echo.
pause
exit /b 1

:NO_ENV
echo.
echo [XATO] .env fayli topilmadi: %CD%\.env
echo .env.example ni .env nomi bilan nusxalang va qiymatlarni to'ldiring.
echo.
pause
exit /b 1

:NO_COMPOSE
echo.
echo [XATO] docker-compose.yml topilmadi: %CD%\docker-compose.yml
echo.
pause
exit /b 1

:COMPOSE_FAIL
echo.
echo [XATO] Konteynerlarni ishga tushirib bo'lmadi.
echo Yuqoridagi xato xabarini tekshiring.
echo.
pause
exit /b 1
