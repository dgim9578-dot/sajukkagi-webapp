"""대체 진입점(선택).

권장: 프로젝트 루트에서 ``streamlit run app.py``  
이 파일은 루트를 ``sys.path``에 넣은 뒤 ``saju_app.app:main``만 호출합니다.
"""

from __future__ import annotations

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from saju_app.app import main

main()
