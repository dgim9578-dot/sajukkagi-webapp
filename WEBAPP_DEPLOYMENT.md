# 사주까기 웹앱 배포 준비 가이드

이 프로젝트는 우선 **웹앱 링크 배포**를 기준으로 운영합니다. 처음에는 Streamlit Community Cloud로 빠르게 공개하고, 사용자가 늘어나면 Render 또는 Google Cloud Run으로 옮기는 흐름을 권장합니다.

## 1. 먼저 준비할 것

- GitHub 계정과 저장소
- 공개 앱 이름: 예) `사주까기`, `사주프로`
- 상담 연락처: 전화번호, 카카오 오픈채팅 URL
- 개인정보처리방침 URL
- 이용약관 URL
- OpenAI API Key: 타로/AI 상담을 실제 AI로 사용할 때만 필요
- 관리자 비밀번호: 길고 추측 어려운 문자열
- 결제/예약 링크: 처음에는 비워두고, 나중에 스마트스토어/토스/카카오 예약 등으로 연결 가능

## 2. Streamlit Community Cloud 배포

배포 전 로컬 점검:

```powershell
python scripts/pre_deploy_check.py
# 또는 scripts\배포전-점검.bat 더블클릭
```

점검 OK 후:

1. 프로젝트를 GitHub 저장소에 올립니다.
2. [Streamlit Community Cloud](https://share.streamlit.io/)에 로그인합니다.
3. `New app`을 누릅니다.
4. 저장소를 선택하고 Main file path에 `app.py`를 입력합니다.
5. Advanced settings의 Secrets에 `.streamlit/secrets.toml.example` 내용을 복사한 뒤 실제 값으로 바꿉니다.
6. Deploy를 누릅니다.

필수 Secrets 예시:

```toml
SAJU_ADMIN_ENABLED = "false"
SAJU_ADMIN_PASSWORD = "강한관리자비밀번호"
SAJU_APP_NAME = "사주까기"
SAJU_OPERATOR_NAME = "사주까기 상담실"
SAJU_PUBLIC_PHONE = "010-8173-7471"
SAJU_KAKAO_OPENCHAT_URL = "https://open.kakao.com/o/..."
SAJU_PRIVACY_URL = "https://..."
SAJU_TERMS_URL = "https://..."
```

선택 Secrets:

```toml
OPENAI_API_KEY = "sk-..."
SAJU_PREMIUM_PAYMENT_URL = "https://..."
SAJU_BOOKING_URL = "https://..."
SAJU_STORAGE = "redis"
REDIS_URL = "redis://..."
```

## 3. 운영 권장 설정

- 공개 배포에서는 `SAJU_ADMIN_ENABLED = "false"`로 두세요.
- 관리자 화면이 필요할 때만 임시로 `true`로 바꾸고, 작업 후 다시 끄는 것을 권장합니다.
- Streamlit Cloud의 무료 파일 저장소는 앱 재시작 때 초기화될 수 있습니다. 상담 기록을 오래 보관하려면 Render/Cloud Run + 외부 Redis 또는 DB를 사용하세요.
- 전화번호, 오픈채팅, 결제 링크는 코드 수정 없이 Secrets에서 교체합니다.

## 4. 수익화 구조

현재 앱은 아래 흐름으로 구성됩니다.

- 무료 진입: STEP 2 입력 후 기본 사주 분석
- 신뢰 형성: 사주, 궁합, 대운, 타로, 주역, 총평 제공
- 전환 지점: 랜딩 화면과 AI 챗봇 화면의 상담/프리미엄 안내 패널
- 상담 연결: 전화상담, 오픈채팅, 예약 링크
- 프리미엄 확장: PDF 리포트, 상세 대운, 궁합 상세, 월 구독 또는 단건 결제

처음에는 결제 링크가 없어도 됩니다. `SAJU_PREMIUM_PAYMENT_URL`을 비워두면 “프리미엄 준비중”으로 표시됩니다.

## 5. 개인정보/정책 주의

앱은 이름, 생년월일, 성별, 선택 연락처, 상담 질문·답변을 다룹니다. 공개 배포 전 아래 문서는 반드시 준비하세요.

- 개인정보처리방침
- 이용약관
- AI/운세 면책 문구
- 상담 기록 삭제 안내

앱 하단에는 기본 면책 문구가 표시됩니다. `SAJU_PRIVACY_URL`, `SAJU_TERMS_URL`을 설정하면 링크도 함께 노출됩니다.

## 6. 외부에서 임시 테스트 (사무실 Wi-Fi 밖)

PC에서 앱을 켠 뒤 **임시 공개 URL**을 만들려면:

1. [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) 설치  
   (또는 `winget install Cloudflare.cloudflared`)
2. 프로젝트 폴더에서 실행:
   - `scripts\start_external_test.bat` 더블클릭, 또는
   - PowerShell: `.\scripts\start_external_test.ps1`
3. 터미널에 나오는 `https://xxxx.trycloudflare.com` 주소를 휴대폰·외부 PC 브라우저에 입력

주의:

- PC를 끄거나 스크립트를 종료하면 링크가 사라집니다.
- 실행할 때마다 URL이 바뀝니다 (임시용).
- OpenAI·관리자 비밀번호 등은 `.streamlit/secrets.toml` 에 두고, 공개 링크는 지인 테스트용으로만 쓰세요.

## 7. 카카오톡·SNS 링크 미리보기 (무료 사주풀이 배너)

1. 배너 PNG 생성 (최초 1회):

   ```powershell
   pip install Pillow
   python scripts/generate_og_share.py
   ```

2. GitHub에 `static/og-share.png` 포함해 push

3. Streamlit Secrets: `SAJU_PUBLIC_APP_URL` = 배포된 앱 URL (끝에 `/` 없이)

4. (선택) GitHub 저장소 → Settings → Social preview → `static/og-share.png` 업로드

5. 카카오 [공유 디버거](https://developers.kakao.com/tool/debugger/sharing)에서 앱 URL 입력 → **캐시 초기화** → 다시 스크랩  
   미리보기 이미지가 안 바뀌면 카카오 [공유 디버거](https://developers.kakao.com/tool/debugger/sharing)에서 아래 URL 로 **캐시 초기화** 후 공유하세요.  
   (jsDelivr·Streamlit `/app/static` 은 카카오 디버거에서 **Invalid URL** 또는 og 미인식)

   1. GitHub 저장소 → **Settings → Pages** → Source: **main** / Folder: **/docs** → Save  
   2. 1~2분 후 공유·디버거 URL:

   `https://dgim9578-dot.github.io/sajukkagi-webapp/share-preview.html`

## 8. 다음 확장 순서

1. Streamlit Cloud 무료 배포
2. 지인/카카오톡/유튜브 링크로 테스트
3. 상담 문의가 실제로 오는지 확인
4. 개인정보처리방침과 이용약관 정리
5. 결제/예약 링크 연결
6. 트래픽이 늘면 Render 또는 Cloud Run 이전
7. 반응이 검증되면 PWA/Play Store 앱 확장 검토

