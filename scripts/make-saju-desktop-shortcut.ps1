# Desktop shortcuts: SajuPro User + Admin (ASCII .lnk names only)
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Scripts = Join-Path $Root "scripts"
$Desktop = [Environment]::GetFolderPath("Desktop")
$Wsh = New-Object -ComObject WScript.Shell

$defs = @(
    @{
        File = "SajuPro-User.lnk"
        Bat  = Join-Path $Scripts "start-saju-user.bat"
        Desc = "SajuPro general - http://localhost:8501"
    },
    @{
        File = "SajuPro-Admin.lnk"
        Bat  = Join-Path $Scripts "start-saju-admin.bat"
        Desc = "SajuPro admin - http://localhost:8502 STEP12"
    }
)

foreach ($d in $defs) {
    if (-not (Test-Path -LiteralPath $d.Bat)) {
        Write-Host "ERROR: missing $($d.Bat)" -ForegroundColor Red
        exit 1
    }
}

# Remove old / broken shortcuts
$removePatterns = @("3D", "SajuPro", "사주프로")
Get-ChildItem -Path $Desktop -Filter "*.lnk" -File -ErrorAction SilentlyContinue | ForEach-Object {
    $n = $_.Name
    foreach ($pat in $removePatterns) {
        if ($n -like "*$pat*") {
            Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue
            Write-Host "Removed: $n" -ForegroundColor DarkYellow
            break
        }
    }
}

Write-Host ""
Write-Host "Creating desktop shortcuts..." -ForegroundColor Cyan
Write-Host ""

foreach ($d in $defs) {
    $lnkPath = Join-Path $Desktop $d.File
    $sc = $Wsh.CreateShortcut($lnkPath)
    $sc.TargetPath = $d.Bat
    $sc.WorkingDirectory = $Root
    $sc.WindowStyle = 1
    $sc.Description = $d.Desc
    $sc.Save()
    Write-Host "  OK: $lnkPath" -ForegroundColor Green
}

Write-Host ""
Write-Host "Done." -ForegroundColor Yellow
Write-Host "  SajuPro-User.lnk   -> general app (port 8501)" -ForegroundColor White
Write-Host "  SajuPro-Admin.lnk  -> admin app (port 8502, opens STEP12)" -ForegroundColor White
Write-Host ""
