# webapp/scripts/dev.ps1 — 一键启动 WebApp（后端 + 前端 dev server）
#
# 用法：
#   cd e:\Projects\NDXinfo
#   .\webapp\scripts\dev.ps1
#
# 用真 trader 引擎：
#   $env:NDXINFO_BACKEND='real' ; $env:NDXINFO_BROKER='simulation' ; .\webapp\scripts\dev.ps1
#
# 接 Alpaca Paper：
#   $env:NDXINFO_BACKEND='real' ; $env:NDXINFO_BROKER='alpaca' ; `
#   $env:APCA_API_KEY_ID='PK...' ; $env:APCA_API_SECRET_KEY='...' ; `
#   .\webapp\scripts\dev.ps1
#
# 默认启两个后台进程：
#   - 后端  FastAPI  http://127.0.0.1:8765   (Swagger / docs)
#   - 前端  Vite      http://127.0.0.1:5173

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot) | Out-Null
Set-Location ".."
$Root = (Get-Location).Path
Set-Location $Root

Write-Host "== Trader WebApp dev launcher =="
Write-Host "  root: $Root"

# ---------- 后端 ----------
if (-not (Test-Path "$Root\.venv\Scripts\python.exe")) {
    Write-Host "  [backend] starting (one-off install may take a while)"
}

$env:PYTHONPATH = $Root
$backendCmd = @"
cd /d $Root && python -m uvicorn webapp.backend.server:app --port 8765 --log-level info
"@
Write-Host ""
Write-Host "== Starting backend (FastAPI on :8765) =="
Write-Host "  URL: http://127.0.0.1:8765/docs"
Write-Host "  Logs will stream below."
Write-Host ""

$backendProc = Start-Process -FilePath powershell -ArgumentList "-NoProfile","-Command",$backendCmd -PassThru -WindowStyle Hidden

# 等待后端 ready
$backendReady = $false
for ($i=0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 800
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:8765/api/health" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) {
            $backendReady = $true
            Write-Host "  [ok] backend health check passed."
            break
        }
    } catch {
        Write-Host "  ... waiting for backend ($($i+1)/30)"
    }
}
if (-not $backendReady) {
    Write-Host "  [err] backend failed to start" -ForegroundColor Red
    exit 1
}

# ---------- 前端 ----------
Write-Host ""
Write-Host "== Starting frontend (Vite on :5173) =="

Set-Location "$Root\webapp\frontend"
if (-not (Test-Path "node_modules")) {
    Write-Host "  [frontend] installing dependencies (one-off, ~1 min)..."
    npm install --no-audit --no-fund --silent
}

$frontendCmd = "cd `"$Root\webapp\frontend`" && npm run dev"
$frontendProc = Start-Process -FilePath powershell -ArgumentList "-NoProfile","-Command",$frontendCmd -PassThru -WindowStyle Hidden

# 等待前端 ready
$frontendReady = $false
for ($i=0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 800
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:5173" -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) {
            $frontendReady = $true
            Write-Host "  [ok] frontend dev server up."
            break
        }
    } catch {
        # Vite 返回 HTML 前可能先返回 404；尝试 /src/main.tsx
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:5173/src/main.tsx" -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) {
                $frontendReady = $true
                Write-Host "  [ok] frontend dev server up."
                break
            }
        } catch {}
        Write-Host "  ... waiting for frontend ($($i+1)/30)"
    }
}

if (-not $frontendReady) {
    Write-Host "  [warn] frontend not yet reachable; process started in background anyway."
}

Write-Host ""
Write-Host "================================================================"
Write-Host "  Backend  : http://127.0.0.1:8765/docs   (Swagger UI)"
Write-Host "  Frontend : http://127.0.0.1:5173       (Vite dev server)"
Write-Host "  Hint     : open the frontend URL in your browser."
Write-Host "  Stop     : close this terminal; press Ctrl+C in either of"
Write-Host "             the popped-up terminals."
Write-Host "================================================================"

# 让当前 ps1 挂住，按 Ctrl+C 退出（kill 两个子进程）
try {
    while ($true) { Start-Sleep -Seconds 60 }
} finally {
    Write-Host "Stopping backend..."
    try { Stop-Process -Id $backendProc.Id -Force -EA SilentlyContinue } catch {}
    Write-Host "Stopping frontend..."
    try { Stop-Process -Id $frontendProc.Id -Force -EA SilentlyContinue } catch {}
    Set-Location $Root
}
