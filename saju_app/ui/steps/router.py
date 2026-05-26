"""``st.session_state.step``(1~12)에 따라 해당 STEP ``render()``만 호출합니다.

표시 순서(1~12):
  홈 → 정보입력 → 사주분석 → 궁합 → 살풀이 → 오늘의 운세 → 주역 → AI 타로 → 대운 → 총평 → 챗봇 → 관리자
"""

from __future__ import annotations

import streamlit as st

from saju_app.ui import components as M
from saju_app.ui.execution import (
    prime_step_navigation_viewport,
    should_scroll_to_top_after_step_change,
    sync_step_dom_now,
)

# session step 번호 → 구현 모듈(stepNN.py) — 1:1 매핑
_STEP_RENDER_IMPORTS: dict[int, str] = {
    1: "saju_app.ui.steps.step01",
    2: "saju_app.ui.steps.step02",
    3: "saju_app.ui.steps.step03",
    4: "saju_app.ui.steps.step04",
    5: "saju_app.ui.steps.step05",
    6: "saju_app.ui.steps.step06",
    7: "saju_app.ui.steps.step07",
    8: "saju_app.ui.steps.step08",
    9: "saju_app.ui.steps.step09",
    10: "saju_app.ui.steps.step10",
    11: "saju_app.ui.steps.step11",
    12: "saju_app.ui.steps.step12",
}

_ICHING_STEP = 7


def _get_step() -> int:
    try:
        s = int(st.session_state.get("step", 1))
    except Exception:
        s = 1
    return max(1, min(12, s))


def _step_mount_key(step: int) -> str:
    """STEP10·11·12가 mount_1·mount_2와 부분 일치하지 않도록 2자리 고정."""
    return f"saju_router_step_mount_{int(step):02d}"


def _clear_step7_widget_state() -> None:
    for k in (
        "step7_iching_question_input",
        "step7_action_row",
        "step7_hex_reveal",
    ):
        st.session_state.pop(k, None)


def _load_step_render(step: int):
    import importlib

    mod_path = _STEP_RENDER_IMPORTS.get(int(step), _STEP_RENDER_IMPORTS[12])
    mod = importlib.import_module(mod_path)
    return mod.render


def render() -> None:
    st.session_state.pop("_saju_step_main_ph", None)
    st.session_state.pop("_saju_step_epoch", None)

    M.try_restore_step2_from_disk_prefill_if_needed()
    M._resync_user_gapja_from_u_data()
    step = _get_step()
    M.track_analysis_step_for_draft(step)
    last = st.session_state.get("_router_last_step")
    try:
        last_int = int(last) if last is not None else None
    except Exception:
        last_int = None
    navigated = last_int is not None and last_int != int(step)

    if navigated and last_int == _ICHING_STEP and int(step) != _ICHING_STEP:
        _clear_step7_widget_state()

    need_scroll = should_scroll_to_top_after_step_change(
        step=int(step),
        last_step=last_int,
        navigated=navigated,
    )
    if need_scroll and not st.session_state.get("_saju_pending_scroll_top"):
        st.session_state["_saju_pending_scroll_top"] = True

    sync_step_dom_now(step, slot="router")
    if navigated:
        prime_step_navigation_viewport(step=step)

    r = _load_step_render(step)

    with st.container(key=_step_mount_key(step)):
        r()

    M.persist_current_session_draft(step)
    st.session_state._router_last_step = step
    M.render_global_bottom_chrome(current_step=step)
