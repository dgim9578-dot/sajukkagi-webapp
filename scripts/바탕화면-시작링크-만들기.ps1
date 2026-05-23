# Wrapper: calls ASCII script (avoids Korean filename encoding errors in PowerShell 5.1)
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $here "make-saju-desktop-shortcut.ps1")
