"""Streamlit 실행 제어 헬퍼 (1.38+).

STEP(다음/이전) 이동 시 최상단 스크롤:
  1) bootstrap 에서 parent 창에 전역 매니저 1회 설치 (rerun 후에도 유지)
  2) STEP 전환 시 매니저 호출 + st_javascript 백업
"""

from __future__ import annotations

import json
import logging
import re
import time
import traceback
from typing import NoReturn

import streamlit as st
import streamlit.components.v1 as components

log = logging.getLogger(__name__)

_FORCE_SCROLL_OPTS_KEY = "_saju_force_scroll_opts"
# parent 창 JS 와 Python 세션 키를 반드시 동일 숫자로 맞출 것 (불일치 시 구버전 JS 가 남아 멈춤·스크롤 미적용)
_SCROLL_MGR_JS_VER = 96


def schedule_force_scroll_after_nav(
    *, delay_ms: int = 0, strength: str = "light"
) -> None:
    """레거시 호환 — 실제 스크롤은 ``finalize_scroll_to_top_if_needed`` 1회만 실행합니다."""
    st.session_state[_FORCE_SCROLL_OPTS_KEY] = {
        "delay_ms": max(0, min(80, int(delay_ms))),
        "strength": str(strength or "light").strip().lower(),
    }


def _pop_force_scroll_nav_opts() -> dict[str, int | str]:
    raw = st.session_state.pop(_FORCE_SCROLL_OPTS_KEY, None)
    if isinstance(raw, dict):
        return raw
    return {"delay_ms": 150, "strength": "strong"}


def force_scroll_to_top(*, delay_ms: int = 0, strength: str = "light") -> None:
    """STEP 전환 시 최상단 스냅(1회) — 모바일 멈춤 방지를 위해 지연 재시도 없음."""
    _ = strength
    _ = delay_ms
    try:
        js_code = """
<script>
(function () {
    const pw = (window.parent && window.parent !== window) ? window.parent : window;
    if (typeof pw.__sajuSnapViewportTop === "function") {
        pw.__sajuSnapViewportTop({ force: true });
        try {
            pw.requestAnimationFrame(function () {
                pw.__sajuSnapViewportTop({ force: true });
            });
        } catch (e) {}
        return;
    }
    if (typeof pw.__sajuSnapStepTopFast === "function") {
        pw.__sajuSnapStepTopFast();
    }
})();
</script>
"""
        st.markdown(js_code, unsafe_allow_html=True)
        st.session_state["last_step_scroll"] = {
            "at": int(time.time()),
            "status": "top_forced",
            "strength": "light",
            "delay_ms": 0,
        }
    except Exception as e:
        log.warning("force_scroll_to_top failed: %s", e)


