# .streamlit/secrets.toml 생성 (SAJU_ADMIN_PASSWORD)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Dir = Join-Path $Root ".streamlit"
$Secrets = Join-Path $Dir "secrets.toml"
$Example = Join-Path $Dir "secrets.toml.example"

if (-not (Test-Path $Dir)) {
    New-Item -ItemType Directory -Path $Dir -Force | Out-Null
}

if (Test-Path $Secrets) {
    Write-Host "Already exists: $Secrets" -ForegroundColor Green
    Write-Host "Edit SAJU_ADMIN_PASSWORD in that file, then restart Streamlit." -ForegroundColor Yellow
    exit 0
}

if (Test-Path $Example) {
    Copy-Item -LiteralPath $Example -Destination $Secrets
    (Get-Content -LiteralPath $Secrets -Raw -Encoding UTF8) `
        -replace 'REPLACE_WITH_STRONG_ADMIN_PASSWORD', 'saju-admin-local' `
        -replace 'SAJU_ADMIN_ENABLED = "false"', 'SAJU_ADMIN_ENABLED = "true"' |
    Set-Content -LiteralPath $Secrets -Encoding UTF8
} else {
    @"
SAJU_ADMIN_PASSWORD = "saju-admin-local"
SAJU_ADMIN_ENABLED = "true"
"@ | Set-Content -LiteralPath $Secrets -Encoding UTF8
}

Write-Host ""
Write-Host "Created: $Secrets" -ForegroundColor Green
Write-Host "Default password: saju-admin-local  (change it in secrets.toml)" -ForegroundColor Yellow
Write-Host ""
