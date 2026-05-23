# 3D 브리핑 덱 — 브라우저에서 샘플 페이지 열기 (dev 서버가 이미 떠 있어야 함)
param(
    [int]$Port = 0
)

$ports = if ($Port -gt 0) { @($Port) } else { @(3000, 3001) }
$path = "/briefing/test_sample_123"
$opened = $false

foreach ($p in $ports) {
    $url = "http://localhost:$p$path"
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:$p/" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -lt 500) {
            Write-Host "브라우저 열기: $url"
            Start-Process $url
            $opened = $true
            break
        }
    } catch {
        continue
    }
}

if (-not $opened) {
    Write-Host ""
    Write-Host "Next.js dev 서버가 안 보입니다. 먼저 다른 터미널에서:" -ForegroundColor Yellow
    Write-Host "  cd frontend" -ForegroundColor Cyan
    Write-Host "  npm run dev" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "서버가 뜬 뒤 터미널에 나온 Local 주소(예: http://localhost:3001) + /briefing/test_sample_123" -ForegroundColor Yellow
    exit 1
}
