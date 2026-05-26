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


def main() -> None:
    configure_application()
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
    try:
        M.purge_all_step2_prefill_from_server()
    except Exception:
        pass
    M.apply_browser_refresh_landing()
    privacy_ok = M.enforce_browser_privacy_isolation()
    if privacy_ok is None:
        # streamlit-javascript 첫 응답 전 — st.stop() 하면 빈 화면만 보임. 렌더는 계속합니다.
        pass
    elif not st.session_state.get("_saju_reload_check_pending"):
        M.restore_session_draft_if_needed()
    M.guard_feature_step_without_explicit_nav()

    from saju_app.ui.execution import (
        finalize_scroll_to_top_if_needed,
        render_step_top_anchor,
    )

    from saju_app.ui.steps import router as step_router

    render_step_top_anchor()
    step_router.render()
    try:
        from saju_app.ui import webapp_launch as webapp_launch

        webapp_launch.render_policy_footer()
    except Exception:
        pass

    finalize_scroll_to_top_if_needed()


if __name__ == "__main__":
    main()
