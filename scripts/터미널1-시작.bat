@echo off
chcp 65001 >nul
set "ROOT=%~dp0.."
cd /d "%ROOT%"
echo.
echo  [안내] 3D 브리핑은 제거되었습니다. 사주앱만 시작합니다.
echo.
start "사주프로 · 사주앱" powershell -NoExit -ExecutionPolicy Bypass -File "%ROOT%\scripts\터미널2-사주앱.ps1"