# parent(window) 에 1회 설치 — STEP 전환 시 가벼운 최상단 스크롤만 (잠금·MO 없음)
_SCROLL_MANAGER_JS = r"""
(function () {
    const pw = window.parent || window;
    const MGR_VER = __SCROLL_MGR_JS_VER__;
    const verKey = "__sajuStepScrollMgrV" + MGR_VER;
    if (pw[verKey] && typeof pw.__sajuNavScrollOnce === "function") return;
    pw[verKey] = true;
    pw.__sajuStepScrollMgrV26 = true;
    pw.__sajuStepScrollMgrV25 = true;
    pw.__sajuStepScrollMgrV24 = true;
    pw.__sajuStepScrollMgrV23 = true;
    pw.__sajuStepScrollMgrV22 = true;
    pw.__sajuStepScrollMgrV21 = true;
    pw.__sajuStepScrollMgrV20 = true;
    pw.__sajuStepScrollMgrV19 = true;
    pw.__sajuStepScrollMgrV18 = true;
    pw.__sajuStepScrollMgrV17 = true;
    pw.__sajuStepScrollMgrV16 = true;
    pw.__sajuStepScrollMgrV15 = true;
    pw.__sajuStepScrollMgrV14 = true;
    pw.__sajuStepScrollMgrV13 = true;
    pw.__sajuStepScrollMgrV12 = true;
    pw.__sajuStepScrollMgrV11 = true;
    pw.__sajuStepScrollMgrV10 = true;
    pw.__sajuStepScrollMgrV9 = true;
    pw.__sajuStepScrollMgrV8 = true;

    const isMobileView = function (pwIn, doc) {
        try {
            const w = pwIn.innerWidth || doc.documentElement.clientWidth || 0;
            if (w > 0 && w <= 768) return true;
            return !!(pwIn.matchMedia && pwIn.matchMedia("(max-width: 768px)").matches);
        } catch (e) {}
        return false;
    };

    pw.__sajuHideStreamlitPlatformChrome = function () {
        const doc = pw.document || document;
        if (!doc || !doc.body) return;

        const hideEl = function (el) {
            if (!el || !el.style) return;
            try {
                el.style.setProperty("display", "none", "important");
                el.style.setProperty("visibility", "hidden", "important");
                el.style.setProperty("pointer-events", "none", "important");
                el.style.setProperty("height", "0", "important");
                el.style.setProperty("overflow", "hidden", "important");
            } catch (e) {}
        };

        const selectors = [
            '[data-testid="stStatusWidget"]',
            '[data-testid="stAppDeployButton"]',
            '[data-testid="stToolbar"]',
            '[data-testid="stDecoration"]',
            ".stDeployButton",
            'a[href*="streamlit.app/manage"]',
            'a[href*="share.streamlit.io/manage"]',
            "[class*='viewerBadge']",
            "[class*='ViewerBadge']",
            "[class*='ManageApp']",
        ];
        selectors.forEach(function (sel) {
            try {
                doc.querySelectorAll(sel).forEach(hideEl);
            } catch (e) {}
        });

        try {
            doc.querySelectorAll("a[href]").forEach(function (a) {
                const h = String(a.getAttribute("href") || "").toLowerCase();
                if (
                    (h.indexOf("streamlit.app") >= 0 || h.indexOf("share.streamlit.io") >= 0) &&
                    h.indexOf("manage") >= 0
                ) {
                    hideEl(a);
                }
            });
        } catch (e) {}

        try {
            doc.querySelectorAll(
                '.st-key-saju_landing_stack [data-testid="stMarkdownContainer"]'
            ).forEach(function (mc) {
                const t = String(mc.textContent || "").replace(/\s+/g, " ").trim();
                if (/오늘의\s*24절기/i.test(t) && t.length < 48) {
                    hideEl(mc);
                    const wrap =
                        mc.closest('[data-testid="stElementContainer"]') ||
                        mc.closest('[data-testid="stVerticalBlockBorderWrapper"]');
                    if (wrap) hideEl(wrap);
                }
            });
        } catch (e) {}
    };

    pw.__sajuHideStreamlitPlatformChrome();
    try {
        const doc0 = pw.document || document;
        const mob0 = doc0 && isMobileView(pw, doc0);
        (mob0 ? [320] : [120, 480]).forEach(function (ms) {
            pw.setTimeout(pw.__sajuHideStreamlitPlatformChrome, ms);
        });
    } catch (e) {}

    pw.__sajuDetectMobilePlatform = function () {
        const doc = pw.document || document;
        const root = doc && doc.documentElement;
        if (!root) return;
        const ua = String((pw.navigator && pw.navigator.userAgent) || "").toLowerCase();
        if (/android/i.test(ua)) {
            root.classList.add("saju-platform-android");
        }
        if (
            /samsung|sm-[a-z0-9]|galaxy|samsungbrowser/i.test(ua) ||
            /android.*samsung/i.test(ua)
        ) {
            root.classList.add("saju-platform-galaxy");
        }
        if (/kakaotalk|kakao/i.test(ua)) {
            root.classList.add("saju-platform-kakao", "saju-platform-inapp");
        }
        if (/instagram|fbav|fban|line\//i.test(ua) || /inapp|wv\)/i.test(ua)) {
            root.classList.add("saju-platform-inapp");
        }
        try {
            const w = pw.innerWidth || root.clientWidth || 0;
            if (
                (w > 0 && w <= 768) ||
                (pw.matchMedia && pw.matchMedia("(max-width: 768px)").matches)
            ) {
                root.classList.add("saju-mobile-stable");
            }
        } catch (e) {}
    };
    pw.__sajuDetectMobilePlatform();

    pw.__sajuCollapseHiddenHard = function (el) {
        if (!el || !el.style) return;
        if (el.id === "saju-step-top-anchor") return;
        try {
            el.style.setProperty("display", "none", "important");
            el.style.setProperty("visibility", "hidden", "important");
            el.style.setProperty("height", "0", "important");
            el.style.setProperty("max-height", "0", "important");
            el.style.setProperty("overflow", "hidden", "important");
            el.style.setProperty("pointer-events", "none", "important");
            el.style.setProperty("opacity", "0", "important");
        } catch (e) {}
    };

    pw.__sajuHideLandingChrome = function (doc) {
        if (!doc) return;
        if (typeof pw.__sajuIsHomeStep === "function" && pw.__sajuIsHomeStep()) return;
        [
            ".st-key-saju_landing_stack",
            ".st-key-saju_landing_hero",
            ".st-key-saju_landing_cta",
            ".st-key-step1_solar24",
            ".st-key-step1_cta_row_main",
            ".st-key-step1_cta_row_free",
            ".saju-landing-hero",
        ].forEach(function (sel) {
            try {
                doc.querySelectorAll(sel).forEach(pw.__sajuCollapseHiddenHard);
            } catch (e) {}
        });
    };

    const _coerceStepNum = function (step) {
        const n = String(step == null ? "" : step).trim();
        if (!/^\d+$/.test(n)) return "1";
        const v = Math.max(1, Math.min(12, parseInt(n, 10) || 1));
        return String(v);
    };

    pw.__sajuHideStaleStepMounts = function (step) {
        /* Streamlit React 트리에 inline style 을 쓰지 않음 — <html data-saju-step> + CSS 만 */
        const doc = pw.document || document;
        const root = doc && doc.documentElement;
        if (!root) return;
        const n = _coerceStepNum(step);
        root.setAttribute("data-saju-step", n);
        root.classList.remove("saju-home-step1", "saju-not-step1");
        if (n === "1") {
            root.classList.add("saju-home-step1");
        } else if (n) {
            root.classList.add("saju-not-step1");
        }
        if (n !== "1") {
            if (typeof pw.__sajuStopMobileHomeLayoutGuard === "function") {
                pw.__sajuStopMobileHomeLayoutGuard();
            }
        }
    };

    pw.__sajuScheduleHideStaleStepMounts = function (step) {
        const n = _coerceStepNum(step);
        if (typeof pw.__sajuHideStaleStepMounts === "function") {
            pw.__sajuHideStaleStepMounts(n);
        }
        try {
            pw.setTimeout(function () {
                if (typeof pw.__sajuHideStaleStepMounts === "function") {
                    pw.__sajuHideStaleStepMounts(n);
                }
            }, 96);
        } catch (e) {}
    };

    pw.__sajuScheduleHomeSolar24Fit = function () {
        if (!pw.__sajuIsHomeStep || !pw.__sajuIsHomeStep()) return;
        const run = function () {
            if (typeof pw.__sajuFitHomeSolar24Iframe === "function") {
                try {
                    pw.__sajuFitHomeSolar24Iframe();
                } catch (e) {}
            }
        };
        run();
        try {
            [360, 1200].forEach(function (ms) {
                pw.setTimeout(function () {
                    if (!pw.__sajuIsHomeStep || !pw.__sajuIsHomeStep()) return;
                    if (pw.__sajuUserIsScrolling) return;
                    run();
                }, ms);
            });
        } catch (e) {}
    };

    pw.__sajuSyncStepToHtml = function (step) {
        const doc = pw.document || document;
        const root = doc && doc.documentElement;
        if (!root) return;
        const n = _coerceStepNum(step);
        root.setAttribute("data-saju-step", n);
        root.classList.remove("saju-home-step1", "saju-not-step1");
        if (n === "1") {
            root.classList.add("saju-home-step1");
            pw.__sajuHomeHeroPinnedEpoch = null;
            pw.__sajuHomeLayoutFixApplied = false;
            if (typeof pw.__sajuPinHomeHeroTop === "function") {
                pw.__sajuPinHomeHeroTop(true);
            }
            if (typeof pw.__sajuStartMobileHomeLayoutGuard === "function") {
                pw.__sajuStartMobileHomeLayoutGuard();
            }
        } else if (n) {
            root.classList.add("saju-not-step1");
            pw.__sajuHomeHeroPinnedEpoch = null;
            if (typeof pw.__sajuClearHomeTopPull === "function") {
                pw.__sajuClearHomeTopPull();
            }
        }
        if (typeof pw.__sajuHideStaleStepMounts === "function") {
            pw.__sajuHideStaleStepMounts(n);
        }
    };

    pw.__sajuRevealMainContent = function (force) {
        const doc = pw.document || document;
        const root = doc && doc.documentElement;
        if (!doc || !root) return;
        const mobile = isMobileView(pw, doc);
        const now = Date.now();
        if (!force && mobile && pw.__sajuRevealLastAt && now - pw.__sajuRevealLastAt < 2500) {
            return;
        }
        pw.__sajuRevealLastAt = now;
        const step = String(root.getAttribute("data-saju-step") || "1");
        if (typeof pw.__sajuHideStaleStepMounts === "function") {
            pw.__sajuHideStaleStepMounts(step);
        }
        const onHome =
            step === "1" ||
            (typeof pw.__sajuIsHomeStep === "function" && pw.__sajuIsHomeStep());
        if (onHome) {
            if (typeof pw.__sajuScheduleHomeSolar24Fit === "function") {
                pw.__sajuScheduleHomeSolar24Fit();
            }
            if (mobile && typeof pw.__sajuPinHomeHeroTop === "function") {
                pw.__sajuPinHomeHeroTop(true);
            }
            if (
                mobile &&
                typeof pw.__sajuStartMobileHomeLayoutGuard === "function"
            ) {
                pw.__sajuStartMobileHomeLayoutGuard();
            }
        } else if (typeof pw.__sajuStopMobileHomeLayoutGuard === "function") {
            pw.__sajuStopMobileHomeLayoutGuard();
        }
    };

    pw.__sajuCollapseHomeTopChrome = function (doc) {
        /* 유틸 위젯만 숨김 — mount 이전 형제를 접으면 모바일에서 본문 전체가 사라질 수 있음 */
        const collapse = function (el) {
            if (!el || !el.style) return;
            if (el.id === "saju-step-top-anchor") return;
            try {
                if (el.closest("[class*='st-key-saju_router_step_mount_']")) return;
                if (el.closest(".st-key-saju_landing_stack")) return;
                el.style.setProperty("display", "none", "important");
                el.style.setProperty("visibility", "hidden", "important");
                el.style.setProperty("height", "0", "important");
                el.style.setProperty("max-height", "0", "important");
                el.style.setProperty("overflow", "hidden", "important");
                el.style.setProperty("pointer-events", "none", "important");
            } catch (e) {}
        };
        if (typeof pw.__sajuHideStaleStepMounts === "function") {
            const root = doc && doc.documentElement;
            const step = root ? String(root.getAttribute("data-saju-step") || "1") : "1";
            pw.__sajuHideStaleStepMounts(step);
        }
        [
            ".st-key-saju_browser_nav_check",
            ".st-key-saju_browser_privacy_client_v2",
            ".st-key-saju_step_html_sync",
            "[class*='st-key-saju_step_html_sync_']",
            "[class*='st-key-saju_scroll_fire_']",
            "[class*='st-key-saju_home_viewport_']",
            ".st-key-saju_home_solar_fit",
        ].forEach(function (sel) {
            try {
                doc.querySelectorAll(sel).forEach(collapse);
            } catch (e) {}
        });
    };

    pw.__sajuWalkParentsFlushTop = function (start) {
        const doc = pw.document || document;
        if (!doc || !start) return;
        let node = start.parentElement;
        while (node && node !== doc.documentElement) {
            if (!node.style) {
                node = node.parentElement;
                continue;
            }
            try {
                const tid = node.getAttribute && node.getAttribute("data-testid");
                const isScrollRoot =
                    tid === "stAppViewContainer" ||
                    tid === "stMain" ||
                    tid === "stMainBlockContainer" ||
                    (node.classList &&
                        (node.classList.contains("stApp") ||
                            node.classList.contains("main") ||
                            node.classList.contains("block-container")));
                if (isScrollRoot) {
                    node.style.setProperty("display", "block", "important");
                }
                node.style.setProperty("justify-content", "flex-start", "important");
                node.style.setProperty("align-items", "stretch", "important");
                node.style.setProperty("align-content", "flex-start", "important");
                node.style.setProperty("min-height", "0", "important");
                node.style.setProperty("height", "auto", "important");
                node.style.setProperty("max-height", "none", "important");
                node.style.setProperty("flex", "none", "important");
                node.style.setProperty("margin-top", "0", "important");
                node.style.setProperty("padding-top", "0", "important");
                if (
                    !node.getAttribute ||
                    node.getAttribute("data-saju-home-pulled") !== "1"
                ) {
                    node.style.setProperty("transform", "none", "important");
                }
            } catch (eWalk) {}
            node = node.parentElement;
        }
    };

    pw.__sajuEnsureHomeTopStyleTag = function () {
        const doc = pw.document || document;
        if (!doc || !doc.head) return;
        const oldTag = doc.getElementById("saju-home-top-flush-style");
        if (oldTag) {
            try {
                oldTag.remove();
            } catch (eRm) {}
        }
        const tag = doc.createElement("style");
        tag.id = "saju-home-top-flush-style";
        tag.textContent =
            "html.saju-home-step1,html[data-saju-step='1']{scroll-padding-top:0!important;}" +
            "html.saju-home-step1 body,html[data-saju-step='1'] body{" +
            "display:block!important;min-height:0!important;height:auto!important;margin:0!important;padding:0!important;}" +
            "html.saju-home-step1 .stApp,html[data-saju-step='1'] .stApp," +
            "html.saju-home-step1 [data-testid='stAppViewContainer'],html[data-saju-step='1'] [data-testid='stAppViewContainer']," +
            "html.saju-home-step1 [data-testid='stAppViewContainer']>.main,html[data-saju-step='1'] [data-testid='stAppViewContainer']>.main," +
            "html.saju-home-step1 section.main,html[data-saju-step='1'] section.main," +
            "html.saju-home-step1 [data-testid='stMain'],html[data-saju-step='1'] [data-testid='stMain']," +
            "html.saju-home-step1 [data-testid='stMainBlockContainer'],html[data-saju-step='1'] [data-testid='stMainBlockContainer']," +
            "html.saju-home-step1 .main .block-container,html[data-saju-step='1'] .main .block-container{" +
            "display:block!important;min-height:0!important;height:auto!important;max-height:none!important;" +
            "justify-content:flex-start!important;align-items:stretch!important;align-content:flex-start!important;" +
            "flex:none!important;margin-top:0!important;padding-top:0!important;}" +
            ".stApp:has(.st-key-saju_router_step_mount_01) .main .block-container{padding-top:0!important;margin-top:0!important;padding-left:0!important;padding-right:0!important;max-width:100%!important;min-height:0!important;}" +
            "html:has(.st-key-saju_router_step_mount_01) [data-testid='stAppViewContainer']{min-height:0!important;height:auto!important;display:block!important;flex:none!important;justify-content:flex-start!important;align-items:stretch!important;}" +
            ".stApp:has(.st-key-saju_router_step_mount_01) .main .block-container>[data-testid='stVerticalBlock']{" +
            "display:flex!important;flex-direction:column!important;justify-content:flex-start!important;" +
            "min-height:0!important;height:auto!important;gap:0!important;padding-top:0!important;margin-top:0!important;}" +
            ".stApp:has(.st-key-saju_router_step_mount_01) .main .block-container>[data-testid='stVerticalBlock']>[data-testid='stElementContainer']:not(:has(.st-key-saju_router_step_mount_01)):not(:has(.st-key-saju_global_bottom_chrome)){" +
            "display:none!important;height:0!important;max-height:0!important;margin:0!important;padding:0!important;visibility:hidden!important;position:absolute!important;left:-99999px!important;width:0!important;}" +
            ".stApp:has(.st-key-saju_router_step_mount_01) .main .block-container>[data-testid='stVerticalBlock']>[data-testid='stElementContainer']:has(.st-key-saju_router_step_mount_01){" +
            "display:block!important;visibility:visible!important;height:auto!important;max-height:none!important;position:relative!important;left:auto!important;width:100%!important;}" +
            ".st-key-saju_router_step_mount_01{margin-top:0!important;padding-top:0!important;}" +
            "html:has(.st-key-saju_router_step_mount_01) [data-testid='stAppViewContainer']," +
            ".stApp:has(.st-key-saju_router_step_mount_01) [data-testid='stAppViewContainer']{" +
            "height:auto!important;min-height:0!important;max-height:none!important;" +
            "display:block!important;justify-content:flex-start!important;}" +
            ".stApp:has(.st-key-saju_router_step_mount_01) [data-testid='stAppViewContainer']>.main," +
            ".stApp:has(.st-key-saju_router_step_mount_01) section.main{" +
            "padding-top:0!important;margin-top:0!important;min-height:0!important;height:auto!important;" +
            "display:block!important;justify-content:flex-start!important;align-items:stretch!important;}" +
            ".stApp:has(.st-key-saju_router_step_mount_01) [data-testid='stVerticalBlockBorderWrapper']{" +
            "display:block!important;min-height:0!important;height:auto!important;margin:0!important;padding:0!important;}" +
            ".st-key-saju_router_step_mount_01 .st-key-saju_landing_stack{margin-top:0!important;padding-top:0!important;}" +
            ".st-key-saju_router_step_mount_01 [data-testid='stVerticalBlock']{gap:0!important;row-gap:0!important;}";
        doc.head.appendChild(tag);
    };

    pw.__sajuHideBlocksBeforeHomeMount = function () {
        const doc = pw.document || document;
        const mount = doc.querySelector(".st-key-saju_router_step_mount_01");
        const block = doc.querySelector(".main .block-container");
        if (!mount || !block) return;
        const hide = function (el) {
            if (!el || !el.style) return;
            try {
                el.style.setProperty("display", "none", "important");
                el.style.setProperty("height", "0", "important");
                el.style.setProperty("max-height", "0", "important");
                el.style.setProperty("visibility", "hidden", "important");
            } catch (e) {}
        };
        if (typeof pw.__sajuHidePreMountStreamlitBlocks === "function") {
            pw.__sajuHidePreMountStreamlitBlocks();
            return;
        }
        const vb = block.querySelector(
            ':scope > [data-testid="stVerticalBlock"]'
        );
        const rows = vb
            ? vb.querySelectorAll(':scope > [data-testid="stElementContainer"]')
            : block.querySelectorAll(':scope > [data-testid="stElementContainer"]');
        rows.forEach(function (ec) {
            if (ec.classList.contains("st-key-saju_router_step_mount_01")) return;
            if (ec.contains(mount)) return;
            if (ec.querySelector(".st-key-saju_global_bottom_chrome")) return;
            hide(ec);
        });
    };

    pw.__sajuSnapAllScrollRootsTop = function () {
        const doc = pw.document || document;
        [
            doc.querySelector('[data-testid="stAppViewContainer"]'),
            doc.querySelector('[data-testid="stMain"]'),
            doc.querySelector('[data-testid="stMainBlockContainer"]'),
            doc.querySelector("section.main"),
            doc.body,
            doc.scrollingElement,
            doc.documentElement,
        ].forEach(function (el) {
            if (!el) return;
            try {
                el.scrollTop = 0;
                el.scrollLeft = 0;
            } catch (e) {}
        });
        try {
            pw.scrollTo(0, 0);
        } catch (eWin) {}
    };

    pw.__sajuClearHomeTopPull = function () {
        const doc = pw.document || document;
        if (!doc) return;
        const nodes = [
            doc.querySelector(".stApp"),
            doc.querySelector('[data-testid="stAppViewContainer"]'),
            doc.querySelector('[data-testid="stAppViewContainer"] > .main'),
            doc.querySelector("section.main"),
            doc.querySelector(".main .block-container"),
            doc.querySelector(
                ".main .block-container > [data-testid='stVerticalBlock']"
            ),
            doc.querySelector(".st-key-saju_router_step_mount_01"),
        ];
        try {
            doc.querySelectorAll("[data-saju-home-flush='1']").forEach(function (el) {
                nodes.push(el);
            });
        } catch (eAll) {}
        nodes.forEach(function (el) {
            if (!el || !el.style) return;
            try {
                el.style.removeProperty("transform");
                el.style.removeProperty("margin-top");
                el.removeAttribute("data-saju-home-pulled");
                el.removeAttribute("data-saju-home-flush");
            } catch (eClr) {}
        });
    };

    pw.__sajuHidePreMountStreamlitBlocks = function () {
        const doc = pw.document || document;
        const block = doc.querySelector(".main .block-container");
        const mount = doc.querySelector(".st-key-saju_router_step_mount_01");
        if (!block || !mount) return;
        const vb = block.querySelector(
            ':scope > [data-testid="stVerticalBlock"]'
        );
        const rows = vb
            ? vb.querySelectorAll(':scope > [data-testid="stElementContainer"]')
            : block.querySelectorAll('[data-testid="stElementContainer"]');
        const hide = function (el) {
            if (!el || !el.style) return;
            if (
                el.querySelector(".st-key-saju_router_step_mount_01") ||
                el.querySelector(".st-key-saju_global_bottom_chrome")
            ) {
                return;
            }
            if (mount.contains(el)) return;
            try {
                el.style.setProperty("display", "none", "important");
                el.style.setProperty("height", "0", "important");
                el.style.setProperty("max-height", "0", "important");
                el.style.setProperty("margin", "0", "important");
                el.style.setProperty("padding", "0", "important");
                el.style.setProperty("visibility", "hidden", "important");
                el.style.setProperty("position", "absolute", "important");
                el.style.setProperty("left", "-99999px", "important");
                el.style.setProperty("width", "0", "important");
            } catch (e) {}
        };
        rows.forEach(hide);
    };

    /* translateY 당김은 배너를 화면 밖으로 밀어냄 — 스크롤만 사용 */
    pw.__sajuTranslateHomeContentToTop = function () {
        const doc = pw.document || document;
        if (typeof pw.__sajuClearHomeTopPull === "function") {
            pw.__sajuClearHomeTopPull();
        }
        const view = doc.querySelector('[data-testid="stAppViewContainer"]');
        const mount = doc.querySelector(".st-key-saju_router_step_mount_01");
        const hero =
            doc.getElementById("saju-home-hero-top") ||
            doc.querySelector(".saju-home-hero-banner") ||
            doc.querySelector(".st-key-saju_landing_hero");
        const align = mount || hero;
        if (!align) return 999;
        if (typeof pw.__sajuSnapAllScrollRootsTop === "function") {
            pw.__sajuSnapAllScrollRootsTop();
        }
        const viewTop = view ? view.getBoundingClientRect().top || 0 : 0;
        let gap = Math.round((align.getBoundingClientRect().top || 0) - viewTop);
        let pass = 0;
        while (view && Math.abs(gap) > 4 && pass < 8) {
            try {
                view.scrollTop = Math.max(0, (view.scrollTop || 0) + gap - 2);
            } catch (eSc) {}
            gap = Math.round(
                (align.getBoundingClientRect().top || 0) - viewTop
            );
            pass += 1;
        }
        try {
            pw.scrollTo(0, 0);
        } catch (eW) {}
        return Math.abs(gap);
    };

    pw.__sajuHideMountUtilBlocksBeforeHero = function () {
        const doc = pw.document || document;
        const mount = doc.querySelector(".st-key-saju_router_step_mount_01");
        if (!mount) return;
        const hide = function (el) {
            if (!el || !el.style) return;
            if (
                el.querySelector(".st-key-saju_landing_hero") ||
                el.querySelector(".st-key-saju_landing_stack") ||
                el.querySelector("#saju-home-hero-top")
            ) {
                return;
            }
            const cls = String(el.className || "");
            if (
                cls.indexOf("saju_landing_hero") >= 0 ||
                cls.indexOf("saju_landing_stack") >= 0
            ) {
                return;
            }
            if (
                cls.indexOf("saju_step_html_sync") < 0 &&
                cls.indexOf("saju_scroll_") < 0
            ) {
                return;
            }
            try {
                el.style.setProperty("display", "none", "important");
                el.style.setProperty("height", "0", "important");
                el.style.setProperty("visibility", "hidden", "important");
            } catch (e) {}
        };
        mount.querySelectorAll(
            '[data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]'
        ).forEach(hide);
    };

    pw.__sajuHomeScrollOffset = function () {
        const doc = pw.document || document;
        let max = 0;
        try {
            const main =
                doc.querySelector('[data-testid="stAppViewContainer"]') ||
                doc.querySelector('[data-testid="stMainBlockContainer"]') ||
                doc.scrollingElement;
            if (main) max = Math.max(max, main.scrollTop || 0);
        } catch (eM) {}
        try {
            max = Math.max(
                max,
                pw.scrollY || 0,
                doc.documentElement.scrollTop || 0,
                doc.body.scrollTop || 0
            );
        } catch (eD) {}
        return max;
    };

    /* margin/translateY 당김 비활성 — 모바일 백화·이중 스크롤 유발. 상단 정렬은 CSS만. */
    pw.__sajuApplyHomeTopPull = function (pinEl) {
        if (typeof pw.__sajuClearHomeTopPull === "function") {
            pw.__sajuClearHomeTopPull();
        }
        if (!pinEl) return 999;
        try {
            return Math.ceil(pinEl.getBoundingClientRect().top || 0);
        } catch (e) {
            return 999;
        }
    };

    /* 사진2 — 상단 백화 제거 + 배너 y=0 (단일 경로) */
    pw.__sajuPhoto2SnapTop = function () {
        const doc = pw.document || document;
        const mount = doc.querySelector(".st-key-saju_router_step_mount_01");
        const hero =
            doc.getElementById("saju-home-hero-top") ||
            doc.querySelector(".saju-home-hero-banner") ||
            (mount && mount.querySelector(".st-key-saju_landing_hero"));
        if (!mount || !hero) return false;
        try {
            const root = doc.documentElement;
            if (root) {
                root.classList.add("saju-home-step1");
                root.classList.remove("saju-not-step1");
                root.setAttribute("data-saju-step", "1");
            }
        } catch (eAttr) {}
        if (typeof pw.__sajuDetectMobilePlatform === "function") {
            try {
                pw.__sajuDetectMobilePlatform();
            } catch (ePlat) {}
        }
        if (typeof pw.__sajuEnsureHomeTopStyleTag === "function") {
            pw.__sajuEnsureHomeTopStyleTag();
        }
        if (typeof pw.__sajuClearHomeTopPull === "function") {
            pw.__sajuClearHomeTopPull();
        }
        if (typeof pw.__sajuHidePreMountStreamlitBlocks === "function") {
            pw.__sajuHidePreMountStreamlitBlocks();
        }
        if (typeof pw.__sajuRevealHomeLandingBlocks === "function") {
            pw.__sajuRevealHomeLandingBlocks();
        }
        if (typeof pw.__sajuHideMountUtilBlocksBeforeHero === "function") {
            pw.__sajuHideMountUtilBlocksBeforeHero();
        }
        const pinChain = function (el, flexCol) {
            if (!el || !el.style) return;
            try {
                if (flexCol) {
                    el.style.setProperty("display", "flex", "important");
                    el.style.setProperty("flex-direction", "column", "important");
                } else {
                    el.style.setProperty("display", "block", "important");
                }
                el.style.setProperty("justify-content", "flex-start", "important");
                el.style.setProperty("align-items", "stretch", "important");
                el.style.setProperty("align-content", "flex-start", "important");
                el.style.setProperty("min-height", "0", "important");
                el.style.setProperty("height", "auto", "important");
                el.style.setProperty("max-height", "none", "important");
                el.style.setProperty("margin-top", "0", "important");
                el.style.setProperty("padding-top", "0", "important");
                el.style.setProperty("flex", "none", "important");
                el.style.setProperty("transform", "none", "important");
            } catch (ePin) {}
        };
        const block = doc.querySelector(".main .block-container");
        const rootVb = block
            ? block.querySelector(
                  ':scope > [data-testid="stVerticalBlock"], :scope > [data-testid="stVerticalBlockBorderWrapper"] > [data-testid="stVerticalBlock"]'
              )
            : null;
        const rootWrap = block
            ? block.querySelector(':scope > [data-testid="stVerticalBlockBorderWrapper"]')
            : null;
        [
            doc.body,
            doc.documentElement,
            doc.querySelector(".stApp"),
            doc.querySelector('[data-testid="stAppViewContainer"]'),
            doc.querySelector('[data-testid="stAppViewContainer"] > .main'),
            doc.querySelector("section.main"),
            doc.querySelector('[data-testid="stMain"]'),
            doc.querySelector('[data-testid="stMainBlockContainer"]'),
            block,
            rootWrap,
            rootVb,
            mount,
        ].forEach(function (el) {
            pinChain(el, false);
        });
        const vb = mount.querySelector('[data-testid="stVerticalBlock"]');
        if (vb) pinChain(vb, true);
        if (typeof pw.__sajuSnapAllScrollRootsTop === "function") {
            pw.__sajuSnapAllScrollRootsTop();
        }
        if (typeof pw.__sajuScrollHomeTopOnce === "function") {
            pw.__sajuScrollHomeTopOnce();
        }
        const view = doc.querySelector('[data-testid="stAppViewContainer"]');
        let topGap = Math.round(hero.getBoundingClientRect().top || 0);
        if (view && topGap > 6) {
            try {
                view.scrollTop = Math.max(
                    0,
                    (view.scrollTop || 0) + topGap - 2
                );
            } catch (eSc) {}
            topGap = Math.round(hero.getBoundingClientRect().top || 0);
        }
        try {
            pw.scrollTo(0, 0);
        } catch (eW) {}
        if (typeof pw.__sajuEnforceMobileHomePhoto2 === "function") {
            try {
                pw.__sajuEnforceMobileHomePhoto2();
            } catch (eM) {}
        }
        return topGap <= 10;
    };

    pw.__sajuLockHomeViewportTop = function () {
        if (typeof pw.__sajuPhoto2SnapTop === "function") {
            return pw.__sajuPhoto2SnapTop();
        }
        return false;
    };
    pw.__sajuSnapHomeHeroToTop = function (force) {
        const doc = pw.document || document;
        if (!doc) return;
        const onHome =
            (typeof pw.__sajuIsHomeOnDom === "function" && pw.__sajuIsHomeOnDom()) ||
            (typeof pw.__sajuIsHomeStep === "function" && pw.__sajuIsHomeStep());
        if (!onHome && !force) return;
        if (typeof pw.__sajuLockHomeViewportTop === "function") {
            pw.__sajuLockHomeViewportTop();
        }
    };

    pw.__sajuFlushHomeTopLayout = function () {
        const doc = pw.document || document;
        if (!doc || !pw.__sajuIsHomeStep()) return;
        if (typeof pw.__sajuEnsureHomeTopStyleTag === "function") {
            pw.__sajuEnsureHomeTopStyleTag();
        }
        if (typeof pw.__sajuHideBlocksBeforeHomeMount === "function") {
            pw.__sajuHideBlocksBeforeHomeMount();
        }
        const flush = function (el) {
            if (!el || !el.style) return;
            try {
                const tid = el.getAttribute && el.getAttribute("data-testid");
                const isMount =
                    el.classList &&
                    el.classList.contains("st-key-saju_router_step_mount_01");
                const isMountVb =
                    tid === "stVerticalBlock" &&
                    el.closest &&
                    el.closest(".st-key-saju_router_step_mount_01");
                if (isMount || isMountVb) {
                    el.style.setProperty("display", "flex", "important");
                    el.style.setProperty("flex-direction", "column", "important");
                } else {
                    el.style.setProperty("display", "block", "important");
                }
                el.style.setProperty("justify-content", "flex-start", "important");
                el.style.setProperty("align-items", "stretch", "important");
                el.style.setProperty("align-content", "flex-start", "important");
                el.style.setProperty("min-height", "0", "important");
                el.style.setProperty("height", "auto", "important");
                el.style.setProperty("max-height", "none", "important");
                el.style.setProperty("flex", "none", "important");
                el.style.setProperty("margin-top", "0", "important");
                el.style.setProperty("padding-top", "0", "important");
                const keepFlush =
                    el.getAttribute &&
                    el.getAttribute("data-saju-home-flush") === "1";
                if (
                    !keepFlush &&
                    (!el.getAttribute ||
                        el.getAttribute("data-saju-home-pulled") !== "1")
                ) {
                    el.style.setProperty("transform", "none", "important");
                }
            } catch (e) {}
        };
        [
            doc.querySelector(".stApp"),
            doc.querySelector('[data-testid="stAppViewContainer"]'),
            doc.querySelector('[data-testid="stAppViewContainer"] > .main'),
            doc.querySelector("section.main"),
            doc.querySelector('[data-testid="stMain"]'),
            doc.querySelector('[data-testid="stMainBlockContainer"]'),
            doc.querySelector(".main .block-container"),
            doc.querySelector(".st-key-saju_router_step_mount_01"),
            doc.querySelector(
                '.st-key-saju_router_step_mount_01 [data-testid="stVerticalBlock"]'
            ),
            doc.querySelector(".st-key-saju_landing_hero"),
            doc.querySelector(".st-key-saju_landing_stack"),
        ].forEach(flush);
        const activeTop = doc.getElementById("saju-step-active-top");
        if (activeTop && activeTop.style) {
            try {
                activeTop.style.setProperty("display", "none", "important");
                activeTop.style.setProperty("height", "0", "important");
                activeTop.style.setProperty("margin", "0", "important");
                activeTop.style.setProperty("padding", "0", "important");
            } catch (eTop) {}
        }
        const hero = doc.getElementById("saju-home-hero-top");
        if (hero && typeof pw.__sajuWalkParentsFlushTop === "function") {
            pw.__sajuWalkParentsFlushTop(hero);
        }
    };

    pw.__sajuIsHomeOnDom = function () {
        const doc = pw.document || document;
        if (!doc) return false;
        return !!doc.querySelector(
            ".st-key-saju_router_step_mount_01 .st-key-saju_landing_hero, " +
                ".st-key-saju_router_step_mount_01 #saju-home-hero-top, " +
                ".st-key-saju_router_step_mount_01 .saju-home-hero-banner"
        );
    };

    pw.__sajuIsHomeStep = function () {
        if (pw.__sajuIsHomeOnDom()) return true;
        const doc = pw.document || document;
        const root = doc && doc.documentElement;
        if (!root) return false;
        return (
            root.classList.contains("saju-home-step1") ||
            String(root.getAttribute("data-saju-step") || "") === "1"
        );
    };

    pw.__sajuScrollMainToHeroTop = function (hero) {
        const doc = pw.document || document;
        if (!doc || !hero) return;
        const main =
            doc.querySelector('[data-testid="stAppViewContainer"]') ||
            getMainScrollEl(doc);
        if (!main) return;
        try {
            const mRect = main.getBoundingClientRect();
            const hRect = hero.getBoundingClientRect();
            const delta = Math.round(hRect.top - mRect.top);
            if (Math.abs(delta) > 2) {
                main.scrollTop = Math.max(0, (main.scrollTop || 0) + delta);
            }
        } catch (e) {}
    };

    pw.__sajuCollapseBlocksBeforeHomeMount = function () {
        const doc = pw.document || document;
        const mount = doc.querySelector(".st-key-saju_router_step_mount_01");
        const block = doc.querySelector(".main .block-container");
        if (!mount || !block) return;
        const mountEc = mount.closest('[data-testid="stElementContainer"]');
        const hide = function (el) {
            if (!el || !el.style) return;
            if (
                el.contains(mount) ||
                el.querySelector(".st-key-saju_global_bottom_chrome") ||
                el.querySelector(".st-key-saju_global_prev_next")
            ) {
                return;
            }
            try {
                el.style.setProperty("display", "none", "important");
                el.style.setProperty("height", "0", "important");
                el.style.setProperty("max-height", "0", "important");
                el.style.setProperty("min-height", "0", "important");
                el.style.setProperty("margin", "0", "important");
                el.style.setProperty("padding", "0", "important");
                el.style.setProperty("overflow", "hidden", "important");
                el.style.setProperty("visibility", "hidden", "important");
                el.style.setProperty("pointer-events", "none", "important");
            } catch (e) {}
        };
        if (typeof pw.__sajuHidePreMountStreamlitBlocks === "function") {
            pw.__sajuHidePreMountStreamlitBlocks();
            return;
        }
        const vb = block.querySelector(
            ':scope > [data-testid="stVerticalBlock"]'
        );
        const kids = vb
            ? vb.querySelectorAll(':scope > [data-testid="stElementContainer"]')
            : block.querySelectorAll(':scope > [data-testid="stElementContainer"]');
        if (mountEc) {
            let beforeMount = true;
            kids.forEach(function (ec) {
                if (ec === mountEc || ec.contains(mount)) {
                    beforeMount = false;
                    return;
                }
                if (beforeMount) hide(ec);
            });
            return;
        }
        let seenMount = false;
        kids.forEach(function (ec) {
            if (ec.contains(mount)) {
                seenMount = true;
                return;
            }
            if (!seenMount) hide(ec);
        });
    };

    pw.__sajuRevealHomeLandingBlocks = function () {
        const doc = pw.document || document;
        if (
            typeof pw.__sajuIsHomeOnDom === "function" &&
            !pw.__sajuIsHomeOnDom()
        ) {
            return;
        }
        const reveal = function (el) {
            if (!el || !el.style) return;
            try {
                [
                    "display",
                    "visibility",
                    "height",
                    "max-height",
                    "min-height",
                    "overflow",
                    "opacity",
                    "pointer-events",
                ].forEach(function (p) {
                    el.style.removeProperty(p);
                });
            } catch (e) {}
        };
        [
            ".st-key-saju_landing_hero",
            ".st-key-saju_landing_stack",
            ".st-key-step1_solar24",
            ".st-key-step1_cta_row_main",
            ".st-key-step1_cta_row_free",
            ".st-key-saju_landing_cta",
        ].forEach(function (sel) {
            try {
                doc.querySelectorAll(sel).forEach(reveal);
            } catch (e) {}
        });
        try {
            doc.querySelectorAll(
                ".st-key-saju_landing_stack [data-testid='stElementContainer'], " +
                    ".st-key-saju_landing_stack [data-testid='stVerticalBlock'], " +
                    ".st-key-saju_landing_hero [data-testid='stElementContainer']"
            ).forEach(reveal);
        } catch (e2) {}
        const hideUtil = function (el) {
            if (!el || !el.style) return;
            try {
                el.style.setProperty("display", "none", "important");
                el.style.setProperty("height", "0", "important");
                el.style.setProperty("visibility", "hidden", "important");
            } catch (e) {}
        };
        try {
            doc.querySelectorAll(
                "[class*='st-key-saju_step_html_sync_'], " +
                    ".st-key-saju_step_html_sync"
            ).forEach(hideUtil);
        } catch (e3) {}
    };

    pw.__sajuIsGalaxyDevice = function () {
        const doc = pw.document || document;
        const root = doc && doc.documentElement;
        if (root && root.classList.contains("saju-platform-galaxy")) return true;
        const ua = String((pw.navigator && pw.navigator.userAgent) || "").toLowerCase();
        return (
            /samsung|sm-[a-z0-9]|galaxy|samsungbrowser/i.test(ua) ||
            /android.*samsung/i.test(ua)
        );
    };

    /* 사진1(상단 빈 여백) 유발 — 자동 절기 스크롤 비활성 */
    pw.__sajuScrollHomeSolar24Peek = function () {
        return;
    };

    pw.__sajuEnforceMobileHomePhoto2 = function () {
        /* 모바일 홈: 마크다운 히어로·절기 iframe 높이만 (Streamlit 블록 display 조작 금지) */
        if (!pw.__sajuIsHomeStep()) return;
        const doc = pw.document || document;
        if (!doc || !isMobileView(pw, doc)) return;
        const mount = doc.querySelector(".st-key-saju_router_step_mount_01");
        if (!mount) return;
        const vh = pw.innerHeight || doc.documentElement.clientHeight || 640;
        const heroMax = Math.min(Math.round(vh * 0.38), 340);
        const hero =
            mount.querySelector("#saju-home-hero-top") ||
            mount.querySelector(".saju-home-hero-banner") ||
            mount.querySelector(".saju-landing-hero--nova") ||
            mount.querySelector(".saju-landing-hero");
        const heroImg =
            mount.querySelector(".saju-home-hero-banner img") ||
            mount.querySelector("#saju-home-hero-top img");
        if (heroImg) {
            try {
                heroImg.style.setProperty("max-height", heroMax + "px", "important");
                heroImg.style.setProperty("object-fit", "cover", "important");
                heroImg.style.setProperty("object-position", "center top", "important");
            } catch (e) {}
        } else if (hero) {
            try {
                hero.style.setProperty("max-height", heroMax + "px", "important");
                hero.style.setProperty("overflow", "hidden", "important");
            } catch (e) {}
        }
        const iframe = mount.querySelector(".st-key-step1_solar24 iframe");
        if (iframe) {
            try {
                iframe.style.setProperty("min-height", "580px", "important");
            } catch (e) {}
        }
    };

    pw.__sajuStopMobileHomeLayoutGuard = function () {
        if (pw.__sajuMobileHomeGuardTimer) {
            try {
                pw.clearInterval(pw.__sajuMobileHomeGuardTimer);
            } catch (e) {}
            pw.__sajuMobileHomeGuardTimer = null;
        }
    };

    pw.__sajuStartHomeLayoutGuard = function () {
        /* 반복 재핀은 이중 스크롤·모바일 백화 유발 — 비활성 */
    };
    pw.__sajuStartMobileHomeLayoutGuard = pw.__sajuStartHomeLayoutGuard;

    pw.__sajuLockMobileHomeLayout = function () {
        if (!pw.__sajuIsHomeStep()) return;
        const doc = pw.document || document;
        if (!isMobileView(pw, doc)) return;
        if (typeof pw.__sajuEnforceMobileHomePhoto2 === "function") {
            pw.__sajuEnforceMobileHomePhoto2();
        }
        if (typeof pw.__sajuScheduleHomeSolar24Fit === "function") {
            pw.__sajuScheduleHomeSolar24Fit();
        }
    };

    pw.__sajuNavEpochFromDom = function (doc) {
        const beacon = doc && doc.querySelector(".saju-live-step-beacon");
        if (beacon) {
            return String(beacon.getAttribute("data-saju-nav-epoch") || "0");
        }
        const root = doc && doc.documentElement;
        return root ? String(root.getAttribute("data-saju-nav-epoch") || "0") : "0";
    };

    pw.__sajuPinHomeHeroTop = function (force) {
        const doc = pw.document || document;
        const root = doc && doc.documentElement;
        if (!root) return;
        if (!pw.__sajuIsHomeStep() && !pw.__sajuIsHomeOnDom()) return;
        let heroTopGap = 999;
        try {
            const h0 =
                doc.getElementById("saju-home-hero-top") ||
                doc.querySelector(".st-key-saju_router_step_mount_01 .saju-home-hero-banner");
            heroTopGap = h0 ? h0.getBoundingClientRect().top || 999 : 999;
        } catch (eGap0) {}
        const scrolled =
            !force &&
            heroTopGap <= 24 &&
            (pw.__sajuUserIsScrolling ||
                (typeof pw.__sajuHomeScrollOffset === "function" &&
                    pw.__sajuHomeScrollOffset() > 48));
        if (scrolled) {
            if (typeof pw.__sajuClearHomeTopPull === "function") {
                pw.__sajuClearHomeTopPull();
            }
            if (typeof pw.__sajuStopMobileHomeLayoutGuard === "function") {
                pw.__sajuStopMobileHomeLayoutGuard();
            }
            return;
        }
        if (typeof pw.__sajuDetectMobilePlatform === "function") {
            pw.__sajuDetectMobilePlatform();
        }
        const epoch =
            typeof pw.__sajuNavEpochFromDom === "function"
                ? pw.__sajuNavEpochFromDom(doc)
                : String(root.getAttribute("data-saju-nav-epoch") || "0");
        if (!force && pw.__sajuHomeHeroPinnedEpoch === epoch) {
            try {
                const h0 = doc.getElementById("saju-home-hero-top");
                const top0 = h0 ? h0.getBoundingClientRect().top || 0 : 999;
                if (top0 <= 6) return;
            } catch (e0) {}
        }

        if (typeof pw.__sajuFlushHomeTopLayout === "function") {
            pw.__sajuFlushHomeTopLayout();
        }
        if (typeof pw.__sajuCollapseHomeTopChrome === "function") {
            pw.__sajuCollapseHomeTopChrome(doc);
        }

        const mount = doc.querySelector(".st-key-saju_router_step_mount_01");
        const stack = doc.querySelector(".st-key-saju_landing_stack");
        const heroWrap = doc.querySelector(".st-key-saju_landing_hero");
        const block = doc.querySelector(".main .block-container");
        const heroImgEl =
            doc.querySelector(".saju-home-hero-banner img") ||
            doc.querySelector("#saju-home-hero-top img");
        const hero =
            doc.getElementById("saju-home-hero-top") ||
            doc.querySelector(".saju-home-hero-banner") ||
            doc.querySelector(".st-key-saju_landing_hero .saju-landing-hero") ||
            doc.querySelector(".st-key-saju_router_step_mount_01 .saju-landing-hero") ||
            doc.querySelector(".saju-landing-hero--luxe, .saju-landing-hero--face");

        const layoutTop = function (el) {
            if (!el || !el.style) return;
            try {
                const testId = el.getAttribute && el.getAttribute("data-testid");
                const isScrollRoot =
                    testId === "stAppViewContainer" ||
                    testId === "stMain" ||
                    testId === "stMainBlockContainer" ||
                    (el.classList &&
                        (el.classList.contains("stApp") ||
                            el.classList.contains("main") ||
                            el.classList.contains("block-container")));
                const isMountFlex =
                    el.classList &&
                    (el.classList.contains("st-key-saju_router_step_mount_01") ||
                        (testId === "stVerticalBlock" &&
                            el.closest &&
                            el.closest(".st-key-saju_router_step_mount_01")));
                if (isMountFlex) {
                    el.style.setProperty("display", "flex", "important");
                    el.style.setProperty("flex-direction", "column", "important");
                } else {
                    el.style.setProperty("display", "block", "important");
                }
                el.style.setProperty("justify-content", "flex-start", "important");
                el.style.setProperty("align-items", "stretch", "important");
                el.style.setProperty("align-content", "flex-start", "important");
                el.style.setProperty("flex", "none", "important");
                el.style.setProperty("min-height", "0", "important");
                el.style.setProperty("height", "auto", "important");
                el.style.setProperty("margin-top", "0", "important");
                el.style.setProperty("padding-top", "0", "important");
                if (
                    !isScrollRoot &&
                    (!el.getAttribute ||
                        el.getAttribute("data-saju-home-pulled") !== "1")
                ) {
                    el.style.setProperty("transform", "none", "important");
                }
            } catch (eFlex) {}
        };

        [
            doc.querySelector(".stApp"),
            doc.querySelector('[data-testid="stAppViewContainer"]'),
            doc.querySelector('[data-testid="stAppViewContainer"] > .main'),
            doc.querySelector('[data-testid="stMain"]'),
            doc.querySelector('[data-testid="stMainBlockContainer"]'),
            doc.querySelector("section.main"),
            block,
            mount,
            heroWrap,
            stack,
            mount &&
                mount.querySelector('[data-testid="stVerticalBlock"]'),
        ].forEach(layoutTop);

        [stack, heroWrap, mount].forEach(function (el) {
            if (!el || !el.style) return;
            el.style.setProperty("margin-top", "0", "important");
            el.style.setProperty("padding-top", "0", "important");
            el.style.setProperty("transform", "none", "important");
        });
        if (stack) {
            stack.style.setProperty("padding-top", "0", "important");
        }
        if (heroWrap) {
            heroWrap.style.setProperty("margin-top", "0", "important");
            heroWrap.style.setProperty("padding-top", "0", "important");
        }
        if (block) {
            block.style.setProperty("padding-top", "0", "important");
        }
        if (hero) {
            hero.style.setProperty("justify-content", "flex-start", "important");
            hero.style.setProperty("min-height", "0", "important");
            hero.style.setProperty("margin-top", "0", "important");
            hero.style.setProperty(
                "padding-top",
                "max(0.06rem, env(safe-area-inset-top, 0px))",
                "important"
            );
        }
        doc.querySelectorAll(
            ".st-key-saju_router_step_mount_01 [data-testid='stElementContainer'], " +
                ".st-key-saju_landing_stack [data-testid='stElementContainer'], " +
                ".st-key-saju_landing_stack [data-testid='stMarkdownContainer'], " +
                ".st-key-saju_landing_hero [data-testid='stElementContainer']"
        ).forEach(function (el) {
            el.style.setProperty("padding-top", "0", "important");
            el.style.setProperty("margin-top", "0", "important");
            el.style.setProperty("min-height", "0", "important");
        });

        [mount, heroWrap, stack].forEach(function (el) {
            if (!el || !el.style) return;
            try {
                el.style.setProperty("margin-top", "0", "important");
                el.style.setProperty("padding-top", "0", "important");
            } catch (eReset) {}
        });

        const pinEl = heroImgEl || hero;
        if (pinEl && typeof pw.__sajuWalkParentsFlushTop === "function") {
            pw.__sajuWalkParentsFlushTop(pinEl);
        }
        if (pinEl) {
            try {
                if (typeof pw.__sajuSnapAllScrollRootsTop === "function") {
                    pw.__sajuSnapAllScrollRootsTop();
                }
                if (typeof pw.__sajuApplyHomeTopPull === "function") {
                    pw.__sajuApplyHomeTopPull(pinEl);
                }
            } catch (e) {}
        }

        if (typeof pw.__sajuEnforceMobileHomePhoto2 === "function") {
            pw.__sajuEnforceMobileHomePhoto2();
        }

        const userScrolled =
            typeof pw.__sajuHomeScrollOffset === "function" &&
            pw.__sajuHomeScrollOffset() > 24;
        if (
            !userScrolled &&
            !pw.__sajuUserIsScrolling &&
            typeof pw.__sajuScrollHomeTopOnce === "function"
        ) {
            pw.__sajuScrollHomeTopOnce();
        }
        if (typeof pw.__sajuSnapHomeHeroToTop === "function") {
            pw.__sajuSnapHomeHeroToTop(!!force);
        }
        pw.__sajuHomeHeroPinnedEpoch = epoch;
    };

    pw.__sajuBindHomeLayoutObserver = function () {
        /* MutationObserver 재핀은 모바일 백화·이중 스크롤 유발 — 비활성 */
    };

    const getMainScrollEl = function (doc) {
        /* 실제로 세로 스크롤이 발생하는 요소를 우선 선택한다.
           최신 Streamlit 은 section.main([data-testid=stMain]) 이 스크롤러이고
           stAppViewContainer 는 스크롤되지 않는 flex 래퍼라 scrollTop=0 이 무효다.
           overflow 가 잡혀 실제 스크롤 가능한(첫) 후보를 돌려준다. */
        const cands = [
            doc.querySelector('[data-testid="stMain"]'),
            doc.querySelector("section.main"),
            doc.querySelector('[data-testid="stMainBlockContainer"]'),
            doc.querySelector('[data-testid="stAppViewContainer"]'),
            doc.scrollingElement,
            doc.documentElement,
        ];
        for (let i = 0; i < cands.length; i++) {
            const el = cands[i];
            if (!el) continue;
            try {
                if ((el.scrollHeight || 0) - (el.clientHeight || 0) > 4) {
                    return el;
                }
            } catch (e) {}
        }
        return (
            doc.querySelector('[data-testid="stMain"]') ||
            doc.querySelector("section.main") ||
            doc.querySelector('[data-testid="stMainBlockContainer"]') ||
            doc.querySelector('[data-testid="stAppViewContainer"]') ||
            doc.scrollingElement ||
            doc.documentElement
        );
    };

    pw.__sajuShouldPreserveWidgetFocus = function () {
        try {
            const de = pw.document && pw.document.documentElement;
            if (de && de.getAttribute("data-saju-nav-pending") === "1") {
                return false;
            }
            if (de && de.getAttribute("data-saju-step") === "2") {
                try {
                    if (pw.sessionStorage.getItem("saju_step2_editing") === "1") {
                        return true;
                    }
                } catch (e2) {}
            }
            try {
                if (pw.sessionStorage.getItem("saju_widget_editing") === "1") {
                    return true;
                }
            } catch (e3) {}
        } catch (e) {}
        const lock2 = pw.__sajuStep2FocusLock;
        if (lock2 && lock2.until && Date.now() < lock2.until) return true;
        const lock = pw.__sajuWidgetFocusLock;
        if (lock && lock.until && Date.now() < lock.until) return true;
        return false;
    };

    pw.__sajuUserIsScrolling = false;
    pw.__sajuBindUserScrollGuard = function () {
        if (pw.__sajuUserScrollGuardBound) return;
        pw.__sajuUserScrollGuardBound = true;
        const doc = pw.document || document;
        if (!doc) return;
        const mobile = isMobileView(pw, doc);
        const markUserScroll = function () {
            if (pw.__sajuStepNavScrollActive) return;
            pw.__sajuUserIsScrolling = true;
            if (pw.__sajuUserScrollTimer) {
                try { clearTimeout(pw.__sajuUserScrollTimer); } catch (e) {}
            }
            pw.__sajuUserScrollTimer = pw.setTimeout(function () {
                pw.__sajuUserIsScrolling = false;
            }, mobile ? 420 : 550);
        };
        const events = mobile
            ? ["touchstart", "touchmove", "scroll"]
            : ["touchstart", "touchmove", "wheel", "scroll"];
        events.forEach(function (ev) {
            doc.addEventListener(ev, markUserScroll, { passive: true, capture: true });
        });
        const releaseHomePull = function () {
            if (!pw.__sajuIsHomeStep || !pw.__sajuIsHomeStep()) return;
            if (
                typeof pw.__sajuHomeScrollOffset === "function" &&
                pw.__sajuHomeScrollOffset() > 48
            ) {
                if (typeof pw.__sajuClearHomeTopPull === "function") {
                    pw.__sajuClearHomeTopPull();
                }
                if (typeof pw.__sajuStopMobileHomeLayoutGuard === "function") {
                    pw.__sajuStopMobileHomeLayoutGuard();
                }
            }
        };
        try {
            const main = getMainScrollEl(doc);
            if (main) {
                main.addEventListener("scroll", markUserScroll, { passive: true });
                main.addEventListener("scroll", releaseHomePull, { passive: true });
            }
        } catch (e) {}
        doc.addEventListener("scroll", releaseHomePull, { passive: true, capture: true });
    };
    pw.__sajuBindUserScrollGuard();

    pw.__sajuFocusTopAnchor = function (doc) {
        if (!doc) return;
        let anchor = null;
        try {
            const root = doc.documentElement;
            const stepRaw = root
                ? String(root.getAttribute("data-saju-step") || "1")
                : "1";
            const pad = stepRaw.length < 2 ? "0" + stepRaw : stepRaw;
            const mount = doc.querySelector(
                ".st-key-saju_router_step_mount_" + pad
            );
            if (mount) {
                anchor =
                    mount.querySelector("#saju-step-active-top") ||
                    mount.querySelector("#saju-step-top-anchor");
            }
        } catch (eMount) {}
        if (!anchor) {
            anchor =
                doc.getElementById("saju-step-top-anchor") ||
                doc.getElementById("saju-step-active-top") ||
                doc.querySelector(".st-key-saju_step_top_anchor #saju-step-top-anchor") ||
                doc.querySelector(".st-key-saju_step_top_anchor");
        }
        /* 실제 스크롤러가 무엇이든 0 으로 — 후보 전부 리셋 */
        [
            doc.querySelector('[data-testid="stMain"]'),
            doc.querySelector("section.main"),
            doc.querySelector('[data-testid="stMainBlockContainer"]'),
            doc.querySelector('[data-testid="stAppViewContainer"]'),
            doc.scrollingElement,
            doc.documentElement,
            doc.body,
        ].forEach(function (el) {
            if (!el) return;
            try {
                if ((el.scrollTop || 0) > 0) el.scrollTop = 0;
                if ((el.scrollLeft || 0) > 0) el.scrollLeft = 0;
            } catch (eEl) {}
        });
        try {
            pw.scrollTo(0, 0);
        } catch (eWin) {}
        if (!anchor) return;
        try {
            if (!anchor.hasAttribute("tabindex")) {
                anchor.setAttribute("tabindex", "-1");
            }
        } catch (eTab) {}
        /* 배너가 페이지 최상단에 있으므로 앵커로 scrollIntoView 하면 배너가 화면 위로
           밀려 가려진다. 스크롤은 scrollTop=0(맨 위)만 사용하고, 여기서는 포커스만 둔다. */
        try {
            if (typeof anchor.focus === "function") {
                anchor.focus({ preventScroll: true });
            }
        } catch (eFocus) {}
        try {
            if (doc.body && typeof doc.body.focus === "function") {
                doc.body.focus({ preventScroll: true });
            }
        } catch (eBody) {}
    };

    /* STEP 이동 전용 — DOM 전체 walk 없이 main+window+mount 만 (멈춤 방지) */
    pw.__sajuSnapNavTop = function (opts) {
        opts = opts || {};
        if (
            typeof pw.__sajuShouldPreserveWidgetFocus === "function" &&
            pw.__sajuShouldPreserveWidgetFocus()
        ) {
            return;
        }
        const doc = pw.document || document;
        if (!doc) return;
        const step = String(opts.step != null ? opts.step : "1");
        const isHome = !!opts.home || step === "1";
        if (isHome) {
            if (typeof pw.__sajuSnapViewportTop === "function") {
                pw.__sajuSnapViewportTop({ force: true, home: true });
            }
            return;
        }
        try {
            const ae = doc.activeElement;
            const tag = ae && ae.tagName ? String(ae.tagName).toLowerCase() : "";
            if (tag === "button" && ae && typeof ae.blur === "function") {
                ae.blur();
            }
        } catch (eBtn) {}
        const main = getMainScrollEl(doc);
        if (main) {
            try {
                main.scrollTop = 0;
                main.scrollLeft = 0;
            } catch (eM) {}
        }
        try {
            pw.scrollTo(0, 0);
        } catch (eW) {}
        try {
            const pad = step.length < 2 ? "0" + step : step;
            const mount = doc.querySelector(
                ".st-key-saju_router_step_mount_" + pad
            );
            if (mount && mount.scrollTop > 0) {
                mount.scrollTop = 0;
            }
        } catch (eMt) {}
        if (opts.focus !== false && typeof pw.__sajuFocusTopAnchor === "function") {
            pw.__sajuFocusTopAnchor(doc);
        }
    };

    /* 이전/다음·메뉴 — 즉시+rAF+1회 보정(최대 3회 스냅, setTimeout 스택 없음) */
    pw.__sajuNavScrollOnce = function (epoch, source, stepHint) {
        if (
            typeof pw.__sajuShouldPreserveWidgetFocus === "function" &&
            pw.__sajuShouldPreserveWidgetFocus()
        ) {
            return;
        }
        const key = String(epoch || "0");
        if (String(source || "") === "tail") {
            pw.__sajuNavScrollDoneEpoch = null;
        }
        const now = Date.now();
        if (
            pw.__sajuNavScrollDoneEpoch === key &&
            pw.__sajuNavScrollDoneAt &&
            now - pw.__sajuNavScrollDoneAt < 500
        ) {
            return;
        }
        pw.__sajuNavScrollDoneEpoch = key;
        pw.__sajuNavScrollDoneAt = now;
        if (typeof pw.__sajuCancelStepScroll === "function") {
            pw.__sajuCancelStepScroll();
        }
        const doc = pw.document || document;
        let step = stepHint != null ? String(stepHint) : "1";
        try {
            const root = doc && doc.documentElement;
            if (root && stepHint == null) {
                step = String(root.getAttribute("data-saju-step") || "1");
            }
        } catch (eStep) {}
        const isHome = step === "1";
        const run = function () {
            if (
                isHome &&
                typeof pw.__sajuPinHomeHeroTop === "function"
            ) {
                pw.__sajuPinHomeHeroTop(true);
                return;
            }
            if (typeof pw.__sajuSnapNavTop === "function") {
                pw.__sajuSnapNavTop({ step: step, home: isHome, focus: true });
            } else if (typeof pw.__sajuSnapViewportTop === "function") {
                pw.__sajuSnapViewportTop({ force: true, home: isHome });
            }
        };
        pw.__sajuStepNavScrollActive = true;
        run();
        try {
            pw.requestAnimationFrame(function () {
                run();
                const tid = pw.setTimeout(function () {
                    let off = false;
                    try {
                        const main = getMainScrollEl(doc);
                        off =
                            (main && main.scrollTop > 10) ||
                            (pw.scrollY || 0) > 10;
                    } catch (eOff) {}
                    if (off) {
                        run();
                    } else if (typeof pw.__sajuFocusTopAnchor === "function") {
                        pw.__sajuFocusTopAnchor(doc);
                    }
                    pw.__sajuStepNavScrollActive = false;
                }, 220);
                pw.__sajuStepScrollSnapTimers.push(tid);
                /* STEP5~11: 렌더 후 내용이 늦게 붙어 스크롤이 밀리는 케이스가 있어 1회 추가 보정 */
                try {
                    const s = String(step);
                    if (s === "5" || s === "6" || s === "7" || s === "8" || s === "9" || s === "10" || s === "11") {
                        const tid2 = pw.setTimeout(function () {
                            try {
                                run();
                            } catch (eR2) {}
                            try {
                                if (typeof pw.__sajuFocusTopAnchor === "function") {
                                    pw.__sajuFocusTopAnchor(doc);
                                }
                            } catch (eF2) {}
                        }, s === "5" ? 620 : s === "6" ? 720 : s === "7" ? 760 : s === "8" ? 780 : s === "9" ? 820 : s === "10" ? 860 : 900);
                        pw.__sajuStepScrollSnapTimers.push(tid2);
                    }
                } catch (eT2) {}
            });
        } catch (eRaf) {
            pw.__sajuStepNavScrollActive = false;
        }
    };

    pw.__sajuSnapViewportTop = function (opts) {
        opts = opts || {};
        if (
            !opts.force &&
            typeof pw.__sajuShouldPreserveWidgetFocus === "function" &&
            pw.__sajuShouldPreserveWidgetFocus()
        ) {
            return;
        }
        const doc = pw.document || document;
        if (!doc) return;
        const mobile = isMobileView(pw, doc);
        const isHome =
            !!opts.home ||
            (typeof pw.__sajuIsHomeStep === "function" && pw.__sajuIsHomeStep());
        const mainQuick = getMainScrollEl(doc);
        if (
            !opts.force &&
            !isHome &&
            mainQuick &&
            mainQuick.scrollTop <= 6 &&
            (pw.scrollY || 0) <= 6
        ) {
            pw.__sajuFocusTopAnchor(doc);
            return;
        }
        try {
            const ae = doc.activeElement;
            const tag = ae && ae.tagName ? String(ae.tagName).toLowerCase() : "";
            const keepFocus =
                tag === "input" || tag === "textarea" || tag === "select";
            const isNavBtn =
                ae &&
                ae.tagName &&
                String(ae.tagName).toLowerCase() === "button";
            if (
                !keepFocus &&
                ae &&
                ae !== doc.body &&
                typeof ae.blur === "function" &&
                (isNavBtn || opts.force)
            ) {
                ae.blur();
            }
        } catch (eBlur) {}
        if (isHome) {
            if (typeof pw.__sajuPinHomeHeroTop === "function") {
                pw.__sajuPinHomeHeroTop(!!opts.force);
            } else if (typeof pw.__sajuScrollHomeTopOnce === "function") {
                pw.__sajuScrollHomeTopOnce();
            }
            const mainHome = getMainScrollEl(doc);
            if (mainHome) {
                try {
                    mainHome.scrollTop = 0;
                    mainHome.scrollLeft = 0;
                } catch (eHome) {}
            }
            try {
                pw.scrollTo(0, 0);
            } catch (eWin) {}
            pw.__sajuFocusTopAnchor(doc);
            return;
        }
        const snapEl = function (el) {
            if (!el) return;
            try {
                el.scrollTop = 0;
                el.scrollLeft = 0;
            } catch (e) {}
            try {
                if (typeof el.scrollTo === "function") {
                    el.scrollTo({ top: 0, left: 0, behavior: "auto" });
                }
            } catch (e2) {}
        };
        [
            doc.querySelector('[data-testid="stAppViewContainer"]'),
            doc.querySelector('[data-testid="stMain"]'),
            doc.querySelector("section.main"),
            doc.querySelector('[data-testid="stMainBlockContainer"]'),
            doc.scrollingElement,
            doc.documentElement,
            doc.body,
        ].forEach(snapEl);
        try {
            pw.scrollTo(0, 0);
        } catch (eWin2) {}
        const resetChain = function (el) {
            let p = el;
            while (p) {
                if (p.scrollTop > 0 || p.scrollLeft > 0) {
                    try {
                        p.scrollTop = 0;
                        p.scrollLeft = 0;
                    } catch (e3) {}
                }
                p = p.parentElement;
            }
        };
        try {
            const main0 = getMainScrollEl(doc);
            if (main0) resetChain(main0);
        } catch (eChain) {}
        pw.__sajuFocusTopAnchor(doc);
        try {
            const root = doc.documentElement;
            const stepRaw = root
                ? String(root.getAttribute("data-saju-step") || "1")
                : "1";
            const pad = stepRaw.length < 2 ? "0" + stepRaw : stepRaw;
            const mount = doc.querySelector(
                ".st-key-saju_router_step_mount_" + pad
            );
            if (mount) {
                resetChain(mount);
            }
        } catch (eMount) {}
    };

    pw.__sajuSnapStepTopFast = function () {
        pw.__sajuSnapViewportTop({ force: false });
    };

    pw.__sajuStepScrollSnapTimers = pw.__sajuStepScrollSnapTimers || [];
    pw.__sajuCancelStepScroll = function () {
        (pw.__sajuStepScrollSnapTimers || []).forEach(function (tid) {
            try {
                pw.clearTimeout(tid);
            } catch (e) {}
        });
        pw.__sajuStepScrollSnapTimers = [];
        pw.__sajuStepNavScrollActive = false;
    };

    pw.__sajuForceStepScrollTop = function (epoch, lockMs, phase) {
        if (typeof pw.__sajuNavScrollOnce === "function") {
            pw.__sajuNavScrollOnce(epoch, String(phase || "main"), null);
            return;
        }
        if (typeof pw.__sajuSnapViewportTop === "function") {
            pw.__sajuSnapViewportTop({ force: true });
        }
    };

    pw.__sajuApplySolar24IframeHeight = function (heightPx) {
        const doc = pw.document || document;
        const solarWrap = doc.querySelector(".st-key-step1_solar24");
        if (!solarWrap) return;
        const iframe = solarWrap.querySelector("iframe");
        if (!iframe) return;
        const mobile = isMobileView(pw, doc);
        const floor = mobile ? 580 : 480;
        const cap = mobile ? 860 : 560;
        const h = Math.min(cap, Math.max(floor, Math.ceil(Number(heightPx) || 0)));

        iframe.style.setProperty("height", h + "px", "important");
        iframe.style.setProperty("min-height", h + "px", "important");
        iframe.style.setProperty("max-height", "none", "important");
        iframe.style.setProperty("overflow", "visible", "important");

        const comp =
            solarWrap.querySelector('[data-testid="stCustomComponentV1"]') ||
            solarWrap.querySelector('[data-testid="stHtml"]');
        if (comp) {
            comp.style.setProperty("height", h + "px", "important");
            comp.style.setProperty("min-height", h + "px", "important");
            comp.style.setProperty("max-height", "none", "important");
            comp.style.setProperty("overflow", "visible", "important");
        }
        solarWrap.style.setProperty("overflow", "visible", "important");
    };

    pw.__sajuFitHomeSolar24Iframe = function () {
        const doc = pw.document || document;
        const solarWrap = doc.querySelector(".st-key-step1_solar24");
        if (!solarWrap) return;
        const iframe = solarWrap.querySelector("iframe");
        if (!iframe) return;

        const mobile = isMobileView(pw, doc);
        const root = doc.documentElement;
        const galaxy =
            root &&
            (root.classList.contains("saju-platform-galaxy") ||
                root.classList.contains("saju-platform-android"));
        const floor = mobile ? (galaxy ? 600 : 580) : 480;
        const cap = mobile ? (galaxy ? 880 : 860) : 560;
        let contentH = 0;
        try {
            const idoc = iframe.contentDocument || (iframe.contentWindow && iframe.contentWindow.document);
            if (idoc && idoc.body) {
                const root = idoc.querySelector(".saju-solar24-master");
                if (root) {
                    const rect = root.getBoundingClientRect();
                    contentH = Math.ceil(rect.height || root.offsetHeight || 0);
                }
                if (!contentH) {
                    contentH = Math.ceil(
                        Math.max(
                            idoc.documentElement.scrollHeight || 0,
                            idoc.body.scrollHeight || 0
                        )
                    );
                }
            }
        } catch (e) {}

        let budget;
        if (contentH > 0) {
            budget = Math.min(cap, Math.max(floor, contentH + 28));
        } else {
            /* 콘텐츠 높이 미측정 시 — iframe 너무 낮으면 절기 기둥 겹침(사진3) */
            budget = mobile ? Math.min(cap, Math.max(floor, 620)) : Math.min(cap, 520);
        }

        pw.__sajuApplySolar24IframeHeight(budget);
    };

    if (!pw.__sajuSolar24ResizeBound) {
        pw.__sajuSolar24ResizeBound = true;
        pw.addEventListener("message", function (ev) {
            try {
                const data = ev && ev.data;
                if (!data || data.type !== "saju-solar24-resize") return;
                if (typeof pw.__sajuApplySolar24IframeHeight === "function") {
                    pw.__sajuApplySolar24IframeHeight(data.height);
                }
            } catch (e) {}
        });
    }

    /* 홈 진입 — 갤럭시·모바일은 window/body 스크롤도 0 (삼성 인터넷은 main 이 아닌 document 를 스크롤) */
    pw.__sajuScrollHomeTopOnce = function () {
        if (pw.__sajuUserIsScrolling) return;
        if (
            typeof pw.__sajuShouldPreserveWidgetFocus === "function" &&
            pw.__sajuShouldPreserveWidgetFocus()
        ) {
            return;
        }
        const doc = pw.document || document;
        const mobile = isMobileView(pw, doc);
        const galaxy =
            typeof pw.__sajuIsGalaxyDevice === "function" && pw.__sajuIsGalaxyDevice();
        const main = getMainScrollEl(doc);
        const snapEl = function (el) {
            if (!el) return;
            try {
                el.scrollTop = 0;
                el.scrollLeft = 0;
            } catch (e) {}
        };
        if (main) {
            snapEl(main);
            if (!mobile || galaxy) {
                try {
                    main.scrollTo({ top: 0, left: 0, behavior: "auto" });
                } catch (e) {}
            }
        }
        if (mobile || galaxy) {
            [
                doc.body,
                doc.documentElement,
                doc.querySelector('[data-testid="stMainBlockContainer"]'),
                doc.querySelector("section.main"),
            ].forEach(snapEl);
            try {
                pw.scrollTo(0, 0);
            } catch (e) {}
            try {
                if (pw.visualViewport && pw.visualViewport.offsetTop > 0) {
                    pw.scrollTo(0, pw.visualViewport.pageTop || 0);
                }
            } catch (eVv) {}
        } else {
            try {
                pw.scrollTo(0, 0);
            } catch (e) {}
        }
    };

    pw.__sajuForceHomeViewport = function (token, lockMs) {
        if (typeof pw.__sajuCancelStepScroll === "function") {
            try { pw.__sajuCancelStepScroll(); } catch (e) {}
            pw.__sajuCancelStepScroll = null;
        }
        const doc = pw.document || document;
        const mobile = isMobileView(pw, doc);
        if (typeof pw.__sajuHideStreamlitPlatformChrome === "function") {
            pw.__sajuHideStreamlitPlatformChrome();
        }
        if (typeof pw.__sajuDetectMobilePlatform === "function") {
            pw.__sajuDetectMobilePlatform();
        }
        if (typeof pw.__sajuSyncStepToHtml === "function") {
            pw.__sajuSyncStepToHtml(1);
        }
        if (typeof pw.__sajuSnapHomeHeroToTop === "function") {
            pw.__sajuSnapHomeHeroToTop(true);
        } else if (typeof pw.__sajuPinHomeHeroTop === "function") {
            pw.__sajuPinHomeHeroTop(true);
        }
        if (typeof pw.__sajuScheduleHomeSolar24Fit === "function") {
            pw.__sajuScheduleHomeSolar24Fit();
        } else {
            pw.__sajuFitHomeSolar24Iframe();
        }
        if (!pw.__sajuUserIsScrolling) {
            if (typeof pw.__sajuScrollHomeTopOnce === "function") {
                pw.__sajuScrollHomeTopOnce();
            }
        }
    };

})();
"""

