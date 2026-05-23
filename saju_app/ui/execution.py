"""Streamlit 실행 제어 헬퍼 (1.38+).

`st.rerun()`은 현재 스크립트 실행을 끊고 다음 런을 예약합니다. 문서상 이후 문장은
실행되지 않으므로, 같은 분기에서 ``st.rerun()`` 뒤에 ``st.stop()``을 두는 것은
도달 불가 코드가 됩니다. 분기마다 **종단은 하나**로 두세요.

- 위젯 ``on_click`` / ``callback`` 안에서는 ``st.rerun()``이 **no-op**일 수 있습니다.
  그 경우 세션만 갱신하고 상위 스크립트에서 재실행을 트리거하는 패턴을 쓰세요.
- ``@st.fragment`` 안에서 전체 앱을 다시 그리려면 ``scope="app"`` 이 필요할 수 있습니다.
  본 헬퍼는 전체 앱 rerun을 명시합니다.

``st.stop()``은 가드·검증 실패 시 아래쪽 위젯 실행을 막을 때만 쓰고,
``st.rerun()``과 **한 직선 경로에 연달아** 쓰지 마세요.

예외를 사용자에게 보여 줄 때는 ``report_exception_to_streamlit`` 을 사용하세요.
"""

from __future__ import annotations

import traceback
from typing import NoReturn

import streamlit as st

# STEP 전환 직후에만 짧게 상단 고정. MutationObserver·전체 DOM 스캔은 제거(스크롤 튕김 방지).
_SCROLL_SCRIPT = """
<script>
(() => {{
    const shouldCollapse = {collapse_js};
    const navEpoch = {run_id};
    const pw = window.parent || window;
    const doc = pw.document || document;

    if (typeof pw.__sajuCancelScrollJob === "function") {{
        try {{ pw.__sajuCancelScrollJob(); }} catch (_) {{}}
    }}

    let cancelled = false;
    const timers = [];
    pw.__sajuCancelScrollJob = () => {{
        cancelled = true;
        timers.forEach((id) => {{ try {{ clearTimeout(id); }} catch (_) {{}} }});
        timers.length = 0;
    }};

    const isNestedScrollArea = (el) => {{
        if (!el || !el.classList) return false;
        const cls = String(el.className || "");
        if (
            cls.includes("saju-fortune-scroll") ||
            cls.includes("saju-dw-hrail-scroll") ||
            cls.includes("hscroll") ||
            cls.includes("step9_timeline")
        ) {{
            return true;
        }}
        try {{
            const key = el.getAttribute("class") || "";
            if (key.includes("st-key-step9_timeline_hscroll")) return true;
        }} catch (_) {{}}
        return false;
    }};

    const scrollMainToTop = () => {{
        if (cancelled) return;
        try {{
            if (pw.__sajuScrollNavEpoch !== navEpoch) return;
        }} catch (_) {{}}

        try {{
            if (pw.history && "scrollRestoration" in pw.history) {{
                pw.history.scrollRestoration = "manual";
            }}
        }} catch (_) {{}}

        if (shouldCollapse) {{
            doc.querySelectorAll(
                '.st-key-saju_bottom_quick_menu_panel details, ' +
                '.st-key-saju_global_bottom_chrome details'
            ).forEach((node) => {{
                try {{ node.open = false; }} catch (_) {{}}
            }});
        }}

        const zero = (node) => {{
            if (!node || isNestedScrollArea(node)) return;
            try {{
                if (typeof node.scrollTo === "function") {{
                    node.scrollTo({{ top: 0, left: 0, behavior: "auto" }});
                }}
            }} catch (_) {{}}
            try {{ node.scrollTop = 0; }} catch (_) {{}}
        }};

        const anchor = doc.getElementById("saju-step-top-anchor");
        if (anchor) {{
            try {{
                anchor.scrollIntoView({{ block: "start", inline: "nearest", behavior: "auto" }});
            }} catch (_) {{}}
        }}

        [
            '[data-testid="stMainBlockContainer"]',
            '[data-testid="stAppViewContainer"]',
            '[data-testid="stMain"]',
            '[data-testid="stApp"]',
            "section.main",
        ].forEach((sel) => {{
            doc.querySelectorAll(sel).forEach((node) => zero(node));
        }});

        zero(doc.documentElement);
        zero(doc.body);
        try {{ pw.scrollTo(0, 0); }} catch (_) {{}}
    }};

    try {{ pw.__sajuScrollNavEpoch = navEpoch; }} catch (_) {{}}

    [0, 80, 220, 450].forEach((ms) => {{
        timers.push(setTimeout(scrollMainToTop, ms));
    }});

    const stopIfUserScrolls = (ev) => {{
        const t = ev && ev.target;
        if (t && isNestedScrollArea(t)) return;
        cancelled = true;
        try {{ pw.__sajuCancelScrollJob(); }} catch (_) {{}}
        pw.__sajuCancelScrollJob = null;
        doc.removeEventListener("scroll", stopIfUserScrolls, true);
        doc.removeEventListener("wheel", stopIfUserScrolls, true);
        doc.removeEventListener("touchmove", stopIfUserScrolls, true);
    }};

    timers.push(setTimeout(() => {{
        doc.addEventListener("scroll", stopIfUserScrolls, {{ capture: true, passive: true }});
        doc.addEventListener("wheel", stopIfUserScrolls, {{ capture: true, passive: true }});
        doc.addEventListener("touchmove", stopIfUserScrolls, {{ capture: true, passive: true }});
        timers.push(setTimeout(() => {{
            doc.removeEventListener("scroll", stopIfUserScrolls, true);
            doc.removeEventListener("wheel", stopIfUserScrolls, true);
            doc.removeEventListener("touchmove", stopIfUserScrolls, true);
            if (!cancelled) {{
                try {{ pw.__sajuCancelScrollJob = null; }} catch (_) {{}}
            }}
        }}, 700));
    }}, 60));
}})();
</script>
"""


