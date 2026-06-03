"""``st.session_state.step``(1~12)에 따라 해당 STEP ``render()``만 호출합니다.

표시 순서(1~12):
  홈 → 정보입력 → 사주분석 → 궁합 → 살풀이 → 오늘의 운세 → 주역 → AI 타로 → 대운 → 총평 → 챗봇 → 관리자
"""

from __future__ import annotations

import traceback

import streamlit as st

from saju_app.ui import components as M
from saju_app.ui.execution import (
    inject_nav_scroll_tail_once,
    inject_router_step_mount_visibility_css,
    inject_step_html_attrs_immediate,
    inject_step_nav_transition_early,
    reset_step_dom_sync_slots_for_run,
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
    st.session_state.pop("_saju_hero_pin_slots", None)
    reset_step_dom_sync_slots_for_run()

    step = _get_step()
    last = st.session_state.get("_router_last_step")
    try:
        last_int = int(last) if last is not None else None
    except Exception:
        last_int = None
    navigated = last_int is not None and last_int != int(step)
    also_show = last_int if navigated and last_int is not None else None

    if navigated and also_show is not None:
        inject_step_nav_transition_early(target_step=step, from_step=also_show)

    if navigated:
        if last_int == _ICHING_STEP and int(step) != _ICHING_STEP:
            _clear_step7_widget_state()
        if int(step) in (3, 4, 5, 6, 7, 8, 9, 10, 11, 12):
            M._resync_user_gapja_from_u_data()
        M.track_analysis_step_for_draft(step)
    # STEP1: mount 앞 st.markdown 은 상단 빈 여백·배너 하단 밀림 유발 → mount 내부만 주입
    r = _load_step_render(step)

    with st.container(key=_step_mount_key(step)):
        # STEP1: mount 앞 script 블록이 상단 여백을 만들지 않게 — STEP 동기화는 mount 뒤 sync 만
        if int(step) != 1:
            inject_step_html_attrs_immediate(step, scroll_top=False)
        if int(step) != 1:
            st.markdown(
                '<div id="saju-step-active-top" tabindex="-1" '
                'style="position:relative;width:1px;height:1px;'
                'margin:0;padding:0;overflow:hidden;scroll-margin-top:0;outline:none;" '
                'aria-hidden="true"></div>',
                unsafe_allow_html=True,
            )
        try:
            r()
        except Exception as exc:
            st.error(f"화면을 불러지 못했습니다 (STEP{step}): {exc}")
            st.code(traceback.format_exc(), language="python")

    if not navigated:
        sync_step_dom_now(step, slot="router_after_mount")

    # 마운트 표시 <style> 은 모든 STEP 에서 매 렌더마다 주입한다.
    # (현재 STEP 마운트만 보이고 나머지 잔존 마운트는 숨김 — 홈/피처 양방향 누수 방지)
    # <style> 전용 element-container 는 bootstrap CSS 가 display:none 처리하므로 여백 없음.
    #
    # ★ 본문 r() '뒤'·마운트 컨테이너 '밖'(매 run 동일 위치)에서 주입한다.
    #   STEP 이동 직후에는 also_show_step 으로 이전 마운트를 함께 표시해, 클라이언트가
    #   새 마운트를 채우기 전 이전 화면이 사라지지 않게 한다(하단 네비만 남는 빈 화면 방지).
    inject_router_step_mount_visibility_css(
        step,
        also_show_step=also_show,
    )

    if navigated and also_show is not None:
        nav_epoch = int(st.session_state.get("saju_nav_epoch", 0))
        inject_nav_scroll_tail_once(nav_epoch=nav_epoch, from_step=also_show)

    st.session_state._router_last_step = step
    M.render_global_bottom_chrome(current_step=step)

    # STEP 스크롤·포커스 최상단은 app.py finalize 1회만 (중복 snap → 모바일 멈춤 방지)