_ST_JS_CALL_MANAGER = """
(function () {
    const pw = (window.parent && window.parent !== window) ? window.parent : window;
    const doc = pw.document || document;
    const epoch = __NAV_EPOCH__;
    const lockMs = __LOCK_MS__;
    const phase = __SCROLL_PHASE__;

    if (typeof pw.__sajuForceStepScrollTop === "function") {
        pw.__sajuForceStepScrollTop(epoch, lockMs, phase);
    }
})()
"""

def inject_live_step_beacon() -> None:
    """현재 STEP·nav epoch — 페이지 맨 끝 비콘(중복 id 방지: class 사용)."""
    try:
        step = max(1, min(12, int(st.session_state.get("step", 1))))
    except Exception:
        step = 1
    try:
        epoch = int(st.session_state.get("saju_nav_epoch", 0))
    except Exception:
        epoch = 0
    st.markdown(
        f'<div class="saju-live-step-beacon" data-saju-step="{step}" '
        f'data-saju-nav-epoch="{epoch}" '
        'style="position:absolute;left:0;top:0;width:0;height:0;overflow:hidden;'
        'opacity:0;pointer-events:none;" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )


def _step_nav_scroll_lock_ms(*, step: int | None = None) -> int:
    """모바일 멈춤 방지 — 스크롤 잠금 없음(0). PC만 짧은 보조."""
    _ = step
    return 0


def inject_step_scroll_engine_every_run() -> None:
    """레거시 no-op — 스크롤은 ``inject_step_scroll_manager_once`` + finalize 1회만."""


def sync_step_nav_scroll_at_page_tail() -> None:
    """레거시 no-op — 중복 스크롤 주입 방지."""


def inject_step_scroll_manager_once() -> None:
    """parent 창 전역 스크롤 매니저 — JS 버전(_SCROLL_MGR_JS_VER)당 1회."""
    ver_key = f"_saju_scroll_mgr_js_{_SCROLL_MGR_JS_VER}"
    if st.session_state.get(ver_key):
        return
    for key in list(st.session_state.keys()):
        sk = str(key)
        if sk.startswith("_saju_scroll_mgr_js_") or sk.startswith("_saju_scroll_mgr_v"):
            st.session_state.pop(key, None)
    st.session_state[ver_key] = True
    # st.markdown("<script>") 은 Streamlit 이 script 를 제거하므로 components.html iframe 으로
    # parent 전역 매니저(__sajuFitHomeSolar24Iframe, __sajuLockHomeViewportTop 등)를 1회 설치한다.
    mgr_js = _SCROLL_MANAGER_JS.replace(
        "__SCROLL_MGR_JS_VER__", str(_SCROLL_MGR_JS_VER)
    )
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:0;overflow:hidden;'>"
        f"<script>{mgr_js}</script></body></html>"
    )
    with st.container(key=f"saju_scroll_mgr_v{_SCROLL_MGR_JS_VER}"):
        components.html(html, height=0, scrolling=False)


