"""PWA 보조 주입.

모바일 인앱 WebView에서 ``streamlit-javascript`` 컴포넌트가 React ``removeChild``
오류를 유발할 수 있어 Manifest/Service Worker 자동 JS 등록을 비활성화합니다.
"""

from __future__ import annotations


def inject_pwa_manifest_and_sw(*, key: str = "saju_pwa_register_v1") -> None:
    """카카오톡 인앱 안정성을 위해 클라이언트 JS 주입을 하지 않습니다."""
    return
