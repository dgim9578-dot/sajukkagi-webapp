# PC 브라우저에 Streamlit 사주앱만 열기 + 모바일용 실제 IP 안내

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "_lan_ip.ps1")



$Lan = Get-SajuLanIPv4

if ($Lan -eq "127.0.0.1") {

    $Lan = ""

}



Write-Host ""

Write-Host "========================================" -ForegroundColor Yellow

Write-Host "  주의: 192.168.x.x 는 예시입니다!" -ForegroundColor Yellow

Write-Host "  x.x 를 그대로 쓰면 연결되지 않습니다." -ForegroundColor Yellow

Write-Host "========================================" -ForegroundColor Yellow

Write-Host ""

Write-Host "  [PC에서 열 주소]" -ForegroundColor Cyan

Write-Host "    http://localhost:8501   (사주분석 앱)"

Write-Host ""



if ($Lan) {

    Write-Host "  [휴대폰·같은 Wi-Fi]" -ForegroundColor Green

    Write-Host "    http://${Lan}:8501"

} else {

    Write-Host "  [휴대폰 IP] ipconfig 로 IPv4 확인 후 사용" -ForegroundColor DarkYellow

}

Write-Host ""



function Test-Port([int]$p) {

    try {

        $t = New-Object Net.Sockets.TcpClient

        $t.Connect("127.0.0.1", $p)

        $t.Close()

        return $true

    } catch { return $false }

}



if (Test-Port 8501) {

    Start-Process "http://localhost:8501"

} else {

    Write-Host "  [꺼짐] 8501 — scripts\터미널2-시작.bat 을 먼저 실행하세요." -ForegroundColor Red

}



Write-Host ""

Write-Host "상태 확인: .\scripts\서버-상태확인.bat" -ForegroundColor DarkGray

Write-Host ""