_CALENDAR_LOCALE_NUDGE_JS = r"""
(function () {
    const pw = window.parent || window;
    const run = function () {
        if (typeof pw.__sajuInstallCalendarLocaleV11 === "function") {
            try { pw.__sajuInstallCalendarLocaleV11(); } catch (e) {}
        }
        if (typeof pw.__sajuCalendarPatchNow === "function") {
            try { pw.__sajuCalendarPatchNow(); } catch (e) {}
        }
    };
    run();
    try { pw.requestAnimationFrame(run); } catch (e) {}
    [0, 8, 16, 32, 64, 120, 200, 320, 480, 720, 1000, 1500, 2200].forEach(function (ms) {
        pw.setTimeout(run, ms);
    });
})();
"""

_CALENDAR_LOCALE_INSTALL_JS = r"""
(function () {
    const pw = window.parent || window;
    const VERSION = 22;
    const BIRTH_TIME_LABELS = [
        "모름",
        "자(23:30~01:29)",
        "축(01:30~03:29)",
        "인(03:30~05:29)",
        "묘(05:30~07:29)",
        "진(07:30~09:29)",
        "사(09:30~11:29)",
        "오(11:30~13:29)",
        "미(13:30~15:29)",
        "신(15:30~17:29)",
        "유(17:30~19:29)",
        "술(19:30~21:29)",
        "해(21:30~23:29)",
    ];

    function installCore() {

    const LABELS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];
    const MONTH_EN = [
        "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december",
    ];
    const MONTH_SHORT = [
        "jan", "feb", "mar", "apr", "may", "jun",
        "jul", "aug", "sep", "oct", "nov", "dec",
    ];
    function getDocs() {
        const docs = [];
        const add = function (d) {
            if (!d || !d.body) return;
            if (docs.indexOf(d) >= 0) return;
            docs.push(d);
        };
        add(pw.document);
        try { add(window.document); } catch (e) {}
        try {
            if (window.parent && window.parent.document && window.parent.document !== pw.document) {
                add(window.parent.document);
            }
        } catch (e2) {}
        return docs;
    }

    const STYLE_ID = "saju-calendar-weekday-en-v11";
    const STYLE_CSS = `
[data-baseweb="popover"] [role="option"][data-saju-month-num],
[data-baseweb="select-dropdown"] [role="option"][data-saju-month-num],
[data-baseweb="option"][data-saju-month-num],
li[data-baseweb="option"][data-saju-month-num],
.st-key-step2_u_bdate_wrap [data-saju-month-num],
.st-key-step2_p_bdate_wrap [data-saju-month-num],
[data-baseweb="calendar"] [data-saju-month-num] {
  font-variant-numeric: tabular-nums !important;
  text-align: center !important;
  min-width: 2.4rem !important;
  letter-spacing: 0 !important;
  word-spacing: 0 !important;
  white-space: nowrap !important;
  font-size: 0 !important;
  line-height: 0 !important;
  color: transparent !important;
  position: relative !important;
}
html.saju-dark-tone [data-baseweb="popover"] [role="option"][data-saju-month-num],
html.saju-dark-tone [data-baseweb="select-dropdown"] [role="option"][data-saju-month-num],
html.saju-dark-tone [data-baseweb="calendar"] [data-saju-month-num] {
  color: #e2e8f0 !important;
}
[data-baseweb="popover"] [role="option"][data-saju-month-num]::before,
[data-baseweb="select-dropdown"] [role="option"][data-saju-month-num]::before,
[data-baseweb="option"][data-saju-month-num]::before,
li[data-baseweb="option"][data-saju-month-num]::before {
  content: none !important;
  display: none !important;
}
[data-baseweb="calendar"] [data-baseweb="calendar-header"] > div,
[data-baseweb="calendar"] [role="grid"] [role="row"]:first-child [role="columnheader"] {
  box-sizing: border-box !important;
  min-width: 2.1rem !important;
  overflow: hidden !important;
  text-align: center !important;
  letter-spacing: 0 !important;
  word-spacing: 0 !important;
  word-break: normal !important;
  white-space: nowrap !important;
  font-size: 0 !important;
  line-height: 0 !important;
  color: transparent !important;
  text-indent: -9999px !important;
}
[data-baseweb="calendar"] [data-baseweb="calendar-header"] > div::after,
[data-baseweb="calendar"] [role="grid"] [role="row"]:first-child [role="columnheader"]::after {
  display: block !important;
  font-size: 0.72rem !important;
  line-height: 1.25 !important;
  font-weight: 600 !important;
  color: #334155 !important;
  text-indent: 0 !important;
}
[data-baseweb="calendar"] [data-baseweb="calendar-header"] > div:nth-child(1)::after,
[data-baseweb="calendar"] [role="grid"] [role="row"]:first-child [role="columnheader"]:nth-child(1)::after { content: "Su" !important; }
[data-baseweb="calendar"] [data-baseweb="calendar-header"] > div:nth-child(2)::after,
[data-baseweb="calendar"] [role="grid"] [role="row"]:first-child [role="columnheader"]:nth-child(2)::after { content: "Mo" !important; }
[data-baseweb="calendar"] [data-baseweb="calendar-header"] > div:nth-child(3)::after,
[data-baseweb="calendar"] [role="grid"] [role="row"]:first-child [role="columnheader"]:nth-child(3)::after { content: "Tu" !important; }
[data-baseweb="calendar"] [data-baseweb="calendar-header"] > div:nth-child(4)::after,
[data-baseweb="calendar"] [role="grid"] [role="row"]:first-child [role="columnheader"]:nth-child(4)::after { content: "We" !important; }
[data-baseweb="calendar"] [data-baseweb="calendar-header"] > div:nth-child(5)::after,
[data-baseweb="calendar"] [role="grid"] [role="row"]:first-child [role="columnheader"]:nth-child(5)::after { content: "Th" !important; }
[data-baseweb="calendar"] [data-baseweb="calendar-header"] > div:nth-child(6)::after,
[data-baseweb="calendar"] [role="grid"] [role="row"]:first-child [role="columnheader"]:nth-child(6)::after { content: "Fr" !important; }
[data-baseweb="calendar"] [data-baseweb="calendar-header"] > div:nth-child(7)::after,
[data-baseweb="calendar"] [role="grid"] [role="row"]:first-child [role="columnheader"]:nth-child(7)::after { content: "Sa" !important; }
[data-baseweb="calendar"] [data-saju-weekday]::after { content: attr(data-saju-weekday) !important; }
[role="option"][data-saju-month-num],
[data-baseweb="option"][data-saju-month-num] {
  font-size: 0 !important;
  color: transparent !important;
  position: relative !important;
}
[role="option"][data-saju-month-num]::after,
[data-baseweb="option"][data-saju-month-num]::after {
  display: block !important;
  font-size: 0.88rem !important;
  color: #334155 !important;
  text-align: center !important;
}
[role="option"][data-saju-month-num="1"]::after { content: "1월" !important; }
[role="option"][data-saju-month-num="2"]::after { content: "2월" !important; }
[role="option"][data-saju-month-num="3"]::after { content: "3월" !important; }
[role="option"][data-saju-month-num="4"]::after { content: "4월" !important; }
[role="option"][data-saju-month-num="5"]::after { content: "5월" !important; }
[role="option"][data-saju-month-num="6"]::after { content: "6월" !important; }
[role="option"][data-saju-month-num="7"]::after { content: "7월" !important; }
[role="option"][data-saju-month-num="8"]::after { content: "8월" !important; }
[role="option"][data-saju-month-num="9"]::after { content: "9월" !important; }
[role="option"][data-saju-month-num="10"]::after { content: "10월" !important; }
[role="option"][data-saju-month-num="11"]::after { content: "11월" !important; }
[role="option"][data-saju-month-num="12"]::after { content: "12월" !important; }
`;

    function injectStyle() {
        getDocs().forEach(function (d) {
            ["saju-calendar-weekday-en-v3", "saju-calendar-weekday-en-v4", "saju-calendar-weekday-en-v5", "saju-calendar-weekday-en-v6", "saju-calendar-weekday-en-v7", "saju-calendar-weekday-en-v8", "saju-calendar-weekday-en-v9", "saju-calendar-weekday-en-v10"].forEach(function (id) {
                const old = d.getElementById(id);
                if (old) {
                    try { old.remove(); } catch (e) {}
                }
            });
            let node = d.getElementById(STYLE_ID);
            if (!node) {
                node = d.createElement("style");
                node.id = STYLE_ID;
                (d.head || d.documentElement).appendChild(node);
            }
            node.textContent = STYLE_CSS;
        });
    }

    function weekdayCells(cal) {
        const rows = cal.querySelectorAll('[role="grid"] [role="row"]');
        for (let r = 0; r < rows.length; r++) {
            const hdr = rows[r].querySelectorAll('[role="columnheader"]');
            if (hdr.length === 7) return Array.from(hdr);
        }
        const header = cal.querySelector('[data-baseweb="calendar-header"]');
        if (header) {
            const hdr2 = header.querySelectorAll('[role="columnheader"]');
            if (hdr2.length === 7) return Array.from(hdr2);
            const kids = Array.from(header.children).filter(function (el) {
                return el && el.nodeType === 1;
            });
            if (kids.length === 7) return kids;
        }
        return [];
    }

    function setPlainText(el, text) {
        if (!el) return;
        const owner = el.ownerDocument || pw.document;
        try {
            while (el.firstChild) el.removeChild(el.firstChild);
            el.appendChild(owner.createTextNode(String(text)));
        } catch (e) {
            try { el.textContent = String(text); } catch (e2) {}
        }
    }

    function paintWeekdayCell(el, label) {
        if (!el) return;
        el.setAttribute("data-saju-weekday", label);
        el.setAttribute("aria-label", label);
        try {
            setPlainText(el, "");
            el.style.setProperty("font-size", "0", "important");
            el.style.setProperty("line-height", "0", "important");
            el.style.setProperty("color", "transparent", "important");
            el.style.setProperty("text-indent", "-9999px", "important");
            el.style.setProperty("overflow", "hidden", "important");
            el.style.setProperty("text-align", "center", "important");
        } catch (e) {}
    }

    function walkAllRoots(fn) {
        getDocs().forEach(function (d) {
            const visit = function (root) {
                if (!root) return;
                fn(root);
                try {
                    root.querySelectorAll("*").forEach(function (el) {
                        if (el.shadowRoot) visit(el.shadowRoot);
                    });
                } catch (e) {}
            };
            if (d.body) visit(d.body);
            try {
                d.querySelectorAll("iframe").forEach(function (ifr) {
                    try {
                        if (ifr.contentDocument && ifr.contentDocument.body) {
                            visit(ifr.contentDocument.body);
                        }
                    } catch (e2) {}
                });
            } catch (e3) {}
        });
    }

    function forceOne(cal) {
        if (!cal) return;
        const cells = weekdayCells(cal);
        if (cells.length < 7) return;
        for (let i = 0; i < 7; i++) {
            paintWeekdayCell(cells[i], LABELS[i]);
        }
    }

    function forceCalendars() {
        walkAllRoots(function (root) {
            root.querySelectorAll('[data-baseweb="calendar"]').forEach(forceOne);
        });
    }

    function formatMonthKo(num) {
        return String(num) + "월";
    }

    function parseMonthNumber(text) {
        const raw = String(text || "").trim();
        const s = raw.replace(/\s+/g, "").toLowerCase();
        if (!s) return null;
        const dotNum = s.match(/^(\d{1,2})\.?$/);
        if (dotNum) {
            const n = parseInt(dotNum[1], 10);
            if (n >= 1 && n <= 12) return String(n);
        }
        const digit = s.match(/^(\d{1,2})월?\.?$/);
        if (digit) {
            const n = parseInt(digit[1], 10);
            if (n >= 1 && n <= 12) return String(n);
        }
        for (let i = 0; i < 12; i++) {
            if (s === MONTH_EN[i] || s.indexOf(MONTH_EN[i]) >= 0) return String(i + 1);
            if (s === MONTH_SHORT[i] || s.indexOf(MONTH_SHORT[i] + ".") === 0) {
                return String(i + 1);
            }
        }
        const ko = raw.match(/^(\d{1,2})\s*월$/);
        if (ko) {
            const n = parseInt(ko[1], 10);
            if (n >= 1 && n <= 12) return String(n);
        }
        return null;
    }

    const MONTH_OPTION_SEL =
        '[role="option"], [data-baseweb="option"], li[role="option"], li[data-baseweb="option"]';

    function paintMonthLabel(el, num) {
        if (!el || !num) return;
        const label = formatMonthKo(num);
        if (
            el.getAttribute("data-saju-month-num") === String(num) &&
            String(el.textContent || "").trim() === label
        ) {
            return;
        }
        el.setAttribute("data-saju-month-num", String(num));
        el.setAttribute("aria-label", label);
        try {
            setPlainText(el, label);
            el.style.setProperty("color", "#334155", "important");
            el.style.setProperty("font-size", "0.88rem", "important");
            el.style.setProperty("line-height", "1.35", "important");
            el.style.setProperty("visibility", "visible", "important");
            el.style.setProperty("opacity", "1", "important");
        } catch (e) {}
    }

    function isSajuBirthTimeOptionList(options) {
        if (!options || !options.length) return false;
        if (options[0] && shouldSkipMonthPatchRoot(options[0])) return true;
        if (options.length === 13) {
            const t0 = String(options[0].textContent || "").trim();
            if (t0 === "모름" || options[0].getAttribute("data-saju-birth-time") === "1") {
                return true;
            }
        }
        let hits = 0;
        for (let i = 0; i < options.length; i++) {
            const t = String(options[i].textContent || "").trim();
            if (!t) continue;
            if (t === "모름") {
                hits += 2;
                continue;
            }
            if (/^(자|축|인|묘|진|사|오|미|신|유|술|해)\(/.test(t)) hits++;
            if (/^\d{1,2}:\d{2}/.test(t)) hits++;
            if (/^\d{1,2}\.$/.test(t) && options.length === 13) return true;
        }
        return hits >= 2;
    }

    function step2HasCalendar() {
        return getDocs().some(function (d) {
            return !!d.querySelector('[data-baseweb="calendar"]');
        });
    }

    function isBdateTextInput(el) {
        if (!el || String(el.tagName || "").toUpperCase() !== "INPUT") return false;
        try {
            return !!el.closest(
                ".st-key-step2_u_bdate_wrap, .st-key-step2_p_bdate_wrap, " +
                    '[class*="step2_u_bdate_text"], [class*="step2_p_bdate_text"], ' +
                    '[class*="st-key-step2_u_bdate"], [class*="st-key-step2_p_bdate"]'
            );
        } catch (e) {
            return false;
        }
    }

    function bdateInputFocused() {
        if (pw.__sajuBdateFocusLock) return true;
        const ae = doc.activeElement;
        return isBdateTextInput(ae);
    }

    function safeToPatchMonths() {
        /* STEP2는 생년월일 직접입력·시간 select만 있음 — 월 패치가 시간 드롭다운을 망가뜨림 */
        if (onStep2BirthPage()) return false;
        return true;
    }

    function birthTimeSelectMenuOpen() {
        return getDocs().some(function (d) {
            if (d.querySelector(
                '.st-key-step2_u_time_wrap [data-baseweb="popover"], ' +
                    '.st-key-step2_p_time_wrap [data-baseweb="popover"], ' +
                    '.st-key-step2_u_time_wrap [data-baseweb="select-dropdown"], ' +
                    '.st-key-step2_p_time_wrap [data-baseweb="select-dropdown"]'
            )) {
                return true;
            }
            return !!d.querySelector(
                '.st-key-step2_u_time_wrap [data-baseweb="select"] [aria-expanded="true"], ' +
                    '.st-key-step2_p_time_wrap [data-baseweb="select"] [aria-expanded="true"]'
            );
        });
    }

    function markBirthTimeSelects() {
        getDocs().forEach(function (d) {
            d.querySelectorAll(
                ".st-key-step2_u_time_wrap [data-baseweb='select'], .st-key-step2_p_time_wrap [data-baseweb='select']"
            ).forEach(function (sel) {
                sel.setAttribute("data-saju-birth-time-select", "1");
            });
        });
    }

    function restoreBirthTimeSelectLabels() {
        /* 드롭다운 열림·터치 선택 중 DOM 변경 시 재선택 불가 → 닫힌 칩만 월 깨짐 복구 */
        if (birthTimeSelectMenuOpen()) return;
        getDocs().forEach(function (d) {
            d.querySelectorAll(
                ".st-key-step2_u_time_wrap, .st-key-step2_p_time_wrap"
            ).forEach(function (wrap) {
                wrap.querySelectorAll(
                    '[data-baseweb="select-value"], [class*="SelectValue"], [class*="select__single-value"]'
                ).forEach(function (node) {
                    const t = String(node.textContent || "").trim();
                    if (!/^\d{1,2}\s*월\.?$/.test(t)) return;
                    const sel = wrap.querySelector('[data-baseweb="select"]');
                    const cur = sel && sel.getAttribute("data-saju-last-label");
                    if (cur && BIRTH_TIME_LABELS.indexOf(cur) >= 0) {
                        try { setPlainText(node, cur); } catch (eFix) {}
                    }
                });
            });
        });
    }

    function shouldSkipMonthPatchRoot(node) {
        if (!node || !node.closest) return false;
        return !!node.closest(
            ".st-key-step2_u_time_wrap, .st-key-step2_p_time_wrap, " +
                "[data-saju-birth-time-select='1'], [data-saju-birth-time='1'], " +
                ".st-key-step2_self_row1_name_gender, .st-key-step2_opp_row1_name_gender, " +
                ".st-key-step2_self_row2_bdate_cal, .st-key-step2_opp_row2_bdate_cal"
        );
    }

    function looksLikeMonthDropdown(options) {
        if (!options || !options.length || options.length > 14) return false;
        if (isYearOptionList(options)) return false;
        if (isSajuBirthTimeOptionList(options)) return false;
        let monthish = 0;
        for (let i = 0; i < options.length; i++) {
            if (parseMonthNumber(options[i].textContent)) monthish++;
        }
        if (options.length >= 12 && options.length <= 14) {
            return monthish >= 8;
        }
        return monthish >= 1 && options.length >= 3;
    }

    function isYearOptionList(options) {
        if (!options || options.length < 4) return false;
        let yearLike = 0;
        const sample = Math.min(options.length, 10);
        for (let i = 0; i < sample; i++) {
            const t = String(options[i].textContent || "").trim();
            if (/^(19|20)\d{2}$/.test(t)) yearLike++;
        }
        return yearLike >= 3;
    }

    function isMonthOptionList(options) {
        return looksLikeMonthDropdown(options);
    }

    function patchMonthOptionList(options) {
        if (!options || !options.length) return;
        if (isYearOptionList(options)) return;
        if (isSajuBirthTimeOptionList(options)) return;
        if (options[0] && shouldSkipMonthPatchRoot(options[0])) return;
        if (options.length >= 12 && options.length <= 14) {
            if (!looksLikeMonthDropdown(options)) return;
            const start = options.length === 13 ? 1 : 0;
            for (let i = 0; i < 12; i++) {
                paintMonthLabel(options[start + i], String(i + 1));
            }
            return;
        }
        if (!looksLikeMonthDropdown(options)) return;
        options.forEach(function (el, idx) {
            let num = parseMonthNumber(el.textContent);
            if (!num && options.length === 12) num = String(idx + 1);
            if (!num && options.length === 13 && idx > 0) num = String(idx);
            if (!num && options.length === 13 && idx === 0) return;
            paintMonthLabel(el, num);
        });
    }

    function scanAllMonthOptions(d) {
        d.querySelectorAll(MONTH_OPTION_SEL).forEach(function (el) {
            if (el.closest('[role="grid"]')) return;
            if (el.closest(".st-key-step2_u_time_wrap, .st-key-step2_p_time_wrap")) return;
            if (shouldSkipMonthPatchRoot(el)) return;
            const listRoot = el.closest(
                '[role="listbox"], [data-baseweb="menu"], [data-baseweb="popover"], [data-baseweb="select-dropdown"]'
            );
            if (listRoot) {
                const siblings = listRoot.querySelectorAll(MONTH_OPTION_SEL);
                if (siblings.length && isSajuBirthTimeOptionList(siblings)) return;
            }
            const num = parseMonthNumber(el.textContent);
            if (num) paintMonthLabel(el, num);
        });
    }

    function forceMonthDropdownNumeric() {
        walkAllRoots(function (root) {
            const roots = new Set();
            root.querySelectorAll(
                '[data-baseweb="popover"], [data-baseweb="select-dropdown"], [role="presentation"], [role="listbox"], [data-baseweb="menu"], ul, ol'
            ).forEach(function (node) {
                roots.add(node);
            });
            if (root.getAttribute && (root.getAttribute("role") === "listbox" || root.tagName === "UL")) {
                roots.add(root);
            }
            roots.forEach(function (box) {
                if (shouldSkipMonthPatchRoot(box)) return;
                const opts = Array.from(box.querySelectorAll(MONTH_OPTION_SEL)).filter(function (el) {
                    return !el.closest('[role="grid"]');
                });
                if (!opts.length) return;
                if (isSajuBirthTimeOptionList(opts)) return;
                if (opts.length >= 12 && opts.length <= 14 && !isYearOptionList(opts)) {
                    if (looksLikeMonthDropdown(opts)) patchMonthOptionList(opts);
                } else if (looksLikeMonthDropdown(opts)) {
                    patchMonthOptionList(opts);
                }
            });
        });
        getDocs().forEach(scanAllMonthOptions);
    }

    function patchBdateMonthSelectDisplays() {
        getDocs().forEach(function (d) {
        d.querySelectorAll(
            ".st-key-step2_u_bdate_wrap [data-baseweb='select'], .st-key-step2_p_bdate_wrap [data-baseweb='select']"
        ).forEach(function (sel) {
            sel.querySelectorAll(
                '[data-baseweb="select-value"], [class*="SelectValue"], [class*="select__single-value"]'
            ).forEach(function (node) {
                const num = parseMonthNumber(node.textContent);
                if (num) paintMonthLabel(node, num);
            });
        });
        });
    }

    function collectMonthOptionGroups(root) {
        const groups = [];
        const seen = new Set();
        const addGroup = function (parent) {
            if (!parent || seen.has(parent)) return;
            const options = Array.from(
                parent.querySelectorAll(
                    '[role="option"], li[role="option"], li[data-baseweb="option"]'
                )
            ).filter(function (el) {
                return !el.closest('[role="grid"]');
            });
            if (!options.length) return;
            seen.add(parent);
            groups.push(options);
        };

        if (!root) return groups;
        if (root.querySelectorAll) {
            root.querySelectorAll('[role="listbox"], [data-baseweb="menu"], ul, ol').forEach(addGroup);
        }
        if (root.getAttribute && (root.getAttribute("role") === "listbox" || root.tagName === "UL")) {
            addGroup(root);
        }
        return groups;
    }

    function patchGlobalMonthOptions() {
        getDocs().forEach(function (d) {
        const parents = new Set();
        d.querySelectorAll(MONTH_OPTION_SEL).forEach(function (el) {
            if (el.closest('[role="grid"]')) return;
            const p = el.closest(
                '[role="listbox"], [data-baseweb="menu"], [data-baseweb="popover"], [data-baseweb="select-dropdown"], ul, ol'
            );
            if (p) parents.add(p);
        });
        parents.forEach(function (parent) {
            collectMonthOptionGroups(parent).forEach(patchMonthOptionList);
        });
        d.querySelectorAll('[data-baseweb="popover"], [data-baseweb="select-dropdown"]').forEach(
            function (pop) {
                collectMonthOptionGroups(pop).forEach(patchMonthOptionList);
            }
        );
        scanAllMonthOptions(d);
        });
    }

    function patchMonthSelectDisplays() {
        getDocs().forEach(function (d) {
        d.querySelectorAll('[data-baseweb="calendar"]').forEach(function (cal) {
            const selects = cal.querySelectorAll('[data-baseweb="select"]');
            if (!selects.length) return;
            const monthSel = selects[0];
            monthSel.querySelectorAll(
                '[data-baseweb="select-value"] *, [class*="SelectValue"]'
            ).forEach(function (node) {
                if (!node || node.childElementCount > 4) return;
                const num = parseMonthNumber(node.textContent);
                if (num) paintMonthLabel(node, num);
            });
        });
        });
    }

    function patchMonths() {
        markBirthTimeSelects();
        restoreBirthTimeSelectLabels();
        if (!safeToPatchMonths()) {
            return;
        }
        patchGlobalMonthOptions();
        forceMonthDropdownNumeric();
        patchMonthSelectDisplays();
        patchBdateMonthSelectDisplays();
    }

    function onStep2BirthPage() {
        return getDocs().some(function (d) {
            return !!d.querySelector(
                ".st-key-step2_u_bdate_wrap, .st-key-step2_p_bdate_wrap, .st-key-saju_router_step_mount_02"
            );
        });
    }

    function hasOpenMonthMenu() {
        return getDocs().some(function (d) {
            const nodes = d.querySelectorAll(
                '[data-baseweb="popover"] ' + MONTH_OPTION_SEL + ', [data-baseweb="select-dropdown"] ' + MONTH_OPTION_SEL
            );
            for (let i = 0; i < nodes.length; i++) {
                if (!shouldSkipMonthPatchRoot(nodes[i])) return true;
            }
            return false;
        });
    }

    function fixStep2FormRows() {
        const gap = pw.matchMedia("(min-width: 769px)").matches ? "12px" : "8px";
        const rowSel =
            '[class*="st-key-step2_self_row"], [class*="st-key-step2_opp_row"]';
        doc.querySelectorAll(rowSel).forEach(function (row) {
            const hb = row.querySelector('[data-testid="stHorizontalBlock"]');
            if (!hb) return;
            hb.style.display = "flex";
            hb.style.flexDirection = "row";
            hb.style.flexWrap = "nowrap";
            hb.style.width = "100%";
            hb.style.maxWidth = "100%";
            hb.style.gap = gap;
            hb.style.boxSizing = "border-box";
            Array.from(hb.children).forEach(function (ch) {
                ch.style.flex = "1 1 0";
                ch.style.minWidth = "0";
                ch.style.maxWidth = "50%";
                ch.style.width = "50%";
                ch.style.boxSizing = "border-box";
            });
        });
    }

    function patchAll() {
        injectStyle();
        markBirthTimeSelects();
        if (onStep2BirthPage() && !step2HasCalendar()) {
            fixStep2FormRows();
            return;
        }
        forceCalendars();
        if (safeToPatchMonths()) patchMonths();
        restoreBirthTimeSelectLabels();
        fixStep2FormRows();
    }

    pw.__sajuCalendarPatchNow = patchAll;
    pw.__sajuMarkBirthTimeSelects = markBirthTimeSelects;
    pw.__sajuRestoreBirthTimeSelectLabels = restoreBirthTimeSelectLabels;
    pw.__sajuBirthTimeSelectMenuOpen = birthTimeSelectMenuOpen;
    pw.__sajuCalendarLocaleVersion = VERSION;

    if (pw.__sajuCalendarMo) {
        try { pw.__sajuCalendarMo.disconnect(); } catch (e) {}
    }
    if (pw.__sajuCalendarTickTimer) {
        try { clearInterval(pw.__sajuCalendarTickTimer); } catch (e) {}
        pw.__sajuCalendarTickTimer = null;
    }

    let tickTimer = null;
    function startTick() {
        if (pw.__sajuCalendarTickTimer) return;
        pw.__sajuCalendarTickTimer = pw.setInterval(function () {
            if (!onStep2BirthPage()) return;
            const mobile = getDocs().some(function (d) {
                try {
                    const w = pw.innerWidth || d.documentElement.clientWidth || 0;
                    if (w > 0 && w <= 768) return true;
                } catch (e) {}
                return false;
            }) || (pw.matchMedia && pw.matchMedia("(max-width: 768px)").matches);
            const calOpen =
                hasOpenMonthMenu() ||
                getDocs().some(function (d) {
                    return !!d.querySelector('[data-baseweb="calendar"]');
                });
            if (!calOpen) return;
            if (!safeToPatchMonths()) return;
            patchMonths();
            if (calOpen) {
                forceCalendars();
            }
        }, (pw.matchMedia && pw.matchMedia("(max-width: 768px)").matches) ? 320 : 48);
        tickTimer = pw.__sajuCalendarTickTimer;
    }

    patchAll();
    startTick();
    let calMoTimer = null;
    function schedulePatch() {
        if (!onStep2BirthPage()) return;
        if (bdateInputFocused()) return;
        const mobile = pw.matchMedia && pw.matchMedia("(max-width: 768px)").matches;
        if (calMoTimer) clearTimeout(calMoTimer);
        calMoTimer = setTimeout(function () {
            calMoTimer = null;
            markBirthTimeSelects();
            if (onStep2BirthPage() && !step2HasCalendar()) {
                fixStep2FormRows();
                return;
            }
            if (safeToPatchMonths()) patchMonths();
            if (hasOpenMonthMenu() || getDocs().some(function (d) {
                return !!d.querySelector('[data-baseweb="popover"] [data-baseweb="calendar"], [data-baseweb="calendar"]');
            })) {
                patchAll();
            }
        }, mobile ? 280 : 24);
    }
    function bindPointerPatch() {
        const mobile = pw.matchMedia && pw.matchMedia("(max-width: 768px)").matches;
        const events = mobile
            ? ["click", "touchend", "pointerup", "focusin"]
            : ["click", "touchend", "pointerup", "focusin", "touchstart"];
        events.forEach(function (ev) {
            getDocs().forEach(function (d) {
            d.addEventListener(
                ev,
                function (e) {
                    if (isBdateTextInput(e && e.target)) return;
                    schedulePatch();
                    if (onStep2BirthPage() && !step2HasCalendar()) {
                        if (!bdateInputFocused()) fixStep2FormRows();
                        return;
                    }
                    if (!safeToPatchMonths()) return;
                    if (mobile) {
                        setTimeout(patchMonths, 0);
                        setTimeout(patchMonths, 160);
                        return;
                    }
                    pw.requestAnimationFrame(patchMonths);
                    setTimeout(patchMonths, 0);
                    setTimeout(patchMonths, 60);
                    setTimeout(patchMonths, 180);
                },
                true
            );
            });
        });
    }
    bindPointerPatch();
    getDocs().forEach(function (d) {
        if (!d.body) return;
        try {
            const obs = new MutationObserver(function () {
                schedulePatch();
            });
            const mobileMo = pw.matchMedia && pw.matchMedia("(max-width: 768px)").matches;
            obs.observe(d.body, {
                childList: true,
                subtree: true,
                characterData: !mobileMo,
                attributes: !mobileMo,
            });
            if (!pw.__sajuCalendarMoList) pw.__sajuCalendarMoList = [];
            pw.__sajuCalendarMoList.push(obs);
            pw.__sajuCalendarMo = obs;
        } catch (e) {}
    });
    }

    pw.__sajuInstallCalendarLocaleV11 = function () {
        const doc = pw.document;
        if (!doc || !doc.body) {
            pw.setTimeout(pw.__sajuInstallCalendarLocaleV11, 50);
            return;
        }
        if (pw.__sajuCalendarLocaleVersion >= VERSION && pw.__sajuCalendarPatchNow) {
            try { pw.__sajuCalendarPatchNow(); } catch (e) {}
            return;
        }
        if (pw.__sajuCalendarLocaleInstalling) return;
        pw.__sajuCalendarLocaleInstalling = true;
        try {
            installCore();
        } finally {
            pw.__sajuCalendarLocaleInstalling = false;
        }
    };

    pw.__sajuInstallCalendarLocaleV11();
})();
"""

