"""Streamlit 엔트리: ``st.session_state.step`` → ``saju_app.ui.steps.router``.

전역 CSS(한지·금박·먹 톤, 과감한 여백, 다크+골드, `streamlit-javascript` 미세 모션)와
``saju.bootstrap.configure_application()`` 안에서 **한 번만** ``st.markdown(..., unsafe_allow_html=True)`` 로 주입합니다.
app.py 에 스타일 블록을 또 넣으면 덮어쓰기 순서만 복잡해지므로, 스타일 수정은 ``saju/bootstrap.py`` 를 편집하세요.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

from saju.bootstrap import configure_application


def _project_root() -> str:
    return str(Path(__file__).resolve().parents[1])


def _ensure_step_and_consume_goto_query() -> None:
    """STEP 세션 기본값 + ``?goto=`` 이동(``STEP_ORDER``에 있는 스텝만).

    쿼리로 이동한 직후에는 URL에서 ``goto`` 를 제거하고, 상단 스크롤 뒤 앱을 다시 실행합니다.
    """
    if "step" not in st.session_state:
        st.session_state.step = 1

    if "goto" not in st.query_params:
        return

    from saju_app.ui import components as M

    try:
        raw = st.query_params.get("goto")
        if raw is None or raw == "":
            try:
                del st.query_params["goto"]
            except Exception:
                pass
            return
        if isinstance(raw, (list, tuple)):
            raw = raw[0] if raw else ""
        goto = int(str(raw).strip())
        if goto in M.STEP_ORDER:
            try:
                del st.query_params["goto"]
            except Exception:
                pass
            M.prepare_step_change_ui(dest=goto)
            st.session_state.step = goto
            if goto in M._FEATURE_STEPS:
                st.session_state["_explicit_feature_step"] = goto
            if goto in (11, 12):
                st.session_state["_navigated_to_chat_this_run"] = True
        else:
            try:
                del st.query_params["goto"]
            except Exception:
                pass
    except Exception:
        try:
            del st.query_params["goto"]
        except Exception:
            pass


def _current_step() -> int:
    try:
        return max(1, min(12, int(st.session_state.get("step", 1))))
    except Exception:
        return 1


def _run_browser_privacy_widgets() -> None:
    """``st_javascript`` iframe — DOM 상 본문 뒤에 붙여야 홈 배너가 위로 밀리지 않음.

    한 번의 스크립트 실행에서 두 번 호출되면 ``st_javascript`` 위젯 key 가 중복돼
    ``StreamlitDuplicateElementKey`` 가 발생하므로, 실행당 1회만 수행합니다.
    """
    if st.session_state.get("_saju_privacy_widgets_run_done"):
        return
    st.session_state["_saju_privacy_widgets_run_done"] = True

    from saju_app.ui import components as M

    M.apply_browser_refresh_landing()
    M.enforce_browser_privacy_isolation()


def _run_session_guards() -> None:
    """draft 복원·기능 STEP 가드(javascript 위젯 없음)."""
    from saju_app.ui import components as M

    if not st.session_state.get("_saju_reload_check_pending"):
        M.restore_session_draft_if_needed()
    M.guard_feature_step_without_explicit_nav()


def main() -> None:
    configure_application()
    # 실행당 브라우저 프라이버시 위젯 1회 가드 초기화(중복 key 방지)
    st.session_state["_saju_privacy_widgets_run_done"] = False
    root = _project_root()
    if root not in sys.path:
        sys.path.insert(0, root)

    from saju_app.ui import components as M

    _ensure_step_and_consume_goto_query()
    try:
        from saju_app.persistence.prefill import ensure_fresh_client_identity

        first_boot = not st.session_state.get("_saju_client_identity_v1")
        ensure_fresh_client_identity()
        if first_boot:
            M.hard_reset_personal_input_state(clear_analysis=True)
    except Exception:
        pass
    if not st.session_state.get("_saju_step2_prefill_purged_v1"):
        try:
            M.purge_all_step2_prefill_from_server()
            st.session_state["_saju_step2_prefill_purged_v1"] = True
        except Exception:
            pass

    step = _current_step()
    home_first = step == 1

    if not home_first:
        _run_browser_privacy_widgets()
        _run_session_guards()
    else:
        _run_session_guards()

    from saju_app.ui.execution import (
        finalize_scroll_to_top_if_needed,
        get_step_nav_from_step,
        inject_step_nav_transition_early,
        prime_step_nav_scroll_before_render,
        render_step_top_anchor,
    )

    from saju_app.ui.steps import router as step_router

    nav_from = get_step_nav_from_step(target_step=step)
    if nav_from is not None:
        inject_step_nav_transition_early(target_step=step, from_step=nav_from)

    if home_first:
        step_router.render()
        _run_browser_privacy_widgets()
    else:
        prime_step_nav_scroll_before_render()
        render_step_top_anchor()
        step_router.render()
        _run_browser_privacy_widgets()

    try:
        from saju_app.ui import webapp_launch as webapp_launch

        webapp_launch.render_policy_footer()
    except Exception:
        pass

    finalize_scroll_to_top_if_needed()


if __name__ == "__main__":
    main()
