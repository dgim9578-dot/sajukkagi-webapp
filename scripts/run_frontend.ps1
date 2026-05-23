# Next.js 3D 브리핑 덱 (frontend)
# 사용법:
#   cd "C:\Users\Administrator\Desktop\사주프로"
#   .\scripts\run_frontend.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Frontend = Join-Path $Root "frontend"
Set-Location $Frontend

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Node.js가 설치되어 있지 않습니다."
    Write-Host "https://nodejs.org 에서 LTS 버전을 설치한 뒤 터미널을 다시 열어 주세요."
    exit 1
}

Write-Host "Node: $(node -v)  npm: $(npm -v)"
Write-Host "의존성 설치 (npm install) ..."
npm install
if ($LASTEXITCODE -ne 0) {
    Write-Host "npm install 실패. 네트워크·권한을 확인하세요."
    exit 1
}

$nextBin = Join-Path $Frontend "node_modules\next\dist\bin\next"
if (-not (Test-Path $nextBin)) {
    Write-Host "next 패키지가 없습니다. frontend 폴더에서 npm install 을 다시 실행하세요."
    exit 1
}

Write-Host "브리핑 덱: http://localhost:3000"
npm run dev
