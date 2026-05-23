# 손상된 .next 캐시 삭제 (vendor-chunks/@swc.js 등 오류 시)
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
if (Test-Path .next) {
    Remove-Item -Recurse -Force .next
    Write-Host "삭제 완료: $root\.next" -ForegroundColor Green
} else {
    Write-Host ".next 폴더가 없습니다." -ForegroundColor Yellow
}
Write-Host ""
Write-Host "다음: npm run dev" -ForegroundColor Cyan
