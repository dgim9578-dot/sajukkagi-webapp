"""앱에서 쓰는 도메인 모델·엔진 타입의 안정적인 import 경로.

실제 구현은 ``saju`` 패키지에 두고, 여기서는 재노출만 합니다.
"""

from __future__ import annotations

from saju.core.engine import SajuEngine

__all__ = ["SajuEngine"]
