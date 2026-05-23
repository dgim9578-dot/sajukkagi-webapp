# SajuPro - admin app (STEP12 enabled, port 8502)
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_lan_ip.ps1")

$Root = Split-Path -Parent $PSScriptRoot
$Lan = Get-SajuLanIPv4

$env:SAJU_ADMIN_ENABLED = "true"
Remove-Item Env:SAJU_BRIEFING_WEB_URL -ErrorAction SilentlyContinue

$SecretsFile = Join-Path $Root ".streamlit\secrets.toml"
if (-not (Test-Path -LiteralPath $SecretsFile)) {
    Write-Host ""
    Write-Host "  [필수] secrets.toml 이 없습니다." -ForegroundColor Red
    Write-Host "  실행: .\scripts\setup-streamlit-secrets.bat" -ForegroundColor Yellow
    Write-Host "  또는 example 을 복사해 SAJU_ADMIN_PASSWORD 를 설정하세요." -ForegroundColor Yellow
    Write-Host ""
    & (Join-Path $PSScriptRoot "setup-streamlit-secrets.ps1")
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  SajuPro - Admin" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  PC:     http://localhost:8502/?goto=12"
Write-Host "  Mobile: http://${Lan}:8502/?goto=12" -ForegroundColor Green
Write-Host ""
Write-Host "  Admin password: .streamlit\secrets.toml -> SAJU_ADMIN_PASSWORD" -ForegroundColor DarkGray
Write-Host ""

$venvPy = Join-Path $Root "venv\Scripts\python.exe"
if (Test-Path $venvPy) {
    $py = $venvPy
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $py = "python"
} else {
    Write-Host "Python not found." -ForegroundColor Red
    exit 1
}

Set-Location $Root
& $py -m streamlit run app.py --server.address 0.0.0.0 --server.port 8502
