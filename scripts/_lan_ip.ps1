# 공통: PC LAN IPv4 (모바일 접속용)

function Get-SajuLanIPv4 {

    $ip = $null

    try {

        $udp = New-Object System.Net.Sockets.Socket(

            [System.Net.Sockets.AddressFamily]::InterNetwork,

            [System.Net.Sockets.SocketType]::Dgram,

            [System.Net.Sockets.ProtocolType]::Udp

        )

        $udp.Connect("8.8.8.8", 80)

        $ip = $udp.LocalEndPoint.Address.ToString()

        $udp.Close()

    } catch {

        $ip = $null

    }

    if ([string]::IsNullOrWhiteSpace($ip)) {

        return "127.0.0.1"

    }

    return $ip

}



function Show-SajuMobileUrls {

    param(

        [string]$LanIp = (Get-SajuLanIPv4)

    )

    Write-Host ""

    Write-Host "  PC (이 컴퓨터)     http://localhost:8501" -ForegroundColor White

    Write-Host "  모바일·태블릿      http://${LanIp}:8501" -ForegroundColor Green

    Write-Host ""

}

