@echo off
setlocal EnableExtensions
chcp 65001 > nul
title IIV EduBot - Barcha Xizmatlarni Ishga Tushirish
color 0B

REM ============================================================================
REM  IIV EDUBOT - BIR TUGMA BILAN TO'LIQ O'RNATISH VA ISHGA TUSHIRISH
REM  Yangi kompyuterda ham ishlaydi: .env, Python venv, pip, npm install,
REM  PostgreSQL/Redis (Docker), Web API, Web App, Tunnel va Telegram Bot.
REM  Eslatma: if-bloklar ichida qavslar bilan echo ishlatilmagan (cmd xatosi).
REM ============================================================================

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
cd /d "%ROOT%"

echo ========================================================
echo   IIV EDUBOT v2.0 - BARCHA XIZMATLARNI ISHGA TUSHIRISH
echo ========================================================
echo   Papka: %ROOT%
echo.

REM ---------------------------------------------------------------------------
REM [1/8] .env konfiguratsiyasi
REM ---------------------------------------------------------------------------
echo [1/8] Konfiguratsiya - .env tekshirilmoqda...
if exist ".env" goto ENV_OK
if not exist ".env.example" goto ENV_FAIL
copy /y ".env.example" ".env" > nul
echo     [OK] .env fayli .env.example dan yaratildi.
echo     [MUHIM] BOT_TOKEN, BOT_ADMIN_IDS va parollarni to'ldiring!
echo     Notepad ochilmoqda - to'ldirib, saqlab, yoping...
start /wait notepad ".env"
goto ENV_DONE

:ENV_FAIL
echo     [XATO] .env ham, .env.example ham topilmadi!
pause
exit /b 1

:ENV_OK
echo     [OK] .env fayli mavjud.

:ENV_DONE

REM ---------------------------------------------------------------------------
REM [2/8] Python topish - Windows Store "soxta" python.exe ni chetlab o'tadi
REM ---------------------------------------------------------------------------
echo [2/8] Python tekshirilmoqda...
set "PY_CMD="
python --version > nul 2>&1
if not errorlevel 1 set "PY_CMD=python"
if defined PY_CMD goto PY_FOUND
py -3 --version > nul 2>&1
if not errorlevel 1 set "PY_CMD=py -3"
if defined PY_CMD goto PY_FOUND

echo     [XATO] Python topilmadi!
echo     Python 3.11+ ni o'rnating: https://www.python.org/downloads/
echo     O'rnatishda "Add python.exe to PATH" ni belgilang va terminalni qayta oching.
pause
exit /b 1

:PY_FOUND
%PY_CMD% -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" > nul 2>&1
if errorlevel 1 echo     [OGOHLANTIRISH] Python 3.11+ tavsiya etiladi. Joriy versiya eskiroq.
for /f "delims=" %%v in ('%PY_CMD% --version 2^>^&1') do echo     [OK] %%v

REM ---------------------------------------------------------------------------
REM [3/8] Virtual muhit - boshqa kompyuterdan ko'chirilgan buzuq venv qayta yaratiladi
REM ---------------------------------------------------------------------------
echo [3/8] Virtual muhit - venv tekshirilmoqda...
set "VPY=%ROOT%\venv\Scripts\python.exe"
if not exist "%VPY%" goto VENV_CREATE
"%VPY%" -c "import sys" > nul 2>&1
if not errorlevel 1 goto VENV_OK
echo     venv buzilgan - boshqa kompyuterdan ko'chirilgan. Qayta yaratilmoqda...
rmdir /s /q "%ROOT%\venv"

:VENV_CREATE
echo     venv yaratilmoqda...
%PY_CMD% -m venv "%ROOT%\venv"
if errorlevel 1 goto VENV_FAIL
if not exist "%VPY%" goto VENV_FAIL
goto VENV_OK

:VENV_FAIL
echo     [XATO] Virtual muhit yaratib bo'lmadi!
pause
exit /b 1

:VENV_OK
echo     [OK] venv tayyor.

REM ---------------------------------------------------------------------------
REM [4/8] Python kutubxonalari
REM ---------------------------------------------------------------------------
echo [4/8] Python kutubxonalari o'rnatilmoqda - requirements.txt...
"%VPY%" -m pip install --disable-pip-version-check -q --upgrade pip > nul 2>&1
"%VPY%" -m pip install --disable-pip-version-check -q -r "%ROOT%\requirements.txt"
if errorlevel 1 goto PIP_FAIL
echo     [OK] Python kutubxonalari tayyor.
goto PIP_DONE

:PIP_FAIL
echo     [XATO] pip install muvaffaqiyatsiz tugadi! Yuqoridagi xatoni ko'ring.
echo     Internet aloqasini tekshiring va qayta urinib ko'ring.
pause
exit /b 1

:PIP_DONE

REM ---------------------------------------------------------------------------
REM [5/8] Node.js va Web App paketlari
REM ---------------------------------------------------------------------------
echo [5/8] Node.js tekshirilmoqda...
node -v > nul 2>&1
if errorlevel 1 goto NODE_FAIL
call npm -v > nul 2>&1
if errorlevel 1 goto NODE_FAIL
for /f "delims=" %%v in ('node -v') do echo     [OK] Node.js %%v

