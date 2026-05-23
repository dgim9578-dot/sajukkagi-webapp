# 상담 아카이브 180일 초과 분 삭제 (작업 스케줄러용)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root "venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}
$Days = if ($env:SAJU_ARCHIVE_PRUNE_DAYS) { $env:SAJU_ARCHIVE_PRUNE_DAYS } else { "180" }
& $Python (Join-Path $Root "scripts\archive_prune.py") --days $Days @args
