@echo off
cd /d "%~dp0.."
echo openai 패키지 설치 중...
"%~dp0..\venv\Scripts\python.exe" -m pip install openai
echo.
echo 완료. Streamlit 창을 Ctrl+C 로 끈 뒤 다시 실행하세요.
pause