_CALENDAR_WEEKDAY_EN_JS = _CALENDAR_LOCALE_INSTALL_JS


def inject_calendar_locale_installer_once() -> None:
    """parent 창에 달력 locale v21 설치(세션당 1회)."""
    if st.session_state.get("_saju_calendar_install_v22"):
        return
    st.session_state["_saju_calendar_install_v22"] = True
    st.session_state.pop("_saju_calendar_install_v21", None)
    st.session_state.pop("_saju_calendar_install_v20", None)
    st.session_state.pop("_saju_calendar_install_v19", None)
    st.session_state.pop("_saju_calendar_install_v17", None)
    st.session_state.pop("_saju_calendar_install_v15", None)
    st.session_state.pop("_saju_calendar_install_v14", None)
    st.session_state.pop("_saju_calendar_install_v13", None)
    st.session_state.pop("_saju_calendar_install_v12", None)
    st.session_state.pop("_saju_calendar_install_v11", None)
    for old in (
        "_saju_calendar_locale_v10",
        "_saju_calendar_locale_v9",
        "_saju_calendar_locale_v8",
        "_saju_calendar_locale_v7",
    ):
        st.session_state.pop(old, None)
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
        f"<script>{_CALENDAR_LOCALE_INSTALL_JS}</script></body></html>"
    )
    with st.container(key="saju_calendar_locale_install_v22"):
        components.html(html, height=1, scrolling=False)


def inject_calendar_weekday_en_once() -> None:
    """date_input 달력: 요일 Su~Sa, 월 1월~12월 — 앱 기동·STEP2 공용."""
    inject_calendar_locale_installer_once()
    nudge_calendar_locale_patch(slot="global_install")


def ensure_calendar_locale_on_step2() -> None:
    """STEP2 화면 진입 시 달력 locale 매니저 설치 + 즉시 패치."""
    inject_calendar_locale_installer_once()
    nudge_calendar_locale_patch(slot="step2_boot")


def inject_step2_bdate_input_focus_guard_once() -> None:
    """STEP2 생년월일 text_input — 첫 포커스 시 DOM 패치·tabIndex 재배치로 커서가 튕기는 현상 방지."""
    if st.session_state.get("_saju_step2_bdate_focus_guard_v2"):
        return
    st.session_state["_saju_step2_bdate_focus_guard_v2"] = True
    trigger_js = r"""
(function () {
  const pw = window.parent !== window ? window.parent : window;
  const doc = pw.document;
  if (!doc) return;

  function isBdateInput(el) {
    if (!el || String(el.tagName || "").toUpperCase() !== "INPUT") return false;
    try {
      return !!el.closest(
        ".st-key-step2_u_bdate_wrap, .st-key-step2_p_bdate_wrap, " +
          '[class*="step2_u_bdate_text"], [class*="step2_p_bdate_text"], ' +
          '[class*="st-key-step2_u_bdate"], [class*="st-key-step2_p_bdate"]'
      );
    } catch (e) {
      return false;
    }
  }

  function lock(on) {
    pw.__sajuBdateFocusLock = !!on;
  }

  function bindOne(input) {
    if (!input || input.dataset.sajuBdateFocusGuard === "1") return;
    input.dataset.sajuBdateFocusGuard = "1";
    input.setAttribute("data-saju-bdate-field", "1");
    input.addEventListener(
      "focus",
      function () {
        lock(true);
        try {
          input.removeAttribute("readonly");
        } catch (e) {}
      },
      true
    );
    input.addEventListener(
      "blur",
      function () {
        pw.setTimeout(function () {
          if (!isBdateInput(doc.activeElement)) lock(false);
        }, 160);
      },
      true
    );
  }

  function scan() {
    doc.querySelectorAll("input").forEach(function (el) {
      if (isBdateInput(el)) bindOne(el);
    });
  }

  scan();
  try {
    pw.requestAnimationFrame(scan);
  } catch (e) {}
  [80, 240, 520].forEach(function (ms) {
    pw.setTimeout(scan, ms);
  });
  try {
    const root = doc.body || doc.documentElement;
    if (root && pw.MutationObserver) {
      new pw.MutationObserver(function () {
        scan();
      }).observe(root, { childList: true, subtree: true });
    }
  } catch (e) {}
})();
"""
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
        f"<script>{trigger_js}</script></body></html>"
    )
    with st.container(key="saju_step2_bdate_focus_guard"):
        components.html(html, height=1, scrolling=False)


def protect_step2_birth_time_selects() -> None:
    """STEP2 태어난 시간 selectbox — 달력 월 패치가 건드리지 않도록 보호."""
    inject_calendar_locale_installer_once()
    if st.session_state.get("_saju_step2_time_protect_done_v1"):
        return
    st.session_state["_saju_step2_time_protect_done_v1"] = True
    trigger_js = (
        "(function(){"
        "const pw=window.parent||window;"
        "if(typeof pw.__sajuMarkBirthTimeSelects==='function'){pw.__sajuMarkBirthTimeSelects();}"
        "})();"
    )
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
        f"<script>{trigger_js}</script></body></html>"
    )
    with st.container(key="saju_step2_time_protect_v1"):
        components.html(html, height=1, scrolling=False)


def nudge_calendar_locale_patch(*, slot: str = "page") -> None:
    """STEP2·date_input 직후 — PC 영문 월·깨진 요일을 1월·Su~Sa 로 고정."""
    inject_calendar_locale_installer_once()
    nonce = int(st.session_state.get("_saju_calendar_locale_nonce", 0)) + 1
    st.session_state["_saju_calendar_locale_nonce"] = nonce
    safe_slot = re.sub(r"[^a-zA-Z0-9_]", "_", str(slot or "page"))[:48]
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
        f"<script>{_CALENDAR_LOCALE_NUDGE_JS}</script></body></html>"
    )
    with st.container(key=f"saju_cal_loc_{safe_slot}_{nonce % 100000}"):
        components.html(html, height=1, scrolling=False)


def render_step_top_anchor() -> None:
    """페이지 최상단 앵커 — ``st.container`` + ``st.empty`` 로 스크롤 기준점을 고정합니다.

    STEP 전환 후 스크롤은 ``finalize_scroll_to_top_if_needed`` 에서
    ``force_scroll_to_top()`` 로 실행합니다 (rerun 직후 1회).

    STEP1(홈)에서는 앵커 컨테이너가 모바일에서 상단 빈 여백을 만들 수 있어 생략합니다.

    수동 패턴::

        render_step_top_anchor()
        schedule_force_scroll_after_nav(delay_ms=150, strength="strong")
        rerun_full_app()
    """
    if int(st.session_state.get("step", 1)) == 1:
        return
    top_anchor = st.container(key="saju_step_top_anchor")
    with top_anchor:
        st.markdown(
            (
                '<div id="saju-step-top-anchor" tabindex="-1" '
                'style="position:relative;width:1px;height:1px;margin:0;padding:0;'
                'overflow:hidden;scroll-margin-top:0;outline:none;" '
                'aria-hidden="true"></div>'
            ),
            unsafe_allow_html=True,
        )
        st.empty()


def render_step_top_anchor_and_force_scroll(
    *,
    delay_ms: int = 150,
    strength: str = "strong",
) -> None:
    """최상단 앵커 + 즉시 ``force_scroll_to_top`` (페이지 tail·finalize 용)."""
    render_step_top_anchor()
    force_scroll_to_top(delay_ms=delay_ms, strength=strength)


def inject_nav_scroll_tail_once(
    *, nav_epoch: int | None = None, from_step: int | None = None
) -> None:
    """페이지 tail 1회 — STEP 이동 후 화면 최상단(scrollTop=0)으로 고정.

    🔒 잠금(회귀 금지) — 이 동작은 검증 완료됐다. 아래 계약을 깨지 말 것:
      1. 반드시 ``components.html``(iframe)로 주입한다.
         ``st.markdown("<script>...")`` 는 브라우저가 실행하지 않으므로(innerHTML
         script 미실행) 절대 그 방식으로 되돌리지 말 것.
      2. iframe 스크립트는 ``window.parent``(메인 문서)의 스크롤러를 0 으로 만든다.
         매니저 함수(``pw.__saju*``)에 의존하지 않는 자립형으로 유지한다.
      3. 배너가 페이지 최상단에 있으므로 STEP 앵커로 ``scrollIntoView`` 하지 말 것
         (배너가 가려진다). scrollTop=0(맨 위)만 사용한다.
      4. 단계 A(강제)에서는 사용자 개입을 무시, 단계 B에서는 사용자 클릭/휠/터치/키
         감지 시 즉시 중단(사용자 방해 금지).
    """
    epoch = int(
        nav_epoch
        if nav_epoch is not None
        else st.session_state.get("saju_nav_epoch", 0)
    )
    if st.session_state.get("_saju_nav_scroll_tail_epoch") == epoch:
        return
    st.session_state["_saju_nav_scroll_tail_epoch"] = epoch
    try:
        step = max(1, min(12, int(st.session_state.get("step", 1))))
    except Exception:
        step = 1
    try:
        nav_from = (
            max(1, min(12, int(from_step)))
            if from_step is not None
            else 0
        )
    except Exception:
        nav_from = 0
    if nav_from == step:
        nav_from = 0
    # 중요: st.markdown("<script>") 은 브라우저가 실행하지 않는다(innerHTML script).
    # 실제 실행을 위해 components.html(iframe) 로 주입하고, iframe 안 스크립트가
    # window.parent(메인 문서)를 스크롤한다. 매니저(pw.__saju*)에 의존하지 않는 자립형.
    trigger_js = (
        "(function(){"
        "var pw=(window.parent&&window.parent!==window)?window.parent:window;"
        f"var epoch={epoch};var step={step};var navFrom={nav_from};var isHome=step===1;"
        "var doc=pw.document||document;"
        "pw.__sajuNavLatestEpoch=epoch;"
        # 중요: <html data-saju-step>/클래스는 그동안 st.markdown('<script>')(Streamlit 이
        # script 를 제거 → 실행 안 됨)로만 설정돼, 홈에서 '1' 로 박힌 뒤 비홈 스텝에서도
        # '1' 로 고정됐다. 그 결과 html[data-saju-step='1'] 홈 전용 규칙이 모든 스텝에 적용되고
        # 빈 홈 마운트가 강제 노출돼 상단 공백을 만들었다. 여기(실행되는 iframe)에서 매 네비마다
        # 실제 step 으로 세팅한다. <html> 속성은 rerun 에도 유지되므로 위젯 클릭에도 안정적.
        # STEP 이동 직후에는 새 마운트가 DOM 에 붙기 전 data-saju-step 만 바꾸면
        # bootstrap CSS 가 이전 마운트를 숨겨 본문이 비고 하단 네비만 남는다(빈 화면 버그).
        "var applyHtmlStep=function(n){"
        "var sn=Math.max(1,Math.min(12,parseInt(String(n),10)||1));"
        "var home=sn===1;"
        "try{var de=doc.documentElement;if(de){"
        "de.setAttribute('data-saju-step',String(sn));"
        "de.classList.remove('saju-home-step1','saju-not-step1');"
        "de.classList.add(home?'saju-home-step1':'saju-not-step1');"
        "if(typeof pw.__sajuHideStaleStepMounts==='function'){pw.__sajuHideStaleStepMounts(sn);}"
        "}}catch(e){}"
        "return sn;};"
        "var setNavPending=function(on){"
        "try{var de=doc.documentElement;if(!de)return;"
        "if(on){de.setAttribute('data-saju-nav-pending','1');}"
        "else{de.removeAttribute('data-saju-nav-pending');}}catch(e){}};"
        "var mountReady=function(n){"
        "var sn=Math.max(1,Math.min(12,parseInt(String(n),10)||1));"
        "var pad=sn<10?('0'+sn):String(sn);"
        "var el=doc.querySelector('.st-key-saju_router_step_mount_'+pad);"
        "if(!el)return false;"
        "var vb=el.querySelector('[data-testid=\"stVerticalBlock\"]');"
        "if(!vb)return false;"
        "var kids=vb.querySelectorAll('[data-testid=\"stElementContainer\"]');"
        "if(!kids||kids.length<1)return false;"
        "var h=el.offsetHeight||0;"
        "var txt=(el.innerText||'').replace(/\\s+/g,'');"
        "if(h<120&&txt.length<16)return false;"
        "if(txt.length<6&&h<220)return false;"
        "return true;};"
        "var scrollers=function(){return ["
        "doc.querySelector('[data-testid=\"stMain\"]'),"
        "doc.querySelector('section.main'),"
        "doc.querySelector('[data-testid=\"stMainBlockContainer\"]'),"
        "doc.querySelector('[data-testid=\"stAppViewContainer\"]'),"
        "doc.scrollingElement,doc.documentElement,doc.body];};"
        "var offTop=function(){var off=false;scrollers().forEach(function(el){"
        "if(el&&(el.scrollTop||0)>2)off=true;});"
        "if((pw.scrollY||0)>2)off=true;return off;};"
        # snap: 포커스된 버튼/라디오 등은 blur(포커스-스크롤로 중간 멈춤 방지),
        # 입력 중인 input/textarea/select 는 건드리지 않음. 모든 스크롤러를 0(맨 위)으로.
        "var snap=function(){"
        "try{var ae=doc.activeElement;var tg=ae&&ae.tagName?String(ae.tagName).toLowerCase():'';"
        "if(ae&&ae!==doc.body&&tg!=='input'&&tg!=='textarea'&&tg!=='select'&&typeof ae.blur==='function'){ae.blur();}}catch(e){}"
        "scrollers().forEach(function(el){if(!el)return;try{if((el.scrollTop||0)>0)el.scrollTop=0;}catch(e){}});"
        "try{pw.scrollTo(0,0);}catch(e){}"
        "};"
        # 자체 사용자 상호작용 감지(매니저 가드에 의존하지 않음).
        # scroll·휠·터치·클릭·키 — 사용자 스크롤 시작 시 즉시 스냅 중단.
        "var userActed=false;"
        "var onUser=function(){userActed=true;};"
        "var evs=['wheel','touchmove','touchstart','keydown','pointerdown','scroll'];"
        "try{evs.forEach(function(ev){doc.addEventListener(ev,onUser,{passive:true,capture:true});});}catch(e){}"
        "var cleanup=function(){try{evs.forEach(function(ev){doc.removeEventListener(ev,onUser,{capture:true});});}catch(e){}};"
        "var runNavTail=function(){"
        # 홈: 배너가 곧 최상단이므로 동일하게 맨 위로 몇 번 맞춘다.
        "if(isHome){snap();try{pw.requestAnimationFrame(snap);}catch(e){}[60,200,420].forEach(function(ms){pw.setTimeout(snap,ms);});cleanup();return;}"
        # STEP 전환 직후만 짧게 보정 — 사용자 스크롤 감지 시 즉시 중단.
        "var t0=Date.now();var settleEnd=180;var hardEnd=900;"
        "var tick=function(){"
        "if(pw.__sajuNavLatestEpoch!==epoch){cleanup();return;}"
        "if(userActed){cleanup();return;}"
        "var dt=Date.now()-t0;"
        "if(dt<settleEnd){snap();}"
        "else{if(offTop())snap();}"
        "if(dt<hardEnd){pw.setTimeout(tick,dt<settleEnd?60:220);}else{cleanup();}"
        "};"
        "snap();try{pw.requestAnimationFrame(snap);}catch(e){}pw.setTimeout(tick,60);"
        "};"
        "var commitTargetStep=function(){setNavPending(false);if(typeof pw.__sajuClearStepNavPending==='function'){pw.__sajuClearStepNavPending();}applyHtmlStep(step);if(navFrom>0&&navFrom!==step){runNavTail();}};"
        "if(navFrom>0&&navFrom!==step){"
        "setNavPending(true);"
        "if(typeof pw.__sajuArmStepNavPending==='function'){pw.__sajuArmStepNavPending(navFrom);}else{applyHtmlStep(navFrom);}"
        "var tries=0;var waitMax=160;var minWait=3;"
        "var wait=function(){"
        "if(pw.__sajuNavLatestEpoch!==epoch){setNavPending(false);return;}"
        "tries+=1;"
        "if(mountReady(step)&&tries>=minWait){commitTargetStep();return;}"
        "if(tries>=waitMax){commitTargetStep();return;}"
        "if(typeof pw.__sajuArmStepNavPending==='function'){pw.__sajuArmStepNavPending(navFrom);}else{applyHtmlStep(navFrom);}"
        "try{pw.setTimeout(wait,36);}catch(e){commitTargetStep();}"
        "};"
        "try{pw.requestAnimationFrame(function(){wait();});}catch(e){wait();}"
        "}else{commitTargetStep();}"
        "})();"
    )
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:0;overflow:hidden;'>"
        f"<script>{trigger_js}</script></body></html>"
    )
    with st.container(key=f"saju_nav_scroll_tail_{epoch}"):
        components.html(html, height=0, scrolling=False)


def scroll_step_top_now(
    *, nav_epoch: int | None = None, slot: str = "main", force: bool = False
) -> None:
    """레거시 래퍼 — ``inject_nav_scroll_tail_once`` 로 위임."""
    _ = slot
    if not force and not step_scroll_is_pending():
        return
    inject_nav_scroll_tail_once(nav_epoch=nav_epoch)


def _fire_step_scroll_to_top(nav_epoch: int, *, phase: str = "late") -> None:
    """STEP 전환 후 최상단 스크롤(1회)."""
    scroll_step_top_now(nav_epoch=nav_epoch)


_SCROLL_PENDING_KEY = "_saju_pending_scroll_top"


def _clear_step_scroll_pending() -> None:
    st.session_state.pop(_SCROLL_PENDING_KEY, None)
    st.session_state.pop("_force_scroll_to_top_after_rerun", None)
    st.session_state.pop("_saju_must_scroll_top", None)


def step_scroll_is_pending() -> bool:
    """STEP 전환 직후 1회 스크롤만 — epoch 불일치로 매 rerun 스크롤하지 않음."""
    if st.session_state.get(_SCROLL_PENDING_KEY):
        return True
    if st.session_state.get("_force_scroll_to_top_after_rerun"):
        return True
    if st.session_state.get("_saju_must_scroll_top"):
        return True
    return False


def arm_step_navigation_scroll(*, step: int | None = None) -> None:
    """이전/다음·메뉴 STEP 이동 직후 — 다음 rerun 에서 최상단 스크롤 예약."""
    st.session_state["_saju_pending_scroll_top"] = True
    st.session_state["_force_scroll_to_top_after_rerun"] = True
    st.session_state["_saju_must_scroll_top"] = True
    st.session_state["_saju_nav_from_prepare"] = True
    st.session_state.pop("_saju_scrolled_nav_epoch", None)
    st.session_state["_saju_scroll_fired_slots"] = []
    st.session_state.pop("_saju_scroll_top_tag", None)
    if step is not None:
        st.session_state["_saju_scroll_target_step"] = int(step)


def prime_step_nav_scroll_before_render() -> None:
    """라우터 본문 렌더 전 — 스크롤 매니저·STEP 속성·1차 스냅."""
    if int(st.session_state.get("step", 1)) == 1:
        return
    inject_step_scroll_manager_once()
    if not step_scroll_is_pending():
        return
    try:
        step = int(
            st.session_state.get(
                "_saju_scroll_target_step", st.session_state.get("step", 1)
            )
        )
    except Exception:
        step = 1
    step = max(1, min(12, step))
    inject_step_html_attrs_immediate(step, scroll_top=False)


