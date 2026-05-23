# dev 서버 준비될 때까지 잠시 대기 후 브라우저 열기
$ports = @(3000, 3001)
$deadline = (Get-Date).AddSeconds(45)

while ((Get-Date) -lt $deadline) {
    foreach ($p in $ports) {
        try {
            $null = Invoke-WebRequest -Uri "http://localhost:$p/" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            & "$PSScriptRoot/open-briefing.ps1" -Port $p
            exit 0
        } catch {
            continue
        }
    }
    Start-Sleep -Seconds 2
}

Write-Host "서버 대기 시간 초과. 터미널의 Local URL을 브라우저에 직접 입력하세요." -ForegroundColor Yellow
exit 1
