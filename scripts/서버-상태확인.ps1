# 포트 8501 — Streamlit 사주앱 켜짐 여부 확인

$ErrorActionPreference = "SilentlyContinue"

. (Join-Path $PSScriptRoot "_lan_ip.ps1")

$Lan = Get-SajuLanIPv4



function Test-PortOpen([int]$Port) {

    try {

        $c = New-Object System.Net.Sockets.TcpClient

        $iar = $c.BeginConnect("127.0.0.1", $Port, $null, $null)

        $ok = $iar.AsyncWaitHandle.WaitOne(800, $false)

        if ($ok -and $c.Connected) {

            $c.Close()

            return $true

        }

        $c.Close()

    } catch {}

    return $false

}



$p8501 = Test-PortOpen 8501



Write-Host ""

Write-Host "========================================" -ForegroundColor White

Write-Host "  사주프로 · 서버 상태" -ForegroundColor White

Write-Host "========================================" -ForegroundColor White

Write-Host ""



function Show-Line($label, $ok, $url) {

    if ($ok) {

        Write-Host "  [켜짐] $label" -ForegroundColor Green

        Write-Host "         $url" -ForegroundColor DarkGreen

    } else {

        Write-Host "  [꺼짐] $label" -ForegroundColor Red

        Write-Host "         연결 거부 = 이 서버를 아직 안 켰습니다." -ForegroundColor DarkGray

    }

}



Show-Line "사주앱 (8501)" $p8501 "http://localhost:8501  /  http://${Lan}:8501"



Write-Host ""

if (-not $p8501) {

    Write-Host "  → 해결: scripts\터미널2-시작.bat 또는 터미널2-시작.bat 실행" -ForegroundColor Yellow

    Write-Host "  → 브라우저: http://localhost:8501" -ForegroundColor Yellow

}

Write-Host ""

