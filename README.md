# 사주까기 · 무료 사주풀이

무료 사주풀이 — 사주·궁합·대운·타로·주역·AI 상담 웹앱입니다.

카카오톡·SNS 링크 미리보기 배너: `static/og-share.png` (생성: `python scripts/generate_og_share.py`)

## 로컬 실행

```powershell
pip install -r requirements.txt
streamlit run app.py
```

## 웹 배포

Streamlit Community Cloud에서는 Main file path를 `app.py`로 설정합니다.

배포 전 점검:

```powershell
python scripts/pre_deploy_check.py
```

GitHub 업로드 준비:

```powershell
.\scripts\prepare_github_upload.ps1
```

배포 전 `.streamlit/secrets.toml.example`을 참고해 Streamlit Secrets에 운영 값을 입력하세요. 자세한 절차는 `WEBAPP_DEPLOYMENT.md`를 참고하세요.

한 번에 점검 + Git 안내:

```powershell
.\scripts\배포-업로드-준비.bat
```

## 주요 환경값

- `SAJU_ADMIN_ENABLED`: 공개 앱에서는 `false` 권장
- `SAJU_ADMIN_PASSWORD`: 관리자 비밀번호
- `OPENAI_API_KEY`: AI 상담/타로 API 사용 시
- `SAJU_PUBLIC_PHONE`: 공개 전화상담 번호
- `SAJU_KAKAO_OPENCHAT_URL`: 카카오 오픈채팅 링크
- `SAJU_PREMIUM_PAYMENT_URL`: 프리미엄 결제 링크
- `SAJU_PRIVACY_URL`: 개인정보처리방침 링크
- `SAJU_TERMS_URL`: 이용약관 링크

