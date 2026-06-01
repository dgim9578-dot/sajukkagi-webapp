홈(STEP1) 배너 이미지 교체 방법
================================

※ PowerShell 에서 경로만 입력하면 실행되지 않습니다.
  (예: C:\...\step01_hero_v2.png  ← 오류 남)

1) 배너 파일 넣기 (권장: images 폴더)
   C:\Users\Administrator\Desktop\사주프로\images\step01_hero_v2.png
   (또는 assets\step01_hero_v2.png)

   - 채팅/다운로드 받은 PNG·JPG 를 위 이름으로 저장
   - 파일 탐색기에서 복사·붙여넣기

2) PowerShell — 프로젝트 폴더에서 실행

   cd C:\Users\Administrator\Desktop\사주프로

   # 다운로드한 사진 경로를 지정
   .\scripts\install-banner.ps1 "C:\Users\Administrator\Downloads\배너.png"

   # assets\step01_hero_v2.png 가 이미 있으면
   .\scripts\install-banner.ps1

   또는:
   python scripts/set_step01_banner.py "C:\경로\배너.png"

3) 앱 홈 화면
   STEP1 홈 → 「배너 이미지 교체」 → 파일 선택

반영: static\mood\step01_hero.png
이후 Streamlit 재시작 + 브라우저 강력 새로고침
