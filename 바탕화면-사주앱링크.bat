@echo off

chcp 65001 >nul

cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\make-saju-desktop-shortcut.ps1"

pause

