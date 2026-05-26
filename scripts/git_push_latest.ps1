# 최신 변경사항 커밋 후 GitHub(main)에 push
# 사용: PowerShell → cd 프로젝트 루트 → .\scripts\git_push_latest.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path (Join-Path $Root ".git"))) {
    Write-Host "Git 저장소가 없습니다. 먼저 .\scripts\prepare_github_upload.ps1 를 실행하세요." -ForegroundColor Red
    exit 1
}

Write-Host "=== git status ===" -ForegroundColor Cyan
git status -sb

$exclude = @(
    ".env", ".env.local", ".env.production",
    ".streamlit\secrets.toml",
    "credentials.json", "secrets.json",
    "_git_push_report.txt", "_shell_test.txt"
)
git add -A
foreach ($rel in $exclude) {
    $p = Join-Path $Root $rel
    if (Test-Path $p) {
        git reset HEAD -- $rel 2>$null
    }
}

$staged = git diff --cached --name-only
if (-not $staged) {
    Write-Host "커밋할 변경이 없습니다. push 만 시도합니다." -ForegroundColor Yellow
} else {
    Write-Host "`n=== commit ===" -ForegroundColor Cyan
    $msg = @"
Improve STEP2 birth date input and step navigation UX

- Replace date_input calendar with YYYY/MM/DD text field (PC/mobile consistent)
- Faster step transitions with early DOM sync and shorter scroll lock
- Home NOVA banner on desktop; STEP2 two-column form layout on PC
"@
    git commit -m $msg
}

$branch = (git branch --show-current).Trim()
if (-not $branch) { $branch = "main" }

Write-Host "`n=== push origin $branch ===" -ForegroundColor Cyan
git push -u origin $branch

Write-Host "`n완료: https://github.com/dgim9578-dot/sajukkagi-webapp" -ForegroundColor Green
git log -1 --oneline
