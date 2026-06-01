사주까기 — 무드 이미지 넣는 방법
================================

1) 이 폴더에 PNG 또는 WebP 파일을 복사합니다.
   경로 예: C:\Users\Administrator\Desktop\사주프로\static\mood\

2) 파일 이름은 아래 slug 와 같아야 자동 표시됩니다.
   (확장자만 .webp / .png / .jpg 중 하나)

   권장 10장 (현재 배치 기준):
   - step01_hero.webp / .png   STEP1 홈 상단 (사진1 배너: 명상·수정구·사주까기)
   - step03_hero.webp          STEP3 사주분석 상단
   - step03_mid_pillars.webp   STEP3 사주 원국(팔자) 위
   - step04_hero.webp          STEP4 궁합 상단
   - step04_mid_score.webp     STEP4 종합 궁합 점수 위
   - step06_hero.webp          STEP6 오늘의 운세 상단
   - step07_hero.webp          STEP7 주역 상단
   - step08_hero.webp          STEP8 타로 상단
   - step08_mid_spread.webp    STEP8 카드 장수 선택 위

   선택(10번째):
   - step01_mid_fortune.webp   STEP1 오늘의 운세 4칸 위

3) 앱을 저장한 뒤 Streamlit 을 다시 실행하거나 브라우저에서 새로고침합니다.
   파일이 없으면 해당 위치는 비워 두고 기존 UI 만 보입니다.

4) 파일명이 다르면 표시되지 않습니다.
   예: hero_step1.png → step01_hero.png 로 이름 변경

5) 제작 가이드·AI 프롬프트: 같은 폴더의 IMAGE_PROMPTS.md
