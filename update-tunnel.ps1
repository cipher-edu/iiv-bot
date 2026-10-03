# ============================================================================
#  IIV EduBot - Telegram Web App uchun yangi HTTPS tunnel va .env yangilash
#
#  trycloudflare.com manzili vaqtinchalik: har safar tunnel qayta ishga
#  tushganda yangi manzil beriladi. Ushbu skript:
#    1. Eski tunnelni to'xtatadi
#    2. Web API (8081) va Web App (3000) ishlamayotgan bo'lsa ishga tushiradi
#    3. cloudflared yo'q bo'lsa yuklab oladi
#    4. Yangi tunnel ochadi va manzilini oladi
#    5. Manzilni .env dagi WEB_APP_URL ga yozadi
#    6. Botni qayta ishga tushiradi (menu tugmasi yangilanadi)
#
#  Ishlatish:  update-tunnel.bat  (ikki marta bosing)
#  -NoServices: 2-bosqich va 6-bosqich o'tkazib yuboriladi (start-all.bat uchun)
# ============================================================================
param([switch]$NoServices)

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

function Test-Port([int]$port) {
    # Tez TCP ulanish tekshiruvi (Get-NetTCPConnection juda sekin ishlaydi)
    $client = New-Object Net.Sockets.TcpClient
    try {
        $task = $client.ConnectAsync('127.0.0.1', $port)
        return ($task.Wait(500) -and $client.Connected)
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

$py = Join-Path $root 'venv\Scripts\python.exe'
if (-not (Test-Path $py)) { $py = 'python' }

Write-Host ''
Write-Host '[1/6] Eski tunnel to''xtatilmoqda...'
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force

if (-not $NoServices) {
    Write-Host '[2/6] Web API va Web App tekshirilmoqda...'
    if (Test-Port 8081) {
        Write-Host '      [OK] Web API allaqachon ishlayapti - port 8081'
    } else {
        Start-Process cmd -ArgumentList '/k', "title IIV Web API && cd /d `"$root`" && `"$py`" -m bot.api.server"
        Write-Host '      Web API ishga tushirildi - port 8081'
    }
    if (Test-Port 3000) {
        Write-Host '      [OK] Web App allaqachon ishlayapti - port 3000'
    } else {
        Start-Process cmd -ArgumentList '/k', "title IIV Web App && cd /d `"$root\webapp`" && npm run dev"
        Write-Host '      Web App ishga tushirildi - port 3000'
    }
} else {
    Write-Host '[2/6] O''tkazib yuborildi'
}

Write-Host '      Web App - port 3000 tayyor bo''lishi kutilmoqda...'
for ($i = 0; $i -lt 30 -and -not (Test-Port 3000); $i++) { Start-Sleep 2 }
if (-not (Test-Port 3000)) { Write-Host '      [OGOHLANTIRISH] Port 3000 hali ochilmadi, tunnel baribir ochiladi.' -ForegroundColor Yellow }

Write-Host '[3/6] cloudflared tekshirilmoqda...'
$cf = Join-Path $env:LOCALAPPDATA 'cloudflared.exe'
if (-not (Test-Path $cf)) {
    Write-Host '      cloudflared yuklanmoqda...'
    $ProgressPreference = 'SilentlyContinue'
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $dl = 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe'
    Invoke-WebRequest -Uri $dl -OutFile $cf
}
if (-not (Test-Path $cf)) { Write-Host '[XATO] cloudflared yuklab bo''lmadi. Internetni tekshiring.' -ForegroundColor Red; exit 1 }

Write-Host '[4/6] Yangi tunnel ochilmoqda...'
$log = Join-Path $env:TEMP 'iiv-tunnel.log'
Remove-Item $log -ErrorAction SilentlyContinue
$cfArgs = @('tunnel', '--edge-ip-version', '4', '--url', 'http://localhost:3000')
Start-Process $cf -ArgumentList $cfArgs -RedirectStandardError $log -WindowStyle Hidden

$pattern = 'https://[a-z0-9-]+\.trycloudflare\.com'
$url = $null
for ($i = 0; $i -lt 30 -and -not $url; $i++) {
    Start-Sleep 2
    if (Test-Path $log) {
        $text = Get-Content $log -Raw -ErrorAction SilentlyContinue
        if ($text) {
            $url = [regex]::Matches($text, $pattern) |
                ForEach-Object Value |
                Where-Object { $_ -ne 'https://api.trycloudflare.com' } |
                Select-Object -First 1
        }
    }
}
if (-not $url) {
    Write-Host '[XATO] Tunnel manzili olinmadi. Log:' -ForegroundColor Red
    if (Test-Path $log) { Get-Content $log -Tail 20 }
    exit 1
}
Write-Host "      [OK] $url"

Write-Host '[5/6] .env dagi WEB_APP_URL yangilanmoqda...'
$envPath = Join-Path $root '.env'
$c = ''
if (Test-Path $envPath) { $c = [IO.File]::ReadAllText($envPath) }
if ($c -match '(?m)^WEB_APP_URL=') {
    $c = [regex]::Replace($c, '(?m)^WEB_APP_URL=[^\r\n]*', "WEB_APP_URL=$url")
} else {
    $c = $c.TrimEnd() + "`r`nWEB_APP_URL=$url`r`n"
}
[IO.File]::WriteAllText($envPath, $c, (New-Object Text.UTF8Encoding $false))
Write-Host '      [OK] .env yangilandi'

if (-not $NoServices) {
    Write-Host '[6/6] Bot qayta ishga tushirilmoqda...'
    Get-CimInstance Win32_Process -Filter "name='python.exe'" |
        Where-Object { $_.CommandLine -like '*run_bot*' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
    Start-Process cmd -ArgumentList '/k', "title IIV Telegram Bot && cd /d `"$root`" && set PYTHONUTF8=1 && `"$py`" run_bot.py"
} else {
    Write-Host '[6/6] O''tkazib yuborildi'
}

Write-Host ''
Write-Host '==========================================================' -ForegroundColor Green
Write-Host "  YANGI WEB APP MANZILI: $url" -ForegroundColor Green
Write-Host '  Telegramda bot chatini yopib, qayta oching.' -ForegroundColor Green
Write-Host '  Tunnelni to''xtatish: Stop-Process -Name cloudflared' -ForegroundColor Green
Write-Host '==========================================================' -ForegroundColor Green
exit 0
