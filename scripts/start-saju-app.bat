@echo off

chcp 65001 >nul

set "ROOT=%~dp0.."

cd /d "%ROOT%"

start "SajuPro" powershell -NoExit -ExecutionPolicy Bypass -File "%ROOT%\scripts\start-saju-app.ps1"

