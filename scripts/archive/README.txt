# 일회성 복구·마이그레이션 스크립트 (삭제됨)

2026-05 배포 정리 시 아래 **일회성** 스크립트를 제거했습니다. Git 이력이 있다면 필요 시 복구할 수 있습니다.

- `restore_step01_hero.py` — STEP1 히어로 배너 복구
- `restore_step02_md08.py` — STEP2 마크다운 복구
- `restore_14h_wv35.py` — 14시 WV35 복구
- `strip_3d_from_storage.py` — storage 3D 필드 제거
- `set_step01_banner.py` — STEP1 배너 설정
- `install_step01_hero_banner.py` — STEP1 히어로 설치

**일상 운영·배포에 쓰는 스크립트**

- `pre_deploy_check.py` — 배포 전 점검
- `prepare_github_upload.ps1` — GitHub 업로드 준비
- `배포-업로드-준비.bat` — 점검 + Git 안내 (더블클릭)
- `start-saju-app.ps1` / `start-saju-app.bat` — 로컬 실행
