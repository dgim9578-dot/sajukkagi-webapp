# 사주까기 — 외부(휴대폰 LTE 등)에서 임시로 테스트할 때 사용
# 사무실 Wi-Fi가 아닌 곳에서도 접속 가능한 공개 URL을 만듭니다 (cloudflared Quick Tunnel).
#
# 사용법 (PowerShell):
#   cd "C:\Users\Administrator\Desktop\사주프로"
#   .\scripts\start_external_test.ps1
#
# 종료: 이 창에서 Ctrl+C → Streamlit / 터널 프로세스도 함께 종료됩니다.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Port = 8501
$VenvPython = Join-Path $Root "venv\Scripts\python.exe"
$Streamlit = Join-Path $Root "venv\Scripts\streamlit.exe"

if (-not (Test-Path $Streamlit)) {
    Write-Host "venv Streamlit이 없습니다. 먼저: python -m venv venv && .\venv\Scripts\pip install -r requirements.txt"
    exit 1
}

$cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflared) {
    Write-Host ""
    Write-Host "cloudflared 가 설치되어 있지 않습니다."
    Write-Host "1) https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
    Write-Host "   에서 Windows용 cloudflared 를 받아 PATH 에 넣거나"
    Write-Host "2) winget install Cloudflare.cloudflared"
    Write-Host ""
    Write-Host "설치 후 이 스크립트를 다시 실행하세요."
    exit 1
}

Write-Host "사주까기 Streamlit 시작 (포트 $Port) ..."
$stArgs = @(
    "run", "app.py",
    "--server.address", "127.0.0.1",
    "--server.port", "$Port",
    "--browser.gatherUsageStats", "false"
)
$stProc = Start-Process -FilePath $Streamlit -ArgumentList $stArgs -WorkingDirectory $Root -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 3
if ($stProc.HasExited) {
    Write-Host "Streamlit 시작 실패. 터미널에서 직접 실행해 보세요:"
    Write-Host "  .\venv\Scripts\streamlit.exe run app.py"
    exit 1
}

Write-Host ""
Write-Host "외부 접속 터널 연결 중... (잠시 후 https://....trycloudflare.com 주소가 나옵니다)"
Write-Host "이 링크를 휴대폰·외부 PC 브라우저에 붙여 넣으세요."
Write-Host "주의: PC를 끄거나 이 창을 닫으면 링크는 사라집니다. URL은 실행할 때마다 바뀝니다."
Write-Host ""

try {
    & cloudflared tunnel --url "http://127.0.0.1:$Port"
}
finally {
    if (-not $stProc.HasExited) {
        Stop-Process -Id $stProc.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host ""
    Write-Host "종료했습니다."
}
