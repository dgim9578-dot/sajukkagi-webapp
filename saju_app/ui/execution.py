"""Streamlit 실행 제어 헬퍼 (1.38+).

STEP(다음/이전) 이동 시 최상단 스크롤:
  1) bootstrap 에서 parent 창에 전역 매니저 1회 설치 (rerun 후에도 유지)
  2) STEP 전환 시 매니저 호출 + st_javascript 백업
"""

from __future__ import annotations

import re
import traceback
from typing import NoReturn

import streamlit as st
import streamlit.components.v1 as components

# parent(window) 에 1회 설치 — STEP 전환 시 가벼운 최상단 스크롤만 (잠금·MO 없음)
_SCROLL_MANAGER_JS = r"""
(function () {
    const pw = window.parent || window;
    if (pw.__sajuStepScrollMgrV21) return;
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
            'iframe[title="streamlit"]',
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
        if (/samsung|sm-[a-z]|galaxy/i.test(ua)) {
            root.classList.add("saju-platform-galaxy");
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

    pw.__sajuSyncStepToHtml = function (step) {
        const doc = pw.document || document;
        const root = doc && doc.documentElement;
        if (!root) return;
        const n = String(step == null ? "" : step);
        root.setAttribute("data-saju-step", n);
        root.classList.remove("saju-home-step1", "saju-not-step1");
        if (n === "1") {
            root.classList.add("saju-home-step1");
        } else if (n) {
            root.classList.add("saju-not-step1");
        }
    };

    pw.__sajuRevealMainContent = function (force) {
        const doc = pw.document || document;
        if (!doc) return;
        const mobile = isMobileView(pw, doc);
        const now = Date.now();
        if (!force && mobile && pw.__sajuRevealLastAt && now - pw.__sajuRevealLastAt < 2500) {
            return;
        }
        pw.__sajuRevealLastAt = now;
        const show = function (el) {
            if (!el || !el.style) return;
            if (el.closest("[class*='saju_scroll_fire_']")) return;
            if (el.closest(".st-key-saju_browser_privacy_client_v2")) return;
            if (el.closest(".st-key-saju_browser_nav_check")) return;
            try {
                el.style.removeProperty("display");
                el.style.removeProperty("visibility");
                el.style.removeProperty("height");
                el.style.removeProperty("max-height");
                el.style.removeProperty("min-height");
                el.style.removeProperty("opacity");
                el.style.removeProperty("position");
                el.style.removeProperty("left");
                el.style.removeProperty("top");
                el.style.removeProperty("pointer-events");
            } catch (e) {}
        };
        try {
            doc.querySelectorAll(
                "[class*='st-key-saju_router_step_mount_'], " +
                    ".st-key-saju_landing_stack, .st-key-saju_landing_hero, .saju-landing-hero"
            ).forEach(show);
        } catch (e) {}
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

    pw.__sajuPinHomeHeroTop = function () {
        const doc = pw.document || document;
        const root = doc && doc.documentElement;
        if (!root) return;
        const onHome =
            root.classList.contains("saju-home-step1") ||
            String(root.getAttribute("data-saju-step") || "") === "1" ||
            !!doc.querySelector(".st-key-saju_landing_stack");
        if (!onHome) return;

        if (typeof pw.__sajuCollapseHomeTopChrome === "function") {
            pw.__sajuCollapseHomeTopChrome(doc);
        }

        const stack = doc.querySelector(".st-key-saju_landing_stack");
        const heroWrap = doc.querySelector(".st-key-saju_landing_hero");
        const hero =
            doc.querySelector(".st-key-saju_landing_hero .saju-landing-hero") ||
            doc.querySelector(".saju-landing-hero--luxe, .saju-landing-hero--face");

        if (stack) {
            stack.style.setProperty("padding-top", "0", "important");
        }
        if (heroWrap) {
            heroWrap.style.setProperty("margin-top", "0", "important");
            heroWrap.style.setProperty("padding-top", "0", "important");
        }
        if (hero) {
            hero.style.setProperty("justify-content", "flex-start", "important");
            hero.style.setProperty("min-height", "auto", "important");
            hero.style.setProperty("padding-top", "0", "important");
        }
        doc.querySelectorAll(
            ".st-key-saju_router_step_mount_01 [data-testid='stElementContainer'], " +
                ".st-key-saju_landing_stack [data-testid='stElementContainer'], " +
                ".st-key-saju_landing_hero [data-testid='stElementContainer']"
        ).forEach(function (el) {
            el.style.setProperty("padding-top", "0", "important");
            el.style.setProperty("margin-top", "0", "important");
        });

        if (stack && hero && !isMobileView(pw, doc)) {
            try {
                const rect = hero.getBoundingClientRect();
                const gap = Math.ceil(rect.top || 0);
                if (gap > 2 && gap < 120) {
                    stack.style.setProperty("margin-top", "-" + gap + "px", "important");
                }
            } catch (e) {}
        } else if (stack) {
            try {
                stack.style.setProperty("margin-top", "0", "important");
            } catch (e) {}
        }

        const mainEl = getMainScrollEl(doc);
        const mobilePin = isMobileView(pw, doc);
        const userScrolled = !!(mainEl && mainEl.scrollTop > 48);
        if (!mobilePin || !userScrolled) {
            if (typeof pw.__sajuScrollHomeTopOnce === "function") {
                pw.__sajuScrollHomeTopOnce();
            }
        }
    };

    const getMainScrollEl = function (doc) {
        return (
            doc.querySelector('[data-testid="stAppViewContainer"]') ||
            doc.querySelector('[data-testid="stMainBlockContainer"]') ||
            doc.querySelector('[data-testid="stMain"]') ||
            doc.scrollingElement ||
            doc.documentElement
        );
    };

    pw.__sajuUserIsScrolling = false;
    pw.__sajuBindUserScrollGuard = function () {
        if (pw.__sajuUserScrollGuardBound) return;
        pw.__sajuUserScrollGuardBound = true;
        const doc = pw.document || document;
        if (!doc) return;
        const markUserScroll = function () {
            if (pw.__sajuStepNavScrollActive) return;
            pw.__sajuUserIsScrolling = true;
            if (pw.__sajuUserScrollTimer) {
                try { clearTimeout(pw.__sajuUserScrollTimer); } catch (e) {}
            }
            pw.__sajuUserScrollTimer = pw.setTimeout(function () {
                pw.__sajuUserIsScrolling = false;
            }, 450);
        };
        const mobile = isMobileView(pw, doc);
        const events = mobile
            ? ["touchstart", "touchmove"]
            : ["touchstart", "touchmove", "wheel"];
        events.forEach(function (ev) {
            doc.addEventListener(ev, markUserScroll, { passive: true, capture: true });
        });
    };
    pw.__sajuBindUserScrollGuard();

    pw.__sajuForceStepScrollTop = function (epoch, lockMs) {
        const doc = pw.document || document;
        const mobile = isMobileView(pw, doc);
        const epochKey = String(epoch || "0");

        if (pw.__sajuLastScrollEpoch === epochKey && pw.__sajuLastScrollAt) {
            const since = Date.now() - pw.__sajuLastScrollAt;
            if (since < (mobile ? 900 : 400)) return;
        }
        pw.__sajuLastScrollEpoch = epochKey;
        pw.__sajuLastScrollAt = Date.now();

        if (typeof pw.__sajuCancelStepScroll === "function") {
            try { pw.__sajuCancelStepScroll(); } catch (e) {}
        }

        let cancelled = false;
        const timers = [];
        const holdMs = mobile
            ? 220
            : Math.min(600, Math.max(320, Number(lockMs) || 400));

        pw.__sajuStepNavScrollActive = true;
        pw.__sajuCancelStepScroll = function () {
            cancelled = true;
            pw.__sajuStepNavScrollActive = false;
            timers.forEach(function (id) {
                try { clearTimeout(id); } catch (e) {}
            });
            timers.length = 0;
            pw.__sajuCancelStepScroll = null;
        };

        const snap = function () {
            if (cancelled) return;
            const main = getMainScrollEl(doc);
            if (!main) return;
            try { main.scrollTop = 0; main.scrollLeft = 0; } catch (e) {}
            if (!mobile) {
                try {
                    if (typeof main.scrollTo === "function") {
                        main.scrollTo({ top: 0, left: 0, behavior: "auto" });
                    }
                } catch (e) {}
                const anchor = doc.getElementById("saju-step-top-anchor");
                if (anchor) {
                    try {
                        anchor.scrollIntoView({
                            block: "start",
                            inline: "nearest",
                            behavior: "auto",
                        });
                    } catch (e) {}
                }
            }
        };

        snap();
        if (mobile) {
            timers.push(setTimeout(snap, 96));
        } else {
            try { requestAnimationFrame(snap); } catch (e) { timers.push(setTimeout(snap, 16)); }
            timers.push(setTimeout(snap, 120));
        }
        timers.push(setTimeout(function () {
            pw.__sajuStepNavScrollActive = false;
            if (typeof pw.__sajuCancelStepScroll === "function") {
                pw.__sajuCancelStepScroll();
            }
        }, holdMs));
    };

    pw.__sajuApplySolar24IframeHeight = function (heightPx) {
        const doc = pw.document || document;
        const solarWrap = doc.querySelector(".st-key-step1_solar24");
        if (!solarWrap) return;
        const iframe = solarWrap.querySelector("iframe");
        if (!iframe) return;
        const mobile = isMobileView(pw, doc);
        const floor = mobile ? 500 : 480;
        const cap = mobile ? 640 : 560;
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
        const floor = mobile ? (galaxy ? 520 : 500) : 480;
        const cap = mobile ? (galaxy ? 680 : 640) : 560;
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
            budget = Math.min(cap, Math.max(floor, contentH + 20));
        } else {
            const viewH = pw.innerHeight || doc.documentElement.clientHeight || 740;
            const hero = doc.querySelector(".saju-landing-hero");
            const heroH = hero ? hero.getBoundingClientRect().height : 140;
            const chrome = mobile ? 48 : 44;
            const maxBudget = viewH - heroH - chrome - 4;
            budget = Math.max(floor, Math.min(cap, maxBudget));
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

    /* 홈 진입 — 모바일은 1회만, PC는 보조 snap 허용 */
    pw.__sajuScrollHomeTopOnce = function () {
        if (pw.__sajuUserIsScrolling) return;
        const doc = pw.document || document;
        const mobile = isMobileView(pw, doc);
        const main = getMainScrollEl(doc);
        if (main) {
            try { main.scrollTop = 0; main.scrollLeft = 0; } catch (e) {}
            if (!mobile) {
                try { main.scrollTo({ top: 0, left: 0, behavior: "auto" }); } catch (e) {}
            }
        }
        if (!mobile) {
            try { pw.scrollTo(0, 0); } catch (e) {}
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
        if (typeof pw.__sajuPinHomeHeroTop === "function") {
            pw.__sajuPinHomeHeroTop();
        }
        pw.__sajuFitHomeSolar24Iframe();
        if (!pw.__sajuUserIsScrolling) {
            pw.__sajuScrollHomeTopOnce();
        }
        if (mobile) return;
        try {
            [80, 240].forEach(function (ms) {
                pw.setTimeout(function () {
                    if (pw.__sajuUserIsScrolling) return;
                    if (typeof pw.__sajuPinHomeHeroTop === "function") {
                        pw.__sajuPinHomeHeroTop();
                    }
                }, ms);
            });
        } catch (e) {}
    };
})();
"""