def mark_scroll_completed_for_current_nav() -> None:
    try:
        st.session_state["_saju_scrolled_nav_epoch"] = int(
            st.session_state.get("saju_nav_epoch", 0)
        )
    except Exception:
        st.session_state["_saju_scrolled_nav_epoch"] = 0
    _clear_step_scroll_pending()
    st.session_state.pop("_saju_scroll_armed_epoch", None)


def should_scroll_to_top_after_step_change(
    *,
    step: int,
    last_step: int | None,
    navigated: bool,
) -> bool:
    if st.session_state.pop("_saju_nav_preserve_scroll", False):
        return False
    if st.session_state.pop("_saju_nav_from_prepare", False):
        return True
    if step_scroll_is_pending():
        return True
    if navigated:
        return True
    if last_step is None and int(step) > 1:
        return True
    return False


def queue_expander_collapse(exp_key: str) -> None:
    """STEP2 접이식 — 선택 후 펼침 상태가 남지 않도록 접기(모바일 포함)."""
    wk = str(exp_key or "").strip()
    if not wk:
        return
    pending = list(st.session_state.get("_saju_expander_collapse_pending") or [])
    if wk not in pending:
        pending.append(wk)
    st.session_state["_saju_expander_collapse_pending"] = pending
    try:
        st.session_state[wk] = False
    except Exception:
        pass


def inject_expander_collapse_once() -> None:
    """``queue_expander_collapse`` 예약분 — details 요소를 강제로 접습니다."""
    pending = st.session_state.pop("_saju_expander_collapse_pending", None)
    if not pending:
        return
    import json

    keys_js = json.dumps([str(k) for k in pending if k], ensure_ascii=False)
    collapse_js = f"""
(function() {{
  const keys = {keys_js};
  const doc = (window.parent || window).document;
  if (!doc || !keys || !keys.length) return;

  function collapseOne(widgetKey) {{
    const exact = "st-key-" + widgetKey;
    const roots = doc.querySelectorAll('[class*="st-key-"]');
    for (let i = 0; i < roots.length; i++) {{
      const root = roots[i];
      if (!root || !root.classList || !root.classList.contains(exact)) continue;
      root.querySelectorAll("details").forEach((d) => {{
        d.open = false;
        d.removeAttribute("open");
      }});
      const summary = root.querySelector('[data-testid="stExpander"] summary, summary');
      if (summary) summary.setAttribute("aria-expanded", "false");
    }}
  }}

  function run() {{
    keys.forEach(collapseOne);
  }}

  run();
  requestAnimationFrame(run);
  setTimeout(run, 0);
  setTimeout(run, 80);
  setTimeout(run, 200);
}})();
"""
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
        f"<script>{collapse_js}</script></body></html>"
    )
    token = int(st.session_state.get("_saju_expander_collapse_token", 0)) + 1
    st.session_state["_saju_expander_collapse_token"] = token
    with st.container(key=f"saju_expander_collapse_{token}"):
        components.html(html, height=1, scrolling=False)


_STEP2_TAB_ORDER_SELF = (
    "step2_self_name_input",
    "u_gender",
    "step2_u_bdate_text",
    "u_lunar",
    "u_time_select_idx",
    "u_contact",
)
_STEP2_TAB_ORDER_OPP = (
    "step2_opp_name_input",
    "p_gender",
    "step2_p_bdate_text",
    "p_lunar",
    "p_time_select_idx",
)
_STEP2_TAB_ORDER_SAVE = (
    "agree",
    "step2_revisit_pin",
    "step2_revisit_pin_confirm",
    "step2_inline_prev_btn",
    "step2_save_and_analyze_btn",
)


def _step2_tab_order_json() -> str:
    import json

    return json.dumps(
        {
            "self": list(_STEP2_TAB_ORDER_SELF),
            "opp": list(_STEP2_TAB_ORDER_OPP),
            "save": list(_STEP2_TAB_ORDER_SAVE),
        },
        ensure_ascii=False,
    )


def inject_step2_tab_manager_global_once() -> None:
    """STEP2 Tab 순서 — parent 문서에 1회 설치 (components.html iframe)."""
    if st.session_state.get("_saju_step2_tab_mgr_v13"):
        return
    st.session_state["_saju_step2_tab_mgr_v13"] = True
    st.session_state.pop("_saju_step2_tab_mgr_v12", None)
    order_js = _step2_tab_order_json()
    mgr_js = _STEP2_TAB_MANAGER_JS.replace("__ORDER_JSON__", order_js)
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
        f"<script>{mgr_js}</script></body></html>"
    )
    with st.container(key="saju_step2_tab_mgr_v13"):
        components.html(html, height=1, scrolling=False)


_STEP2_TAB_MANAGER_JS = r"""
(function () {
  const pw = window.parent !== window ? window.parent : window;
  const ORDER = __ORDER_JSON__;
  const SCOPE_SEL =
    ".st-key-step2_navertone_self, .st-key-step2_navertone_opp, .st-key-step2_save_actions, .st-key-step2_fixed_next_bar, .st-key-step2_action_block";

  pw.__sajuStep2TabOrder = ORDER;

  if (pw.__sajuStep2TabMgrV12) {
    if (typeof pw.__sajuStep2TabRefresh === "function") pw.__sajuStep2TabRefresh();
    return;
  }
  pw.__sajuStep2TabMgrV12 = true;
  pw.__sajuStep2TabMgrV11 = true;

  let chainCache = [];
  let keyToIdxCache = {};
  let refreshQueued = false;

  function forEachDoc(fn) {
    const seen = new Set();
    function walk(doc) {
      if (!doc || seen.has(doc)) return;
      seen.add(doc);
      fn(doc);
      doc.querySelectorAll("iframe").forEach((fr) => {
        try {
          walk(fr.contentDocument);
        } catch (e) {}
      });
    }
    walk(pw.document);
    if (window.document && window.document !== pw.document) walk(window.document);
  }

  function step2Active() {
    return !!findRootAny("step2_navertone_self") || !!findRootAny("step2_navertone_opp");
  }

  function findRoot(doc, widgetKey) {
    const exact = "st-key-" + widgetKey;
    const nodes = doc.querySelectorAll('[class*="st-key-"]');
    for (let i = 0; i < nodes.length; i++) {
      const el = nodes[i];
      if (el && el.classList && el.classList.contains(exact)) return el;
    }
    return null;
  }

  function findRootAny(widgetKey) {
    let found = null;
    forEachDoc((doc) => {
      if (found) return;
      const r = findRoot(doc, widgetKey);
      if (r) found = r;
    });
    return found;
  }

  function isVisible(el, win) {
    if (!el) return false;
    let node = el;
    const view = win || pw;
    while (node) {
      const st = view.getComputedStyle(node);
      if (st.display === "none" || st.visibility === "hidden") return false;
      if (node.getAttribute && node.getAttribute("aria-hidden") === "true") return false;
      node = node.parentElement;
    }
    return true;
  }

  function pickPrimary(root, win) {
    if (!root || !isVisible(root, win)) return null;
    const expander = root.querySelector('[data-testid="stExpander"]');
    if (expander) {
      const summary =
        expander.querySelector("summary") ||
        root.querySelector("details > summary");
      if (summary && isVisible(summary, win)) {
        summary.setAttribute("tabindex", "0");
        expander.querySelectorAll("button").forEach((b) => {
          b.tabIndex = -1;
        });
        return summary;
      }
    }
    const combo = root.querySelector(
      '[data-baseweb="select"] [role="combobox"], [data-baseweb="select"] [aria-haspopup="listbox"]'
    );
    if (combo && isVisible(combo, win)) return combo;
    const numIn = root.querySelector(
      '[data-testid="stNumberInput"] input:not([type="hidden"]):not([disabled])'
    );
    if (numIn && isVisible(numIn, win)) return numIn;
    const inputs = root.querySelectorAll(
      'input:not([type="hidden"]):not([disabled])'
    );
    for (let i = 0; i < inputs.length; i++) {
      if (inputs[i].type === "checkbox") return inputs[i];
    }
    for (let i = 0; i < inputs.length; i++) {
      const t = (inputs[i].type || "text").toLowerCase();
      if (t === "checkbox") continue;
      return inputs[i];
    }
    const summary = root.querySelector(
      '[data-testid="stExpander"] summary, details > summary'
    );
    if (summary && isVisible(summary, win)) {
      summary.setAttribute("tabindex", "0");
      return summary;
    }
    const btn = root.querySelector(
      '[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primary"], button:not([disabled])'
    );
    if (btn && isVisible(btn, win)) return btn;
    return null;
  }

  function mergedKeys() {
    const keys = [];
    const O = pw.__sajuStep2TabOrder || ORDER;
    const selfRoot = findRootAny("step2_navertone_self");
    const oppRoot = findRootAny("step2_navertone_opp");
    if (selfRoot && isVisible(selfRoot, pw)) keys.push.apply(keys, O.self || []);
    if (oppRoot && isVisible(oppRoot, pw)) keys.push.apply(keys, O.opp || []);
    keys.push.apply(keys, O.save || []);
    return keys;
  }

  function buildChain() {
    const keys = mergedKeys();
    const chain = [];
    const keyToIdx = {};
    let idx = 1;
    keys.forEach((widgetKey) => {
      const root = findRootAny(widgetKey);
      const win = root ? root.ownerDocument.defaultView || pw : pw;
      const el = pickPrimary(root, win);
      if (!el) return;
      el.tabIndex = idx;
      idx += 1;
      keyToIdx[widgetKey] = chain.length;
      chain.push(el);
      root.querySelectorAll("button").forEach((b) => {
        if (b !== el) b.tabIndex = -1;
      });
    });
    chainCache = chain;
    keyToIdxCache = keyToIdx;
    return { chain, keyToIdx };
  }

  function widgetKeyFrom(el) {
    let node = el;
    while (node) {
      if (node.classList) {
        for (let i = 0; i < node.classList.length; i++) {
          const c = node.classList[i];
          if (c.indexOf("st-key-") === 0) return c.slice(7);
        }
      }
      node = node.parentElement;
    }
    return null;
  }

  function indexInChain(chain, anchor, keyToIdx) {
    if (!anchor) return -1;
    let pos = chain.indexOf(anchor);
    if (pos >= 0) return pos;
    for (let i = 0; i < chain.length; i++) {
      if (chain[i] && chain[i].contains && chain[i].contains(anchor)) return i;
    }
    const wk = widgetKeyFrom(anchor);
    if (wk && keyToIdx[wk] !== undefined) return keyToIdx[wk];
    return -1;
  }

  function hardFocus(el) {
    if (!el) return;
    const win = el.ownerDocument.defaultView || pw;
    if (!isVisible(el, win)) return;
    const onStep2 =
      pw.document &&
      pw.document.documentElement &&
      pw.document.documentElement.getAttribute("data-saju-step") === "2";
    try {
      if (typeof pw.__sajuStep2SaveScroll === "function") pw.__sajuStep2SaveScroll();
    } catch (e0) {}
    if (!onStep2) {
      try {
        el.scrollIntoView({ block: "nearest", inline: "nearest", behavior: "auto" });
      } catch (e) {}
    }
    try {
      if (typeof pw.__sajuStep2RestoreScroll === "function") pw.__sajuStep2RestoreScroll();
    } catch (e1) {}
    const snap = function () {
      try {
        el.focus({ preventScroll: true });
      } catch (e) {
        try {
          el.focus();
        } catch (e2) {}
      }
    };
    snap();
    try {
      requestAnimationFrame(snap);
    } catch (e) {
      setTimeout(snap, 0);
    }
    setTimeout(snap, 16);
    setTimeout(snap, 48);
  }

  function moveFrom(anchor, backward, isEnter) {
    if (!step2Active()) return false;
    const built = buildChain();
    const chain = built.chain.filter(
      (el) => el && isVisible(el, el.ownerDocument.defaultView || pw)
    );
    if (!chain.length) return false;

    let pos = indexInChain(chain, anchor, built.keyToIdx);
    if (pos < 0) {
      hardFocus(backward ? chain[chain.length - 1] : chain[0]);
      return true;
    }
    let next = backward ? pos - 1 : pos + 1;
    if (next < 0) next = chain.length - 1;
    if (next >= chain.length) next = 0;
    if (next === pos && chain.length > 1) {
      next = backward ? pos - 1 : pos + 1;
      if (next < 0) next = chain.length - 1;
      if (next >= chain.length) next = 0;
    }
    hardFocus(chain[next]);
    return true;
  }

  function isStep2FieldTarget(t) {
    if (!t) return false;
    try {
      if (t.closest && t.closest(SCOPE_SEL)) return true;
    } catch (e) {}
    const wk = widgetKeyFrom(t);
    if (!wk) return false;
    return mergedKeys().indexOf(wk) >= 0;
  }

  function isEditingInScope() {
    const ae = pw.document && pw.document.activeElement;
    if (!ae) return false;
    const tag = String(ae.tagName || "").toUpperCase();
    if (tag !== "INPUT" && tag !== "TEXTAREA") return false;
    return isStep2FieldTarget(ae);
  }

  function onTabIntent(e) {
    if (e.__sajuTabHandled) return;
    if (e.isComposing || e.keyCode === 229) return;
    const code = e.keyCode || e.which;
    const isTab = e.key === "Tab" || code === 9;
    const isEnter =
      e.key === "Enter" &&
      !e.shiftKey &&
      e.target &&
      e.target.tagName === "INPUT" &&
      (e.target.type || "text").toLowerCase() !== "checkbox";
    if (!isTab && !isEnter) return;
    if (!step2Active()) return;
    if (!isStep2FieldTarget(e.target)) return;

    const backward = isTab && e.shiftKey;
    const anchor = e.target || (e.currentTarget && e.currentTarget.ownerDocument
      ? e.currentTarget.ownerDocument.activeElement
      : null);
    const lock = pw.__sajuStep2FocusLock;
    if (lock && lock.until && Date.now() < lock.until && lock.key) {
      const lockRoot = findRootAny(lock.key);
      const lockEl = lockRoot
        ? pickPrimary(lockRoot, lockRoot.ownerDocument.defaultView || pw)
        : null;
      if (lockEl) {
        hardFocus(lockEl);
        e.__sajuTabHandled = true;
        e.preventDefault();
        e.stopPropagation();
        return;
      }
    }

    if (!moveFrom(anchor, backward, isEnter)) return;

    e.__sajuTabHandled = true;
    e.preventDefault();
    e.stopPropagation();
    try {
      e.stopImmediatePropagation();
    } catch (err) {}
  }

  function demoteScopeTabStops() {
    if (typeof pw.__sajuBirthTimeSelectMenuOpen === "function" && pw.__sajuBirthTimeSelectMenuOpen()) {
      return;
    }
    forEachDoc((doc) => {
      doc.querySelectorAll(SCOPE_SEL).forEach((scope) => {
        scope
          .querySelectorAll(
            "button, a, select, textarea, input, summary, [tabindex]"
          )
          .forEach((el) => {
            if (chainCache.indexOf(el) >= 0) return;
            if (
              el.closest(
                '[data-baseweb="popover"], [data-baseweb="select-dropdown"], [data-baseweb="menu"], [role="listbox"]'
              )
            ) {
              return;
            }
            if (el.closest('[data-testid="stNumberInput"]') && el.tagName === "BUTTON") {
              el.tabIndex = -1;
              return;
            }
            if (el.closest('[data-testid="stExpander"]') && el.tagName === "BUTTON") {
              el.tabIndex = -1;
            }
          });
      });
    });
  }

  function bindScopeHandlers() {
    forEachDoc((doc) => {
      doc.querySelectorAll(SCOPE_SEL).forEach((scope) => {
        if (scope.__sajuTabScopeV11) return;
        scope.__sajuTabScopeV11 = true;
        scope.addEventListener("keydown", onTabIntent, true);
      });
    });
  }

  function scheduleRefresh() {
    if (refreshQueued) return;
    refreshQueued = true;
    const run = function () {
      refreshQueued = false;
      if (!step2Active()) return;
      if (pw.__sajuBdateFocusLock || isEditingInScope()) return;
      if (typeof pw.__sajuBirthTimeSelectMenuOpen === "function" && pw.__sajuBirthTimeSelectMenuOpen()) {
        return;
      }
      buildChain();
      demoteScopeTabStops();
      bindScopeHandlers();
    };
    run();
    try {
      requestAnimationFrame(run);
    } catch (e) {}
    [0, 64, 180].forEach((ms) => setTimeout(run, ms));
  }

  pw.__sajuStep2TabSetOrder = function (o) {
    pw.__sajuStep2TabOrder = o || ORDER;
    scheduleRefresh();
  };

  pw.__sajuStep2TabRefresh = scheduleRefresh;

  function rememberFocus(el) {
    if (!el || !isStep2FieldTarget(el)) return;
    const wk = widgetKeyFrom(el);
    if (!wk) return;
    try {
      pw.sessionStorage.setItem("saju_step2_last_focus", wk);
    } catch (e) {}
    pw.__sajuStep2FocusLock = { key: wk, until: Date.now() + 1800 };
  }

  function restoreLastFocus() {
    if (!step2Active()) return;
    let wk = null;
    try {
      wk = pw.sessionStorage.getItem("saju_step2_last_focus");
    } catch (e) {}
    const lock = pw.__sajuStep2FocusLock;
    if (lock && lock.key && lock.until && Date.now() < lock.until) {
      wk = lock.key;
    }
    if (!wk) return;
    const root = findRootAny(wk);
    const win = root ? root.ownerDocument.defaultView || pw : pw;
    const el = pickPrimary(root, win);
    if (el) hardFocus(el);
  }

  if (!pw.__sajuStep2FocusInBound) {
    pw.__sajuStep2FocusInBound = true;
    forEachDoc(function (doc) {
      doc.addEventListener(
        "focusin",
        function (ev) {
          if (!step2Active()) return;
          rememberFocus(ev.target);
        },
        true
      );
      doc.addEventListener(
        "mousedown",
        function (ev) {
          if (!step2Active()) return;
          rememberFocus(ev.target);
        },
        true
      );
    });
  }

  const origRefresh = scheduleRefresh;
  pw.__sajuStep2TabRefresh = function () {
    origRefresh();
    [0, 48, 120, 240, 420].forEach(function (ms) {
      setTimeout(restoreLastFocus, ms);
    });
  };

  let tabMoTimer = null;
  try {
    const root =
      pw.document.querySelector('[data-testid="stAppViewContainer"]') ||
      pw.document.body;
    if (root && pw.MutationObserver) {
      const obs = new pw.MutationObserver(function () {
        if (!step2Active()) return;
        if (tabMoTimer) clearTimeout(tabMoTimer);
        tabMoTimer = setTimeout(function () {
          tabMoTimer = null;
          if (typeof pw.__sajuStep2TabRefresh === "function") {
            pw.__sajuStep2TabRefresh();
          } else {
            scheduleRefresh();
          }
        }, 140);
      });
      obs.observe(root, { childList: true, subtree: true });
    }
  } catch (e) {}

  if (typeof pw.__sajuStep2TabRefresh === "function") {
    pw.__sajuStep2TabRefresh();
  } else {
    scheduleRefresh();
  }
})();
"""


def inject_step2_scroll_preserve_once() -> None:
    """STEP2 — 위젯 rerun 시 스크롤·포커스가 화면 상단으로 튕기지 않도록 유지."""
    ver = "v3"
    if not st.session_state.get(f"_saju_step2_scroll_preserve_{ver}"):
        st.session_state[f"_saju_step2_scroll_preserve_{ver}"] = True
        st.session_state.pop("_saju_step2_scroll_preserve_v2", None)
        js = r"""
(function () {
  const pw = window.parent !== window ? window.parent : window;
  const doc = pw.document;
  if (!doc) return;
  if (pw.__sajuStep2ScrollPreserveV3) return;
  pw.__sajuStep2ScrollPreserveV3 = true;
  pw.__sajuStep2ScrollPreserveV2 = true;

  const KEY = "saju_step2_scroll_y";
  const EDIT_KEY = "saju_step2_editing";
  const FIELD_SEL =
    ".st-key-step2_navertone_self, .st-key-step2_navertone_opp, .st-key-step2_revisit_expander_wrap, .st-key-step2_fixed_next_bar, .st-key-step2_action_block, .st-key-step2_save_actions";

  function onStep2() {
    try {
      return doc.documentElement.getAttribute("data-saju-step") === "2";
    } catch (e) {
      return false;
    }
  }

  function getMainScrollEl() {
    const cands = [
      doc.querySelector('[data-testid="stMain"]'),
      doc.querySelector("section.main"),
      doc.querySelector('[data-testid="stMainBlockContainer"]'),
      doc.querySelector('[data-testid="stAppViewContainer"]'),
      doc.scrollingElement,
      doc.documentElement,
    ];
    for (let i = 0; i < cands.length; i++) {
      const el = cands[i];
      if (!el) continue;
      try {
        if ((el.scrollHeight || 0) - (el.clientHeight || 0) > 4) return el;
      } catch (e) {}
    }
    return (
      doc.querySelector('[data-testid="stMain"]') ||
      doc.querySelector("section.main") ||
      doc.documentElement
    );
  }

  function scrollTargets() {
    const out = [];
    const main = getMainScrollEl();
    if (main) out.push(main);
    [
      doc.querySelector('[data-testid="stMainBlockContainer"]'),
      doc.querySelector('[data-testid="stAppViewContainer"]'),
      doc.scrollingElement,
      doc.documentElement,
    ].forEach(function (el) {
      if (el && out.indexOf(el) < 0) out.push(el);
    });
    return out;
  }

  function markEditing() {
    if (!onStep2()) return;
    try {
      pw.sessionStorage.setItem(EDIT_KEY, "1");
    } catch (e) {}
    pw.__sajuStep2FocusLock = { key: "step2", until: Date.now() + 2800 };
    saveScroll();
  }

  function readY() {
    let y = 0;
    scrollTargets().forEach(function (el) {
      try {
        y = Math.max(y, el.scrollTop || 0);
      } catch (e) {}
    });
    try {
      y = Math.max(y, pw.scrollY || doc.documentElement.scrollTop || 0);
    } catch (e2) {}
    return y;
  }

  function writeY(y) {
    const top = Math.max(0, parseInt(String(y || 0), 10) || 0);
    scrollTargets().forEach(function (el) {
      try {
        el.scrollTop = top;
      } catch (e) {}
    });
    try {
      pw.scrollTo(0, top);
    } catch (e2) {}
  }

  function saveScroll() {
    if (!onStep2()) return;
    try {
      pw.sessionStorage.setItem(KEY, String(readY()));
    } catch (e) {}
  }

  function restoreScroll() {
    if (!onStep2()) return;
    let raw = null;
    try {
      raw = pw.sessionStorage.getItem(KEY);
    } catch (e) {}
    if (raw == null) return;
    const y = parseInt(raw, 10);
    if (!Number.isFinite(y)) return;
    const apply = function () {
      writeY(y);
    };
    apply();
    try {
      pw.requestAnimationFrame(apply);
    } catch (e) {}
    [8, 32, 96].forEach(function (ms) {
      pw.setTimeout(apply, ms);
    });
  }

  pw.__sajuStep2SaveScroll = saveScroll;
  pw.__sajuStep2RestoreScroll = restoreScroll;

  if (!pw.__sajuStep2ScrollSaveBound) {
    pw.__sajuStep2ScrollSaveBound = true;
    doc.addEventListener("input", markEditing, true);
    doc.addEventListener("change", markEditing, true);
    ["focusin", "mousedown", "pointerdown", "touchstart"].forEach(function (ev) {
      doc.addEventListener(
        ev,
        function (e) {
          if (!onStep2()) return;
          const t = e.target;
          if (!t || !t.closest) return;
          if (t.closest(FIELD_SEL)) markEditing();
        },
        true
      );
    });
  }

  restoreScroll();
})();
"""
        with st.container(key="saju_step2_scroll_preserve_v3"):
            components.html(
                "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
                "<body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
                f"<script>{js}</script></body></html>",
                height=1,
                scrolling=False,
            )

    # 스크롤 복원은 1회 설치 JS(이벤트·__sajuStep2RestoreScroll)에 맡김 — rerun마다 iframe 추가 금지


def inject_step2_tab_order_once() -> None:
    """STEP2 정보 입력 — Tab/다음 키로 성함→년월일→시간→… 순서 이동."""
    inject_step2_tab_manager_global_once()


def queue_widget_focus(widget_key: str, *, kind: str = "control") -> None:
    """rerun 후 방금 조작한 위젯(버튼·접이식·입력)으로 포커스·스크롤 위치 복귀."""
    wk = str(widget_key or "").strip()
    if not wk:
        return
    st.session_state["_saju_focus_return_key"] = wk
    st.session_state["_saju_focus_return_kind"] = str(kind or "control")
    st.session_state["_saju_nav_preserve_scroll"] = True
    st.session_state["_saju_widget_skip_finalize_scroll"] = True


