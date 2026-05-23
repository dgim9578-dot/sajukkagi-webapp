# 사주앱 접속 주소만 출력 (서버는 안 켬)

#   .\scripts\모바일-접속주소.ps1



. (Join-Path $PSScriptRoot "_lan_ip.ps1")

$Lan = Get-SajuLanIPv4



Write-Host ""

Write-Host "========================================" -ForegroundColor White

Write-Host "  사주프로 · 모바일 접속 주소" -ForegroundColor White

Write-Host "  (PC IP: $Lan · 같은 Wi-Fi 필요)" -ForegroundColor DarkGray

Write-Host "========================================" -ForegroundColor White

Write-Host ""

Write-Host "서버 실행:" -ForegroundColor Magenta

Write-Host '  (더블클릭) .\scripts\터미널2-시작.bat'

Write-Host '  (PowerShell) .\scripts\터미널2-사주앱.ps1'

Write-Host ""

Show-SajuMobileUrls -LanIp $Lan

