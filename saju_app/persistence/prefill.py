"""STEP2 입력 prefill 저장/복구.

UI 모듈에서 직접 KV를 만지지 않도록(관심사 분리) persistence로 이관합니다.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from saju_app.persistence import storage
from saju_app.utils import now_kst


def ensure_visit_id() -> str:
    """브라우저/세션 단위의 임시 visit_id (cookie 없이 session_state 기반)."""
    vid = st.session_state.get("visit_id")
    if isinstance(vid, str) and vid.strip():
        return vid.strip()
    try:
        import uuid

        vid2 = uuid.uuid4().hex
    except Exception:
        import time

        vid2 = str(int(time.time() * 1000))
    st.session_state.visit_id = str(vid2)
    return str(vid2)


def load_step2_prefill_payload() -> dict[str, Any]:
    """STEP2 입력 기본값용 prefill 로드.

    우선순위:
    - 현재 visit_id용 prefill
    - 레거시 단일 키(step2_prefill)
    - 마지막 저장(last) fallback (visit_id가 바뀌어도 UX 유지)
    """
    try:
        vid = ensure_visit_id()

        v = storage.kv_get_json(f"step2_prefill:by_visit:{vid}")
        if isinstance(v, dict) and isinstance(v.get("payload"), dict):
            return dict(v["payload"])

        legacy = storage.kv_get_json("step2_prefill")
        if isinstance(legacy, dict) and isinstance(legacy.get("payload"), dict):
            return dict(legacy["payload"])

        last = storage.kv_get_json("step2_prefill:last")
        if isinstance(last, dict) and isinstance(last.get("payload"), dict):
            return dict(last["payload"])
    except Exception:
        pass
    return {}


def persist_step2_prefill_to_disk(payload: dict[str, Any]) -> None:
    """STEP2 입력값 저장 (visit_id별 + last fallback)."""
    try:
        vid = ensure_visit_id()
        rec = {
            "visit_id": vid,
            "payload": dict(payload or {}),
            "saved_at": now_kst().isoformat(timespec="seconds"),
        }
        storage.kv_set_json(f"step2_prefill:by_visit:{vid}", rec)
        storage.kv_set_json("step2_prefill:last", rec)
    except Exception:
        pass