if exist "%ROOT%\webapp\node_modules\.bin\next.cmd" goto NPM_OK
echo     Web App paketlari o'rnatilmoqda - npm install, biroz kuting...
pushd "%ROOT%\webapp"
call npm install
set "NPM_ERR=%errorlevel%"
popd
if not "%NPM_ERR%"=="0" goto NPM_FAIL
if not exist "%ROOT%\webapp\node_modules\.bin\next.cmd" goto NPM_FAIL

:NPM_OK
echo     [OK] Web App paketlari tayyor.
goto NODE_DONE

:NODE_FAIL
echo     [XATO] Node.js yoki npm topilmadi!
echo     Node.js LTS ni o'rnating: https://nodejs.org
echo     O'rnatgandan keyin terminalni yopib, qayta oching.
pause
exit /b 1

:NPM_FAIL
echo     [XATO] npm install muvaffaqiyatsiz tugadi!
echo     webapp\node_modules papkasini o'chirib, qayta urinib ko'ring.
pause
exit /b 1

:NODE_DONE

REM ---------------------------------------------------------------------------
REM [6/8] PostgreSQL va Redis - Docker orqali, agar mavjud bo'lsa
REM ---------------------------------------------------------------------------
echo [6/8] PostgreSQL va Redis tekshirilmoqda...
docker info > nul 2>&1
if errorlevel 1 goto NO_DOCKER
docker compose -p iiv-bot up -d postgres redis
if errorlevel 1 goto NO_DOCKER
echo     [OK] PostgreSQL va Redis Docker'da ishga tushirildi.
echo     Bazaning tayyor bo'lishi kutilmoqda...
timeout /t 8 /nobreak > nul
goto DB_DONE

:NO_DOCKER
echo     [OGOHLANTIRISH] Docker topilmadi yoki ishlamayapti.
echo     PostgreSQL :5432 va Redis :6379 shu kompyuterda ishlab turishi kerak.

:DB_DONE

REM Lokal ishga tushirishda Docker servis nomlari o'rniga localhost ishlatiladi.
REM Muhit o'zgaruvchilari .env dagi qiymatlardan ustun turadi - pydantic-settings.
set "DB_HOST=localhost"
set "REDIS_HOST=localhost"
set "MINIO_HOST=localhost"
set "PYTHONUTF8=1"

REM ---------------------------------------------------------------------------
REM [7/8] Xizmatlarni alohida oynalarda ishga tushirish
REM ---------------------------------------------------------------------------
echo [7/8] Xizmatlar ishga tushirilmoqda...

REM Port band bo'lsa - xizmat allaqachon ishlayapti, ikkinchi nusxa ochilmaydi
REM - WinError 10048 xatosining oldini oladi.
echo     - Web API - port 8081
netstat -ano | findstr /R /C:":8081 .*LISTENING" > nul
if not errorlevel 1 goto API_RUNNING
start "IIV Web API (Port 8081)" /D "%ROOT%" cmd /k ""%VPY%" -m bot.api.server"
timeout /t 2 /nobreak > nul
goto API_DONE
:API_RUNNING
echo       [OK] Web API allaqachon ishlayapti.
:API_DONE

echo     - Web App - port 3000
netstat -ano | findstr /R /C:":3000 .*LISTENING" > nul
if not errorlevel 1 goto WEB_RUNNING
start "IIV Web App Server (Port 3000)" /D "%ROOT%\webapp" cmd /k "npm run dev"
goto WEB_DONE
:WEB_RUNNING
echo       [OK] Web App allaqachon ishlayapti.
:WEB_DONE

REM trycloudflare manzili har safar yangi - uni .env ga yozib, keyin botni ochamiz
echo     - Telegram HTTPS tunnel - yangi manzil .env ga yoziladi
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\update-tunnel.ps1" -NoServices
if errorlevel 1 echo       [OGOHLANTIRISH] Tunnel ochilmadi - Mini App telefonda ishlamasligi mumkin.

echo     - Telegram Bot
REM Eski bot nusxalarini yopish - bir token bilan ikki bot Conflict beradi
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*run_bot.py*' -and $_.Name -like 'python*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" > nul 2>&1
start "IIV Telegram Bot (@ijaransubot)" /D "%ROOT%" cmd /k ""%VPY%" run_bot.py"

REM ---------------------------------------------------------------------------
REM [8/8] Yakun
REM ---------------------------------------------------------------------------
echo.
echo [8/8] Tayyor!
echo ========================================================
echo   BARCHA TIZIMLAR ISHGA TUSHIRILDI!
echo   - Web App:       http://localhost:3000
echo   - Admin Panel:   http://localhost:3000/admin
echo   - Web API:       http://localhost:8081
echo   - Telegram Bot:  @ijaransubot
echo.
echo   To'xtatish: har bir oynani yoping yoki stop.bat
echo ========================================================
echo.
pause
endlocal
