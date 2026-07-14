# webapp/scripts/start_alpaca_paper.ps1 — 用 Alpaca Paper 账户启 webapp
#
# 前提：
#   1) 注册 Alpaca Paper: https://app.alpaca.markets/signup
#   2) 生成 API Key (https://app.alpaca.markets/paper/dashboard/overview)
#   3) 安装: pip install alpaca-py
#   4) 把 PK... 和 SK... 替换成你的真 key
#
# 启动：
#   cd e:\Projects\NDXinfo
#   $env:APCA_API_KEY_ID='PK...'
#   $env:APCA_API_SECRET_KEY='SK...'
#   .\webapp\scripts\start_alpaca_paper.ps1

$ErrorActionPreference = "Stop"
$env:NDXINFO_BACKEND  = "real"
$env:NDXINFO_BROKER   = "alpaca"
# 其它可选：
#   $env:NDXINFO_STRATEGY = "multi"  (macd / rsi / ma_trend / bollinger / kdj / boll_width / ensemble)
#   $env:NDXINFO_CASH     = "100000"

# 验证 key 在
if (-not $env:APCA_API_KEY_ID -or -not $env:APCA_API_SECRET_KEY) {
    Write-Host ""
    Write-Host "  [ERROR] APCA_API_KEY_ID / APCA_API_SECRET_KEY 未设置。" -ForegroundColor Red
    Write-Host ""
    Write-Host "  1. 打开 https://app.alpaca.markets/signup 注册一个 Paper 账户（免费）"
    Write-Host "  2. 在 https://app.alpaca.markets/paper/dashboard/overview 复制 API Key"
    Write-Host "  3. 在 PowerShell 里："
    Write-Host "       \$env:APCA_API_KEY_ID='PK...your-key...'"
    Write-Host "       \$env:APCA_API_SECRET_KEY='SK...your-key...'"
    Write-Host "       .\webapp\scripts\start_alpaca_paper.ps1"
    Write-Host ""
    exit 1
}

# AlpacaPy 没装就提示
try {
    python -c "import alpaca" 2>$null
    if ($LASTEXITCODE -ne 0) { throw "no alpaca" }
} catch {
    Write-Host ""
    Write-Host "  [ERROR] 未安装 alpaca-py. 先执行: pip install alpaca-py" -ForegroundColor Red
    Write-Host ""
    exit 1
}

Write-Host "  backend   = real (Alpaca Paper)"
Write-Host "  key_id    = $($env:APCA_API_KEY_ID.Substring(0, 6))..."
Write-Host "  strategy  = $($env:NDXINFO_STRATEGY ?? 'multi')"
Write-Host ""

# 复用 dev.ps1
& "$PSScriptRoot\dev.ps1"
