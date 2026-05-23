@echo off

chcp 65001 >nul

set "ROOT=%~dp0.."

cd /d "%ROOT%"

start "SajuPro-Admin" powershell -NoExit -ExecutionPolicy Bypass -File "%ROOT%\scripts\start-saju-admin.ps1"

timeout /t 10 /nobreak >nul

start "" "http://localhost:8502/?goto=12"

