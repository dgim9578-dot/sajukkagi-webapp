"""프리미엄 모션 스타일 주입.

모바일 인앱 WebView(카카오톡/네이버)에서 ``streamlit-javascript`` 컴포넌트가
React ``removeChild`` 오류를 유발할 수 있어 JS 주입을 비활성화합니다.
핵심 CSS는 ``bootstrap.py`` 에서 서버 렌더링 방식으로 적용됩니다.
"""

from __future__ import annotations


def inject_premium_motion_styles(*, key: str = "saju_premium_motion_v5") -> None:
    """카카오톡 인앱 안정성을 위해 클라이언트 JS 주입을 하지 않습니다."""
    return