def inject_widget_focus_return_once() -> None:
    """``queue_widget_focus`` 로 예약된 위젯에 포커스(STEP2 입력 등)."""
    key = st.session_state.pop("_saju_focus_return_key", None)
    if not key:
        return
    kind = str(st.session_state.pop("_saju_focus_return_kind", None) or "control")
    import json

    key_js = json.dumps(str(key), ensure_ascii=False)
    kind_js = json.dumps(kind, ensure_ascii=False)
    focus_js = f"""
(function() {{
  const widgetKey = {key_js};
  const kind = {kind_js};
  const pw = window.parent || window;
  const doc = pw.document;
  if (!doc || !widgetKey) return;

  function findRoot() {{
    const exact = "st-key-" + widgetKey;
    const list = doc.querySelectorAll('[class*="st-key-"]');
    for (let i = 0; i < list.length; i++) {{
      const el = list[i];
      if (!el || !el.classList) continue;
      if (el.classList.contains(exact)) return el;
    }}
    try {{
      return doc.querySelector("." + exact.replace(/:/g, "\\\\:"));
    }} catch (e) {{
      return null;
    }}
  }}

  function collapseExpanderRoot(root) {{
    if (!root) return;
    root.querySelectorAll("details").forEach((d) => {{
      d.open = false;
      d.removeAttribute("open");
    }});
    const summary = root.querySelector(
      '[data-testid="stExpander"] summary, details > summary'
    );
    if (summary) summary.setAttribute("aria-expanded", "false");
    root.querySelectorAll("button").forEach((b) => {{
      b.tabIndex = -1;
    }});
  }}

  function pickTarget(root) {{
    if (!root) return null;
    if (kind === "expander") {{
      collapseExpanderRoot(root);
      const exp = root.querySelector('[data-testid="stExpander"]');
      const summary =
        (exp && exp.querySelector("summary")) ||
        root.querySelector("details > summary");
      if (summary) {{
        summary.setAttribute("tabindex", "0");
        return summary;
      }}
    }}
    if (kind === "control") {{
      return (
        root.querySelector(
          '[data-baseweb="select"] [role="combobox"], [data-baseweb="select"] [aria-haspopup="listbox"]'
        ) ||
        root.querySelector('[data-baseweb="popover"] button') ||
        root.querySelector("button:not([disabled])") ||
        root.querySelector(
          'input:not([type="hidden"]):not([disabled]), textarea:not([disabled])'
        )
      );
    }}
    if (kind === "input") {{
      return root.querySelector(
        'input:not([type="hidden"]):not([disabled]), textarea:not([disabled])'
      );
    }}
    if (kind === "button") {{
      return root.querySelector("button:not([disabled])");
    }}
    return (
      root.querySelector('[data-testid="stExpander"] summary') ||
      root.querySelector("button:not([disabled])") ||
      root.querySelector(
        'input:not([type="hidden"]):not([disabled]), textarea:not([disabled])'
      )
    );
  }}

  function apply() {{
    const root = findRoot();
    const target = pickTarget(root) || root;
    if (!target) return;
    const sel =
      target.selectionStart != null && target.selectionEnd != null
        ? {{ start: target.selectionStart, end: target.selectionEnd }}
        : null;
    try {{
      if (
        target.tagName !== "INPUT" &&
        target.tagName !== "TEXTAREA" &&
        target.tagName !== "BUTTON" &&
        !target.hasAttribute("tabindex")
      ) {{
        target.setAttribute("tabindex", "-1");
      }}
      const onStep2 =
        doc.documentElement &&
        doc.documentElement.getAttribute("data-saju-step") === "2";
      if (!onStep2) {{
        target.scrollIntoView({{ block: "nearest", inline: "nearest", behavior: "auto" }});
      }}
      target.focus({{ preventScroll: true }});
      if (onStep2 && typeof pw.__sajuStep2RestoreScroll === "function") {{
        pw.__sajuStep2RestoreScroll();
      }}
      if (
        sel &&
        (target.tagName === "INPUT" || target.tagName === "TEXTAREA")
      ) {{
        try {{
          target.setSelectionRange(sel.start, sel.end);
        }} catch (e3) {{}}
      }}
    }} catch (e) {{
      try {{ target.focus(); }} catch (e2) {{}}
    }}
  }}

  const delays =
    kind === "expander" ? [0, 40, 100, 200, 360, 520, 720] : [0, 60, 180, 360];
  delays.forEach((ms) => {{
    if (ms === 0) apply();
    else setTimeout(apply, ms);
  }});
  try {{
    pw.requestAnimationFrame(apply);
  }} catch (e) {{
    setTimeout(apply, 16);
  }}
  if (kind === "expander" && widgetKey) {{
    try {{
      pw.__sajuStep2FocusLock = {{ key: widgetKey, until: Date.now() + 900 }};
    }} catch (e) {{}}
  }} else if (widgetKey) {{
    try {{
      const lock = {{ key: widgetKey, until: Date.now() + 2200 }};
      pw.__sajuWidgetFocusLock = lock;
      pw.__sajuStep2FocusLock = lock;
      pw.sessionStorage.setItem("saju_widget_focus_v1", widgetKey);
      pw.sessionStorage.setItem("saju_step2_last_focus", widgetKey);
    }} catch (e2) {{}}
  }}
}})();
"""
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
        f"<script>{focus_js}</script></body></html>"
    )
    token = int(st.session_state.get("_saju_focus_return_token", 0)) + 1
    st.session_state["_saju_focus_return_token"] = token
    with st.container(key=f"saju_focus_return_{token}"):
        components.html(html, height=1, scrolling=False)
    inject_cancel_step_scroll_lock()


def inject_cancel_step_scroll_lock() -> None:
    """위젯 rerun·포커스 복귀 — STEP 전환용 스크롤 잠금 해제."""
    st.markdown(
        "<script>(function(){const pw=window.parent||window;"
        "if(typeof pw.__sajuCancelStepScroll==='function'){pw.__sajuCancelStepScroll();}"
        "if(typeof pw.__sajuCancelHomeViewport==='function'){pw.__sajuCancelHomeViewport();}"
        "})();</script>",
        unsafe_allow_html=True,
    )


def inject_cancel_step_scroll_lock_once() -> None:
    """레거시 — 매 run ``inject_cancel_step_scroll_lock`` 호출."""
    inject_cancel_step_scroll_lock()


def _trigger_home_solar_iframe_fit_js() -> None:
    """24절기 iframe 높이만 조정 — 스크롤 위치는 변경하지 않습니다."""
    trigger_js = (
        "(function(){"
        "const pw=window.parent||window;"
        "if(typeof pw.__sajuScheduleHomeSolar24Fit==='function'){"
        "pw.__sajuScheduleHomeSolar24Fit();"
        "}else if(typeof pw.__sajuFitHomeSolar24Iframe==='function'){"
        "pw.__sajuFitHomeSolar24Iframe();"
        "}"
        "})();"
    )
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
        f"<script>{trigger_js}</script></body></html>"
    )
    with st.container(key="saju_home_solar_fit"):
        components.html(html, height=1, scrolling=False)


def inject_step_dom_boot_once() -> None:
    """앱 기동 직후 — (구) STEP 동기화 스크립트 주입 지점. 현재는 no-op.

    data-saju-step 세팅·스크롤은 inject_nav_scroll_tail_once(실행되는 iframe)가 담당한다.
    여기서 st.markdown("<script>") 을 쓰면 Streamlit 이 script 를 제거해 실행도 안 되고,
    빈 element-container 가 본문 상단 공백(flex gap)만 키우므로 더 이상 주입하지 않는다.
    """
    st.session_state["_saju_step_dom_boot_v1"] = True
    return


def reset_step_dom_sync_slots_for_run() -> None:
    """라우터 rerun 시작 시 호출 — ``sync_step_dom_now`` slot 중복 key 방지."""
    st.session_state["_saju_html_sync_slots"] = []


_GLOBAL_WIDGET_FOCUS_PRESERVE_JS = r"""
(function () {
  const pw = window.parent !== window ? window.parent : window;
  if (pw.__sajuGlobalWidgetFocusV4) return;
  pw.__sajuGlobalWidgetFocusV4 = true;
  pw.__sajuGlobalWidgetFocusV3 = true;
  pw.__sajuGlobalWidgetFocusV2 = true;
  pw.__sajuGlobalWidgetFocusV1 = true;

  const SKIP_KEY_RE =
    /^(saju_global_bottom|saju_bottom_prev_next|saju_bottom_quick|saju_scroll_mgr|saju_step2_tab|saju_focus_return|saju_widget_focus|saju_nav_pending|saju_step_nav_click)/;

  function getMainScrollEl(doc) {
    const cands = [
      doc.querySelector('[data-testid="stMain"]'),
      doc.querySelector("section.main"),
      doc.querySelector('[data-testid="stMainBlockContainer"]'),
      doc.querySelector('[data-testid="stAppViewContainer"]'),
      doc.scrollingElement,
      doc.documentElement,
    ];
    for (let i = 0; i < cands.length; i++) {
      const el = cands[i];
      if (!el) continue;
      try {
        if ((el.scrollHeight || 0) - (el.clientHeight || 0) > 4) return el;
      } catch (e) {}
    }
    return (
      doc.querySelector('[data-testid="stMain"]') ||
      doc.querySelector("section.main") ||
      doc.documentElement
    );
  }

  function widgetKeyFrom(el) {
    let node = el;
    while (node) {
      if (node.classList) {
        for (let i = 0; i < node.classList.length; i++) {
          const c = node.classList[i];
          if (c.indexOf("st-key-") !== 0) continue;
          const key = c.slice(7);
          if (SKIP_KEY_RE.test(key)) continue;
          return key;
        }
      }
      node = node.parentElement;
    }
    return null;
  }

  function isInteractive(el) {
    if (!el) return false;
    const tag = String(el.tagName || "").toUpperCase();
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || tag === "BUTTON") {
      return true;
    }
    try {
      if (el.getAttribute && el.getAttribute("role") === "combobox") return true;
      if (el.closest && el.closest('[data-baseweb="select"]')) return true;
      if (el.closest && el.closest('[data-testid="stExpander"] summary')) return true;
    } catch (e) {}
    return false;
  }

  function pickTarget(root) {
    if (!root) return null;
    const combo = root.querySelector(
      '[data-baseweb="select"] [role="combobox"], [data-baseweb="select"] [aria-haspopup="listbox"]'
    );
    if (combo) return combo;
    const inputs = root.querySelectorAll(
      'input:not([type="hidden"]):not([disabled]), textarea:not([disabled])'
    );
    for (let i = 0; i < inputs.length; i++) {
      if ((inputs[i].type || "").toLowerCase() !== "checkbox") return inputs[i];
    }
    for (let j = 0; j < inputs.length; j++) {
      if ((inputs[j].type || "").toLowerCase() === "checkbox") return inputs[j];
    }
    const summary = root.querySelector(
      '[data-testid="stExpander"] summary, details > summary'
    );
    if (summary) return summary;
    return root.querySelector("button:not([disabled])");
  }

  function hardFocus(el) {
    if (!el) return;
    const de = doc.documentElement;
    const step = de ? String(de.getAttribute("data-saju-step") || "") : "";
    const lock = pw.__sajuWidgetFocusLock;
    const savedY =
      lock && lock.scrollTop != null
        ? lock.scrollTop
        : readSavedScrollY();
    const inPageTab =
      el.closest &&
      !!el.closest(
        ".st-key-step6_today_pick_row, .st-key-step8_pick_row, .st-key-step4_compat_tabs"
      );
    const skipScrollInto = step === "2" || inPageTab || savedY > 8;
    if (!skipScrollInto) {
      try {
        el.scrollIntoView({ block: "nearest", inline: "nearest", behavior: "auto" });
      } catch (e) {}
    }
    try {
      el.focus({ preventScroll: true });
    } catch (e2) {
      try {
        el.focus();
      } catch (e3) {}
    }
    if (step === "2" && typeof pw.__sajuStep2RestoreScroll === "function") {
      pw.__sajuStep2RestoreScroll();
    } else if (savedY > 0) {
      restoreScroll(lock || { scrollTop: savedY, scrollY: savedY });
    }
  }

  function readSavedScrollY() {
    try {
      const raw = pw.sessionStorage.getItem("saju_widget_scroll_y");
      if (raw == null) return 0;
      const y = parseInt(raw, 10);
      return Number.isFinite(y) ? Math.max(0, y) : 0;
    } catch (e) {
      return 0;
    }
  }

  function rememberFocus(target) {
    if (!target || !isInteractive(target)) return;
    const doc = pw.document;
    if (!doc) return;
    const wk = widgetKeyFrom(target);
    if (!wk) return;
    const main = getMainScrollEl(doc);
    const lock = {
      key: wk,
      until: Date.now() + 2600,
      scrollTop: main ? main.scrollTop : 0,
      scrollY: pw.scrollY || 0,
    };
    pw.__sajuWidgetFocusLock = lock;
    pw.__sajuStep2FocusLock = lock;
    try {
      pw.sessionStorage.setItem("saju_widget_focus_v1", wk);
      pw.sessionStorage.setItem("saju_widget_scroll_y", String(lock.scrollTop || 0));
      pw.sessionStorage.setItem("saju_widget_editing", "1");
      pw.setTimeout(function () {
        try {
          pw.sessionStorage.removeItem("saju_widget_editing");
        } catch (e0) {}
      }, 3200);
    } catch (e) {}
  }

  function restoreScroll(lock) {
    const doc = pw.document;
    if (!doc) return;
    const main = getMainScrollEl(doc);
    let top =
      lock && lock.scrollTop != null ? lock.scrollTop : readSavedScrollY();
    top = Math.max(0, parseInt(String(top || 0), 10) || 0);
    if (top <= 0) return;
    const apply = function () {
      if (main) {
        try {
          main.scrollTop = top;
        } catch (e) {}
      }
      try {
        pw.scrollTo(0, top);
      } catch (e2) {}
    };
    apply();
    try {
      pw.requestAnimationFrame(apply);
    } catch (e3) {}
    [8, 32, 96, 200].forEach(function (ms) {
      pw.setTimeout(apply, ms);
    });
  }

  function restoreWidgetFocus() {
    const doc = pw.document;
    if (!doc) return;
    const de = doc.documentElement;
    if (de && de.getAttribute("data-saju-nav-pending") === "1") return;

    if (de && de.getAttribute("data-saju-step") === "2") {
      try {
        if (
          pw.sessionStorage.getItem("saju_step2_editing") === "1" ||
          pw.sessionStorage.getItem("saju_widget_editing") === "1"
        ) {
          const lock2 = pw.__sajuWidgetFocusLock;
          restoreScroll(lock2);
          if (typeof pw.__sajuStep2RestoreScroll === "function") {
            pw.__sajuStep2RestoreScroll();
          }
          return;
        }
      } catch (eStep2) {}
    }

    let wk = null;
    const lock = pw.__sajuWidgetFocusLock;
    if (lock && lock.until && Date.now() < lock.until) {
      wk = lock.key;
      restoreScroll(lock);
    }
    if (!wk) {
      try {
        wk = pw.sessionStorage.getItem("saju_widget_focus_v1");
      } catch (e) {}
    }
    if (!wk) return;

    const exact = "st-key-" + wk;
    const nodes = doc.querySelectorAll('[class*="st-key-"]');
    let root = null;
    for (let i = 0; i < nodes.length; i++) {
      if (nodes[i].classList && nodes[i].classList.contains(exact)) {
        root = nodes[i];
        break;
      }
    }
    const target = pickTarget(root);
    if (target) hardFocus(target);
  }

  pw.__sajuRestoreWidgetFocus = restoreWidgetFocus;

  const doc = pw.document;
  if (!doc) return;

  function onInteract(ev) {
    rememberFocus(ev.target);
  }

  ["focusin", "mousedown", "pointerdown", "touchstart"].forEach(function (ev) {
    try {
      doc.addEventListener(ev, onInteract, true);
    } catch (e) {}
  });

  let moTimer = null;
  try {
    const root =
      doc.querySelector('[data-testid="stAppViewContainer"]') || doc.body;
    if (root && pw.MutationObserver) {
      new pw.MutationObserver(function () {
        if (moTimer) clearTimeout(moTimer);
        moTimer = setTimeout(function () {
          moTimer = null;
          restoreWidgetFocus();
        }, 80);
      }).observe(root, { childList: true, subtree: true });
    }
  } catch (e) {}

  [0, 48, 120, 240, 420, 680].forEach(function (ms) {
    pw.setTimeout(restoreWidgetFocus, ms);
  });
})();
"""


def inject_global_widget_focus_preserve_once() -> None:
    """전 STEP — 위젯 클릭·입력 rerun 후 포커스·스크롤 위치 유지."""
    if st.session_state.get("_saju_global_widget_focus_v4"):
        return
    st.session_state["_saju_global_widget_focus_v4"] = True
    st.session_state.pop("_saju_global_widget_focus_v3", None)
    st.session_state.pop("_saju_global_widget_focus_v2", None)
    st.session_state.pop("_saju_global_widget_focus_v1", None)
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:0;overflow:hidden;'>"
        f"<script>{_GLOBAL_WIDGET_FOCUS_PRESERVE_JS}</script></body></html>"
    )
    with st.container(key="saju_widget_focus_preserve_v4"):
        components.html(html, height=0, scrolling=False)


_STEP_NAV_CLICK_GUARD_JS = r"""
(function () {
  const pw = window.parent !== window ? window.parent : window;
  const doc = pw.document;
  if (!doc || pw.__sajuStepNavClickGuardV2) return;
  pw.__sajuStepNavClickGuardV2 = true;

  function readStep() {
    const de = doc.documentElement;
    const n = parseInt(String(de.getAttribute("data-saju-step") || "1"), 10);
    return Math.max(1, Math.min(12, n || 1));
  }

  function applyFromStep(n) {
    const de = doc.documentElement;
    if (!de) return;
    const sn = Math.max(1, Math.min(12, parseInt(String(n), 10) || 1));
    de.setAttribute("data-saju-step", String(sn));
    de.setAttribute("data-saju-nav-from", String(sn));
    de.classList.remove("saju-home-step1", "saju-not-step1");
    de.classList.add(sn === 1 ? "saju-home-step1" : "saju-not-step1");
  }

  function setPending(on) {
    const de = doc.documentElement;
    if (!de) return;
    if (on) de.setAttribute("data-saju-nav-pending", "1");
    else de.removeAttribute("data-saju-nav-pending");
  }

  pw.__sajuArmStepNavPending = function (fromStep) {
    const fs =
      fromStep != null
        ? Math.max(1, Math.min(12, parseInt(String(fromStep), 10) || 1))
        : readStep();
    applyFromStep(fs);
    setPending(true);
  };

  pw.__sajuClearStepNavPending = function () {
    setPending(false);
  };

  function isStepNavControl(el) {
    if (!el) return false;
    try {
      if (
        el.closest(
          ".st-key-saju_global_bottom_chrome, " +
            ".st-key-saju_bottom_quick_menu_panel, " +
            ".st-key-saju_bottom_prev_next_row, " +
            ".st-key-step11_inline_nav_row"
        )
      ) {
        return !!el.closest("button");
      }
      const root = el.closest('[class*="st-key-"]');
      if (!root || !root.classList) return false;
      for (let i = 0; i < root.classList.length; i++) {
        const c = root.classList[i];
        if (
          c.indexOf("st-key-saju_bottom_nav_") === 0 ||
          c.indexOf("st-key-saju_dock_nav_") === 0
        ) {
          return !!el.closest("button");
        }
      }
    } catch (e) {}
    return false;
  }

  function onNavPointer(e) {
    if (!isStepNavControl(e.target)) return;
    try {
      pw.__sajuWidgetFocusLock = null;
      pw.__sajuStep2FocusLock = null;
    } catch (e0) {}
    pw.__sajuArmStepNavPending(readStep());
  }

  ["pointerdown", "touchstart", "mousedown"].forEach(function (ev) {
    try {
      doc.addEventListener(ev, onNavPointer, true);
    } catch (e) {}
  });
})();
"""


def clear_step_nav_pending_now() -> None:
    """STEP2 저장 실패 등 — 클릭 guard 가 켠 ``data-saju-nav-pending`` 을 즉시 해제."""
    slot = int(st.session_state.get("_saju_clear_nav_pending_n", 0)) + 1
    st.session_state["_saju_clear_nav_pending_n"] = slot
    rid = int(st.session_state.get("reset_id", 0))
    trigger_js = (
        "(function(){"
        "var pw=(window.parent&&window.parent!==window)?window.parent:window;"
        "var doc=pw.document;if(!doc)return;"
        "if(typeof pw.__sajuClearStepNavPending==='function'){pw.__sajuClearStepNavPending();return;}"
        "try{doc.documentElement.removeAttribute('data-saju-nav-pending');}catch(e){}"
        "})();"
    )
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:0;overflow:hidden;'>"
        f"<script>{trigger_js}</script></body></html>"
    )
    with st.container(key=f"saju_clear_nav_pending_{rid}_{slot}"):
        components.html(html, height=0, scrolling=False)


def inject_step2_validation_alert_scroll_once() -> None:
    """STEP2 검증 실패 시 안내 박스가 보이도록 스크롤."""
    if not st.session_state.pop("_step2_scroll_to_alert", False):
        return
    rid = int(st.session_state.get("reset_id", 0))
    trigger_js = (
        "(function(){"
        "var pw=(window.parent&&window.parent!==window)?window.parent:window;"
        "var doc=pw.document;if(!doc)return;"
        "function scrollToAlert(){"
        "var el=doc.querySelector('.st-key-step2_validation_alert,.st-key-step2_action_block,.st-key-step2_fixed_next_bar,.st-key-step2_save_actions');"
        "if(!el)return;"
        "try{el.scrollIntoView({behavior:'smooth',block:'center'});}catch(e){"
        "try{el.scrollIntoView(true);}catch(e2){}"
        "}"
        "}"
        "scrollToAlert();"
        "try{pw.setTimeout(scrollToAlert,120);}catch(e){}"
        "})();"
    )
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:0;overflow:hidden;'>"
        f"<script>{trigger_js}</script></body></html>"
    )
    with st.container(key=f"saju_step2_alert_scroll_{rid}"):
        components.html(html, height=0, scrolling=False)


def inject_step_nav_click_guard_once() -> None:
    """STEP 이동 버튼 클릭 직후( rerun 대기 전) pending·출발 STEP 고정 — 빈 하단 네비 방지."""
    if st.session_state.get("_saju_step_nav_click_guard_v2"):
        return
    st.session_state["_saju_step_nav_click_guard_v2"] = True
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:0;overflow:hidden;'>"
        f"<script>{_STEP_NAV_CLICK_GUARD_JS}</script></body></html>"
    )
    with st.container(key="saju_step_nav_click_guard_v2"):
        components.html(html, height=0, scrolling=False)


def get_step_nav_from_step(*, target_step: int | None = None) -> int | None:
    """STEP 이동 직후 run — 전환 출발 STEP(이전 STEP) 번호. 없으면 ``None``."""
    try:
        step = max(1, min(12, int(target_step if target_step is not None else st.session_state.get("step", 1))))
    except Exception:
        step = 1
    try:
        fs = int(st.session_state.get("_saju_nav_from_step") or 0)
        if 1 <= fs <= 12 and fs != step:
            return fs
    except Exception:
        pass
    try:
        last = st.session_state.get("_router_last_step")
        if last is not None:
            li = max(1, min(12, int(last)))
            if li != step:
                return li
    except Exception:
        pass
    return None


def inject_step_nav_transition_early(*, target_step: int, from_step: int) -> None:
    """STEP 이동 run — 라우터보다 먼저 pending 플래그만 주입(빈 화면 방지).

    마운트 가시성 <style> 은 라우터 본문 뒤 1회만 주입한다.
    여기서 also_show CSS 를 중복 주입하면 이전·새 마운트가 세로로 겹쳐 상단 공백이 생긴다.
    """
    fs = max(1, min(12, int(from_step)))
    ts = max(1, min(12, int(target_step)))
    if fs == ts:
        return
    inject_step_nav_pending_flag(from_step=fs)


def inject_step_nav_pending_flag(*, from_step: int) -> None:
    """STEP 이동 run 시작 — 전환 중 ``data-saju-nav-pending``·이전 ``data-saju-step`` 즉시 고정.

    bootstrap CSS 가 새 step 으로 바뀌어 이전 마운트를 숨기기 전에 실행되어,
    하단 네비만 남는 빈 화면(1~2초)을 막습니다.
    """
    fs = max(1, min(12, int(from_step)))
    nav_epoch = int(st.session_state.get("saju_nav_epoch", 0))
    if st.session_state.get("_saju_nav_pending_flag_epoch") == nav_epoch:
        return
    st.session_state["_saju_nav_pending_flag_epoch"] = nav_epoch
    home_cls = "saju-home-step1" if fs == 1 else "saju-not-step1"
    trigger_js = (
        "(function(){"
        "var pw=(window.parent&&window.parent!==window)?window.parent:window;"
        "var doc=pw.document||document;"
        "var de=doc.documentElement;if(!de)return;"
        f"if(typeof pw.__sajuArmStepNavPending==='function'){{pw.__sajuArmStepNavPending({fs});return;}}"
        "de.setAttribute('data-saju-nav-pending','1');"
        f"de.setAttribute('data-saju-step','{fs}');"
        f"de.setAttribute('data-saju-nav-from','{fs}');"
        "de.classList.remove('saju-home-step1','saju-not-step1');"
        f"de.classList.add('{home_cls}');"
        "})();"
    )
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:0;overflow:hidden;'>"
        f"<script>{trigger_js}</script></body></html>"
    )
    with st.container(key=f"saju_nav_pending_flag_{nav_epoch}"):
        components.html(html, height=0, scrolling=False)


def inject_router_step_mount_visibility_css(
    step: int, *, also_show_step: int | None = None
) -> None:
    """현재 STEP 마운트만 표시 — ``data-saju-step`` JS 지연 시에도 세션 STEP 기준으로 즉시 적용.

    ``also_show_step``(이전 STEP)을 함께 넘기면 STEP 이동 직후 전환 구간에서
    새 마운트가 DOM 에 채워지기 전에 이전 마운트를 숨기지 않아 '빈 화면'을 막습니다.
    """
    s = max(1, min(12, int(step)))
    visible: set[int] = {s}
    if also_show_step is not None:
        try:
            a = max(1, min(12, int(also_show_step)))
        except Exception:
            a = 0
        if a and a != s:
            visible.add(a)
    # 캐시 가드 금지: 스텝이 안 바뀐 rerun(위젯 클릭 등)에서 재주입을 건너뛰면
    # Streamlit 이 이전 run 의 <style> 요소를 DOM 에서 제거해, 숨겨두던 잔존 마운트
    # (특히 홈 mount_01)가 다시 노출된다. 매 렌더마다 반드시 다시 주입한다.
    st.session_state["_saju_router_mount_css_step"] = s

    # specificity 강화: bootstrap 의 html[data-saju-step]:not(...) 숨김 규칙(0,3,1)보다
    # 높게 잡아, also_show_step 전환 구간에서 inject <style> 이 항상 이기게 한다.
    def _mount_hide_sel(i: int) -> str:
        c = f"st-key-saju_router_step_mount_{i:02d}"
        dup = f".{c}.{c}.{c}.{c}"
        return f"html[data-saju-step] body {dup}, html[data-saju-nav-pending=\"1\"] body {dup}"

    def _mount_show_sel(i: int) -> str:
        return _mount_hide_sel(i)

    hide_sel = ",\n".join(_mount_hide_sel(i) for i in range(1, 13) if i not in visible)
    show_blocks = "\n".join(
        f"""{_mount_show_sel(i)} {{
    display: block !important;
    visibility: visible !important;
    height: auto !important;
    max-height: none !important;
    overflow: visible !important;
    margin: 0 !important;
    padding: 0 !important;
    pointer-events: auto !important;
    opacity: 1 !important;
    position: relative !important;
}}"""
        for i in sorted(visible)
    )
    transition_shell_css = ""
    if len(visible) > 1:
        # 전환 중 pending 해제 전 — 하단 안내(푸터)만 남는 빈 화면 방지
        transition_shell_css = """
html[data-saju-nav-pending="1"] .st-key-saju_global_bottom_chrome,
html[data-saju-nav-pending="1"] .st-key-saju_bottom_prev_next_row,
html[data-saju-nav-pending="1"] .st-key-saju_bottom_quick_menu_panel,
html[data-saju-nav-pending="1"] .st-key-saju_policy_footer {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    max-height: 0 !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
    pointer-events: none !important;
    opacity: 0 !important;
}
"""
    style_id = f"saju-router-mount-visibility-{s}"
    if len(visible) > 1:
        also_only = sorted(visible - {s})
        if also_only:
            style_id += f"-also-{also_only[0]:02d}"
    st.markdown(
        f"""
<style id="{style_id}">
{hide_sel} {{
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    max-height: 0 !important;
    overflow: hidden !important;
    margin: 0 !important;
    padding: 0 !important;
    pointer-events: none !important;
    opacity: 0 !important;
}}
{show_blocks}
{transition_shell_css}
</style>
""",
        unsafe_allow_html=True,
    )


