@echo off
chcp 65001 >nul
set "ROOT=%~dp0.."
cd /d "%ROOT%"
start "터미널2 · 사주앱" powershell -NoExit -ExecutionPolicy Bypass -File "%ROOT%\scripts\터미널2-사주앱.ps1"
