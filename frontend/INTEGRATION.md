# 전체 통합 페이지 레이아웃

## 구조

```
app/page.tsx
  └── BriefingIntegratedPage
        └── (생성/샘플 성공 시) → /briefing/[fingerprint]

app/briefing/[fingerprint]/page.tsx
  └── GET /api/briefing/get/{fingerprint} → SajuBriefingDeck
        ├── [landing] BriefingShell + BriefingLanding
        │     ├── 샘플 브리핑 → GET /api/briefing/sample
        │     └── API 생성   → POST /api/briefing/generate
        └── [deck] BriefingShell(immersive)
              ├── 상단 바 (뒤로 · 제목 · 새로고침)
              ├── SajuBriefingDeck (Swiper 슬라이드)
              │     ├── 오프닝
              │     ├── 일간·키워드
              │     ├── Saju3DChart
              │     ├── fortune_cards × N
              │     └── recommendations
              └── 데스크톱 사이드: energy_flow 요약
```

## 파일

| 경로 | 역할 |
|------|------|
| `components/BriefingIntegratedPage.tsx` | 상태·라우팅·통합 레이아웃 |
| `components/BriefingLanding.tsx` | 시작 화면 |
| `components/layout/BriefingShell.tsx` | 공통 헤더/쉘 |
| `components/SajuBriefingDeck.tsx` | 스와이프 덱 |
| `components/Saju3DChart.tsx` | 3D 4주 |
| `lib/briefing-api.ts` | 브라우저 API 클라이언트 |
| `lib/storage.ts` | 서버 → FastAPI 프록시 (`get_briefing_by_fingerprint`) |
| `app/api/briefing/get/[fingerprint]/route.ts` | Next Route Handler (rewrite보다 우선) |

## 실행

```bash
# 1) API
cd ..
uvicorn saju_app.api.app:app --reload --port 8000

# 2) 프론트 (PowerShell — 프로젝트 루트)
.\scripts\run_frontend.ps1

# 또는 수동:
cd frontend
npm install
npm run dev
```

`next` 를 찾을 수 없다면 **먼저 `npm install`** (frontend 폴더). Windows는 `node node_modules/next/...` 로 실행합니다.

http://localhost:3000

## Streamlit과 병행

- Streamlit: `streamlit run app.py` (기존 사주프로)
- Next 브리핑: `frontend` (3D·스와이프 전용 UI)

동일 백엔드 `saju_storage.generate_saju_briefing` / FastAPI 라우터 사용.

## Streamlit 연동 (P0~P1)

| 모듈 | 역할 |
|------|------|
| `saju_app/ui/briefing_bridge.py` | `ensure_user_briefing`, `render_briefing_deck_cta`, `SAJU_BRIEFING_WEB_URL` |
| `saju_app/ui/briefing_slides.py` | 운세 카드·조언·궁합 4슬라이드·대운 타임라인 |

환경 변수: `SAJU_BRIEFING_WEB_URL=http://localhost:3000` (Next 덱 URL)

## P2 (선택) 반영

- Streamlit STEP1~2,5,7,8,11: `briefing_slides.py` + `bootstrap.css`
- Next 덱: `BriefingParticles`, 에너지 흐름·십성 슬라이드 추가

## P3 (장기) 반영

| 영역 | 내용 |
|------|------|
| `saju_storage.py` | `generate_match_briefing`, `match_briefing_fingerprint`, `load_cached_briefing` (match 캐시) |
| FastAPI | `POST /api/briefing/generate/match`, `GET /api/briefing/get/match/{fp}` |
| `briefing_bridge.py` | `?embed=1` URL, `render_briefing_deck_embed`, `ensure_match_briefing`, 궁합 패널 |
| Streamlit | STEP3·6·10 임베드 토글, STEP4 궁합 3D 덱 |
| Next | `/briefing/match/[fingerprint]`, `SajuEnergyFlow3D` (R3F 생극·상극) |

### 재방문 비밀번호 (STEP1)

- 홈 **「최근 분석 기록」 목록은 제거** — 타인 기록 노출 방지
- **재방문 비밀번호** 입력 → 본인 프로필만 STEP3으로 로드
- 설정: 홈 expander 또는 STEP2 저장 시 **「재방문 비밀번호 (선택)」**
- DB: `user_profiles.revisit_pin_hash` (평문 저장 없음, 전역 중복 불가)

### Streamlit iframe 임베드

1. `npm run dev` (frontend, port 3000)
2. `SAJU_BRIEFING_WEB_URL=http://localhost:3000`
3. STEP3 등에서 **「앱 안에서 3D 덱 보기」** 토글 → `components.iframe` (`embed=1`은 헤더 숨김)

### 궁합 덱 URL

- 전체: `http://localhost:3000/briefing/match/{fingerprint}`
- 임베드: `...?embed=1`