def render_step_top_anchor() -> None:
    """STEP 본문 최상단 앵커 — 스크롤 대상."""
    st.markdown(
        (
            '<mtop id="saju-step-top-anchor" '
            'style="position:relative;width:1px;height:1px;margin:0;padding:0;'
            'overflow:hidden;scroll-margin-top:0;" aria-hidden="true"></mtop>'
        ).replace("mtop", "div"),
        unsafe_allow_html=True,
    )


def force_scroll_to_top(*, collapse_quick_menu: bool = True) -> None:
    """STEP 전환 직후에만 화면 최상단으로 이동(일반 스크롤 중 튕김 없음)."""
    collapse_js = "true" if collapse_quick_menu else "false"
    run_id = int(st.session_state.get("saju_nav_epoch", 0))
    script = _SCROLL_SCRIPT.format(collapse_js=collapse_js, run_id=run_id)
    try:
        import streamlit.components.v1 as components

        components.html(
            f"<!DOCTYPE html><html><body style='margin:0;padding:0;'>{script}</body></html>",
            height=0,
            scrolling=False,
        )
    except Exception:
        st.markdown(script, unsafe_allow_html=True)


def mark_scroll_completed_for_current_nav() -> None:
    """이번 STEP 전환에 대한 상단 스크롤 완료 표시."""
    try:
        st.session_state["_saju_scrolled_nav_epoch"] = int(
            st.session_state.get("saju_nav_epoch", 0)
        )
    except Exception:
        st.session_state["_saju_scrolled_nav_epoch"] = 0
    st.session_state.pop("_force_scroll_to_top_after_rerun", None)
    st.session_state.pop("_saju_must_scroll_top", None)
    st.session_state.pop("_saju_pending_scroll_top", None)


def should_scroll_to_top_after_step_change(
    *,
    step: int,
    last_step: int | None,
    navigated: bool,
) -> bool:
    """STEP 바로가기·이전/다음 이동 시 상단 고정이 필요한지."""
    if st.session_state.get("_force_scroll_to_top_after_rerun"):
        return True
    if st.session_state.get("_saju_must_scroll_top"):
        return True
    if st.session_state.get("_saju_pending_scroll_top"):
        return True
    if navigated:
        return True
    try:
        nav_epoch = int(st.session_state.get("saju_nav_epoch", 0))
        done_epoch = int(st.session_state.get("_saju_scrolled_nav_epoch", -1))
        if nav_epoch != done_epoch:
            return True
    except Exception:
        pass
    if last_step is None and int(step) > 1:
        return True
    return False


def finalize_scroll_to_top_if_needed() -> None:
    """본문·하단 크롬·푸터 렌더 후 마지막 상단 스크롤(가장 신뢰도 높음)."""
    if not should_scroll_to_top_after_step_change(
        step=int(st.session_state.get("step", 1)),
        last_step=None,
        navigated=False,
    ):
        return
    force_scroll_to_top(collapse_quick_menu=True)
    mark_scroll_completed_for_current_nav()


def rerun_full_app() -> NoReturn:
    """전체 앱 스크립트를 다시 실행합니다 (`scope="app"` rerun)."""
    st.rerun(scope="app")


def force_scroll_to_top_then_rerun() -> NoReturn:
    """전체 앱 rerun 후 상단 스크롤."""
    st.session_state["_force_scroll_to_top_after_rerun"] = True
    st.session_state["_saju_must_scroll_top"] = True
    st.session_state["_saju_pending_scroll_top"] = True
    rerun_full_app()


def report_exception_to_streamlit(exc: BaseException, *, prefix: str = "오류 발생") -> None:
    """예외 메시지와 전체 스택을 Streamlit에 표시합니다."""
    st.error(f"{prefix}: {exc}")
    st.code(traceback.format_exc(), language="python")
