"""사주프로 Streamlit 앱 패키지.

디렉터리 요약:

- ``core/`` — 계산 로직(대운·신살 등)과 엔진 구성에 쓰이는 순수 함수
- ``ui/`` — 화면·세션 헬퍼; 단계별 화면은 ``ui/steps/``
- ``utils/`` — HTML 이스케이프·KST 시각 등 소형 유틸
- ``models/`` — 앱에서 쓰는 타입의 안정적 import 경로(구현은 ``saju`` 재노출)
- ``persistence/`` — 공유 채팅·KV 등 영속화(루트 ``saju_storage.py`` 래퍼)

엔트리: ``saju_app.app:main`` · 루트 ``app.py``는 여기로만 위임합니다.
"""
