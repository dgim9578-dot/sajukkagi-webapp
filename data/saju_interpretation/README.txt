STEP3 개인화 해석 보강 데이터
================================

STEP3는 `saju_app/ui/saju_interpretation_core.py`에서
일주 DB · 십성 · 용신 · 시주 · 대운·세운 · 상담 코퍼스를 조합합니다.

1. data/saju_interpretation/ilju_60.json
   - 60일주별 personality / career / relationship (각 200자 이상)
   - 최초 로드 시 없으면 `saju_app/ui/ilju_data.py`에서 자동 생성
   - 수동 재생성: python tools/generate_ilju_60_db.py

2. data/saju_consulting/*.md (11개 주제)
   - frontmatter applies 에 step3 포함 → STEP3 코퍼스 자동 매칭
   - 05_timing, 03_wealth 등은 step9/step10도 포함해 대운·세운 Q&A 연결

3. 출생 정보
   - 생년월일·성별·출생시간(시주) — 시간 입력 시 말년·저녁 리듬·세부 성격 정밀도 상승
   - STEP3 요약에 현재 대운·올해 세운 1~2문장 연결 (STEP9/10 로직 공유)
