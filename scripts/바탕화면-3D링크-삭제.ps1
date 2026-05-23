# 바탕화면 등에서 구버전 3D 브리핑(.lnk) 바로가기 제거
$ErrorActionPreference = "Continue"

$Wsh = New-Object -ComObject WScript.Shell

$desktopPaths = @(
    [Environment]::GetFolderPath("Desktop")
    [Environment]::GetFolderPath("CommonDesktopDirectory")
)
$desktopPaths = $desktopPaths | Where-Object { $_ -and (Test-Path $_) } | Select-Object -Unique

$exactNames = @(
    "사주프로 · 터미널1 (3D브리핑).lnk"
    "사주프로 · 터미널1 (3D브리핑)"
    "터미널1 · 3D 브리핑.lnk"
)

$targetHints = @(
    "터미널1-3D브리핑"
    "run_frontend"
    "npm run dev"
    "localhost:3000"
)

$removed = @()
$kept = @()

foreach ($desk in $desktopPaths) {
    Get-ChildItem -Path $desk -Filter "*.lnk" -File -ErrorAction SilentlyContinue | ForEach-Object {
        $name = $_.Name
        $path = $_.FullName
        $shouldRemove = $false
        $reason = ""

        if ($exactNames -contains $name -or ($name -match "3D\s*브리핑") -or ($name -match "터미널1.*3D")) {
            $shouldRemove = $true
            $reason = "이름 일치"
        } else {
            try {
                $sc = $Wsh.CreateShortcut($path)
                $blob = ($sc.TargetPath, $sc.Arguments, $sc.Description, $sc.WorkingDirectory) -join " "
                foreach ($hint in $targetHints) {
                    if ($blob -like "*$hint*") {
                        $shouldRemove = $true
                        $reason = "대상 경로: $hint"
                        break
                    }
                }
            } catch {
                # 읽기 실패 시 건너뜀
            }
        }

        if ($shouldRemove) {
            Remove-Item -LiteralPath $path -Force -ErrorAction SilentlyContinue
            if (-not (Test-Path -LiteralPath $path)) {
                $removed += [PSCustomObject]@{ Path = $path; Reason = $reason }
            }
        } else {
            $kept += $path
        }
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  바탕화면 · 3D 브리핑 링크 정리" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($removed.Count -gt 0) {
    Write-Host "  삭제됨 ($($removed.Count)개):" -ForegroundColor Green
    foreach ($r in $removed) {
        Write-Host "    - $($r.Path)" -ForegroundColor DarkGreen
        Write-Host "      ($($r.Reason))" -ForegroundColor DarkGray
    }
} else {
    Write-Host "  삭제할 3D 브리핑 바로가기가 없습니다." -ForegroundColor Yellow
    Write-Host "  (이미 삭제했거나 바탕화면에 없음)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "  사주앱만 쓰려면:" -ForegroundColor Cyan
Write-Host "    .\scripts\바탕화면-시작링크-만들기.ps1" -ForegroundColor White
Write-Host ""
