@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo === 사주까기 배포 준비 ===
echo.

python scripts\pre_deploy_check.py
if errorlevel 1 (
    echo.
    echo [실패] FAIL 항목을 수정한 뒤 다시 실행하세요.
    pause
    exit /b 1
)

if not exist static\og-share.png (
    echo og-share.png 생성 중...
    python scripts\generate_og_share.py
)

echo.
echo === Git 상태 ===
if not exist .git (
    git init
    git branch -M main
    echo Git 저장소를 초기화했습니다.
)
git status -sb

echo.
echo === 다음 단계 ===
echo 1. GitHub에서 새 저장소 생성 (Private 권장)
echo 2. git add .
echo 3. git commit -m "Release: 사주까기 Streamlit 웹앱"
echo 4. git remote add origin https://github.com/USER/REPO.git
echo 5. git push -u origin main
echo 6. https://share.streamlit.io/ 에서 New app - Main file: app.py
echo.
echo 자세한 내용: WEBAPP_DEPLOYMENT.md
pause
