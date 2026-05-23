# 사주까기 — 무드 이미지 AI 프롬프트

앱 다크 테마(#0A0A14) + 골드 악센트(#D4AF37)용 **투명 배경 일러스트** 제작 가이드.  
납품 파일명은 아래 **파일명** 열과 동일하게 `static/mood/`에 저장.

---

## 공통 설정

| 항목 | 값 |
|------|-----|
| 출력 | PNG 투명 배경 (또는 WebP) |
| 히어로 원본 | 1080×360px (3:1) |
| 중간 배너 원본 | 900×200px (~4.5:1) |
| 소형 아이콘 | 512×512px (1:1, 신살·오행용) |

### Positive suffix (모든 프롬프트 끝에 붙이기)

```
, flat vector illustration, minimal line art, elegant Korean mystic fortune-telling app aesthetic, metallic gold accent #D4AF37, subtle warm glow, transparent background, no text, no letters, no watermark, no UI mockup, no photograph, no realistic human face, abstract silhouettes only, centered composition, high contrast for dark UI background #0A0A14
```

### Negative prompt (공통)

```
text, letters, numbers, logo, watermark, signature, emoji, photorealistic, 3D render, cluttered background, white solid background, busy pattern, cartoon chibi, anime face, horror, blood, skull, religious symbols, tarot card faces with readable titles, copyrighted characters
```

### 도구별 팁

- **Midjourney:** `--ar 3:1` (히어로), `--ar 9:2` (중간), `--no text,letters,photo`
- **DALL·E / ChatGPT:** “transparent background”가 잘 안 되면 → **단색 #0A0A14 배경**으로 생성 후 remove.bg
- **Stable Diffusion:** `png transparent` LoRA 또는 rembg 후처리

---

## STEP 1 · 홈

### `step01_hero.webp` — 상단 히어로

**한글 설명:** 한지 질감 위 금박 인장, 별·달, 오늘의 운세 분위기.

**Prompt:**
```
Wide horizontal banner, traditional Korean hanji paper texture suggested subtly at edges, golden seal stamp and crescent moon with small stars, soft mystical mist, fortune and daily rhythm mood, premium minimal flat illustration
```

### `step01_mid_fortune.webp` — 오늘의 운세 4칸 위

**Prompt:**
```
Small wide banner, four stylized fortune cards or scroll panels fanned slightly, golden edges, subtle sparkles, daily luck theme, compact horizontal layout
```

### `step01_mid_cta.webp` — 메인 CTA 위 (선택)

**Prompt:**
```
Compact banner, abstract hand silhouette holding brush over unrolled scroll, invitation to begin reading, gentle golden light rays, minimal
```

---

## STEP 2 · 정보 입력

### `step02_hero.webp` — 상단

**Prompt:**
```
Wide banner, calendar page, clock, and birth chart symbols combined gently, form and birth data theme, clean icons, soft gold highlights, welcoming not clinical
```

### `step02_mid_self.webp` — 본인 탭 상단

**Prompt:**
```
Medium wide banner, single abstract person silhouette beside calendar and clock icons, self profile theme, balanced spacing
```

### `step02_mid_partner.webp` — 상대 탭 상단

**Prompt:**
```
Medium wide banner, two abstract silhouettes facing each other with subtle connecting golden thread, partner and relationship input theme
```

---

## STEP 3 · 사주 분석

### `step03_hero.webp` — 상단 (우선 제작)

**Prompt:**
```
Wide banner, four vertical pillars representing year month day hour pillars of saju birth chart, golden pillar frames, subtle cosmic dots, authoritative mystical saju analysis hero, strongest visual weight
```

### `step03_mid_pillars.webp` — 팔자 4카드 위

**Prompt:**
```
Compact horizontal illustration, four pillar columns in a row with hanja-style abstract blocks not readable text, saju four pillars diagram aesthetic, gold and deep navy accents
```

### `step03_mid_oheng.webp` — 오행 비중 위

**Prompt:**
```
Five circles in a gentle arc representing wood fire earth metal water, each circle with distinct subtle color hint green red yellow white blue, five elements wuxing balance chart, minimal icons inside circles
```

### `step03_mid_yongshin.webp` — 용신 팁 위

**Prompt:**
```
Compass rose combined with auspicious mark, guiding beneficial element theme yongsin, golden needle on dark-friendly palette, direction and luck
```

### `step03_mid_aptitude.webp` — 성격·적성 블록 위

**Prompt:**
```
Unrolled scroll with constellation dots and small star map, personality aptitude insight theme, scholarly mystical, not zodiac cartoon
```

---

## STEP 4 · 궁합

### `step04_hero.webp` — 상단 (우선 제작)

**Prompt:**
```
Wide banner, two abstract silhouettes left and right connected by golden thread and soft heart shape formed by light not emoji, romantic compatibility harmony theme, pink and gold accents on dark-friendly design
```

### `step04_mid_score.webp` — 종합 궁합 점수 위

**Prompt:**
```
Circular progress ring or gauge abstract, two small silhouettes inside ring, compatibility percentage mood without numbers, golden ring partial fill
```

### `step04_mid_love.webp` — 감정·인연 탭 직전

**Prompt:**
```
Two silhouettes close together, cherry blossom petals or soft petals abstract, emotional bond and romance tab illustration, warm rose gold accent
```

### `step04_mid_life.webp` — 생활·커리어 탭 직전

**Prompt:**
```
Simple house icon and briefcase icon side by side with path between them, daily life and career harmony theme, professional calm gold lines
```

### `step04_mid_money.webp` — 재물 탭 직전

**Prompt:**
```
Stack of coins and wallet silhouette abstract, wealth flow theme, golden coins with soft glow, not greedy or flashy
```

### `step04_mid_caution.webp` — 주의점 탭 직전

**Prompt:**
```
Balanced scales and gentle distance between two silhouettes, mindful caution and communication theme, amber gold accent not alarming red horror
```

---

## STEP 5 · 12신살

### `step05_hero.webp` — 상단

**Prompt:**
```
Wide banner, twelve small mystical symbols arranged in circle or hexagon pattern, twelve sinsal Korean fortune stars theme, incense smoke wisps, mysterious elegant
```

### `step05_mid_grid.webp` — 신살 결과 리스트 옆/위

**Prompt:**
```
Square-friendly wide illustration, grid of twelve minimal distinct abstract glyphs each unique silhouette, twelve spiritual stars icons set unified style, gold line icons
```

### `step05_mid_warning.webp` — 주의사항 블록 위

**Prompt:**
```
Shield outline with soft warning triangle merged subtly, protective advice theme, amber #F59E0B accent lines, calm not scary
```

---

## STEP 6 · 오늘의 운세

### `step06_hero.webp` — 상단

**Prompt:**
```
Wide banner, sunrise over calendar page showing abstract date block without readable numbers, today daily fortune theme, warm gold morning light
```

### `step06_mid_focus.webp` — 핵심 운세 3카드 위

**Prompt:**
```
Three cards in row with sun moon and star symbols above each, today's key fortune highlights, compact triptych layout
```

### `step06_mid_categories.webp` — 5카테고리 선택 위

**Prompt:**
```
Horizontal row of five minimal icons: briefcase, heart, coins, book, medical cross stylized as wellness leaf, five life categories daily luck, equal spacing, illustration not emoji
```

---

## STEP 7 · 주역

### `step07_hero.webp` — 상단

**Prompt:**
```
Wide banner, yin yang symbol subtle center, eight trigrams arranged in circle around it, I Ching divination theme, monochrome gold lines with soft smoke
```

### `step07_mid_question.webp` — 질문 입력 위

**Prompt:**
```
Brush pen and scroll with empty space, asking question before divination theme, contemplative minimal
```

### `step07_mid_hex.webp` — 괘 공개 위

**Prompt:**
```
Six horizontal lines stacked vertically representing six yao lines, mix of solid and broken lines abstract, hexagram reveal mood, do not copy specific named hexagram, generic I Ching line art
```

---

## STEP 8 · AI 타로

### `step08_hero.webp` — 상단 (우선 제작)

**Prompt:**
```
Wide banner, night sky with moon and stars and mystical fog, tarot reading atmosphere, do not show readable tarot card faces or Rider-Waite copies, only mood and silhouettes
```

### `step08_mid_spread.webp` — 1·3·5장 선택 위

**Prompt:**
```
Three tarot card backs in fan shape from behind only, ornate back pattern generic not copyrighted, spread selection one three five mood
```

### `step08_mid_table.webp` — 카드 선택 영역 장식

**Prompt:**
```
Abstract hand reaching toward face-down card, soft spotlight, anticipation before reveal, side accent illustration not full scene
```

### `step08_mid_reading.webp` — 해석문 위

**Prompt:**
```
Single tarot card turning with light burst from edge, revelation and interpretation moment, card back transitioning to glow not showing face details
```

---

## STEP 9 · 대운

### `step09_hero.webp` — 상단

**Prompt:**
```
Wide banner, life path as ascending road or staircase through time, decades milestones abstract markers, major luck cycles daewoon theme, forward journey
```

### `step09_mid_daewoon.webp` — 대운 목록 위

**Prompt:**
```
Horizontal timeline with nodes and connecting line, ten year periods abstract blocks without readable years, luck period list mood
```

### `step09_mid_roadmap.webp` — 인생 로드맵 위

**Prompt:**
```
Roadmap with three milestone flags at different heights representing 30s 40s 50s life stages abstract, life planning illustration
```

### `step09_mid_timing.webp` — 행동 타이밍 위

**Prompt:**
```
Calendar with checkmarks and small house wedding ring and moving box icons abstract, best timing for life actions theme, decisive but calm
```

---

## STEP 10 · 심층 총평

### `step10_hero.webp` — 상단

**Prompt:**
```
Wide banner, large rolled scroll with golden seal closure, comprehensive life summary report theme, dignified premium
```

### `step10_mid_health.webp` — 건강·노후 위

**Prompt:**
```
Stylized leaf and water drop and gentle hill silhouette, wellness and longevity lifestyle theme, no hospital syringe, holistic health
```

### `step10_mid_action.webp` — 실행 포인트 위

**Prompt:**
```
Three small icons in row: star, key, compass, actionable advice execution points theme, motivational minimal
```

---

## STEP 11 · AI 챗봇

### `step11_hero.webp` — 상단 (얇은 배너)

**Prompt:**
```
Extra wide thin banner height, speech bubbles and calm counselor silhouette from behind, AI consultation chat theme, friendly professional, low vertical height composition
```

### `step11_mid_chat.webp` — 채팅창 위 (선택)

**Prompt:**
```
Two overlapping speech bubbles with soft dots inside suggesting conversation, minimal chat decoration, small height
```

---

## STEP 12 · 관리자

이미지 불필요 (관리 UI만 사용).

---

## 우선 제작 8장 — 프롬프트만 모음

복사 시 각 줄 끝에 **공통 Positive suffix**를 붙이세요.

1. **step01_hero** — `Wide horizontal banner, traditional Korean hanji paper texture at edges, golden seal stamp and crescent moon with small stars, soft mystical mist, fortune daily rhythm mood`

2. **step03_hero** — `Wide banner, four vertical pillars year month day hour saju birth chart, golden pillar frames, subtle cosmic dots, saju analysis hero`

3. **step03_mid_pillars** — `Four pillar columns in a row with abstract blocks not readable text, saju four pillars diagram, gold and deep navy`

4. **step04_hero** — `Two abstract silhouettes connected by golden thread and soft heart light shape, romantic compatibility harmony, pink and gold accents`

5. **step04_mid_score** — `Circular progress ring with two silhouettes inside, compatibility gauge mood without numbers, golden partial ring`

6. **step08_hero** — `Night sky moon stars mystical fog, tarot reading atmosphere, no readable card faces`

7. **step08_mid_spread** — `Three tarot card backs in fan from behind only, generic ornate back pattern, spread selection mood`

8. **step06_hero** — `Sunrise over calendar page abstract date, today daily fortune, warm gold morning light`

---

## 후처리 체크리스트

- [ ] 배경 완전 투명 (또는 #0A0A14 단색 후 투명화)
- [ ] 가장자리 8% 세이프존 (잘림 방지)
- [ ] WebP 변환 후 80~180KB 목표 (히어로)
- [ ] `static/mood/`에 파일명 그대로 저장
- [ ] 앱 연동 전 `IMAGE_PREP.txt` 색상(#D4AF37)과 톤 대조 확인
