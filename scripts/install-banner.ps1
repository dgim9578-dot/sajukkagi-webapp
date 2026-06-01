# Install STEP1 home banner -> static\mood\step01_hero.png
# Usage:
#   .\scripts\install-banner.ps1
#   .\scripts\install-banner.ps1 "C:\path\to\banner.png"

param(
    [Parameter(Position = 0)]
    [string]$Source
)

$Root = Split-Path -Parent $PSScriptRoot
if (-not $Root) { $Root = (Get-Location).Path }

$DstDir = Join-Path $Root "static\mood"
$Dst = Join-Path $DstDir "step01_hero.png"
$ImagesV2 = Join-Path $Root "images\step01_hero_v2.png"
$Images = Join-Path $Root "images\step01_hero.png"
$AssetsV2 = Join-Path $Root "assets\step01_hero_v2.png"
$Assets = Join-Path $Root "assets\step01_hero.png"
$CursorV2 = "C:\Users\Administrator\.cursor\projects\empty-window\assets\step01_hero_v2.png"

New-Item -ItemType Directory -Force -Path (Join-Path $Root "images") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $Root "assets") | Out-Null
New-Item -ItemType Directory -Force -Path $DstDir | Out-Null

if ($Source) {
    if (-not (Test-Path -LiteralPath $Source)) {
        Write-Host "ERROR: file not found: $Source" -ForegroundColor Red
        exit 1
    }
    $Src = (Resolve-Path -LiteralPath $Source).Path
}
elseif (Test-Path -LiteralPath $ImagesV2) { $Src = $ImagesV2 }
elseif (Test-Path -LiteralPath $Images) { $Src = $Images }
elseif (Test-Path -LiteralPath $AssetsV2) { $Src = $AssetsV2 }
elseif (Test-Path -LiteralPath $Assets) { $Src = $Assets }
elseif (Test-Path -LiteralPath $CursorV2) { $Src = $CursorV2 }
else {
    Write-Host ""
    Write-Host "ERROR: banner image not found." -ForegroundColor Yellow
    Write-Host "Put your PNG here (recommended name):"
    Write-Host "  $ImagesV2"
    Write-Host ""
    Write-Host "Or run with a file path:"
    Write-Host '  .\scripts\install-banner.ps1 "C:\path\to\your-banner.png"'
    Write-Host ""
    exit 1
}

Copy-Item -LiteralPath $Src -Destination $Dst -Force
$size = (Get-Item -LiteralPath $Dst).Length
Write-Host ("OK: {0} ({1} bytes) <- {2}" -f $Dst, $size, $Src) -ForegroundColor Green
Write-Host "Restart Streamlit, then refresh the home page in your browser."
