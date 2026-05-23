# GitHub 업로드 준비 (최초 1회)
# 사용: PowerShell에서 .\scripts\prepare_github_upload.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== GitHub 업로드 준비 ===" -ForegroundColor Cyan

# 1) 배포 점검
Write-Host "`n[1/4] 배포 전 점검..." -ForegroundColor Yellow
python scripts\pre_deploy_check.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "점검 실패. FAIL 항목 수정 후 다시 실행하세요." -ForegroundColor Red
    exit 1
}

# 2) secrets / DB 미포함 확인
$secrets = Join-Path $Root ".streamlit\secrets.toml"
if (Test-Path $secrets) {
    Write-Host "`n[2/4] secrets.toml 존재 — .gitignore 로 제외됩니다." -ForegroundColor Green
} else {
    Write-Host "`n[2/4] secrets.toml 없음 — Streamlit Cloud Secrets 에 직접 입력하세요." -ForegroundColor Yellow
}

foreach ($f in @("saju_app.db", "step2_form_prefill.json", "consultation_chat_archive.jsonl")) {
    if (Test-Path (Join-Path $Root $f)) {
        Write-Host "  로컬 데이터 $f — Git에 올리지 않습니다 (.gitignore)" -ForegroundColor DarkGray
    }
}

# 3) git init
Write-Host "`n[3/4] Git 저장소..." -ForegroundColor Yellow
if (-not (Test-Path (Join-Path $Root ".git"))) {
    git init
    Write-Host "  git init 완료" -ForegroundColor Green
} else {
    Write-Host "  이미 Git 저장소입니다." -ForegroundColor Green
}

git status -sb

# 4) 다음 단계 안내
Write-Host "`n[4/4] 다음 단계" -ForegroundColor Yellow
Write-Host @"

1. GitHub에서 새 저장소 생성 (Private 권장)
2. 아래 명령으로 첫 푸시 (YOUR_USER/YOUR_REPO 교체):

   git add .
   git commit -m "Initial commit: 사주까기 Streamlit 웹앱"
   git branch -M main
   git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
   git push -u origin main

3. https://share.streamlit.io/ → New app
   - Main file: app.py
   - Secrets: .streamlit/secrets.toml.example 참고
   - SAJU_ADMIN_ENABLED = false (공개 배포)

자세한 내용: WEBAPP_DEPLOYMENT.md

"@ -ForegroundColor White
