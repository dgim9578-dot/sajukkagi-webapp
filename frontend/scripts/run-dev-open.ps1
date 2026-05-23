# Next dev 시작 + 준비되면 브라우저에서 샘플 브리핑 열기
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

$job = Start-Job -ScriptBlock {
    Set-Location $using:root
    node ./node_modules/next/dist/bin/next dev 2>&1
}

Start-Sleep -Seconds 2
& "$PSScriptRoot/wait-and-open-briefing.ps1"
$code = $LASTEXITCODE

if ($code -ne 0) {
    Write-Host ""
    Write-Host "터미널에 표시된 Local 주소를 확인하세요 (보통 http://localhost:3001)." -ForegroundColor Yellow
}

Receive-Job $job -Wait
