# SajuPro - general user app (STEP12 hidden, port 8501)
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_lan_ip.ps1")

$Root = Split-Path -Parent $PSScriptRoot
$Lan = Get-SajuLanIPv4

$env:SAJU_ADMIN_ENABLED = "false"
Remove-Item Env:SAJU_BRIEFING_WEB_URL -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SajuPro - User (general)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PC:     http://localhost:8501"
Write-Host "  Mobile: http://${Lan}:8501" -ForegroundColor Green
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
& $py -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
