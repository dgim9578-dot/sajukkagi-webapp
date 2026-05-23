@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo === 배포 전 점검 ===
python scripts\pre_deploy_check.py
if errorlevel 1 (
  echo.
  echo 점검 실패. 위 FAIL 항목을 수정한 뒤 다시 실행하세요.
  pause
  exit /b 1
)
echo.
echo 다음: GitHub 업로드 후 Streamlit Cloud 에서 app.py 로 배포
echo 자세한 절차: WEBAPP_DEPLOYMENT.md
pause
