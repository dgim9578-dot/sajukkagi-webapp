"""앱 배포·UI 빌드 식별자 — PC/모바일 구버전 화면 방지용."""

from __future__ import annotations

import os

# 코드 배포 시 수동으로 올리거나 SAJU_RELEASE_TAG 환경변수로 덮어씁니다.
_DEFAULT_DEPLOY_TAG = "20260522-md08"


def deploy_tag() -> str:
    return str(os.environ.get("SAJU_RELEASE_TAG") or _DEFAULT_DEPLOY_TAG).strip()


def input_form_build() -> str:
    try:
        from saju.ui.step_02 import STEP2_UI_BUILD

        return str(STEP2_UI_BUILD).strip()
    except Exception:
        return "unknown"


def full_release_id() -> str:
    return f"{deploy_tag()}:{input_form_build()}"


def sw_cache_name() -> str:
    """Service Worker 정적 캐시 버킷 — deploy_tag 와 함께 갱신."""
    safe = deploy_tag().replace(":", "-").replace("/", "-")
    return f"saju-pwa-static-{safe}"
