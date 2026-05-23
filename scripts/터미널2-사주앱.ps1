# 사주프로 — Streamlit 사주분석 (모바일 접속 가능)

# 사용: PowerShell에서

#   cd "C:\Users\Administrator\Desktop\사주프로"

#   .\scripts\터미널2-사주앱.ps1



$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "_lan_ip.ps1")



$Root = Split-Path -Parent $PSScriptRoot

$Lan = Get-SajuLanIPv4



Write-Host ""

Write-Host "========================================" -ForegroundColor Magenta

Write-Host "  사주프로 · 사주분석 (Streamlit)" -ForegroundColor Magenta

Write-Host "========================================" -ForegroundColor Magenta

Write-Host ""

Write-Host "  [PC]     http://localhost:8501"

Write-Host "  [모바일] http://${Lan}:8501" -ForegroundColor Green

Write-Host ""

Write-Host "  종료: Ctrl+C" -ForegroundColor DarkGray

Write-Host ""



$venvPy = Join-Path $Root "venv\Scripts\python.exe"

if (Test-Path $venvPy) {

    $py = $venvPy

} elseif (Get-Command python -ErrorAction SilentlyContinue) {

    $py = "python"

} else {

    Write-Host "Python을 찾을 수 없습니다. venv를 만들거나 Python을 설치하세요." -ForegroundColor Red

    exit 1

}



Set-Location $Root

Remove-Item Env:SAJU_BRIEFING_WEB_URL -ErrorAction SilentlyContinue



& $py -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501