_ST_JS_CALL_MANAGER = """
(function () {
    const pw = (window.parent && window.parent !== window) ? window.parent : window;
    const doc = pw.document || document;
    const epoch = __NAV_EPOCH__;
    const lockMs = __LOCK_MS__;

    if (typeof pw.__sajuForceStepScrollTop === "function") {
        pw.__sajuForceStepScrollTop(epoch, lockMs);
    }

    const main =
        doc.querySelector('[data-testid="stAppViewContainer"]') ||
        doc.querySelector('[data-testid="stMainBlockContainer"]');
    if (main) {
        try { main.scrollTop = 0; } catch (e) {}
        try { main.scrollTo({ top: 0, left: 0, behavior: "auto" }); } catch (e) {}
    }
    try { pw.scrollTo(0, 0); } catch (e) {}

    return main ? (main.scrollTop || 0) : 0;
})()
"""

_LOCK_MS = 400
_LOCK_MS_MOBILE = 220


def inject_step_scroll_manager_once() -> None:
    """parent 창 전역 스크롤 매니저 — 세션당 1회."""
    if st.session_state.get("_saju_scroll_mgr_v21"):
        return
    st.session_state["_saju_scroll_mgr_v21"] = True
    st.session_state.pop("_saju_scroll_mgr_v20", None)
    st.session_state.pop("_saju_scroll_mgr_v19", None)
    st.session_state.pop("_saju_scroll_mgr_v18", None)
    st.session_state.pop("_saju_scroll_mgr_v17", None)
    st.session_state.pop("_saju_scroll_mgr_v16", None)
    st.session_state.pop("_saju_scroll_mgr_v15", None)
    st.session_state.pop("_saju_scroll_mgr_v8", None)
    st.session_state.pop("_saju_scroll_mgr_v7", None)
    st.session_state.pop("_saju_scroll_mgr_v6", None)
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
        f"<script>{_SCROLL_MANAGER_JS}</script></body></html>"
    )
    components.html(html, height=1, scrolling=False)


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
    const VERSION = 14;
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

    function safeToPatchMonths() {
        if (onStep2BirthPage() && !step2HasCalendar()) return false;
        return true;
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
        getDocs().forEach(function (d) {
            d.querySelectorAll(
                ".st-key-step2_u_time_wrap, .st-key-step2_p_time_wrap"
            ).forEach(function (wrap) {
                const options = wrap.querySelectorAll(
                    '[data-baseweb="popover"] [role="option"], ' +
                        '[data-baseweb="select-dropdown"] [role="option"], ' +
                        '[data-baseweb="menu"] [role="option"], ' +
                        '[role="listbox"] [role="option"]'
                );
                options.forEach(function (el, idx) {
                    if (idx >= BIRTH_TIME_LABELS.length) return;
                    const label = BIRTH_TIME_LABELS[idx];
                    el.setAttribute("data-saju-birth-time", "1");
                    el.removeAttribute("data-saju-month-num");
                    try {
                        setPlainText(el, label);
                        el.style.removeProperty("font-size");
                        el.style.removeProperty("color");
                    } catch (e) {}
                });
                wrap.querySelectorAll(
                    '[data-baseweb="select-value"], [class*="SelectValue"], [class*="select__single-value"]'
                ).forEach(function (node) {
                    const t = String(node.textContent || "").trim();
                    if (/^\d{1,2}\.?$/.test(t)) return;
                    for (let i = 0; i < BIRTH_TIME_LABELS.length; i++) {
                        const lab = BIRTH_TIME_LABELS[i];
                        if (t === lab || (t && lab.indexOf(t) === 0)) {
                            try { setPlainText(node, lab); } catch (e2) {}
                            break;
                        }
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
            if (shouldSkipMonthPatchRoot(el)) return;
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
        restoreBirthTimeSelectLabels();
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
                function () {
                    schedulePatch();
                    if (onStep2BirthPage() && !step2HasCalendar()) {
                        fixStep2FormRows();
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
    """parent 창에 달력 locale v14 설치(세션당 1회)."""
    if st.session_state.get("_saju_calendar_install_v14"):
        return
    st.session_state["_saju_calendar_install_v14"] = True
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
    with st.container(key="saju_calendar_locale_install_v14"):
        components.html(html, height=1, scrolling=False)


def inject_calendar_weekday_en_once() -> None:
    """date_input 달력: 요일 Su~Sa, 월 1월~12월 — 앱 기동·STEP2 공용."""
    inject_calendar_locale_installer_once()
    nudge_calendar_locale_patch(slot="global_install")


def ensure_calendar_locale_on_step2() -> None:
    """STEP2 화면 진입 시 달력 locale 매니저 설치 + 즉시 패치."""
    inject_calendar_locale_installer_once()
    nudge_calendar_locale_patch(slot="step2_boot")


def protect_step2_birth_time_selects() -> None:
    """STEP2 태어난 시간 selectbox — 달력 월 패치가 건드리지 않도록 보호."""
    inject_calendar_locale_installer_once()
    trigger_js = (
        "(function(){"
        "const pw=window.parent||window;"
        "if(typeof pw.__sajuMarkBirthTimeSelects==='function'){pw.__sajuMarkBirthTimeSelects();}"
        "if(typeof pw.__sajuRestoreBirthTimeSelectLabels==='function'){pw.__sajuRestoreBirthTimeSelectLabels();}"
        "if(typeof pw.__sajuCalendarPatchNow==='function'){pw.__sajuCalendarPatchNow();}"
        "})();"
    )
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
        f"<script>{trigger_js}</script></body></html>"
    )
    with st.container(key="saju_step2_time_protect"):
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
    st.markdown(
        (
            '<mtop id="saju-step-top-anchor" '
            'style="position:relative;width:1px;height:1px;margin:0;padding:0;'
            'overflow:hidden;scroll-margin-top:0;" aria-hidden="true"></mtop>'
        ).replace("mtop", "div"),
        unsafe_allow_html=True,
    )


def _fire_step_scroll_to_top(nav_epoch: int, *, phase: str = "late") -> None:
    """STEP 전환 — 전역 매니저 호출(early=본문 전, late=본문 후 재시도)."""
    epoch = int(nav_epoch)
    phase_tag = f"{epoch}:{phase}"
    if st.session_state.get("_saju_scroll_phase_fired") == phase_tag:
        return
    st.session_state["_saju_scroll_phase_fired"] = phase_tag
    st.session_state["_saju_scroll_widgets_fired"] = epoch

    lock_ms = int(st.session_state.get("_saju_step_scroll_lock_ms", _LOCK_MS))

    trigger_js = (
        f"(function(){{"
        f"const pw=window.parent||window;"
        f"if(typeof pw.__sajuCancelStepScroll==='function'){{pw.__sajuCancelStepScroll();}}"
        f"if(typeof pw.__sajuForceStepScrollTop==='function'){{"
        f"pw.__sajuForceStepScrollTop({epoch},{lock_ms});"
        f"}}}})();"
    )
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
        f"<script>{trigger_js}</script></body></html>"
    )
    with st.container(key=f"saju_scroll_fire_{epoch}_{phase}"):
        components.html(html, height=1, scrolling=False)


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
    "u_time",
    "u_contact",
)
_STEP2_TAB_ORDER_OPP = (
    "step2_opp_name_input",
    "p_gender",
    "step2_p_bdate_text",
    "p_lunar",
    "p_time",
)
_STEP2_TAB_ORDER_SAVE = (
    "agree",
    "step2_revisit_pin",
    "step2_revisit_pin_confirm",
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
    """STEP2 Tab 순서 — parent 문서에 1회 설치 (st.markdown, iframe 우회)."""
    if st.session_state.get("_saju_step2_tab_mgr_v11"):
        return
    st.session_state["_saju_step2_tab_mgr_v11"] = True
    order_js = _step2_tab_order_json()
    mgr_js = _STEP2_TAB_MANAGER_JS.replace("__ORDER_JSON__", order_js)
    st.markdown(f"<script>{mgr_js}</script>", unsafe_allow_html=True)


_STEP2_TAB_MANAGER_JS = r"""
(function () {
  const pw = window.parent !== window ? window.parent : window;
  const ORDER = __ORDER_JSON__;
  const SCOPE_SEL =
    ".st-key-step2_navertone_self, .st-key-step2_navertone_opp, .st-key-step2_save_actions";

  pw.__sajuStep2TabOrder = ORDER;

  if (pw.__sajuStep2TabMgrV11) {
    if (typeof pw.__sajuStep2TabRefresh === "function") pw.__sajuStep2TabRefresh();
    return;
  }
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
    try {
      el.scrollIntoView({ block: "nearest", inline: "nearest", behavior: "auto" });
    } catch (e) {}
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
    forEachDoc((doc) => {
      doc.querySelectorAll(SCOPE_SEL).forEach((scope) => {
        scope
          .querySelectorAll(
            "button, a, select, textarea, input, summary, [tabindex]"
          )
          .forEach((el) => {
            if (chainCache.indexOf(el) >= 0) return;
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
      if (isEditingInScope()) return;
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
          scheduleRefresh();
        }, 140);
      });
      obs.observe(root, { childList: true, subtree: true });
    }
  } catch (e) {}

  scheduleRefresh();
})();
"""


def inject_step2_tab_order_once() -> None:
    """STEP2 정보 입력 — Tab/다음 키로 성함→년월일→시간→… 순서 이동."""
    inject_step2_tab_manager_global_once()
    order_js = _step2_tab_order_json()
    bump_js = f"""
(function() {{
  const pw = window.parent !== window ? window.parent : window;
  const order = {order_js};
  pw.__sajuStep2TabOrder = order;
  if (typeof pw.__sajuStep2TabSetOrder === "function") pw.__sajuStep2TabSetOrder(order);
  else if (typeof pw.__sajuStep2TabRefresh === "function") pw.__sajuStep2TabRefresh();
}})();
"""
    st.markdown(f"<script>{bump_js}</script>", unsafe_allow_html=True)
    token = int(st.session_state.get("_saju_step2_tab_order_token", 0)) + 1
    st.session_state["_saju_step2_tab_order_token"] = token
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
        f"<script>{bump_js}</script></body></html>"
    )
    with st.container(key=f"saju_step2_tab_order_{token}"):
        components.html(html, height=1, scrolling=False)


def queue_widget_focus(widget_key: str, *, kind: str = "control") -> None:
    """rerun 후 방금 조작한 위젯(버튼·접이식·입력)으로 포커스·스크롤 위치 복귀."""
    wk = str(widget_key or "").strip()
    if not wk:
        return
    st.session_state["_saju_focus_return_key"] = wk
    st.session_state["_saju_focus_return_kind"] = str(kind or "control")
    st.session_state["_saju_nav_preserve_scroll"] = True


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
      target.scrollIntoView({{ block: "nearest", inline: "nearest", behavior: "auto" }});
      target.focus({{ preventScroll: true }});
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
    inject_cancel_step_scroll_lock_once()


def inject_cancel_step_scroll_lock_once() -> None:
    """기능 바로가기 등 — 이전 STEP 전환의 스크롤 잠금 해제."""
    if st.session_state.get("_saju_cancel_scroll_lock_injected"):
        return
    st.session_state["_saju_cancel_scroll_lock_injected"] = True
    st.markdown(
        "<script>(function(){const pw=window.parent||window;"
        "if(typeof pw.__sajuCancelStepScroll==='function'){pw.__sajuCancelStepScroll();}"
        "if(typeof pw.__sajuCancelHomeViewport==='function'){pw.__sajuCancelHomeViewport();}"
        "})();</script>",
        unsafe_allow_html=True,
    )


def _home_viewport_is_pending() -> bool:
    """홈 최상단 스크롤 — 홈으로 이동·새로고침 시에만(매 rerun 반복 금지)."""
    if int(st.session_state.get("step", 1)) != 1:
        return False
    return bool(st.session_state.get("_saju_apply_home_viewport"))


def _next_home_viewport_token() -> int:
    n = int(st.session_state.get("_saju_home_viewport_token", 0)) + 1
    st.session_state["_saju_home_viewport_token"] = n
    return n


def _trigger_home_solar_iframe_fit_js() -> None:
    """24절기 iframe 높이만 조정 — 스크롤 위치는 변경하지 않습니다."""
    trigger_js = (
        "(function(){"
        "const pw=window.parent||window;"
        "if(typeof pw.__sajuFitHomeSolar24Iframe==='function'){"
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


def _fire_step1_home_viewport() -> None:
    """STEP1 홈 진입 시 1회 — 최상단으로만 이동(스크롤 잠금 없음)."""
    token = _next_home_viewport_token()
    if st.session_state.get("_saju_home_scroll_widgets_fired") == token:
        return
    st.session_state["_saju_home_scroll_widgets_fired"] = token

    trigger_js = (
        "(function(){"
        "const pw=window.parent||window;"
        "if(typeof pw.__sajuForceHomeViewport==='function'){"
        f"pw.__sajuForceHomeViewport({token},0);"
        "}else{"
        "if(typeof pw.__sajuScrollHomeTopOnce==='function'){pw.__sajuScrollHomeTopOnce();}"
        "if(typeof pw.__sajuFitHomeSolar24Iframe==='function'){pw.__sajuFitHomeSolar24Iframe();}"
        "}"
        "})();"
    )
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
        f"<script>{trigger_js}</script></body></html>"
    )
    with st.container(key=f"saju_home_viewport_{token}"):
        components.html(html, height=1, scrolling=False)

    st.session_state["_saju_home_viewport_done"] = True
    st.session_state.pop("_saju_apply_home_viewport", None)


def inject_step_dom_boot_once() -> None:
    """앱 기동 직후 — STEP·본문 표시(모바일 빈 화면 방지)."""
    if st.session_state.get("_saju_step_dom_boot_v1"):
        return
    st.session_state["_saju_step_dom_boot_v1"] = True
    inject_step_scroll_manager_once()
    step = max(1, min(12, int(st.session_state.get("step", 1))))
    boot_js = (
        "(function(){"
        "const pw=window.parent||window;"
        f"if(typeof pw.__sajuSyncStepToHtml==='function'){{pw.__sajuSyncStepToHtml({step});}}"
        "if(typeof pw.__sajuRevealMainContent==='function'){pw.__sajuRevealMainContent(true);}"
        "})();"
    )
    st.markdown(f"<script>{boot_js}</script>", unsafe_allow_html=True)


def sync_step_dom_now(
    step: int | None = None, *, slot: str = "main", reveal: bool = False
) -> None:
    """현재 STEP을 parent ``<html>`` 에 즉시 반영(라우터·finalize 공용).

    ``slot`` 마다 Streamlit ``key`` 를 달리해 동일 rerun 내 중복 key 오류를 막습니다.
    """
    s = max(1, min(12, int(step if step is not None else st.session_state.get("step", 1))))
    safe_slot = re.sub(r"[^a-zA-Z0-9_]", "_", str(slot or "main"))[:48]
    reveal_js = (
        "if(typeof pw.__sajuRevealMainContent==='function'){pw.__sajuRevealMainContent(true);}"
        if reveal
        else ""
    )
    trigger_js = (
        "(function(){"
        "const pw=window.parent||window;"
        f"if(typeof pw.__sajuSyncStepToHtml==='function'){{pw.__sajuSyncStepToHtml({s});}}"
        f"{reveal_js}"
        "})();"
    )
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
        f"<script>{trigger_js}</script></body></html>"
    )
    with st.container(key=f"saju_step_html_sync_{safe_slot}"):
        components.html(html, height=1, scrolling=False)


def prime_step_navigation_viewport(*, step: int) -> None:
    """STEP 본문 렌더 전 — 모바일 깜박임 방지를 위해 스크롤은 finalize 1회만."""
    return


def _inject_home_chrome_tail_once() -> None:
    """STEP1 홈 진입 1회 — 히어로 정렬(매 rerun 호출 시 모바일 깜박임)."""
    if st.session_state.get("_saju_home_chrome_tail_done"):
        return
    st.session_state["_saju_home_chrome_tail_done"] = True
    home_nav = True
    scroll_home_js = (
        "if(!pw.__sajuUserIsScrolling&&typeof pw.__sajuScrollHomeTopOnce==='function')"
        "{pw.__sajuScrollHomeTopOnce();}"
        if home_nav
        else ""
    )
    trigger_js = (
        "(function(){"
        "const pw=window.parent||window;"
        "const doc=pw.document||document;"
        "if(typeof pw.__sajuCollapseHomeTopChrome==='function'){"
        "pw.__sajuCollapseHomeTopChrome(doc);"
        "}"
        "if(typeof pw.__sajuPinHomeHeroTop==='function'){pw.__sajuPinHomeHeroTop();}"
        f"{scroll_home_js}"
        "})();"
    )
    html = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
        "<body style='margin:0;padding:0;height:1px;overflow:hidden;'>"
        f"<script>{trigger_js}</script></body></html>"
    )
    with st.container(key="saju_step_home_tail_sync"):
        components.html(html, height=1, scrolling=False)


def inject_sync_step_to_html() -> None:
    """레거시 호환 — 홈 크롬 보정만 필요 시 호출."""
    if int(st.session_state.get("step", 1)) == 1 and _home_viewport_is_pending():
        _inject_home_chrome_tail_once()


def finalize_scroll_to_top_if_needed() -> None:
    """페이지 최하단 — STEP1 홈 뷰포트 또는 STEP 전환 후 최상단 스크롤."""
    if st.session_state.pop("_saju_cancel_active_scroll_lock", False):
        inject_cancel_step_scroll_lock_once()

    step = int(st.session_state.get("step", 1))
    if step == 1:
        if _home_viewport_is_pending():
            sync_step_dom_now(step, slot="finalize_home")
            _inject_home_chrome_tail_once()
            _fire_step1_home_viewport()
        return

    if not step_scroll_is_pending():
        return

    nav_epoch = int(st.session_state.get("saju_nav_epoch", 0))
    try:
        if int(st.session_state.get("_saju_scrolled_nav_epoch", -1)) == nav_epoch:
            _clear_step_scroll_pending()
            return
    except Exception:
        pass

    _fire_step_scroll_to_top(nav_epoch, phase="late")
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