def inject_step_html_attrs_immediate(step: int, *, scroll_top: bool = False) -> None:
    """(구) 라우터 본문 렌더 전 ``<html data-saju-step>`` 주입 지점. 현재는 no-op.

    이 함수는 ``st.markdown("<script>")`` 로 동작했는데, Streamlit 이 script 를 제거해
    실행되지 않았고(그래서 data-saju-step 이 갱신되지 않아 홈 전용 CSS 가 모든 STEP 에
    적용되는 버그가 있었다), 빈 element-container 가 본문 상단 공백(flex gap)만 키웠다.
    data-saju-step/클래스 세팅과 스크롤은 ``inject_nav_scroll_tail_once``(실행되는
    components.html iframe)가 담당하므로 여기서는 아무것도 렌더하지 않는다.
    """
    return


def sync_step_dom_now(
    step: int | None = None, *, slot: str = "main", reveal: bool = False
) -> None:
    """현재 STEP을 parent ``<html>`` 에 즉시 반영(라우터·finalize 공용).

    ``slot`` 마다 Streamlit ``key`` 를 달리해 동일 rerun 내 중복 key 오류를 막습니다.
    """
    s = max(1, min(12, int(step if step is not None else st.session_state.get("step", 1))))
    safe_slot = re.sub(r"[^a-zA-Z0-9_]", "_", str(slot or "main"))[:48]
    used: list[str] = list(st.session_state.get("_saju_html_sync_slots") or [])
    if safe_slot in used:
        return
    used.append(safe_slot)
    st.session_state["_saju_html_sync_slots"] = used
    hide_js = (
        f"if(typeof pw.__sajuHideStaleStepMounts==='function'){{pw.__sajuHideStaleStepMounts({s});}}"
    )
    trigger_js = (
        "(function(){"
        "const pw=window.parent||window;"
        f"if(typeof pw.__sajuSyncStepToHtml==='function'){{pw.__sajuSyncStepToHtml({s});}}"
        f"{hide_js}"
        "})();"
    )
    # STEP1 라우터 tail — container 없이 script 만 (상단 빈 EC 방지)
    if int(s) == 1 and safe_slot == "router_after_mount":
        st.markdown(f"<script>{trigger_js}</script>", unsafe_allow_html=True)
        return
    with st.container(key=f"saju_step_html_sync_{safe_slot}"):
        st.markdown(f"<script>{trigger_js}</script>", unsafe_allow_html=True)


_HOME_TOP_SNAP_JS = (
    "(function(){"
    "const pw=window.parent&&window.parent!==window?window.parent:window;"
    "const e=pw.document&&pw.document.documentElement;"
    "if(e){e.classList.add('saju-home-step1');e.setAttribute('data-saju-step','1');}"
    "const run=function(){"
    "if(typeof pw.__sajuPhoto2SnapTop==='function'){pw.__sajuPhoto2SnapTop();}"
    "else if(typeof pw.__sajuLockHomeViewportTop==='function'){pw.__sajuLockHomeViewportTop();}"
    "};"
    "run();"
    "try{pw.requestAnimationFrame(run);}catch(e0){}"
    "[40,120,280,560,1100,2000].forEach(function(ms){try{pw.setTimeout(run,ms);}catch(e1){}});"
    "})();"
)


def inject_home_hero_pin_once(*, slot: str = "tail") -> None:
    """STEP1 홈 — 히어로 배너를 뷰포트 최상단에 고정.

    ``finalize``·rerun 마다 tail 슬롯은 항상 재주입(상단 빈 여백 복구).
    """
    if int(st.session_state.get("step", 1)) != 1:
        return
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", str(slot or "tail"))[:24]
    if safe != "tail":
        used: list[str] = list(st.session_state.get("_saju_hero_pin_slots") or [])
        if safe in used:
            return
        used.append(safe)
        st.session_state["_saju_hero_pin_slots"] = used
    st.markdown(f"<script>{_HOME_TOP_SNAP_JS}</script>", unsafe_allow_html=True)


_HOME_LAYOUT_FIX_HTML = """
<script>
(function () {
    const pw =
        window.parent && window.parent !== window ? window.parent : window;
    const doc = pw.document;
    if (!doc) return;
    const root = doc.documentElement;
    // IMPORTANT: 절대 STEP을 강제로 1로 설정하지 않습니다.
    // 홈(STEP1)에서만 동작하도록 가드하고, 다른 STEP에서는 즉시 종료합니다.
    const isHomeNow = function () {
        try {
            if (doc.querySelector(".st-key-saju_router_step_mount_02")) return false;
            if (
                doc.querySelector(
                    ".st-key-saju_router_step_mount_01 .st-key-saju_landing_hero, " +
                        "#saju-home-hero-top"
                )
            ) {
                return true;
            }
            const r = doc.documentElement;
            const stepAttr = r ? String(r.getAttribute("data-saju-step") || "") : "";
            if (stepAttr && stepAttr !== "1") return false;
            if (r && r.classList && r.classList.contains("saju-not-step1")) return false;
            return !!doc.querySelector(".st-key-saju_router_step_mount_01");
        } catch (e) {
            return false;
        }
    };
    if (!isHomeNow()) return;

    // 이전 홈 보정 타이머가 남아있으면 정리
    try {
        (pw.__sajuHomeLayoutFixTimers || []).forEach(function (t) {
            try { pw.clearTimeout(t); } catch (e) {}
        });
    } catch (eClr) {}
    pw.__sajuHomeLayoutFixTimers = [];
    const setTopLayout = function (el, opts) {
        if (!el || !el.style) return;
        try {
            const display = opts && opts.display ? opts.display : "block";
            el.style.setProperty("display", display, "important");
            if (display === "flex") {
                el.style.setProperty("flex-direction", "column", "important");
            }
            el.style.setProperty("justify-content", "flex-start", "important");
            el.style.setProperty("align-items", "stretch", "important");
            el.style.setProperty("align-content", "flex-start", "important");
            el.style.setProperty("min-height", "0", "important");
            el.style.setProperty("height", "auto", "important");
            el.style.setProperty("max-height", "none", "important");
            el.style.setProperty("margin-top", "0", "important");
            el.style.setProperty("padding-top", "0", "important");
            el.style.setProperty("transform", "none", "important");
        } catch (e) {}
    };
    const snapScrollTop = function () {
        [
            doc.querySelector('[data-testid="stAppViewContainer"]'),
            doc.querySelector('[data-testid="stMain"]'),
            doc.querySelector('[data-testid="stMainBlockContainer"]'),
            doc.querySelector("section.main"),
            doc.body,
            doc.scrollingElement,
            doc.documentElement,
        ].forEach(function (el) {
            if (!el) return;
            try {
                el.scrollTop = 0;
                el.scrollLeft = 0;
            } catch (e) {}
        });
        try {
            pw.scrollTo(0, 0);
        } catch (eWin) {}
    };
    const run = function () {
        if (!isHomeNow()) return;
        const mount = doc.querySelector(".st-key-saju_router_step_mount_01");
        const hero = doc.getElementById("saju-home-hero-top");
        const block = doc.querySelector(".main .block-container");
        // 핵심: flex center를 만드는 부모들을 직접 top 정렬로 덮어쓰기
        setTopLayout(doc.querySelector(".stApp"));
        setTopLayout(doc.querySelector('[data-testid="stAppViewContainer"]'));
        setTopLayout(doc.querySelector('[data-testid="stAppViewContainer"] > .main'));
        setTopLayout(doc.querySelector("section.main"));
        setTopLayout(doc.querySelector('[data-testid="stMain"]'));
        setTopLayout(doc.querySelector('[data-testid="stMainBlockContainer"]'));
        if (block) setTopLayout(block);
        if (mount) setTopLayout(mount);
        if (mount) {
            const vb = mount.querySelector('[data-testid="stVerticalBlock"]');
            if (vb) setTopLayout(vb, { display: "flex" });
        }
        snapScrollTop();
        if (typeof pw.__sajuHidePreMountStreamlitBlocks === "function") {
            pw.__sajuHidePreMountStreamlitBlocks();
        }
        if (typeof pw.__sajuLockHomeViewportTop === "function") {
            try {
                pw.__sajuLockHomeViewportTop();
            } catch (eLock) {}
        }
        if (typeof pw.__sajuTranslateHomeContentToTop === "function") {
            try {
                pw.__sajuTranslateHomeContentToTop();
            } catch (eTr) {}
        } else if (typeof pw.__sajuSnapHomeHeroToTop === "function") {
            try {
                pw.__sajuSnapHomeHeroToTop(true);
            } catch (eSnap) {}
        }
        snapScrollTop();
    };
    let needRun = true;
    try {
        const heroProbe = doc.getElementById("saju-home-hero-top");
        const topGap = heroProbe
            ? heroProbe.getBoundingClientRect().top || 0
            : 0;
        if (pw.__sajuHomeLayoutFixApplied && topGap <= 12) {
            needRun = false;
        }
    } catch (eProbe) {}
    if (!needRun) return;
    pw.__sajuHomeLayoutFixApplied = true;
    run();
    try {
        pw.requestAnimationFrame(run);
    } catch (e) {}
    [80, 280, 720].forEach(function (ms) {
        try {
            pw.__sajuHomeLayoutFixTimers.push(
                pw.setTimeout(run, ms)
            );
        } catch (e2) {}
    });
})();
</script>
"""


def inject_home_layout_fix_component() -> None:
    """모바일 WebView — parent DOM 레이아웃 보정(legacy)."""
    inject_home_viewport_lock_component()


def inject_home_photo2_layout_css() -> None:
    """STEP1 mount 안 — 사진2: 배너·24절기·버튼 상단 밀착(매 rerun)."""
    if int(st.session_state.get("step", 1)) != 1:
        return
    st.markdown(
        """
<style id="saju-home-photo2-layout-v10">
/* 사진2 — 상단 flex-center 차단(스크롤 루트는 100dvh 유지) */
/* Cloud: stHeader·block-container 상단 padding 제거 — 배너 최상단 밀착 */
.stApp:has(.st-key-saju_landing_hero) header[data-testid="stHeader"],
.stApp:has(.st-key-saju_router_step_mount_01) header[data-testid="stHeader"],
.stApp:has(.st-key-saju_landing_hero) > header,
.stApp:has(.st-key-saju_router_step_mount_01) > header {
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
  min-height: 0 !important;
  max-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
  pointer-events: none !important;
  position: absolute !important;
  width: 0 !important;
  z-index: -1 !important;
}
.stApp:has(.st-key-saju_landing_hero) .main .block-container,
.stApp:has(.st-key-saju_router_step_mount_01) .main .block-container {
  padding-top: 0 !important;
  margin-top: 0 !important;
}
.stApp:has(.st-key-saju_landing_hero) [data-testid="stAppViewContainer"],
.stApp:has(.st-key-saju_landing_hero) [data-testid="stMainBlockContainer"] {
  padding-top: 0 !important;
  margin-top: 0 !important;
}
.stApp:has(.st-key-saju_landing_hero) .st-key-saju_landing_hero,
.stApp:has(.st-key-saju_landing_hero) #saju-home-hero-top,
.stApp:has(.st-key-saju_landing_hero) .saju-home-hero-banner {
  margin-top: 0 !important;
  padding-top: 0 !important;
}
html:has(.st-key-saju_router_step_mount_01),
html:has(.st-key-saju_router_step_mount_01) body,
html:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"] > .main,
html:has(.st-key-saju_router_step_mount_01) section.main,
html:has(.st-key-saju_router_step_mount_01) [data-testid="stMain"],
html:has(.st-key-saju_router_step_mount_01) [data-testid="stMainBlockContainer"],
.stApp:has(.st-key-saju_router_step_mount_01) .main .block-container,
.stApp:has(.st-key-saju_router_step_mount_01) .main .block-container > [data-testid="stVerticalBlock"],
.stApp:has(.st-key-saju_router_step_mount_01) .main .block-container > [data-testid="stVerticalBlockBorderWrapper"] {
  min-height: 0 !important;
  height: auto !important;
  max-height: none !important;
  display: block !important;
  flex: none !important;
  flex-grow: 0 !important;
  justify-content: flex-start !important;
  align-items: stretch !important;
  align-content: flex-start !important;
  align-self: stretch !important;
  margin-top: 0 !important;
  padding-top: 0 !important;
}
.st-key-saju_router_step_mount_01 [data-testid="stVerticalBlock"] {
  display: flex !important;
  flex-direction: column !important;
  justify-content: flex-start !important;
  align-items: stretch !important;
  gap: 0 !important;
  row-gap: 0 !important;
}
.st-key-saju_landing_stack > [data-testid="stVerticalBlock"] {
  gap: 0.55rem !important;
  row-gap: 0.55rem !important;
}
[data-testid="stElementContainer"][data-stale="true"]:has(.saju-home-hero-banner),
[data-testid="stElementContainer"][data-stale="true"]:has(.st-key-step1_cta_row_main),
[data-testid="stElementContainer"][data-stale="true"]:has(.st-key-step1_cta_row_free),
[data-testid="stElementContainer"][data-stale="true"]:has(.st-key-saju_landing_hero) {
  display: none !important;
  height: 0 !important;
  overflow: hidden !important;
  visibility: hidden !important;
  pointer-events: none !important;
}
#saju-home-hero-top ~ #saju-home-hero-top {
  display: none !important;
}
/* mount 이전 유틸 행만 숨김 (:has — mount 래퍼 EC 는 유지) */
.stApp:has(.st-key-saju_router_step_mount_01) .main .block-container > [data-testid="stVerticalBlock"] {
  display: flex !important;
  flex-direction: column !important;
  justify-content: flex-start !important;
  align-items: stretch !important;
  min-height: 0 !important;
  height: auto !important;
  gap: 0 !important;
  margin-top: 0 !important;
  padding-top: 0 !important;
}
.stApp:has(.st-key-saju_router_step_mount_01) .main .block-container
  > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:not(:has(.st-key-saju_router_step_mount_01)):not(:has(.st-key-saju_global_bottom_chrome)) {
  display: none !important;
  height: 0 !important;
  max-height: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
  visibility: hidden !important;
  pointer-events: none !important;
  position: absolute !important;
  left: -99999px !important;
  width: 0 !important;
}
.stApp:has(.st-key-saju_router_step_mount_01) .main .block-container
  > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(.st-key-saju_router_step_mount_01) {
  display: block !important;
  visibility: visible !important;
  height: auto !important;
  max-height: none !important;
  position: relative !important;
  left: auto !important;
  width: 100% !important;
  opacity: 1 !important;
  pointer-events: auto !important;
}
.stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"],
.stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"] > .main,
.stApp:has(.st-key-saju_router_step_mount_01) section.main,
.stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stMain"],
.stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stMainBlockContainer"],
.stApp:has(.st-key-saju_router_step_mount_01) .main .block-container,
.st-key-saju_router_step_mount_01 {
  display: block !important;
  flex: none !important;
  flex-grow: 0 !important;
  min-height: 0 !important;
  height: auto !important;
  max-height: none !important;
  margin-top: 0 !important;
  padding-top: 0 !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
  justify-content: flex-start !important;
  align-items: stretch !important;
  align-content: flex-start !important;
}
.stApp:has(.st-key-saju_router_step_mount_01) .main .block-container [data-testid="stVerticalBlockBorderWrapper"] {
  display: block !important;
  min-height: 0 !important;
  height: auto !important;
  margin: 0 !important;
  padding: 0 !important;
  flex: none !important;
}
.st-key-saju_router_step_mount_01 [data-testid="stVerticalBlock"] {
  display: flex !important;
  flex-direction: column !important;
  justify-content: flex-start !important;
  align-items: stretch !important;
  min-height: 0 !important;
  gap: 0 !important;
}
.st-key-saju_landing_hero,
.st-key-saju_landing_stack,
.st-key-step1_solar24,
.st-key-step1_cta_row_main,
.st-key-step1_cta_row_free,
.st-key-saju_landing_cta {
  display: block !important;
  visibility: visible !important;
  height: auto !important;
  max-height: none !important;
  opacity: 1 !important;
  pointer-events: auto !important;
  overflow: visible !important;
}
.st-key-saju_router_step_mount_01 .st-key-saju_landing_hero {
  order: 0 !important;
  margin-top: 0 !important;
  padding-top: 0 !important;
}
.st-key-saju_router_step_mount_01 .st-key-saju_landing_stack {
  order: 1 !important;
  margin-top: 0 !important;
  padding-top: 0 !important;
  margin-bottom: 0 !important;
  padding-left: clamp(0.55rem, 3vw, 1.1rem) !important;
  padding-right: clamp(0.55rem, 3vw, 1.1rem) !important;
}
.st-key-saju_router_step_mount_01 .st-key-saju_landing_hero {
  margin-bottom: 0 !important;
  padding-bottom: 0 !important;
}
.st-key-saju_router_step_mount_01 [data-testid="stVerticalBlock"] {
  gap: 0 !important;
  row-gap: 0 !important;
}
html:has(.st-key-saju_router_step_mount_01) body {
  min-height: 0 !important;
  height: auto !important;
}
html:has(.st-key-saju_router_step_mount_01) .stApp {
  height: 100vh !important;
  height: 100dvh !important;
  max-height: 100dvh !important;
  overflow: hidden !important;
}
html:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"] {
  min-height: 0 !important;
  height: 100vh !important;
  height: 100dvh !important;
  max-height: 100dvh !important;
  overflow-y: auto !important;
  overflow-x: hidden !important;
  -webkit-overflow-scrolling: touch !important;
}
.st-key-step1_solar24 iframe {
  display: block !important;
  min-height: 520px !important;
  height: auto !important;
}
.saju-home-hero-banner,
#saju-home-hero-top.saju-home-hero-banner {
  width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
}
.saju-home-hero-banner img,
#saju-home-hero-top.saju-home-hero-banner img {
  display: block !important;
  width: 100% !important;
  height: auto !important;
  margin: 0 !important;
  vertical-align: top !important;
}
@media (max-width: 768px) {
  .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"] {
    display: block !important;
    overflow-y: auto !important;
  }
  .saju-home-hero-banner img,
  #saju-home-hero-top.saju-home-hero-banner img {
    max-height: min(36vh, 220px) !important;
    object-fit: cover !important;
    object-position: center top !important;
  }
}
</style>
""",
        unsafe_allow_html=True,
    )


def inject_home_critical_css_head() -> None:
    """레거시 별칭."""
    inject_home_photo2_layout_css()


def inject_home_viewport_lock_component() -> None:
    """홈 — parent 창에서 배너를 뷰포트 최상단에 고정(모바일 WebView)."""
    if int(st.session_state.get("step", 1)) != 1:
        return
    import streamlit.components.v1 as components

    inject_step_scroll_manager_once()
    nonce = int(st.session_state.get("_saju_home_viewport_lock_nonce", 0)) + 1
    st.session_state["_saju_home_viewport_lock_nonce"] = nonce
    with st.container(key=f"saju_home_viewport_lock_{nonce % 100000}"):
        components.html(_HOME_VIEWPORT_LOCK_HTML, height=0, scrolling=False)


def inject_home_hero_pin_tail() -> None:
    """페이지 tail — 홈 배너·24절기 상단 스냅(모바일 WebView 포함)."""
    inject_home_hero_pin_once(slot="tail")


_HOME_VIEWPORT_LOCK_HTML = """<!DOCTYPE html>
<html lang="ko">
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;height:0;overflow:hidden;">
<script>
(function () {
    const pw =
        window.parent && window.parent !== window ? window.parent : window;
    const doc = pw.document;
    if (!doc) return;
    const run = function () {
        if (typeof pw.__sajuLockHomeViewportTop === "function") {
            return pw.__sajuLockHomeViewportTop();
        }
        if (typeof pw.__sajuSnapHomeHeroToTop === "function") {
            pw.__sajuSnapHomeHeroToTop(true);
        }
        return false;
    };
    let tries = 0;
    const tick = function () {
        tries += 1;
        const ok = run();
        if (ok || tries >= 12) {
            try {
                if (pw.__sajuHomeViewportLockObs) {
                    pw.__sajuHomeViewportLockObs.disconnect();
                    pw.__sajuHomeViewportLockObs = null;
                }
            } catch (eDisc) {}
            return;
        }
        pw.setTimeout(tick, tries < 4 ? 80 : 160);
    };
    tick();
    try {
        const mount = doc.querySelector(".st-key-saju_router_step_mount_01");
        if (mount && typeof ResizeObserver !== "undefined") {
            if (pw.__sajuHomeViewportLockObs) {
                try {
                    pw.__sajuHomeViewportLockObs.disconnect();
                } catch (e0) {}
            }
            pw.__sajuHomeViewportLockObs = new ResizeObserver(function () {
                run();
            });
            pw.__sajuHomeViewportLockObs.observe(mount);
            pw.setTimeout(function () {
                try {
                    if (pw.__sajuHomeViewportLockObs) {
                        pw.__sajuHomeViewportLockObs.disconnect();
                        pw.__sajuHomeViewportLockObs = null;
                    }
                } catch (e1) {}
            }, 4000);
        }
    } catch (eObs) {}
})();
</script>
</body>
</html>
"""


def inject_home_top_snap_head() -> None:
    """홈 렌더 직후 — 배너·24절기 DOM 붙은 뒤 상단 고정."""
    if int(st.session_state.get("step", 1)) != 1:
        return
    inject_step_scroll_manager_once()
    st.markdown(f"<script>{_HOME_TOP_SNAP_JS}</script>", unsafe_allow_html=True)


def inject_home_top_snap_tail_force() -> None:
    """finalize — 매 rerun 홈 상단 스냅(early-return 이전에도 tail에서 1회 호출)."""
    if int(st.session_state.get("step", 1)) != 1:
        return
    inject_step_scroll_manager_once()
    st.markdown(f"<script>{_HOME_TOP_SNAP_JS}</script>", unsafe_allow_html=True)


def finalize_scroll_to_top_if_needed() -> None:
    """페이지 최하단 — STEP 본문·하단 네비 렌더 후 최상단 스크롤(레이아웃 안정화)."""
    if int(st.session_state.get("step", 1)) == 1:
        inject_step_scroll_manager_once()
    nav_epoch = int(st.session_state.get("saju_nav_epoch", 0))
    try:
        scrolled_epoch = int(st.session_state.get("_saju_scrolled_nav_epoch", -1))
    except Exception:
        scrolled_epoch = -1
    pending = step_scroll_is_pending()
    step = int(st.session_state.get("step", 1))

    if int(step) == 1:
        if not pending and scrolled_epoch == nav_epoch:
            inject_cancel_step_scroll_lock()
            mark_scroll_completed_for_current_nav()
            return
        inject_home_top_snap_tail_force()
        st.session_state.pop("_saju_nav_from_step", None)
        _pop_force_scroll_nav_opts()
        sync_step_nav_scroll_at_page_tail()
        if pending or scrolled_epoch != nav_epoch:
            inject_nav_scroll_tail_once(nav_epoch=nav_epoch)
        mark_scroll_completed_for_current_nav()
        return

    if int(step) == 2:
        if st.session_state.pop("_saju_widget_skip_finalize_scroll", False):
            inject_cancel_step_scroll_lock()
            mark_scroll_completed_for_current_nav()
            return
        if st.session_state.pop("_saju_nav_preserve_scroll", False):
            inject_cancel_step_scroll_lock()
            mark_scroll_completed_for_current_nav()
            return
        if not pending:
            inject_cancel_step_scroll_lock()
            mark_scroll_completed_for_current_nav()
            return

    if st.session_state.pop("_saju_widget_skip_finalize_scroll", False):
        inject_cancel_step_scroll_lock()
        mark_scroll_completed_for_current_nav()
        return

    if not pending:
        inject_cancel_step_scroll_lock()
        mark_scroll_completed_for_current_nav()
        return

    nav_from_step: int | None = None
    try:
        fs = int(st.session_state.get("_saju_nav_from_step") or 0)
        if 1 <= fs <= 12 and fs != int(step):
            nav_from_step = fs
    except Exception:
        nav_from_step = None
    st.session_state.pop("_saju_nav_from_step", None)
    _pop_force_scroll_nav_opts()
    sync_step_nav_scroll_at_page_tail()
    inject_nav_scroll_tail_once(nav_epoch=nav_epoch, from_step=nav_from_step)
    mark_scroll_completed_for_current_nav()


def rerun_full_app() -> NoReturn:
    st.rerun(scope="app")


def report_exception_to_streamlit(exc: BaseException, *, prefix: str = "오류 발생") -> None:
    st.error(f"{prefix}: {exc}")
    st.code(traceback.format_exc(), language="python")


def inject_home_scroll_after_solar24() -> None:
    """24절기 iframe 직후 — 높이만 맞춤(스크롤 위치·홈 뷰포트 재실행 없음)."""
    if int(st.session_state.get("step", 1)) != 1:
        return
    _trigger_home_solar_iframe_fit_js()
