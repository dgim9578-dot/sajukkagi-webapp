# [구버전] 3D/Next.js 브리핑은 제거되었습니다. 사주앱(Streamlit)만 사용합니다.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  3D 브리핑(포트 3000)은 사용하지 않습니다" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "  사주분석은 Streamlit 한 가지로만 제공합니다." -ForegroundColor Cyan
Write-Host "  아래 사주앱 서버를 시작합니다 (http://localhost:8501)" -ForegroundColor Cyan
Write-Host ""

& (Join-Path $PSScriptRoot "터미널2-사주앱.ps1")
