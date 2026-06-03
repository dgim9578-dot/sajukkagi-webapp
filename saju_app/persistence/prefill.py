"""STEP2 입력 prefill — 서버 공유 저장 비활성(개인정보 교차 노출 방지).

분석 세션(u_gapja 등)은 ``st.session_state`` + 세션 draft(이름 제외)로만 유지합니다.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from saju_app.persistence import storage

_STEP2_KV_PREFIX = "step2_prefill"
_PURGE_FLAG = "_saju_step2_prefill_purged_v4"


def ensure_visit_id() -> str:
    """브라우저/Streamlit 세션 단위 visit_id."""
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


def rotate_visit_identity() -> str:
    """정보입력(STEP2) 새 방문마다 visit_id 분리 — 타 사용자 입력 혼선 방지."""
    try:
        import uuid

        vid = uuid.uuid4().hex
    except Exception:
        import time

        vid = str(int(time.time() * 1000))
    st.session_state.visit_id = str(vid)
    return str(vid)


def ensure_fresh_client_identity() -> None:
    """앱 세션 시작 시 visit·위젯 epoch 분리(타 단말/타 사용자 혼선 방지)."""
    if st.session_state.get("_saju_client_identity_v1"):
        return
    st.session_state["_saju_client_identity_v1"] = True
    try:
        import uuid

        st.session_state.visit_id = uuid.uuid4().hex
        st.session_state.session_id = uuid.uuid4().hex
        st.session_state["_saju_privacy_epoch"] = uuid.uuid4().hex
    except Exception:
        ensure_visit_id()
    st.session_state["_step2_widget_epoch"] = (
        int(st.session_state.get("_step2_widget_epoch", 0)) + 1
    )
    purge_all_step2_prefill_from_server()


def purge_all_step2_prefill_from_server() -> None:
    """서버 KV·레거시 파일에 남은 STEP2 prefill 전부 삭제(공유 키 교차 노출 차단)."""
    try:
        storage.kv_delete_json_prefix(_STEP2_KV_PREFIX)
        for key in (
            "step2_prefill",
            "step2_prefill:last",
            "session:last_current_step",
        ):
            storage.kv_delete_json(key)
    except Exception:
        pass
    try:
        import os

        legacy = os.path.join(storage._app_dir(), "step2_form_prefill.json")
        if os.path.isfile(legacy):
            try:
                os.remove(legacy)
            except OSError:
                pass
    except Exception:
        pass


def purge_shared_step2_prefill_once() -> None:
    """매 요청 공유 prefill 삭제(세션당 1회가 아닌 서버 전역 키 제거)."""
    purge_all_step2_prefill_from_server()
    st.session_state[_PURGE_FLAG] = True


def clear_step2_prefill_storage(*, visit_id: str | None = None) -> None:
    """STEP2 prefill KV 삭제 (현재 visit + 공유 fallback)."""
    purge_all_step2_prefill_from_server()
    _ = visit_id  # 서버 prefill 미사용 — API 호환


def load_step2_prefill_payload() -> dict[str, Any]:
    """서버 prefill 비활성 — 항상 빈 dict."""
    return {}


def persist_step2_prefill_to_disk(payload: dict[str, Any]) -> None:
    """서버 prefill 저장 비활성 (타 사용자 입력 노출 방지)."""
    _ = payload
    return
