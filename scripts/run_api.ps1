# Briefing FastAPI — 프로젝트 루트에서 uvicorn 실행
# 사용법:
#   cd "C:\Users\Administrator\Desktop\사주프로"
#   .\scripts\run_api.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$env:PYTHONPATH = $Root

$Python = Join-Path $Root "venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$uvicornOk = & $Python -c "import uvicorn" 2>$null
if (-not $uvicornOk) {
    Write-Host "uvicorn이 venv에 없습니다. 설치 중..."
    & $Python -m pip install "fastapi>=0.115.0" "uvicorn[standard]>=0.30.0"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "설치 실패. 수동 실행: .\venv\Scripts\pip install -r requirements.txt"
        exit 1
    }
}

Write-Host "cwd: $Root"
Write-Host "API: http://127.0.0.1:8000  (health: /health)"
& $Python -m uvicorn saju_app.api.app:app --reload --host 127.0.0.1 --port 8000
