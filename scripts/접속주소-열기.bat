@echo off
chcp 65001 >nul
set "ROOT=%~dp0.."
cd /d "%ROOT%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\접속주소-열기.ps1"
pause
