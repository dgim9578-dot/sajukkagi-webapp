# 사주프로 3D 브리핑 (Next.js)

`Saju3DChart` — React Three Fiber 4주 입체 차트. Python 브리핑 API와 연동합니다.

## 실행

터미널 1 — API:

```bash
cd ..
pip install fastapi "uvicorn[standard]"
uvicorn saju_app.api.app:app --reload --port 8000
```

터미널 2 — 프론트:

```bash
npm install
npm run dev
```

http://localhost:3000 — 통합 페이지 (`BriefingIntegratedPage`)

자세한 구조는 [INTEGRATION.md](./INTEGRATION.md) 참고.

## 컴포넌트

### 전체 브리핑 덱 (Swiper + Framer Motion)

```tsx
import SajuBriefingDeck from "@/components/SajuBriefingDeck";

<SajuBriefingDeck briefing={briefing} />
```

슬라이드: 오프닝 → 핵심 키워드 → 3D 사주팔자 → 운세 카드 → 조언

### 3D 차트만

```tsx
import Saju3DChart from "@/components/Saju3DChart";

<Saju3DChart
  pillars={briefing.pillars_3d}
  visualThemes={briefing.visual_themes}
/>
```

- 기둥 색: `pillar.stem.color` (없으면 오행 기본색)
- 일주(index 2): `visualThemes.primary` + 발광 강조
- 라벨: 년주 · 월주 · 일주 · 시주

## 환경 변수

`SAJU_API_URL` — 기본 `http://127.0.0.1:8000` (`next.config.mjs` rewrite)
