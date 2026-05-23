@echo off

chcp 65001 >nul

set "ROOT=%~dp0.."

cd /d "%ROOT%"

start "사주프로 · 사주앱" powershell -NoExit -ExecutionPolicy Bypass -File "%ROOT%\scripts\터미널2-사주앱.ps1"

echo.

echo  사주앱 서버 창이 열렸습니다. Ready 가 보일 때까지 잠시 기다려 주세요.

echo  PC: http://localhost:8501

echo  (3D 브리핑 포트 3000 은 더 이상 사용하지 않습니다)

pause

