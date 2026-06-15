"""Streamlit 최초 설정: `set_page_config` + 전역 CSS.

다크/라이트 테마는 `.streamlit/config.toml`의 `[theme.light]` / `[theme.dark]`
(Deep Luxury Dark + Gold / 크림·골드 라이트) 및 앱 우상단 ⋮ → Settings → Theme 에서 전환합니다.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import streamlit as st

_BOOTSTRAP_CSS_FILENAME = "saju_bootstrap.css"
# 프로세스 1회만 디스크 기록하도록 마지막 기록 해시 캐시
_bootstrap_css_state: dict[str, str] = {}


def _project_static_dir() -> Path:
    """``/app/static`` 로 서빙되는 프로젝트 루트 ``static/`` 디렉터리."""
    return Path(__file__).resolve().parents[1] / "static"


def _streamlit_cloud_deploy() -> bool:
    """Streamlit Community Cloud 등 배포 환경 여부(로컬 ``streamlit run`` 과 구분)."""
    import os
    from pathlib import Path

    try:
        import streamlit as st

        flag = str(st.secrets.get("saju_deploy_inline_css", "")).strip().lower()
        if flag in ("1", "true", "yes", "cloud", "inline"):
            return True
        if flag in ("0", "false", "no", "local", "link"):
            return False
    except Exception:
        pass

    if Path("/mount/src/app.py").is_file() or Path("/mount/src").is_dir():
        return True

    blob = " ".join(
        str(os.environ.get(k, "") or "")
        for k in (
            "HOSTNAME",
            "STREAMLIT_SERVER_ADDRESS",
            "STREAMLIT_RUNTIME_ENV",
            "STREAMLIT_SHARING",
            "IS_STREAMLIT_CLOUD",
        )
    ).lower()
    return "streamlit.app" in blob or "streamlit-cloud" in blob


def _inject_bootstrap_global_css(head_html: str) -> None:
    """거대한 정적 ``<style>`` 블록을 주입한다.

    로컬: ``/app/static/saju_bootstrap.css`` 링크(브라우저 캐시) 우선.
    Cloud: ``enableStaticServing`` 이 배포 번들만 서빙하거나 링크가 404 HTML 을
    돌려주면 MIME 오류로 **전역 CSS 전체가 미적용** → 상단 대공백·레이아웃 붕괴.
    배포 환경에서는 항상 인라인 ``<style>`` 을 사용한다.
    """
    try:
        marker_open = "<style>"
        marker_close = "</style>"
        start = head_html.index(marker_open) + len(marker_open)
        end = head_html.index(marker_close, start)
        css = head_html[start:end]
        rest = head_html[end + len(marker_close):]  # 뒤따르는 <script> 등은 그대로 유지
        digest = hashlib.md5(css.encode("utf-8")).hexdigest()[:12]
        static_dir = _project_static_dir()
        css_path = static_dir / _BOOTSTRAP_CSS_FILENAME
        if _bootstrap_css_state.get("hash") != digest:
            static_dir.mkdir(parents=True, exist_ok=True)
            need_write = True
            try:
                if css_path.is_file() and css_path.read_text(encoding="utf-8") == css:
                    need_write = False
            except OSError:
                need_write = True
            if need_write:
                try:
                    css_path.write_text(css, encoding="utf-8")
                except OSError:
                    pass
            _bootstrap_css_state["hash"] = digest
        # 항상 인라인 — Cloud 에서 /app/static/*.css 링크가 SPA HTML(text/html)을
        # 반환하면 MIME 오류로 전역 CSS 전체가 미적용되어 상단 공백·레이아웃이 붕괴된다.
        # static/ 파일은 og-share 등 다른 용도로만 동기화한다.
        _ = _streamlit_cloud_deploy()
        st.markdown(
            f'<style id="saju-bootstrap-global-{digest}">{css}</style>{rest}',
            unsafe_allow_html=True,
        )
    except Exception:
        st.markdown(head_html, unsafe_allow_html=True)


def init_session_state() -> None:
    """앱 공통 세션 키 기본값. 이미 있는 키는 덮어쓰지 않습니다."""
    defaults = {
        "step": 1,
        "reset_id": 0,
        "shared_chat": [],
        "saju_options": {
            "month_method": "lichun_lunar",
        },
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def inject_early_step_html_attrs() -> None:
    """첫 페인트 전 ``data-saju-step``·홈 클래스 — JS 지연 시에도 모바일 홈 CSS가 적용되게."""
    try:
        step = max(1, min(12, int(st.session_state.get("step", 1))))
    except Exception:
        step = 1
    home_cls = "saju-home-step1" if step == 1 else "saju-not-step1"
    # JS가 막혀도 홈/비홈 CSS가 적용되도록 클래스를 style로 선반영
    st.markdown(
        (
            f"<style>html{{scroll-padding-top:0!important;}}"
            f"html.{home_cls},html[data-saju-step=\"{step}\"]"
            f'[data-testid="stAppViewContainer"]{{min-height:0!important;height:100dvh!important;'
            f"max-height:100dvh!important;overflow-y:auto!important;justify-content:flex-start!important;"
            f"align-items:stretch!important;align-content:flex-start!important;"
            f"display:block!important;flex:none!important;padding-top:0!important;margin-top:0!important;}}"
            f"html.{home_cls} .main .block-container,"
            f'html[data-saju-step="{step}"] .main .block-container'
            f"{{padding-top:0!important;margin-top:0!important;min-height:0!important;}}"
            f"html.{home_cls} [data-testid='stAppViewContainer']>.main,"
            f"html[data-saju-step=\"{step}\"] [data-testid='stAppViewContainer']>.main,"
            f"html.{home_cls} [data-testid='stMain'],"
            f'html[data-saju-step="{step}"] [data-testid="stMain"],'
            f"html.{home_cls} [data-testid='stMainBlockContainer'],"
            f'html[data-saju-step="{step}"] [data-testid="stMainBlockContainer"]'
            f"{{min-height:0!important;height:auto!important;padding-top:0!important;"
            f"margin-top:0!important;display:block!important;"
            f"justify-content:flex-start!important;align-items:stretch!important;}}"
            + (
                "html.saju-home-step1 header[data-testid='stHeader'],"
                "html[data-saju-step='1'] header[data-testid='stHeader'],"
                "html.saju-home-step1 .stApp>header,"
                "html[data-saju-step='1'] .stApp>header,"
                "html.saju-home-step1 [data-testid='stToolbar'],"
                "html[data-saju-step='1'] [data-testid='stToolbar'],"
                "html.saju-home-step1 [data-testid='stDecoration'],"
                "html[data-saju-step='1'] [data-testid='stDecoration']"
                "{display:none!important;visibility:hidden!important;height:0!important;"
                "min-height:0!important;max-height:0!important;margin:0!important;"
                "padding:0!important;overflow:hidden!important;pointer-events:none!important;"
                "position:absolute!important;width:0!important;}"
                if step == 1
                else ""
            )
            + "</style>"
            "<script>(function(){"
            "var e=document.documentElement;"
            f'e.setAttribute("data-saju-step","{step}");'
            'e.classList.remove("saju-home-step1","saju-not-step1");'
            f'e.classList.add("{home_cls}");'
            "})();</script>"
        ),
        unsafe_allow_html=True,
    )


def configure_application() -> None:
    st.set_page_config(
        page_title="사주까기 · 무료 사주풀이",
        page_icon="🔮",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    try:
        st.set_option("client.toolbarMode", "minimal")
    except Exception:
        pass
    init_session_state()
    try:
        from saju.ui.home_hero_banner import ensure_step01_hero_banner_file

        ensure_step01_hero_banner_file(force=True)
    except Exception:
        pass
    inject_early_step_html_attrs()
    st.markdown(
        (
            '<meta name="viewport" '
            'content="width=device-width, initial-scale=1, viewport-fit=cover">'
        ),
        unsafe_allow_html=True,
    )
    try:
        from saju_app.ui.execution import inject_step_dom_boot_once

        inject_step_dom_boot_once()
    except Exception:
        pass
    try:
        from saju_app.ui import share_meta as _share_meta

        _share_meta.inject_link_share_meta()
    except Exception:
        pass
    _saju_bootstrap_head_html = (
        """
<style>
    /* 라틴: Playfair Display · 한글·한자: Noto Serif KR (앞글꼴에 없는 코드포인트는 뒤로 폴백) */
    @import url("https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;500;600;700;900&family=Playfair+Display:ital,wght@0,400;0,500;0,600;0,700;1,400;1,500&display=swap");
    /* 골드 + 다크 팔레트 토큰 (Top5: 전역 컬러 교체용) */
    :root {
        /* 프리미엄: 고급 한지 + 금박 + Deep Dark */
        --saju-bg-deep: #05050c;
        --saju-bg-mid: #0a0a14;
        --saju-bg-elevated: #16213e;
        --saju-bg-card-a: #1a1a2e;
        --saju-bg-card-b: #16213e;
        --saju-bg-paper: #f7f4ef;
        --saju-bg-paper-soft: #f2eee6;
        --saju-bg-canvas-light: #faf8f5;
        --saju-bg-canvas-light-mid: #f3efe8;
        --saju-bg-canvas-light-deep: #ebe6de;
        --saju-bg-canvas-dark: #0a0a12;
        --saju-bg-canvas-dark-mid: #0e0e18;
        /* 정보입력(년·월·일) 칩과 동일 — 이동·안내 버튼 배경 */
        --saju-soft-fill: #fff5ee;
        --saju-soft-fill-hover: #fff0e6;
        --saju-soft-fill-active: #ffede2;
        --saju-soft-fill-dark: rgba(40, 36, 32, 0.88);
        --saju-soft-fill-dark-hover: rgba(50, 44, 38, 0.94);
        --saju-soft-radius: 16px;
        --saju-gold: #d4af37;
        --saju-gold-bright: #e8b923;
        --saju-gold-soft: #c9a227;
        --saju-gold-deep: #7a5e12;
        --saju-ink: #1a1208;
        --saju-text-readable: #1c1510;
        --saju-text-body: #e5e5e5;
        --saju-text-accent: #a5b4fc;
        --saju-glow: rgba(212, 175, 55, 0.38);
        /* 오행 (차트·바와 동일 톤) */
        --saju-el-wood: #4ade80;
        --saju-el-fire: #f87171;
        --saju-el-earth: #facc15;
        --saju-el-metal: #cbd5e1;
        --saju-el-water: #60a5fa;
    }
    /* Streamlit Light/Dark: `.streamlit/config.toml` (Deep Luxury Dark + Gold) + ⋮ → Theme */
    /* ===== 접근성: 기본 16px, 대비, 키보드 포커스 ===== */
    html {
        font-size: 16px;
        -webkit-text-size-adjust: 100%;
    }
    /* 브라우저 자동 번역이 JS·입력란을 깨뜨리는 것 방지 */
    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        translate: no !important;
    }
    .stApp {
        font-size: 1rem;
        font-family: "Playfair Display", "Noto Serif KR", "Apple SD Gothic Neo", "Malgun Gothic",
            Georgia, "Times New Roman", "Noto Color Emoji", serif !important;
        /* 테마 배경: 한지 노이즈 대신 고급 아이보리·딥 네이비 그라데이션 (모바일 가독성) */
        background-color: light-dark(var(--saju-bg-canvas-light), var(--saju-bg-canvas-dark)) !important;
        background-image: light-dark(
            radial-gradient(ellipse 110% 72% at 50% -16%, rgba(201, 162, 39, 0.07), transparent 54%),
            linear-gradient(
                168deg,
                var(--saju-bg-canvas-light) 0%,
                var(--saju-bg-canvas-light-mid) 46%,
                var(--saju-bg-canvas-light-deep) 100%
            ),
            radial-gradient(ellipse 95% 68% at 50% -18%, rgba(212, 175, 55, 0.1), transparent 56%),
            linear-gradient(
                168deg,
                var(--saju-bg-canvas-dark) 0%,
                var(--saju-bg-canvas-dark-mid) 54%,
                #12121f 100%
            )
        ) !important;
        background-attachment: scroll !important;
    }
    /* 본문 래퍼는 투명 — .stApp 단일 캔버스만 보이게 (iPhone 이중 질감·색 번짐 방지) */
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    section.main,
    [data-testid="stMainBlockContainer"],
    .stApp > [data-testid="stAppViewContainer"] > .main {
        background: transparent !important;
        background-image: none !important;
    }
    /* Streamlit 플랫폼 UI — 사주 앱 기능과 무관 (Fork·Deploy·왕관·관리 등) */
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    [data-testid="stAppDeployButton"],
    [data-testid="stHeaderActionElements"],
    [data-testid="stToolbarActions"],
    .stDeployButton,
    #MainMenu,
    footer,
    a[href*="streamlit.app/manage"],
    a[href*="share.streamlit.io/manage"],
    a[href*="/manage/"],
    a[title*="Manage"],
    a[title*="manage"],
    a[aria-label*="Manage"],
    a[aria-label*="manage"],
    iframe[title="streamlit"],
    iframe[title*="Manage"],
    iframe[title*="manage"],
    [class*="viewerBadge"],
    [class*="ViewerBadge"],
    [class*="ManageApp"],
    [class*="manageApp"] {
        visibility: hidden !important;
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
        pointer-events: none !important;
        margin: 0 !important;
        padding: 0 !important;
        opacity: 0 !important;
        position: absolute !important;
        left: -99999px !important;
        top: auto !important;
        z-index: -9999 !important;
    }
    .stApp > header {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
    }
    .stApp {
        height: 100vh !important;
        height: 100dvh !important;
        max-height: 100dvh !important;
        overflow: hidden !important;
    }
    [data-testid="stAppViewContainer"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        -webkit-overflow-scrolling: touch;
        overscroll-behavior-y: auto;
        scroll-behavior: auto !important;
        touch-action: pan-y !important;
        height: 100vh !important;
        height: 100dvh !important;
        min-height: 0 !important;
        max-height: 100dvh !important;
        /* 모바일 WebView에서 flex center로 밀리는 현상 방지(홈/전체 공통) */
        display: block !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
    }
    /* 홈 STEP1 — 스크롤 루트는 뷰포트 고정(상단 flex-center 만 차단) */
    html.saju-home-step1 [data-testid="stAppViewContainer"],
    html[data-saju-step="1"] [data-testid="stAppViewContainer"] {
        display: block !important;
        min-height: 0 !important;
        height: 100vh !important;
        height: 100dvh !important;
        max-height: 100dvh !important;
        overflow-y: auto !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
    }
    html.saju-home-step1 [data-testid="stMain"],
    html[data-saju-step="1"] [data-testid="stMain"],
    html.saju-home-step1 section.main,
    html[data-saju-step="1"] section.main {
        display: block !important;
        min-height: 0 !important;
        height: auto !important;
        flex: none !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
    }
    html.saju-home-step1 [data-testid="stMainBlockContainer"],
    html[data-saju-step="1"] [data-testid="stMainBlockContainer"] {
        display: block !important;
        min-height: 0 !important;
        height: auto !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
    }
    html.saju-home-step1 #saju-step-active-top,
    html[data-saju-step="1"] #saju-step-active-top,
    .st-key-saju_router_step_mount_01 #saju-step-active-top {
        display: none !important;
        height: 0 !important;
        max-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }
    @media (max-width: 768px) {
        html,
        body,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        section.main {
            touch-action: pan-y !important;
            -webkit-overflow-scrolling: touch !important;
            overscroll-behavior-y: contain !important;
        }
        [data-testid="stAppViewContainer"] {
            scroll-behavior: auto !important;
        }
        .stApp [data-testid="stVerticalBlock"],
        .stApp [data-testid="stHorizontalBlock"] {
            touch-action: pan-y !important;
        }
    }
    [data-testid="stMainBlockContainer"],
    section.main,
    [data-testid="stMain"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
        overflow: visible !important;
        /* flex center 차단(전역) */
        display: block !important;
        min-height: 0 !important;
        height: auto !important;
        max-height: none !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
    }

    /* Streamlit 컨테이너가 flex로 잡혀도 상단부터 쌓이게(전역) */
    [data-testid="stAppViewContainer"] > .main,
    .stApp > [data-testid="stAppViewContainer"] > .main {
        display: block !important;
        min-height: 0 !important;
        height: auto !important;
        max-height: none !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    /* STEP 스크롤 펄스 iframe — 레이아웃·스크롤 간섭 제거 */
    [class*="st-key-saju_scroll_fire_"],
    [class*="st-key-saju_scroll_pulse_"],
    [class*="st-key-saju_scroll_top_js_"],
    [class*="st-key-saju_home_viewport_"],
    .st-key-saju_home_solar_fit,
    .st-key-saju_home_hero_pin_tail,
    [class*="st-key-saju_home_viewport_lock_"],
    .st-key-saju_step_html_sync,
    [class*="st-key-saju_step_html_sync_"],
    [class*="st-key-saju_expander_collapse_"],
    [class*="st-key-saju_cal_loc_"],
    [class*="st-key-saju_step2_time_protect_"],
    [class*="st-key-saju_step2_tab_order_"],
    [class*="st-key-saju_focus_return_"],
    .st-key-saju_calendar_locale_install_v21,
    .st-key-saju_browser_nav_check,
    .st-key-saju_browser_privacy_client_v2,
    .st-key-saju_browser_nav_check [data-testid="stElementContainer"],
    .st-key-saju_browser_privacy_client_v2 [data-testid="stElementContainer"],
    .st-key-saju_browser_nav_check [data-testid="stVerticalBlock"],
    .st-key-saju_browser_privacy_client_v2 [data-testid="stVerticalBlock"],
    .st-key-saju_browser_nav_check iframe,
    .st-key-saju_browser_privacy_client_v2 iframe {
        display: none !important;
        height: 0 !important;
        max-height: 0 !important;
        min-height: 0 !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
        pointer-events: none !important;
        visibility: hidden !important;
        border: none !important;
    }
    /* st.markdown("<script>") 으로 주입된 죽은 스크립트 element-container 는
       화면에 아무것도 안 그리지만 세로 flex 슬롯을 차지해 상단·중간 공백(gap)을
       만든다. (스크롤 매니저·html attrs 등) → 본문 흐름에서 완전히 제거. */
    .main .block-container [data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] script),
    .main .block-container [data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] style),
    .main .block-container [data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] > [data-testid="stMarkdownContainer"]:empty),
    .main .block-container [data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] > [data-testid="stMarkdownContainer"] > div:empty:only-child) {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    /* STEP 본문 위 1px 스크롤 앵커(#saju-step-active-top)의 element-container 도
       세로 flex gap 슬롯을 차지해 상단 공백을 만든다 → 흐름에서 제거.
       (STEP 전환 스크롤은 scrollTop=0(맨 위) 으로 처리하므로 앵커가 없어도 무방) */
    .main .block-container [data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] #saju-step-active-top),
    .main .block-container [data-testid="stElementContainer"]:has(#saju-step-active-top) {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    /* 스크롤 tail iframe(잠금된 최상단 스크롤 기능)은 반드시 실행돼야 하므로
       display:none(모바일 WebView 미실행 위험) 대신 흐름에서만 빼서(absolute) gap 제거. */
    [class*="st-key-saju_nav_scroll_tail_"] {
        position: absolute !important;
        height: 0 !important;
        width: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
        pointer-events: none !important;
        visibility: hidden !important;
    }
    /* STEP 최상단 앵커(1px)는 스크롤 기준점일 뿐 — 세로 flex 슬롯에서 빼서(absolute)
       gap 으로 인한 상단 공백을 만들지 않게 한다. (스크롤은 scrollTop=0 으로 처리) */
    .st-key-saju_step_top_anchor {
        position: absolute !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
        pointer-events: none !important;
    }
    /* 모든 비홈 STEP(정보입력~관리자): 본문을 화면 위로 — block-container 상단 패딩 최소화.
       (홈 STEP1 은 이미 padding-top:0) */
    html[data-saju-step]:not([data-saju-step="1"]) .main .block-container,
    html.saju-not-step1 .main .block-container {
        padding-top: clamp(0.2rem, 0.8vw, 0.5rem) !important;
        margin-top: 0 !important;
    }
    /* Cloud 하단 고정 왕관·관리 링크(모바일 포함) */
    .stApp a[href*="streamlit.app/manage"],
    .stApp a[href*="share.streamlit.io/manage"],
    body a[href*="streamlit.app/manage"],
    body a[href*="share.streamlit.io/manage"] {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }
    .main .block-container {
        font-size: 1rem;
        line-height: 1.62;
        position: relative;
        /* minimal & luxurious: 읽기 폭 캡 + 과감한 여백 */
        padding-top: clamp(0.45rem, 1.4vw, 1.65rem) !important;
        padding-bottom: clamp(1.35rem, 3vw, 2.5rem) !important;
        padding-left: clamp(1.1rem, 3.5vw, 2.6rem) !important;
        padding-right: clamp(1.1rem, 3.5vw, 2.6rem) !important;
        max-width: min(1100px, 100%) !important;
        margin-left: auto !important;
        margin-right: auto !important;
        isolation: isolate;
    }
    /* 은은한 상단 골드 앰비언트만 (미세 노이즈·한지 질감 없음) */
    .main .block-container::before {
        content: "";
        position: absolute;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        opacity: light-dark(0.72, 0.48);
        background: radial-gradient(
            ellipse 92% 48% at 50% -8%,
            rgba(212, 175, 55, 0.07),
            transparent 62%
        );
    }
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    .stMarkdown p,
    .stMarkdown li {
        font-size: max(16px, 1rem) !important;
    }
    [data-testid="stWidgetLabel"] label,
    .stWidgetLabel label,
    .stCheckbox label,
    .stRadio label,
    .stSelectbox label,
    .stMultiSelect label,
    .stTextInput label,
    .stNumberInput label,
    .stSlider label {
        font-size: max(16px, 1rem) !important;
    }
    .stCaption,
    div[data-testid="stCaption"] {
        font-size: max(16px, 1rem) !important;
        line-height: 1.45 !important;
    }
    [data-testid="stChatInput"] textarea {
        font-size: max(16px, 1rem) !important;
        line-height: 1.45 !important;
    }
    .stTextArea textarea {
        font-size: max(16px, 1rem) !important;
        line-height: 1.45 !important;
        color: light-dark(var(--saju-text-readable), #f0ece4) !important;
        background: light-dark(#fffefb, rgba(26, 26, 46, 0.92)) !important;
        border: 1px solid light-dark(rgba(212, 175, 55, 0.32), rgba(212, 175, 55, 0.22)) !important;
    }
    [data-testid="stAlert"] {
        font-size: max(15px, 0.95rem) !important;
        line-height: 1.55 !important;
        border-radius: 18px !important;
    }
    [data-testid="stAlert"] > div {
        border-radius: 18px !important;
        border: 1px solid light-dark(rgba(99, 102, 241, 0.22), rgba(165, 180, 252, 0.28)) !important;
        background: light-dark(
            linear-gradient(145deg, #f8fafc 0%, #eef2ff 55%, #fdf4ff 100%),
            linear-gradient(145deg, #12121f 0%, #1a1a32 55%, #1f1630 100%)
        ) !important;
        box-shadow: 0 10px 28px light-dark(rgba(99, 102, 241, 0.08), rgba(0, 0, 0, 0.35)) !important;
    }
    .saju-step-intro {
        display: flex;
        align-items: flex-start;
        gap: 0.65rem;
        margin: 0.35rem 0 1rem;
        padding: 0.85rem 1rem;
        border-radius: 18px;
        border: 1px solid light-dark(rgba(244, 114, 182, 0.35), rgba(244, 114, 182, 0.45));
        background: light-dark(
            linear-gradient(120deg, rgba(253, 242, 248, 0.95), rgba(237, 233, 254, 0.9)),
            linear-gradient(120deg, rgba(42, 18, 34, 0.85), rgba(26, 22, 48, 0.9))
        );
        box-shadow: 0 8px 24px light-dark(rgba(244, 114, 182, 0.12), rgba(0, 0, 0, 0.28));
    }
    .saju-step-intro-emoji {
        font-size: 1.35rem;
        line-height: 1.2;
        flex-shrink: 0;
    }
    .saju-step-intro-text {
        font-size: 0.98rem;
        line-height: 1.55;
        color: light-dark(#1f2937, #e2e8f0);
        font-weight: 650;
    }
    .saju-mood-hero,
    .saju-mood-mid {
        display: block;
        width: 100%;
        margin: 0.15rem auto 0.85rem;
        text-align: center;
        line-height: 0;
    }
    .saju-mood-hero img {
        width: min(100%, 720px);
        max-height: 168px;
        height: auto;
        object-fit: contain;
        margin: 0 auto;
        filter: drop-shadow(0 10px 28px rgba(212, 175, 55, 0.22));
    }
    .saju-mood-mid {
        margin: 0.5rem auto 0.75rem;
    }
    .saju-mood-mid img {
        width: min(100%, 640px);
        max-height: 96px;
        height: auto;
        object-fit: contain;
        margin: 0 auto;
        opacity: 0.96;
        filter: drop-shadow(0 6px 18px rgba(212, 175, 55, 0.16));
    }
    /* STEP6 오늘의 운세 — images/오늘의 운세.png 와이드 배너 */
    .st-key-step6_hero_banner [data-testid="stMarkdownContainer"],
    .st-key-step6_hero_banner [data-testid="stMarkdownContainer"] > div {
        overflow: visible !important;
        max-width: 100% !important;
    }
    .saju-mood-step6-hero,
    .st-key-step6_hero_banner .saju-mood-step6-hero {
        display: block;
        width: 100%;
        max-width: 920px;
        margin: 0.2rem auto 0.85rem;
        text-align: center;
        line-height: 0;
    }
    .saju-mood-step6-hero img,
    .st-key-step6_hero_banner .saju-mood-step6-hero img {
        width: 100%;
        max-width: 920px;
        height: auto;
        object-fit: contain;
        margin: 0 auto;
        border-radius: 14px;
        border: 1px solid rgba(139, 105, 20, 0.22);
        box-shadow: 0 10px 28px rgba(80, 60, 30, 0.14);
    }
    [data-testid="stExpander"] details {
        border-radius: 16px !important;
        border: 1px solid light-dark(rgba(148, 163, 184, 0.35), rgba(148, 163, 184, 0.22)) !important;
        background: light-dark(rgba(255, 255, 255, 0.72), rgba(22, 22, 40, 0.72)) !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: max(16px, 1rem) !important;
    }
    .stLinkButton > a {
        font-size: max(16px, 1rem) !important;
        font-weight: 600 !important;
    }
    .stFormSubmitButton > button {
        font-size: max(16px, 1.05rem) !important;
    }
    /* 탭 타깃·모바일 터치: 주요 액션 버튼 (세부 스텝 전용 규칙이 !important 로 덮음) */
    .stApp .stButton > button,
    .stApp .stDownloadButton > button {
        border-radius: 16px;
        min-height: 52px;
        font-size: 1.05rem;
    }
    .stButton > button:focus-visible,
    .stTextInput input:focus-visible,
    .stSelectbox div[data-baseweb="select"]:focus-within,
    .stCheckbox input:focus-visible,
    .stRadio input:focus-visible,
    .stNumberInput input:focus-visible,
    [data-testid="stChatInput"] textarea:focus-visible,
    .stTextArea textarea:focus-visible,
    .stLinkButton > a:focus-visible {
        outline: 3px solid light-dark(#1d4ed8, rgba(232, 185, 35, 0.85)) !important;
        outline-offset: 2px !important;
    }

    /*
     * (안정화) Streamlit 내부 레이아웃 블록(`stHorizontalBlock`)의 display/flex를 강제로 바꾸면
     * 모바일 WebView에서 insertBefore/removeChild 오류가 날 수 있어 제거합니다.
     * 레이아웃은 Streamlit 기본/코드 레벨 컨테이너로만 구성합니다.
     */

    /* 이전/다음 바: 블록 전체 너비 기준 정중앙(데스크톱·모바일 공통) */
    .st-key-saju_global_prev_next {
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .st-key-saju_global_prev_next [data-testid="stVerticalBlock"],
    .st-key-saju_global_prev_next [data-testid="stElementContainer"] {
        width: 100% !important;
        max-width: 100% !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    .st-key-saju_global_prev_next [data-testid="stMarkdownContainer"] {
        width: 100% !important;
        max-width: 100% !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    .st-key-saju_global_prev_next [data-testid="stMarkdownContainer"] p {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        text-align: center !important;
    }
    .st-key-saju_global_prev_next .saju-pn-html {
        display: block !important;
        width: max-content !important;
        max-width: min(52rem, 100%) !important;
        margin-left: auto !important;
        margin-right: auto !important;
        box-sizing: border-box !important;
    }
    .st-key-saju_global_prev_next .saju-pn-html a {
        text-decoration: none !important;
    }

    /* 하단 기능 바로가기(세션 제어 패널): 펼침 토글 버튼 */
    .st-key-saju_bottom_quick_menu_panel {
        margin-top: 0.35rem !important;
    }
    .st-key-saju_bottom_quick_menu_panel [data-testid="stButton"] > button {
        font-weight: 700 !important;
        border-radius: 14px !important;
    }
    .st-key-saju_global_bottom_chrome [data-testid="stExpander"] summary {
        pointer-events: auto !important;
        cursor: pointer !important;
        position: relative !important;
        z-index: 6 !important;
    }
    /* 인앱 WebView 등에서 이전/다음 행이 두 번 삽입되는 경우 두 번째 행 숨김 */
    .st-key-saju_global_bottom_chrome .st-key-saju_bottom_prev_next_row ~ .st-key-saju_bottom_prev_next_row {
        display: none !important;
    }
    /* 본문과 하단 크롬 사이: 실선 대신 여백(이중 divider/HR 제거 효과) */
    .st-key-saju_global_bottom_chrome {
        margin-top: 0.65rem !important;
        padding-top: 0.15rem !important;
    }

    /*
     * 하단 글로벌 크롬: 이전/다음 + 기능 바로가기(expander 안) 2열 강제
     * (네이버·카카오 등 인앱 WebView에서 st.columns 가 세로로 무너지는 현상 완화 — STEP2 s2self_r* 와 동일 패턴)
     */
    .st-key-saju_bottom_prev_next_row [data-testid="stVerticalBlock"] {
        flex-wrap: nowrap !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    .st-key-saju_bottom_prev_next_row [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 8px !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    .st-key-saju_bottom_prev_next_row [data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0 !important;
        min-width: 0 !important;
    }
    .st-key-saju_bottom_quick_grid_2col [data-testid="stVerticalBlock"] {
        flex-wrap: nowrap !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    .st-key-saju_bottom_quick_grid_2col [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: flex-start !important;
        gap: 8px !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    .st-key-saju_bottom_quick_grid_2col [data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0 !important;
        min-width: 0 !important;
    }

    @media (max-width: 768px) {
        /* 하단 이전/다음: 본문과 함께 스크롤, 카드형 */
        .st-key-saju_global_prev_next {
            position: static !important;
            width: 100% !important;
            max-width: 100% !important;
            box-sizing: border-box !important;
            margin: 0.35rem 0 0.2rem 0 !important;
            padding: 0.4rem 0.45rem 0.4rem !important;
            background: rgba(250, 250, 252, 0.97);
            background: light-dark(rgba(250, 248, 243, 0.97), rgba(15, 15, 26, 0.94)) !important;
            -webkit-backdrop-filter: blur(10px);
            backdrop-filter: blur(10px);
            border: none !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            background: transparent !important;
        }
        .st-key-saju_global_bottom_chrome [data-testid="stExpander"] {
            margin-top: 0.35rem !important;
        }
        .main .block-container {
            padding-bottom: 1rem !important;
        }
    }

    /* ----- 하단 STEP 독: ``st.html`` + ``.saju-step-dock-html`` CSS grid (모바일에서 st.columns 세로 스택 회피) ----- */
    .st-key-saju_step_dock {
        margin-top: 0.25rem !important;
        padding: 0 !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        background: transparent !important;
        border: 0 !important;
        box-shadow: none !important;
    }
    .st-key-saju_step_dock [data-testid="stVerticalBlock"],
    .st-key-saju_step_dock [data-testid="stElementContainer"] {
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    .saju-step-dock-html {
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        margin-top: 0.08rem !important;
        padding: 0.38rem 0.2rem 0.42rem !important;
        border-radius: 0 !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    .saju-step-dock-html .saju-dock-row {
        display: grid !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        column-gap: 0.08rem !important;
    }
    .saju-step-dock-html .saju-dock-row.r1 {
        grid-template-columns: repeat(6, minmax(0, 1fr)) !important;
        margin-bottom: 0.28rem !important;
    }
    .saju-step-dock-html .saju-dock-row.r2 {
        grid-template-columns: repeat(5, minmax(0, 1fr)) !important;
    }
    .saju-step-dock-html .saju-dock-a,
    .saju-step-dock-html .saju-dock-off {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: flex-start !important;
        box-sizing: border-box !important;
        min-height: 2.75rem !important;
        padding: 0.12rem 0.03rem 0.14rem !important;
        border-radius: 10px !important;
        text-decoration: none !important;
        color: light-dark(#1a1a2e, #e8e8ef) !important;
        -webkit-tap-highlight-color: transparent !important;
        touch-action: manipulation !important;
    }
    .saju-step-dock-html .saju-dock-a:focus-visible {
        outline: 2px solid light-dark(rgba(29, 78, 216, 0.65), rgba(232, 185, 35, 0.75)) !important;
        outline-offset: 1px !important;
    }
    .saju-step-dock-html .saju-dock-a:active {
        opacity: 0.88 !important;
    }
    .saju-step-dock-html .saju-dock-off {
        opacity: 0.42 !important;
        cursor: not-allowed !important;
    }
    .saju-step-dock-html .saju-dock-emo {
        font-size: clamp(1rem, 4vw, 1.48rem) !important;
        line-height: 1.12 !important;
        font-weight: 800 !important;
    }
    .saju-step-dock-html .saju-dock-cap {
        margin-top: 0.08rem !important;
        font-size: clamp(8.5px, 2.45vw, 0.74rem) !important;
        line-height: 1.12 !important;
        font-weight: 800 !important;
        text-align: center !important;
        word-break: keep-all !important;
        color: light-dark(rgba(26, 26, 46, 0.88), rgba(232, 232, 240, 0.9)) !important;
    }
    @media (max-width: 768px) {
        .st-key-saju_step_dock {
            position: static !important;
            margin: 0.55rem 0 0 0 !important;
        }
        .saju-step-dock-html {
            padding: 0.34rem 0.14rem calc(0.36rem + env(safe-area-inset-bottom, 0px)) !important;
        }
    }
    @media (min-width: 769px) {
        .saju-step-dock-html .saju-dock-a,
        .saju-step-dock-html .saju-dock-off {
            min-height: 3.6rem !important;
            padding: 0.24rem 0.08rem 0.28rem !important;
        }
        .saju-step-dock-html .saju-dock-emo {
            font-size: clamp(1.35rem, 2.1vw, 2.05rem) !important;
        }
        .saju-step-dock-html .saju-dock-cap {
            font-size: clamp(11px, 0.82rem + 0.2vw, 0.95rem) !important;
        }
    }

    /* ✅ 모바일·STEP1: 상단 여백 최소화 */
    @media (max-width: 768px){
        .main .block-container {
            padding-top: 0 !important;
            padding-bottom: 0.85rem !important;
        }
        h1, h2, h3 {
            margin-top: 0.25rem !important;
            margin-bottom: 0.65rem !important;
        }
    }
    
    /* 제목: 골드 톤 + 세리프(가독) — 라이트/다크 */
    h1, h2, h3 {
        font-size: clamp(1.0625rem, 0.95rem + 0.6vw, 1.45rem) !important;
        margin-top: 0.6rem !important;
        margin-bottom: 0.9rem !important;
        color: light-dark(var(--saju-gold-deep), var(--saju-gold-bright)) !important;
        font-family: "Playfair Display", "Noto Serif KR", "Apple SD Gothic Neo", "Malgun Gothic",
            Georgia, serif !important;
        font-weight: 800 !important;
        letter-spacing: -0.01em;
    }
    
    /* 버튼: 터치 영역(색은 Streamlit 테마 primary / secondary 사용) */
    .stButton > button {
        height: 3.8rem;
        font-size: max(16px, 1.05rem) !important;
        font-weight: 700;
        border-radius: 12px;
        margin: 0.35rem 0;
    }
    .stButton > button:disabled {
        opacity: 0.5 !important;
    }

    /* 입력 필드 */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div,
    .stNumberInput input {
        font-size: max(16px, 1rem) !important;
        height: 3.3rem !important;
    }
    
    /* 컬럼 간격 줄이기 */
    [data-testid="column"] {
        padding: 0.2rem 0.3rem !important;
    }
    
    /*
     * Streamlit 루트(html/body/stApp)에 overflow·height를 강제하면
     * 프론트엔드에서 NotFoundError(removeChild)가 날 수 있어 여기서는 건드리지 않습니다.
     * (모바일 스크롤은 브라우저 기본 동작에 맡깁니다.)
     */
    
    /* 아코디언·확장 패널 제목 */
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary span {
        font-size: max(16px, 1rem) !important;
    }

    /* 카드 및 박스 여백 */
    .stMarkdown, div[data-testid="stExpander"] {
        margin-bottom: 1rem;
    }

    /* (하단 3탭 네비게이션 제거됨) */

    /* ===== STEP1 메인(항상 로드 — step별 <style> 삽입 제거로 DOM 불일치 방지) ===== */
    .main-title {
        text-align: center;
        font-size: clamp(1.25rem, 1.1rem + 1.2vw, 2.1rem);
        font-weight: 900;
        background-image: light-dark(
            linear-gradient(90deg, #1a1a2e 0%, #8a6d1a 42%, #c9a227 100%),
            linear-gradient(90deg, #3d3318 0%, #d4af37 50%, #e8b923 100%)
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0.2rem 0 0.1rem 0;
        letter-spacing: -0.5px;
    }
    .subtitle {
        text-align: center;
        font-size: max(16px, 1.05rem);
        margin-bottom: 1.2rem;
        font-weight: 500;
        opacity: 0.92;
    }
    .step1-menu-wrap { margin-bottom: 5rem; }

    /* STEP 전환 스크롤 앵커 */
    #saju-step-top-anchor,
    .st-key-saju_step_top_anchor {
        scroll-margin-top: 0 !important;
        min-height: 0 !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    .st-key-saju_step_top_anchor [data-testid="stVerticalBlock"] {
        min-height: 0 !important;
        gap: 0 !important;
    }
    html[data-saju-step] [data-testid="stAppViewContainer"],
    html[data-saju-step] [data-testid="stMain"],
    html[data-saju-step] section.main {
        scroll-behavior: auto !important;
    }

    /* STEP 라우터 — 단일 마운트(이전 STEP DOM 겹침 방지) */
    .st-key-saju_router_step_mount {
        width: 100% !important;
        max-width: 100% !important;
    }
    /* 레거시 step별 마운트(누적 DOM) — 전부 숨김(position 절대 이동은 removeChild 유발) */
    [class*="st-key-saju_step_mount_"] {
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
    /* STEP2~12: STEP1 홈 배너·24절기 DOM 잔존 시 겹침 차단 */
    html.saju-not-step1 .st-key-saju_landing_stack,
    html.saju-not-step1 .st-key-saju_landing_hero,
    html.saju-not-step1 .st-key-saju_landing_cta,
    html.saju-not-step1 .st-key-step1_solar24,
    html.saju-not-step1 .st-key-step1_cta_row_main,
    html.saju-not-step1 .st-key-step1_cta_row_free,
    html.saju-not-step1 .saju-landing-hero,
    html[data-saju-step]:not([data-saju-step="1"]) .st-key-saju_landing_stack,
    html[data-saju-step]:not([data-saju-step="1"]) .st-key-saju_landing_hero,
    html[data-saju-step]:not([data-saju-step="1"]) .st-key-step1_solar24,
    html[data-saju-step]:not([data-saju-step="1"]) .saju-landing-hero {
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
    /* STEP 라우터 — 현재 STEP 마운트만 표시(이전 STEP DOM 잔존 시 관리자·채팅 화면 겹침 방지) */
    html[data-saju-step]:not([data-saju-step="1"]) .st-key-saju_router_step_mount_01,
    html[data-saju-step]:not([data-saju-step="2"]) .st-key-saju_router_step_mount_02,
    html[data-saju-step]:not([data-saju-step="3"]) .st-key-saju_router_step_mount_03,
    html[data-saju-step]:not([data-saju-step="4"]) .st-key-saju_router_step_mount_04,
    html[data-saju-step]:not([data-saju-step="5"]) .st-key-saju_router_step_mount_05,
    html[data-saju-step]:not([data-saju-step="6"]) .st-key-saju_router_step_mount_06,
    html[data-saju-step]:not([data-saju-step="7"]) .st-key-saju_router_step_mount_07,
    html[data-saju-step]:not([data-saju-step="8"]) .st-key-saju_router_step_mount_08,
    html[data-saju-step]:not([data-saju-step="9"]) .st-key-saju_router_step_mount_09,
    html[data-saju-step]:not([data-saju-step="10"]) .st-key-saju_router_step_mount_10,
    html[data-saju-step]:not([data-saju-step="11"]) .st-key-saju_router_step_mount_11,
    html[data-saju-step]:not([data-saju-step="12"]) .st-key-saju_router_step_mount_12,
    html.saju-not-step1 .st-key-saju_router_step_mount_01 {
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
    html:not([data-saju-step]) .st-key-saju_router_step_mount_01,
    html[data-saju-step="1"] .st-key-saju_router_step_mount_01,
    html.saju-home-step1 .st-key-saju_router_step_mount_01,
    html[data-saju-step="2"] .st-key-saju_router_step_mount_02,
    html[data-saju-step="3"] .st-key-saju_router_step_mount_03,
    html[data-saju-step="4"] .st-key-saju_router_step_mount_04,
    html[data-saju-step="5"] .st-key-saju_router_step_mount_05,
    html[data-saju-step="6"] .st-key-saju_router_step_mount_06,
    html[data-saju-step="7"] .st-key-saju_router_step_mount_07,
    html[data-saju-step="8"] .st-key-saju_router_step_mount_08,
    html[data-saju-step="9"] .st-key-saju_router_step_mount_09,
    html[data-saju-step="10"] .st-key-saju_router_step_mount_10,
    html[data-saju-step="11"] .st-key-saju_router_step_mount_11,
    html[data-saju-step="12"] .st-key-saju_router_step_mount_12 {
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
    }

    /* ===== STEP 전환(data-saju-nav-pending) — 하단 네비만 보이는 빈 화면 방지 =====
       클릭 직후·rerun 중 pending 이 켜져 있을 때 하단 크롬·푸터를 숨기고,
       data-saju-step(출발 STEP) 본문 마운트만 유지한다. */
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
    html[data-saju-nav-pending="1"] [class*="st-key-saju_router_step_mount_"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        max-height: 0 !important;
        overflow: hidden !important;
        pointer-events: none !important;
        opacity: 0 !important;
    }
    html[data-saju-nav-pending="1"][data-saju-step="1"] .st-key-saju_router_step_mount_01,
    html[data-saju-nav-pending="1"][data-saju-step="2"] .st-key-saju_router_step_mount_02,
    html[data-saju-nav-pending="1"][data-saju-step="3"] .st-key-saju_router_step_mount_03,
    html[data-saju-nav-pending="1"][data-saju-step="4"] .st-key-saju_router_step_mount_04,
    html[data-saju-nav-pending="1"][data-saju-step="5"] .st-key-saju_router_step_mount_05,
    html[data-saju-nav-pending="1"][data-saju-step="6"] .st-key-saju_router_step_mount_06,
    html[data-saju-nav-pending="1"][data-saju-step="7"] .st-key-saju_router_step_mount_07,
    html[data-saju-nav-pending="1"][data-saju-step="8"] .st-key-saju_router_step_mount_08,
    html[data-saju-nav-pending="1"][data-saju-step="9"] .st-key-saju_router_step_mount_09,
    html[data-saju-nav-pending="1"][data-saju-step="10"] .st-key-saju_router_step_mount_10,
    html[data-saju-nav-pending="1"][data-saju-step="11"] .st-key-saju_router_step_mount_11,
    html[data-saju-nav-pending="1"][data-saju-step="12"] .st-key-saju_router_step_mount_12 {
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
    }

    /* ===== STEP1 랜딩: 한지·먹·금박 톤 히어로 ===== */
    html.saju-home-step1 .main .block-container,
    html[data-saju-step="1"] .main .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
        scroll-padding-top: 0 !important;
        min-height: 0 !important;
    }
    html.saju-home-step1 .st-key-saju_router_step_mount_01 [data-testid="stVerticalBlock"],
    html[data-saju-step="1"] .st-key-saju_router_step_mount_01 [data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
        min-height: 0 !important;
    }
    html.saju-home-step1 .st-key-saju_router_step_mount_01 .saju-home-hero-banner,
    html[data-saju-step="1"] .st-key-saju_router_step_mount_01 .saju-home-hero-banner,
    html.saju-home-step1 #saju-home-hero-top.saju-home-hero-banner,
    html[data-saju-step="1"] #saju-home-hero-top.saju-home-hero-banner {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    html.saju-home-step1 .st-key-saju_landing_stack,
    html[data-saju-step="1"] .st-key-saju_landing_stack,
    html.saju-home-step1 .st-key-saju_landing_hero,
    html[data-saju-step="1"] .st-key-saju_landing_hero,
    html.saju-home-step1 .st-key-saju_landing_hero [data-testid="stElementContainer"],
    html[data-saju-step="1"] .st-key-saju_landing_hero [data-testid="stElementContainer"],
    html.saju-home-step1 .st-key-saju_landing_hero [data-testid="stVerticalBlock"],
    html[data-saju-step="1"] .st-key-saju_landing_hero [data-testid="stVerticalBlock"] {
        overflow: visible !important;
        max-height: none !important;
    }
    html.saju-home-step1 .st-key-saju_router_step_mount_01,
    html[data-saju-step="1"] .st-key-saju_router_step_mount_01 {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    html.saju-home-step1 .st-key-saju_landing_stack,
    html[data-saju-step="1"] .st-key-saju_landing_stack {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    html.saju-home-step1 .st-key-saju_landing_stack [data-testid="stVerticalBlock"],
    html[data-saju-step="1"] .st-key-saju_landing_stack [data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
    }
    html.saju-home-step1 .st-key-saju_landing_hero,
    html[data-saju-step="1"] .st-key-saju_landing_hero {
        order: 0 !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
    html.saju-home-step1 .st-key-step1_solar24,
    html[data-saju-step="1"] .st-key-step1_solar24 {
        order: 1 !important;
    }
    html.saju-home-step1 .st-key-saju_landing_hero [data-testid="stMarkdownContainer"],
    html[data-saju-step="1"] .st-key-saju_landing_hero [data-testid="stMarkdownContainer"] {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    html.saju-home-step1 .saju-landing-hero,
    html[data-saju-step="1"] .saju-landing-hero {
        padding-top: clamp(0.55rem, 2.2vw, 1.1rem) !important;
        padding-bottom: clamp(0.65rem, 2vw, 1rem) !important;
        scroll-margin-top: 0 !important;
        min-height: auto !important;
    }
    html.saju-home-step1 .saju-landing-hero--face.saju-landing-hero--intense,
    html[data-saju-step="1"] .saju-landing-hero--face.saju-landing-hero--intense {
        padding-top: clamp(0.5rem, 2vw, 0.85rem) !important;
        padding-bottom: clamp(0.6rem, 1.8vw, 0.9rem) !important;
        min-height: auto !important;
        justify-content: flex-start !important;
    }
    html.saju-home-step1 .st-key-step1_solar24,
    html[data-saju-step="1"] .st-key-step1_solar24 {
        margin-top: -0.2rem !important;
    }
    .st-key-saju_landing_stack {
        margin-top: 0;
        margin-bottom: 0.05rem;
        padding-top: 0;
        width: 100% !important;
        max-width: 100% !important;
        overflow: visible !important;
    }
    .saju-home-scroll-mark {
        display: none !important;
        height: 0 !important;
        width: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        border: 0 !important;
        overflow: hidden !important;
        pointer-events: none !important;
        opacity: 0 !important;
    }
    .st-key-saju_landing_stack [data-testid="stVerticalBlock"] > div {
        gap: 0.2rem !important;
    }
    html.saju-home-step1 .st-key-saju_landing_stack [data-testid="stVerticalBlock"] > div,
    html[data-saju-step="1"] .st-key-saju_landing_stack [data-testid="stVerticalBlock"] > div {
        gap: 0.06rem !important;
    }
    .st-key-saju_landing_hero,
    .st-key-saju_landing_hero [data-testid="stMarkdownContainer"],
    .st-key-saju_landing_hero [data-testid="stMarkdownContainer"] > div {
        overflow: visible !important;
        max-height: none !important;
        height: auto !important;
    }
    .st-key-saju_landing_hero [data-testid="stMarkdownContainer"],
    .st-key-saju_fortune_strip [data-testid="stMarkdownContainer"] {
        margin-bottom: 0 !important;
    }
    .saju-landing-hero {
        position: relative;
        width: 100%;
        max-width: min(1200px, 100%);
        margin-left: auto;
        margin-right: auto;
        box-sizing: border-box;
        padding: clamp(1.75rem, 5vw, 3rem) clamp(1.15rem, 4.5vw, 2.35rem)
            clamp(1.15rem, 3vw, 2rem);
        min-height: 0;
        height: auto;
        overflow: visible;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        text-align: center;
        border-radius: 0 0 clamp(20px, 4vw, 28px) clamp(20px, 4vw, 28px);
        background-color: #ebe3d6;
        background-image:
            radial-gradient(ellipse 120% 90% at 50% -15%, rgba(212, 175, 55, 0.18) 0%, transparent 52%),
            radial-gradient(ellipse 90% 70% at 110% 35%, rgba(15, 15, 26, 0.06) 0%, transparent 48%),
            radial-gradient(ellipse 70% 55% at -10% 75%, rgba(15, 15, 26, 0.05) 0%, transparent 42%),
            repeating-linear-gradient(
                90deg,
                rgba(212, 175, 55, 0.035) 0px,
                rgba(212, 175, 55, 0.035) 1px,
                transparent 1px,
                transparent 9px
            ),
            linear-gradient(165deg, #faf6ef 0%, #f0e8da 42%, #e4d6c4 100%),
            radial-gradient(ellipse 85% 70% at 0% 100%, rgba(62, 48, 32, 0.08), transparent 52%);
        box-shadow:
            inset 0 1px 0 rgba(255, 255, 255, 0.65),
            inset 0 -1px 0 rgba(201, 162, 39, 0.25),
            inset 0 0 80px rgba(212, 175, 55, 0.06),
            0 18px 56px rgba(42, 32, 18, 0.12),
            0 6px 22px rgba(212, 175, 55, 0.14);
        border: 1px solid rgba(201, 162, 39, 0.32);
        border-top: none;
    }
    .saju-landing-hero--premium .saju-landing-hero-topline,
    .saju-landing-hero--intense .saju-landing-hero-topline {
        position: absolute;
        top: 0;
        left: 6%;
        right: 6%;
        height: 4px;
        border-radius: 0 0 6px 6px;
        background: linear-gradient(
            90deg,
            transparent 0%,
            #8b6914 8%,
            #f5e6a8 32%,
            #fffdf5 50%,
            #f5e6a8 68%,
            #8b6914 92%,
            transparent 100%
        );
        box-shadow:
            0 2px 14px rgba(212, 175, 55, 0.65),
            0 0 24px rgba(245, 230, 168, 0.35);
        z-index: 4;
        pointer-events: none;
    }
    /* 홈 히어로 — 강렬한 시선 집중(비네트 + 스포트라이트) */
    .saju-landing-hero--intense {
        background-color: #1c1610;
        background-image:
            radial-gradient(ellipse 95% 75% at 50% 38%, rgba(255, 248, 232, 0.92) 0%, rgba(245, 232, 200, 0.55) 28%, transparent 62%),
            radial-gradient(ellipse 120% 100% at 50% -8%, rgba(212, 175, 55, 0.42) 0%, transparent 48%),
            radial-gradient(ellipse 80% 90% at 0% 50%, rgba(12, 10, 8, 0.55) 0%, transparent 55%),
            radial-gradient(ellipse 80% 90% at 100% 50%, rgba(12, 10, 8, 0.55) 0%, transparent 55%),
            linear-gradient(168deg, #2a2218 0%, #f7f0e4 38%, #efe4d2 52%, #2a2218 100%);
        border: 2px solid rgba(212, 175, 55, 0.72);
        border-top: none;
        box-shadow:
            inset 0 0 100px rgba(212, 175, 55, 0.14),
            inset 0 2px 0 rgba(255, 255, 255, 0.35),
            0 28px 72px rgba(18, 12, 6, 0.28),
            0 8px 28px rgba(212, 175, 55, 0.32),
            0 0 0 1px rgba(138, 109, 26, 0.25);
    }
    @keyframes saju-hero-shimmer {
        0% { transform: translateX(-130%) skewX(-14deg); opacity: 0; }
        12% { opacity: 0.85; }
        45% { transform: translateX(130%) skewX(-14deg); opacity: 0; }
        100% { transform: translateX(130%) skewX(-14deg); opacity: 0; }
    }
    @keyframes saju-hero-glow-pulse {
        0%, 100% { opacity: 0.72; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.04); }
    }
    @keyframes saju-hero-seal-float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-4px); }
    }
    .saju-landing-hero--face.saju-landing-hero--intense,
    .saju-landing-hero--luxe.saju-landing-hero--intense {
        --saju-hero-stack-gap: clamp(0.65rem, 2.2vw, 1rem);
        min-height: auto;
        padding: clamp(0.65rem, 2.5vw, 1.35rem) clamp(0.85rem, 3.5vw, 1.5rem)
            clamp(0.75rem, 2vw, 1.1rem);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        border-width: 2px;
        border-color: rgba(212, 175, 55, 0.55);
        border-top: none;
        box-shadow:
            inset 0 1px 0 rgba(255, 255, 255, 0.75),
            0 16px 48px rgba(180, 140, 50, 0.18),
            0 4px 20px rgba(212, 175, 55, 0.22);
    }
    .saju-landing-hero--face .saju-landing-hero-inner,
    .saju-landing-hero--luxe .saju-landing-hero-inner {
        flex: 0 1 auto;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        width: 100%;
        max-width: min(100%, 26rem);
        padding: 0;
        margin: 0 auto;
    }
    .saju-landing-hero-stack {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        gap: var(--saju-hero-stack-gap);
        width: 100%;
        box-sizing: border-box;
    }
    .saju-landing-hero--face .saju-landing-eyebrow {
        margin: 0;
        flex-shrink: 0;
    }
    .saju-landing-hero--face .saju-landing-logo-row--stacked,
    .saju-landing-hero--face .saju-landing-logo-row {
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: clamp(0.5rem, 1.8vw, 0.75rem) !important;
        margin: 0 !important;
        width: min(100%, 21.5rem);
        padding: clamp(0.95rem, 3vw, 1.3rem) clamp(1rem, 3.5vw, 1.35rem) !important;
        position: relative;
        z-index: 2;
        isolation: isolate;
    }
    .saju-landing-hero--face .saju-landing-logo-row::before {
        content: "";
        position: absolute;
        inset: -8% -6%;
        z-index: -1;
        border-radius: 22px;
        pointer-events: none;
        background: radial-gradient(
            ellipse 88% 95% at 50% 48%,
            rgba(255, 248, 228, 0.38) 0%,
            rgba(212, 175, 55, 0.14) 42%,
            transparent 72%
        );
        filter: blur(2px);
    }
    .saju-landing-hero--face .saju-landing-brand-block {
        width: 100%;
        text-align: center;
    }
    .saju-landing-hero--face .saju-landing-seal-wrap {
        margin: 0 auto;
    }
    .saju-landing-hero--face .saju-landing-seal-svg {
        width: clamp(4.5rem, 18vw, 6.5rem);
        height: auto;
    }
    .saju-landing-hero--face .saju-landing-tagline {
        margin: 0;
        flex-shrink: 0;
        width: 100%;
        max-width: 20rem;
        text-align: center;
        line-height: 1.5;
    }
    .saju-landing-hero--face .saju-landing-hero-shimmer {
        position: absolute;
        inset: 0;
        z-index: 1;
        pointer-events: none;
        overflow: hidden;
        border-radius: inherit;
    }
    .saju-landing-hero--face .saju-landing-hero-shimmer::after {
        content: "";
        position: absolute;
        top: -20%;
        left: 0;
        width: 42%;
        height: 140%;
        background: linear-gradient(
            105deg,
            transparent 0%,
            rgba(255, 252, 244, 0.08) 35%,
            rgba(255, 248, 220, 0.55) 50%,
            rgba(255, 252, 244, 0.08) 65%,
            transparent 100%
        );
        animation: saju-hero-shimmer 5.5s ease-in-out infinite;
    }
    .saju-landing-hero--face .saju-landing-hero-glow {
        animation: saju-hero-glow-pulse 4s ease-in-out infinite;
    }
    .saju-landing-hero--face .saju-landing-seal-wrap {
        animation: saju-hero-seal-float 5s ease-in-out infinite;
    }
    .saju-landing-hero--face .saju-landing-hero-topline {
        height: 5px;
        box-shadow:
            0 2px 18px rgba(212, 175, 55, 0.85),
            0 0 36px rgba(245, 230, 168, 0.5);
    }
    .saju-landing-hero--intense .saju-landing-hero-beam {
        position: absolute;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        background: conic-gradient(
            from 200deg at 50% 50%,
            transparent 0deg,
            rgba(245, 230, 168, 0.22) 40deg,
            rgba(212, 175, 55, 0.38) 90deg,
            rgba(245, 230, 168, 0.22) 140deg,
            transparent 200deg
        );
        opacity: 0.85;
        mix-blend-mode: soft-light;
    }
    .saju-landing-hero--intense .saju-landing-hero-glow {
        inset: 6% 10%;
        background: radial-gradient(
            ellipse 72% 68% at 50% 50%,
            rgba(255, 248, 220, 0.55) 0%,
            rgba(212, 175, 55, 0.28) 35%,
            rgba(212, 175, 55, 0.08) 55%,
            transparent 72%
        );
        filter: blur(4px);
    }
    .saju-landing-hero--face.saju-landing-hero--intense:not(.saju-landing-hero--nova),
    .saju-landing-hero--luxe.saju-landing-hero--intense:not(.saju-landing-hero--nova) {
        background-color: #fff9f0;
        background-image:
            radial-gradient(ellipse 110% 85% at 50% -5%, rgba(255, 252, 244, 1) 0%, rgba(250, 238, 210, 0.75) 42%, transparent 70%),
            radial-gradient(ellipse 90% 55% at 50% 105%, rgba(232, 201, 113, 0.28) 0%, transparent 58%),
            linear-gradient(175deg, #fffdf8 0%, #f8edd4 38%, #f0e0c0 100%);
    }
    .saju-landing-hero--face .saju-landing-illu-wrap,
    .saju-landing-hero--luxe .saju-landing-illu-wrap {
        opacity: 0.28;
    }
    .saju-landing-hero--intense .saju-landing-illu-wrap {
        opacity: 0.62;
    }
    .saju-landing-hero--intense .saju-landing-corner {
        opacity: 1;
        border-color: rgba(232, 201, 113, 0.95);
        border-width: 3px;
        box-shadow: 0 0 18px rgba(212, 175, 55, 0.35);
    }
    .saju-landing-eyebrow {
        margin: 0;
        padding: 0.28rem 0.85rem;
        display: inline-block;
        border-radius: 999px;
        font-size: clamp(0.62rem, 1.8vw, 0.74rem);
        font-weight: 800;
        letter-spacing: 0.1em;
        color: #f8f0dc;
        background: linear-gradient(135deg, #3d3020 0%, #1a1410 100%);
        border: 1px solid rgba(232, 201, 113, 0.55);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.22);
    }
    .saju-landing-hero--intense .saju-landing-logo-row {
        background: linear-gradient(
            145deg,
            rgba(22, 18, 14, 0.82) 0%,
            rgba(48, 38, 26, 0.62) 48%,
            rgba(22, 18, 14, 0.78) 100%
        );
        border: 1.5px solid rgba(232, 201, 113, 0.62);
        box-shadow:
            inset 0 1px 0 rgba(255, 255, 255, 0.12),
            0 16px 44px rgba(0, 0, 0, 0.28),
            0 0 32px rgba(212, 175, 55, 0.18);
        backdrop-filter: blur(6px);
    }
    .saju-landing-hero--luxe.saju-landing-hero--intense:not(.saju-landing-hero--nova) .saju-landing-logo-row {
        background: linear-gradient(
            165deg,
            rgba(255, 255, 252, 0.94) 0%,
            rgba(255, 246, 228, 0.9) 45%,
            rgba(255, 238, 210, 0.88) 100%
        );
        border: 1.5px solid rgba(212, 175, 55, 0.42);
        box-shadow:
            inset 0 1px 0 rgba(255, 255, 255, 0.9),
            0 14px 36px rgba(212, 175, 55, 0.22),
            0 0 28px rgba(255, 248, 220, 0.35);
        backdrop-filter: blur(8px);
    }
    .saju-landing-hero--intense .saju-landing-kicker {
        color: rgba(248, 236, 200, 0.88);
        font-weight: 700;
        letter-spacing: 0.14em;
        text-shadow: 0 1px 8px rgba(0, 0, 0, 0.35);
    }
    .saju-landing-hero--luxe.saju-landing-hero--intense:not(.saju-landing-hero--nova) .saju-landing-kicker {
        color: #6b5420;
        text-shadow: none;
    }
    .saju-landing-hero--luxe.saju-landing-hero--intense:not(.saju-landing-hero--nova) .saju-landing-eyebrow {
        color: #5c4210;
        background: linear-gradient(135deg, #fffef9 0%, #f5e6b8 48%, #e8d49a 100%);
        border: 1px solid rgba(201, 162, 39, 0.45);
        box-shadow: 0 4px 14px rgba(212, 175, 55, 0.2);
    }
    .saju-landing-hero--luxe.saju-landing-hero--intense:not(.saju-landing-hero--nova) .saju-landing-tagline {
        color: #3d3020;
    }

    /* ===== 홈 히어로 NOVA — 현대적·고대비·시선 집중 ===== */
    @keyframes saju-nova-bg-shift {
        0%, 100% { background-position: 0% 40%; }
        50% { background-position: 100% 60%; }
    }
    @keyframes saju-nova-aurora {
        0%, 100% { opacity: 0.55; transform: scale(1) rotate(0deg); }
        50% { opacity: 0.95; transform: scale(1.06) rotate(2deg); }
    }
    @keyframes saju-nova-rays {
        0% { transform: rotate(0deg); opacity: 0.35; }
        100% { transform: rotate(360deg); opacity: 0.55; }
    }
    @keyframes saju-nova-spark {
        0%, 100% { opacity: 0; transform: scale(0.4); }
        45% { opacity: 1; transform: scale(1); }
        70% { opacity: 0; transform: scale(0.2); }
    }
    @keyframes saju-nova-brand-glow {
        0%, 100% { filter: drop-shadow(0 0 18px rgba(255, 220, 120, 0.45)); }
        50% { filter: drop-shadow(0 0 32px rgba(255, 248, 200, 0.85)); }
    }
    .saju-landing-hero--nova {
        position: relative;
        overflow: hidden;
        isolation: isolate;
    }
    .saju-landing-hero--luxe.saju-landing-hero--intense.saju-landing-hero--nova {
        background-color: #08060f !important;
        background-image:
            radial-gradient(ellipse 130% 90% at 50% -25%, rgba(255, 214, 110, 0.55) 0%, transparent 58%),
            radial-gradient(ellipse 70% 55% at 92% 88%, rgba(124, 92, 255, 0.42) 0%, transparent 52%),
            radial-gradient(ellipse 65% 50% at 8% 92%, rgba(212, 175, 55, 0.35) 0%, transparent 48%),
            linear-gradient(155deg, #0c0a14 0%, #1a1230 38%, #0f0c18 72%, #050408 100%) !important;
        background-size: 220% 220%;
        animation: saju-nova-bg-shift 14s ease-in-out infinite;
        border: 1px solid rgba(255, 220, 140, 0.42) !important;
        box-shadow:
            0 28px 72px rgba(0, 0, 0, 0.55),
            0 0 0 1px rgba(255, 230, 160, 0.12),
            0 0 64px rgba(212, 175, 55, 0.28),
            inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
    }
    .saju-landing-hero--nova .saju-landing-hero-aurora {
        position: absolute;
        inset: -15% -10%;
        z-index: 0;
        pointer-events: none;
        background:
            radial-gradient(ellipse 55% 45% at 20% 30%, rgba(255, 200, 80, 0.35) 0%, transparent 70%),
            radial-gradient(ellipse 50% 40% at 80% 25%, rgba(160, 120, 255, 0.28) 0%, transparent 68%),
            radial-gradient(ellipse 60% 50% at 50% 80%, rgba(255, 240, 180, 0.2) 0%, transparent 72%);
        filter: blur(18px);
        animation: saju-nova-aurora 8s ease-in-out infinite;
        mix-blend-mode: screen;
    }
    .saju-landing-hero--nova .saju-landing-hero-mesh {
        position: absolute;
        inset: 0;
        z-index: 0;
        pointer-events: none;
        opacity: 0.22;
        background-image:
            linear-gradient(rgba(255, 220, 140, 0.14) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 220, 140, 0.1) 1px, transparent 1px);
        background-size: 28px 28px;
        mask-image: radial-gradient(ellipse 85% 75% at 50% 45%, #000 20%, transparent 72%);
    }
    .saju-landing-hero--nova .saju-landing-hero-rays {
        position: absolute;
        inset: -40%;
        z-index: 0;
        pointer-events: none;
        background: conic-gradient(
            from 0deg at 50% 50%,
            transparent 0deg,
            rgba(255, 230, 160, 0.12) 25deg,
            transparent 50deg,
            rgba(212, 175, 55, 0.18) 90deg,
            transparent 130deg,
            rgba(255, 248, 220, 0.1) 200deg,
            transparent 280deg
        );
        animation: saju-nova-rays 28s linear infinite;
        mix-blend-mode: screen;
    }
    .saju-landing-hero--nova .saju-landing-illu-wrap {
        opacity: 0.55 !important;
        mix-blend-mode: screen;
    }
    .saju-landing-hero--nova .saju-landing-sparks {
        position: absolute;
        inset: 0;
        z-index: 1;
        pointer-events: none;
        overflow: hidden;
    }
    .saju-landing-hero--nova .saju-landing-spark {
        position: absolute;
        width: 4px;
        height: 4px;
        border-radius: 50%;
        background: #fff8dc;
        box-shadow: 0 0 10px 2px rgba(255, 230, 150, 0.9);
        animation: saju-nova-spark 3.2s ease-in-out infinite;
    }
    .saju-landing-hero--nova .saju-landing-spark:nth-child(1) { top: 18%; left: 12%; animation-delay: 0s; }
    .saju-landing-hero--nova .saju-landing-spark:nth-child(2) { top: 28%; right: 14%; animation-delay: 0.6s; }
    .saju-landing-hero--nova .saju-landing-spark:nth-child(3) { top: 62%; left: 8%; animation-delay: 1.1s; }
    .saju-landing-hero--nova .saju-landing-spark:nth-child(4) { top: 72%; right: 10%; animation-delay: 1.8s; }
    .saju-landing-hero--nova .saju-landing-spark:nth-child(5) { top: 42%; left: 48%; animation-delay: 0.3s; }
    .saju-landing-hero--nova .saju-landing-spark:nth-child(6) { top: 12%; left: 55%; animation-delay: 2.2s; }
    .saju-landing-hero--nova .saju-landing-hero-beam {
        opacity: 1 !important;
        mix-blend-mode: screen;
    }
    .saju-landing-hero--nova .saju-landing-hero-shimmer::after {
        animation-duration: 3.8s;
        background: linear-gradient(
            105deg,
            transparent 0%,
            rgba(255, 252, 244, 0.05) 30%,
            rgba(255, 248, 220, 0.75) 50%,
            rgba(255, 252, 244, 0.05) 70%,
            transparent 100%
        );
    }
    .saju-landing-hero--nova .saju-landing-hero-topline {
        height: 4px;
        box-shadow:
            0 0 24px rgba(255, 220, 120, 0.95),
            0 0 48px rgba(212, 175, 55, 0.55);
    }
    .saju-landing-hero--nova .saju-landing-corner {
        border-color: rgba(255, 230, 160, 0.9);
        box-shadow: 0 0 22px rgba(255, 215, 120, 0.45);
    }
    .saju-landing-hero--nova .saju-landing-eyebrow {
        color: #1a1008 !important;
        background: linear-gradient(90deg, #ffd86a 0%, #fff8e8 45%, #ffd86a 100%) !important;
        border: 1px solid rgba(255, 240, 200, 0.65) !important;
        box-shadow: 0 4px 20px rgba(255, 200, 80, 0.45) !important;
        letter-spacing: 0.14em;
        text-transform: uppercase;
    }
    .saju-landing-hero--nova .saju-landing-logo-row {
        background: linear-gradient(
            160deg,
            rgba(12, 8, 22, 0.88) 0%,
            rgba(32, 22, 48, 0.72) 50%,
            rgba(10, 8, 18, 0.9) 100%
        ) !important;
        border: 1px solid rgba(255, 220, 140, 0.38) !important;
        box-shadow:
            inset 0 1px 0 rgba(255, 255, 255, 0.1),
            0 20px 48px rgba(0, 0, 0, 0.45),
            0 0 48px rgba(212, 175, 55, 0.32) !important;
        backdrop-filter: blur(12px);
    }
    .saju-landing-hero--nova .saju-landing-logo-row::before {
        background: radial-gradient(
            ellipse 90% 95% at 50% 50%,
            rgba(255, 220, 120, 0.28) 0%,
            rgba(124, 92, 255, 0.12) 45%,
            transparent 72%
        ) !important;
    }
    .saju-landing-hero--nova .saju-landing-brand {
        background: linear-gradient(
            118deg,
            #fffef8 0%,
            #ffe566 18%,
            #ffffff 38%,
            #ffd24a 58%,
            #fff9e6 78%,
            #d4af37 100%
        );
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: saju-nova-brand-glow 4s ease-in-out infinite;
        filter: none;
    }
    .saju-landing-hero--nova .saju-landing-kicker {
        color: rgba(255, 236, 200, 0.92) !important;
        font-weight: 800 !important;
        letter-spacing: 0.22em !important;
        font-size: clamp(0.62rem, 1.9vw, 0.76rem) !important;
        text-shadow: 0 0 18px rgba(255, 200, 80, 0.55);
    }
    .saju-landing-hero--nova .saju-landing-tagline {
        color: rgba(255, 248, 235, 0.95) !important;
        font-weight: 800 !important;
        text-shadow: 0 2px 16px rgba(0, 0, 0, 0.55);
    }
    .saju-landing-hero--nova .saju-landing-tagline-accent {
        background: linear-gradient(105deg, #fff8e8 0%, #ffe566 35%, #ffffff 50%, #ffd24a 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        filter: drop-shadow(0 0 12px rgba(255, 220, 100, 0.65));
    }
    .saju-landing-hero--nova .saju-landing-seal-wrap {
        filter: drop-shadow(0 0 28px rgba(255, 215, 100, 0.65))
            drop-shadow(0 12px 28px rgba(0, 0, 0, 0.5));
    }
    @media (prefers-reduced-motion: reduce) {
        .saju-landing-hero--luxe.saju-landing-hero--intense.saju-landing-hero--nova,
        .saju-landing-hero--nova .saju-landing-hero-aurora,
        .saju-landing-hero--nova .saju-landing-hero-rays,
        .saju-landing-hero--nova .saju-landing-spark,
        .saju-landing-hero--nova .saju-landing-brand,
        .saju-landing-hero--nova .saju-landing-hero-shimmer::after {
            animation: none !important;
        }
    }
  /* PC 홈: 모바일과 동일 NOVA 다크 배너(크림 라이트 덮어쓰기 방지) */
    @media (min-width: 769px) {
        html.saju-home-step1 .main .block-container,
        html[data-saju-step="1"] .main .block-container {
            padding-left: 0.45rem !important;
            padding-right: 0.45rem !important;
            padding-top: 0 !important;
        }
        html.saju-home-step1 .st-key-saju_landing_hero,
        html[data-saju-step="1"] .st-key-saju_landing_hero {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        .saju-landing-hero--face.saju-landing-hero--intense.saju-landing-hero--nova,
        .saju-landing-hero--luxe.saju-landing-hero--intense.saju-landing-hero--nova {
            min-height: auto !important;
            padding: max(0.65rem, env(safe-area-inset-top, 0px)) 0.85rem 0.75rem !important;
            border-radius: 0 0 clamp(18px, 2vw, 22px) clamp(18px, 2vw, 22px) !important;
        }
        .saju-landing-hero--nova .saju-landing-hero-beam,
        .saju-landing-hero--nova .saju-landing-hero-shimmer {
            opacity: 0.7 !important;
        }
        .saju-landing-hero--nova .saju-landing-illu-wrap {
            opacity: 0.55 !important;
        }
    }

    .saju-landing-hero--intense .saju-landing-brand {
        font-size: clamp(2.85rem, 9vw, 5.1rem);
        letter-spacing: 0.08em;
        filter:
            drop-shadow(0 2px 0 rgba(0, 0, 0, 0.25))
            drop-shadow(0 6px 20px rgba(212, 175, 55, 0.55))
            drop-shadow(0 0 40px rgba(245, 230, 168, 0.35));
    }
    .saju-landing-hero--face .saju-landing-brand {
        font-size: clamp(2.15rem, 7.2vw, 3.35rem);
        line-height: 1.1;
        margin: 0;
        filter:
            drop-shadow(0 3px 0 rgba(0, 0, 0, 0.32))
            drop-shadow(0 8px 28px rgba(212, 175, 55, 0.72))
            drop-shadow(0 0 56px rgba(255, 248, 220, 0.45));
    }
    .saju-landing-hero--intense .saju-landing-seal-wrap {
        filter: drop-shadow(0 12px 32px rgba(0, 0, 0, 0.45))
            drop-shadow(0 0 28px rgba(212, 175, 55, 0.55));
    }
    .saju-landing-tagline-accent {
        font-weight: 900;
        background: linear-gradient(105deg, #6d4f0f 0%, #d4af37 40%, #fff8e8 55%, #c9a227 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.15));
    }
    .saju-landing-hero--intense .saju-landing-tagline {
        font-size: clamp(1.22rem, 4.2vw, 1.72rem);
        font-weight: 800;
        color: #1a1410;
        margin: 0;
        text-shadow:
            0 1px 0 rgba(255, 255, 255, 0.65),
            0 2px 12px rgba(212, 175, 55, 0.25);
    }
    .saju-landing-hero--face .saju-landing-tagline {
        font-size: clamp(0.98rem, 3.2vw, 1.28rem);
    }
    .saju-landing-hero-glow {
        position: absolute;
        inset: 8% 12%;
        pointer-events: none;
        z-index: 0;
        border-radius: 50%;
        background: radial-gradient(
            ellipse 70% 55% at 50% 45%,
            rgba(212, 175, 55, 0.22) 0%,
            rgba(212, 175, 55, 0.06) 42%,
            transparent 72%
        );
        filter: blur(8px);
    }
    .saju-landing-corner {
        position: absolute;
        width: clamp(2.6rem, 9vw, 4rem);
        height: clamp(2.6rem, 9vw, 4rem);
        pointer-events: none;
        z-index: 2;
        opacity: 0.88;
        border-color: rgba(212, 175, 55, 0.82);
        border-style: solid;
        box-shadow: 0 0 12px rgba(212, 175, 55, 0.12);
    }
    .saju-landing-corner-tl {
        top: clamp(1rem, 3.2vw, 1.45rem);
        left: clamp(0.75rem, 2.5vw, 1.1rem);
        border-width: 2.5px 0 0 2.5px;
        border-radius: 14px 0 0 0;
    }
    .saju-landing-corner-tr {
        top: clamp(1rem, 3.2vw, 1.45rem);
        right: clamp(0.75rem, 2.5vw, 1.1rem);
        border-width: 2.5px 2.5px 0 0;
        border-radius: 0 14px 0 0;
    }
    .saju-landing-corner-bl {
        bottom: clamp(1rem, 3.2vw, 1.45rem);
        left: clamp(0.75rem, 2.5vw, 1.1rem);
        border-width: 0 0 2.5px 2.5px;
        border-radius: 0 0 0 14px;
    }
    .saju-landing-corner-br {
        bottom: clamp(1rem, 3.2vw, 1.45rem);
        right: clamp(0.75rem, 2.5vw, 1.1rem);
        border-width: 0 2.5px 2.5px 0;
        border-radius: 0 0 14px 0;
    }
    .saju-landing-hero--face .saju-landing-corner-tl,
    .saju-landing-hero--face .saju-landing-corner-tr,
    .saju-landing-hero--face .saju-landing-corner-bl,
    .saju-landing-hero--face .saju-landing-corner-br {
        top: auto;
        bottom: auto;
    }
    .saju-landing-hero--face .saju-landing-corner-tl {
        top: clamp(0.85rem, 2.8vw, 1.25rem);
        left: clamp(0.75rem, 2.5vw, 1.1rem);
    }
    .saju-landing-hero--face .saju-landing-corner-tr {
        top: clamp(0.85rem, 2.8vw, 1.25rem);
        right: clamp(0.75rem, 2.5vw, 1.1rem);
    }
    .saju-landing-hero--face .saju-landing-corner-bl {
        bottom: clamp(0.85rem, 2.8vw, 1.25rem);
        left: clamp(0.75rem, 2.5vw, 1.1rem);
    }
    .saju-landing-hero--face .saju-landing-corner-br {
        bottom: clamp(0.85rem, 2.8vw, 1.25rem);
        right: clamp(0.75rem, 2.5vw, 1.1rem);
    }
    .saju-landing-illu-wrap {
        position: absolute;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0.42;
        overflow: hidden;
        border-radius: inherit;
    }
    .saju-landing-illus-svg,
    .saju-landing-pattern-svg {
        width: min(98%, 42rem);
        max-height: min(70%, 22rem);
        height: auto;
        flex-shrink: 0;
        filter: drop-shadow(0 0 32px rgba(212, 175, 55, 0.14));
    }
    @media (max-width: 768px) {
        .st-key-saju_landing_stack {
            margin-top: 0 !important;
        }
        .main .block-container:has(.st-key-saju_landing_stack) {
            padding-top: 0 !important;
            margin-top: 0 !important;
            min-height: 0 !important;
        }
        [data-testid="stAppViewContainer"]:has(.st-key-saju_landing_stack),
        .stApp [data-testid="stAppViewContainer"]:has(.st-key-saju_landing_stack),
        .stApp [data-testid="stAppViewContainer"]:has(.st-key-saju_landing_stack) > .main,
        .stApp section.main:has(.st-key-saju_landing_stack),
        [data-testid="stMain"]:has(.st-key-saju_landing_stack) {
            padding-top: 0 !important;
            margin-top: 0 !important;
            align-items: flex-start !important;
            justify-content: flex-start !important;
        }
        .st-key-saju_router_step_mount_01:has(.st-key-saju_landing_stack),
        .st-key-saju_router_step_mount_01:has(.st-key-saju_landing_stack) [data-testid="stVerticalBlock"],
        .st-key-saju_router_step_mount_01:has(.st-key-saju_landing_stack) [data-testid="stElementContainer"] {
            margin-top: 0 !important;
            padding-top: 0 !important;
            gap: 0 !important;
            row-gap: 0 !important;
        }
        .st-key-saju_landing_stack:has(.st-key-saju_landing_hero) {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        .stApp [data-testid="stAppViewContainer"],
        .stApp [data-testid="stAppViewContainer"] > .main,
        .stApp section.main {
            padding-top: 0 !important;
        }
        .main .block-container {
            padding-top: 0 !important;
            padding-left: 0.45rem !important;
            padding-right: 0.45rem !important;
        }
        .st-key-saju_landing_hero {
            display: block !important;
            margin-top: 0 !important;
            overflow: visible !important;
        }
        html.saju-home-step1 .st-key-saju_router_step_mount_01,
        html[data-saju-step="1"] .st-key-saju_router_step_mount_01,
        html.saju-home-step1 .st-key-saju_router_step_mount_01 [data-testid="stVerticalBlock"],
        html[data-saju-step="1"] .st-key-saju_router_step_mount_01 [data-testid="stVerticalBlock"] {
            margin-top: 0 !important;
            padding-top: 0 !important;
            gap: 0 !important;
        }
        #saju-step-top-anchor {
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        html.saju-home-step1 [data-testid="stAppViewContainer"],
        html[data-saju-step="1"] [data-testid="stAppViewContainer"],
        html.saju-home-step1 [data-testid="stMain"],
        html[data-saju-step="1"] [data-testid="stMain"],
        html.saju-home-step1 section.main,
        html[data-saju-step="1"] section.main {
            align-items: flex-start !important;
            justify-content: flex-start !important;
        }
        html.saju-home-step1 .main .block-container,
        html[data-saju-step="1"] .main .block-container {
            padding-top: 0 !important;
            margin-top: 0 !important;
            min-height: 0 !important;
        }
        html.saju-home-step1 .st-key-saju_router_step_mount_01 [data-testid="stVerticalBlock"],
        html[data-saju-step="1"] .st-key-saju_router_step_mount_01 [data-testid="stVerticalBlock"] {
            min-height: 0 !important;
            justify-content: flex-start !important;
            align-items: stretch !important;
        }
        html.saju-home-step1 .st-key-saju_landing_stack,
        html[data-saju-step="1"] .st-key-saju_landing_stack {
            margin-top: 0 !important;
        }
        html.saju-home-step1 .st-key-saju_landing_hero,
        html[data-saju-step="1"] .st-key-saju_landing_hero {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        html.saju-home-step1 .saju-landing-hero,
        html[data-saju-step="1"] .saju-landing-hero {
            padding-top: max(0.2rem, env(safe-area-inset-top, 0px)) !important;
            padding-bottom: 0.55rem !important;
            min-height: auto !important;
            justify-content: flex-start !important;
        }
        .saju-landing-hero {
            border-radius: 0 0 18px 18px;
        }
        html.saju-home-step1 .saju-landing-hero--face.saju-landing-hero--intense,
        html[data-saju-step="1"] .saju-landing-hero--face.saju-landing-hero--intense,
        html.saju-home-step1 .saju-landing-hero--luxe.saju-landing-hero--intense,
        html[data-saju-step="1"] .saju-landing-hero--luxe.saju-landing-hero--intense,
        .st-key-saju_landing_hero .saju-landing-hero--luxe.saju-landing-hero--intense {
            --saju-hero-stack-gap: clamp(0.45rem, 1.8vw, 0.7rem);
            min-height: auto !important;
            padding: max(0.12rem, env(safe-area-inset-top, 0px)) 0.55rem 0.55rem !important;
            overflow: hidden !important;
            justify-content: flex-start !important;
            border-radius: 0 0 clamp(16px, 4.5vw, 20px) clamp(16px, 4.5vw, 20px) !important;
        }
        html.saju-home-step1 .saju-landing-hero.saju-landing-hero--nova,
        html[data-saju-step="1"] .saju-landing-hero.saju-landing-hero--nova,
        html.saju-home-step1 .saju-landing-hero--luxe.saju-landing-hero--intense.saju-landing-hero--nova,
        html[data-saju-step="1"] .saju-landing-hero--luxe.saju-landing-hero--intense.saju-landing-hero--nova,
        .st-key-saju_landing_hero .saju-landing-hero--nova {
            background-color: #08060f !important;
            background-image:
                radial-gradient(ellipse 130% 90% at 50% -25%, rgba(255, 214, 110, 0.55) 0%, transparent 58%),
                radial-gradient(ellipse 70% 55% at 92% 88%, rgba(124, 92, 255, 0.42) 0%, transparent 52%),
                radial-gradient(ellipse 65% 50% at 8% 92%, rgba(212, 175, 55, 0.35) 0%, transparent 48%),
                linear-gradient(155deg, #0c0a14 0%, #1a1230 38%, #0f0c18 72%, #050408 100%) !important;
            border: 1px solid rgba(255, 220, 140, 0.42) !important;
            box-shadow:
                0 28px 72px rgba(0, 0, 0, 0.55),
                0 0 0 1px rgba(255, 230, 160, 0.12),
                0 0 64px rgba(212, 175, 55, 0.28),
                inset 0 1px 0 rgba(255, 255, 255, 0.1) !important;
        }
        html.saju-home-step1 .saju-landing-hero--nova .saju-landing-hero-beam,
        html[data-saju-step="1"] .saju-landing-hero--nova .saju-landing-hero-beam,
        html.saju-home-step1 .saju-landing-hero--nova .saju-landing-hero-shimmer,
        html[data-saju-step="1"] .saju-landing-hero--nova .saju-landing-hero-shimmer {
            opacity: 0.7 !important;
        }
        html.saju-home-step1 .st-key-step1_solar24,
        html[data-saju-step="1"] .st-key-step1_solar24 {
            margin-top: -0.25rem !important;
        }
        .saju-landing-hero--intense .saju-landing-hero-shimmer,
        .saju-landing-hero--intense .saju-landing-hero-beam {
            opacity: 0.22 !important;
        }
        .saju-landing-hero--luxe .saju-landing-hero-beam {
            opacity: 0.35 !important;
        }
        .saju-landing-hero--nova .saju-landing-hero-beam,
        .saju-landing-hero--nova .saju-landing-hero-shimmer {
            opacity: 0.7 !important;
        }
        .saju-landing-hero--nova .saju-landing-hero-mesh {
            opacity: 0.16 !important;
        }
        .saju-landing-hero--face .saju-landing-hero-inner {
            max-width: 100% !important;
            padding-left: 0.35rem !important;
            padding-right: 0.35rem !important;
        }
        .saju-landing-hero--face .saju-landing-logo-row {
            width: min(100%, 19.5rem) !important;
            padding: 0.85rem 0.9rem !important;
        }
        .saju-landing-hero--face .saju-landing-eyebrow {
            font-size: clamp(0.58rem, 2.4vw, 0.68rem) !important;
            letter-spacing: 0.06em !important;
            padding: 0.24rem 0.7rem !important;
        }
        .saju-landing-hero--face .saju-landing-brand {
            font-size: clamp(1.9rem, 7vw, 2.45rem) !important;
        }
        .saju-landing-hero--face .saju-landing-kicker {
            font-size: clamp(0.68rem, 2.6vw, 0.8rem) !important;
            letter-spacing: 0.06em !important;
            max-width: 16rem !important;
        }
        .saju-landing-hero--face .saju-landing-tagline {
            font-size: clamp(0.9rem, 3.4vw, 1.02rem) !important;
            max-width: 17rem !important;
        }
        .saju-landing-hero--face .saju-landing-seal-svg {
            width: clamp(3.75rem, 15vw, 4.65rem) !important;
        }
        .saju-landing-hero--intense .saju-landing-corner {
            width: clamp(1.65rem, 5.5vw, 2.1rem) !important;
            height: clamp(1.65rem, 5.5vw, 2.1rem) !important;
            opacity: 0.62 !important;
        }
        .st-key-step1_solar24 {
            max-width: min(100%, 480px) !important;
            margin-left: auto !important;
            margin-right: auto !important;
            margin-top: 0.15rem !important;
        }
        .saju-step1-solar24-heading {
            margin-bottom: 0.25rem !important;
        }
        .st-key-step1_solar24 [data-testid="stHtml"],
        .st-key-step1_solar24 iframe {
            height: auto !important;
            max-height: none !important;
            min-height: 500px !important;
            overflow: visible !important;
        }
    }
    .saju-landing-hero::before {
        content: "";
        position: absolute;
        inset: 0;
        opacity: 0.055;
        pointer-events: none;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
        mix-blend-mode: multiply;
    }
    .saju-landing-hero::after {
        content: "";
        position: absolute;
        inset: 0;
        pointer-events: none;
        background: radial-gradient(circle at 50% 88%, rgba(212, 175, 55, 0.12) 0%, transparent 45%);
    }
    .saju-landing-hero--face::after {
        background:
            radial-gradient(ellipse 80% 50% at 50% 100%, rgba(212, 175, 55, 0.14) 0%, transparent 55%),
            radial-gradient(ellipse 80% 50% at 50% 0%, rgba(212, 175, 55, 0.1) 0%, transparent 55%);
    }
    .saju-landing-hero-inner {
        position: relative;
        z-index: 1;
        max-width: 46rem;
        width: 100%;
        padding-top: clamp(0.35rem, 1.5vw, 0.75rem);
    }
    html.saju-dark-tone .saju-landing-hero {
        background-color: #0c0c14;
        background-image:
            radial-gradient(ellipse 120% 80% at 50% -20%, rgba(212, 175, 55, 0.14) 0%, transparent 55%),
            radial-gradient(ellipse 85% 60% at 105% 40%, rgba(212, 175, 55, 0.06) 0%, transparent 45%),
            repeating-linear-gradient(
                92deg,
                rgba(212, 175, 55, 0.045) 0px,
                rgba(212, 175, 55, 0.045) 1px,
                transparent 1px,
                transparent 8px
            ),
            linear-gradient(168deg, #16182a 0%, #0a0a12 42%, #101828 100%),
            radial-gradient(ellipse 80% 65% at 0% 100%, rgba(212, 175, 55, 0.06), transparent 50%);
        border-bottom: 1px solid rgba(212, 175, 55, 0.28);
        box-shadow:
            inset 0 0 120px rgba(0, 0, 0, 0.35),
            0 14px 48px rgba(0, 0, 0, 0.45);
    }
    html.saju-dark-tone .saju-landing-hero::before {
        opacity: 0.09;
        mix-blend-mode: soft-light;
    }
    html.saju-dark-tone .saju-landing-kicker {
        color: rgba(212, 175, 55, 0.55);
    }
    html.saju-dark-tone .saju-landing-tagline {
        color: rgba(245, 240, 230, 0.94);
    }
    html.saju-dark-tone .saju-landing-sub {
        color: rgba(200, 198, 210, 0.78);
    }
    html.saju-dark-tone .saju-landing-illu-wrap {
        opacity: 0.28;
    }
    html.saju-dark-tone .saju-landing-logo-row {
        background: rgba(18, 16, 28, 0.55);
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
    }
    html.saju-dark-tone .saju-landing-kicker {
        color: rgba(212, 175, 55, 0.62);
        letter-spacing: 0.1em;
    }
    html.saju-dark-tone .saju-landing-hero--premium .saju-landing-hero-topline,
    html.saju-dark-tone .saju-landing-hero--intense .saju-landing-hero-topline {
        opacity: 0.95;
    }
    html.saju-dark-tone .saju-landing-hero--intense {
        background-color: #050508;
        background-image:
            radial-gradient(ellipse 90% 70% at 50% 40%, rgba(212, 175, 55, 0.22) 0%, rgba(18, 16, 28, 0.85) 45%, transparent 68%),
            radial-gradient(ellipse 120% 90% at 50% -12%, rgba(232, 185, 35, 0.35) 0%, transparent 52%),
            radial-gradient(ellipse 70% 80% at 0% 55%, rgba(0, 0, 0, 0.75) 0%, transparent 58%),
            radial-gradient(ellipse 70% 80% at 100% 55%, rgba(0, 0, 0, 0.75) 0%, transparent 58%),
            linear-gradient(168deg, #0a0a12 0%, #1a1828 38%, #12121c 100%);
        border-color: rgba(212, 175, 55, 0.55);
        box-shadow:
            inset 0 0 120px rgba(212, 175, 55, 0.1),
            0 24px 64px rgba(0, 0, 0, 0.55),
            0 0 48px rgba(212, 175, 55, 0.12);
    }
    html.saju-dark-tone .saju-landing-hero--intense .saju-landing-logo-row {
        background: linear-gradient(
            145deg,
            rgba(8, 8, 16, 0.92) 0%,
            rgba(28, 24, 40, 0.78) 50%,
            rgba(8, 8, 16, 0.9) 100%
        );
        border-color: rgba(212, 175, 55, 0.48);
    }
    html.saju-dark-tone .saju-landing-hero--intense .saju-landing-tagline {
        color: rgba(252, 248, 240, 0.96);
        text-shadow: 0 2px 16px rgba(0, 0, 0, 0.45);
    }
    html.saju-dark-tone .saju-landing-eyebrow {
        color: #f5e6a8;
        background: linear-gradient(135deg, #1a1828 0%, #0a0a12 100%);
        border-color: rgba(212, 175, 55, 0.45);
    }
    .saju-landing-free-badge {
        display: inline-block;
        margin: 0 auto 0.85rem;
        padding: 0.45rem 1.15rem;
        border-radius: 999px;
        font-size: clamp(0.95rem, 2.2vw, 1.15rem);
        font-weight: 800;
        letter-spacing: 0.04em;
        color: #1a1208;
        background: linear-gradient(135deg, #e8c547 0%, #d4af37 48%, #c9a227 100%);
        border: 1px solid rgba(138, 109, 26, 0.55);
        box-shadow: 0 4px 18px rgba(212, 175, 55, 0.28);
    }
    .saju-landing-logo-row {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.65rem;
        padding: clamp(0.5rem, 2vw, 0.85rem) clamp(0.65rem, 3vw, 1.25rem);
        border-radius: 18px;
        background: rgba(255, 252, 245, 0.35);
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.5);
    }
    @media (min-width: 520px) {
        .saju-landing-logo-row:not(.saju-landing-logo-row--stacked) {
            flex-direction: row;
            justify-content: center;
            align-items: center;
            gap: 1.5rem;
        }
    }
    @media (min-width: 769px) {
        .saju-landing-hero--face.saju-landing-hero--intense:not(.saju-landing-hero--nova) {
            --saju-hero-stack-gap: clamp(0.9rem, 2vw, 1.2rem);
            min-height: clamp(15.5rem, 28vw, 18.5rem);
            padding: clamp(1.85rem, 3.5vw, 2.45rem) clamp(1.25rem, 3vw, 2rem);
        }
        .saju-landing-hero--face.saju-landing-hero--intense:not(.saju-landing-hero--nova) .saju-landing-logo-row {
            width: min(100%, 23rem);
            padding: clamp(1.05rem, 2.2vw, 1.4rem) clamp(1.15rem, 2.5vw, 1.5rem) !important;
        }
        .saju-landing-hero--face.saju-landing-hero--intense:not(.saju-landing-hero--nova) .saju-landing-brand {
            font-size: clamp(2.35rem, 4.8vw, 3.15rem);
        }
        .saju-landing-hero--face.saju-landing-hero--intense:not(.saju-landing-hero--nova) .saju-landing-seal-svg {
            width: clamp(5rem, 9vw, 6.25rem);
        }
        .saju-landing-hero--face.saju-landing-hero--intense.saju-landing-hero--nova .saju-landing-logo-row {
            width: min(100%, 21.5rem);
        }
        .saju-landing-hero--nova .saju-landing-brand {
            font-size: clamp(2.15rem, 5vw, 3.35rem);
        }
    }
    .saju-landing-seal-wrap {
        flex-shrink: 0;
        filter: drop-shadow(0 10px 28px rgba(138, 109, 26, 0.45))
            drop-shadow(0 2px 6px rgba(0, 0, 0, 0.2));
    }
    .saju-landing-seal-svg {
        width: clamp(6.25rem, 20vw, 9.25rem);
        height: auto;
        display: block;
    }
    .saju-landing-brand-block {
        text-align: center;
    }
    .saju-landing-brand {
        font-family: "Playfair Display", "Noto Serif KR", "Apple SD Gothic Neo", "Malgun Gothic", Georgia, serif;
        font-size: clamp(2.65rem, 8.2vw, 4.65rem);
        font-weight: 800;
        letter-spacing: 0.06em;
        margin: 0 0 0.35rem 0;
        line-height: 1.08;
        background: linear-gradient(
            108deg,
            #6d4f0f 0%,
            #b8892b 18%,
            #f0d878 36%,
            #e8c547 48%,
            #d4af37 58%,
            #c9a227 72%,
            #7a6020 100%
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        filter: drop-shadow(0 3px 18px rgba(138, 109, 26, 0.35));
    }
    .saju-landing-kicker {
        font-family: "Noto Serif KR", "Apple SD Gothic Neo", "Malgun Gothic", Georgia, serif;
        font-size: clamp(0.72rem, 2.2vw, 0.92rem);
        font-weight: 600;
        letter-spacing: 0.12em;
        text-indent: 0;
        margin: 0;
        color: rgba(72, 58, 36, 0.78);
        text-transform: none;
    }
    .saju-landing-tagline {
        font-size: clamp(1.12rem, 3.8vw, 1.42rem);
        font-weight: 700;
        color: rgba(32, 28, 22, 0.9);
        margin: 1rem 0 0.25rem 0;
        line-height: 1.5;
        letter-spacing: -0.02em;
        text-shadow: 0 1px 0 rgba(255, 255, 255, 0.45);
    }
    .saju-landing-sub {
        font-size: clamp(0.86rem, 2.6vw, 0.98rem);
        font-weight: 600;
        margin: 0 0 1.35rem 0;
        color: rgba(42, 36, 28, 0.66);
        letter-spacing: -0.015em;
    }
    .st-key-saju_landing_cta {
        width: 100%;
        max-width: min(100%, 520px);
        margin: 1.1rem auto 0.65rem auto;
        padding: 0.65rem clamp(0.5rem, 3vw, 1rem) 0.35rem;
        box-sizing: border-box;
        clear: both;
        position: relative;
        z-index: 30;
        overflow: hidden;
        background: light-dark(rgba(255, 250, 240, 0.92), rgba(26, 26, 40, 0.94));
        border-radius: 14px;
        border: 1px solid light-dark(rgba(212, 175, 55, 0.28), rgba(212, 175, 55, 0.18));
    }
    .saju-step1-solar24-heading {
        margin: 0.05rem auto 0.35rem !important;
        padding: 0 0.25rem;
        font-size: clamp(1.05rem, 2.8vw, 1.2rem) !important;
        font-weight: 800 !important;
        color: light-dark(#7a5e12, #e8c547) !important;
        letter-spacing: 0.02em;
        text-align: center;
        width: 100%;
        max-width: 520px;
    }
    .saju-step1-solar24-heading--intense {
        display: flex !important;
        align-items: center;
        justify-content: center;
        gap: 0.45rem;
        margin: 0.2rem auto 0.5rem !important;
        padding: 0.55rem 1.1rem !important;
        max-width: min(100%, 520px);
        border-radius: 14px;
        font-size: clamp(1.12rem, 3.2vw, 1.32rem) !important;
        color: light-dark(#4a3710, #fce9a8) !important;
        background: light-dark(
            linear-gradient(135deg, rgba(212, 175, 55, 0.28) 0%, rgba(255, 252, 244, 0.95) 100%),
            linear-gradient(135deg, rgba(212, 175, 55, 0.22) 0%, rgba(22, 20, 36, 0.92) 100%)
        );
        border: 1.5px solid light-dark(rgba(201, 162, 39, 0.55), rgba(212, 175, 55, 0.4));
        box-shadow:
            0 8px 24px light-dark(rgba(98, 79, 39, 0.18), rgba(0, 0, 0, 0.35)),
            inset 0 1px 0 light-dark(rgba(255, 255, 255, 0.65), rgba(255, 255, 255, 0.08));
    }
    .saju-step1-solar24-heading-icon {
        font-size: 1.15em;
        line-height: 1;
        filter: drop-shadow(0 0 8px rgba(255, 180, 60, 0.65));
    }
    .saju-step1-solar24-heading,
    .saju-step1-solar24-heading--intense {
        display: none !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }
    .st-key-step1_solar24 {
        margin: 0.35rem auto 0.35rem !important;
        isolation: isolate;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        width: 100% !important;
        max-width: min(100%, 520px) !important;
        min-height: 200px !important;
        padding: 0 !important;
        box-sizing: border-box !important;
    }
    .st-key-step1_solar24 [data-testid="stVerticalBlock"],
    .st-key-step1_solar24 [data-testid="stElementContainer"] {
        width: 100% !important;
        max-width: 520px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        align-items: center !important;
    }
    .saju-step1-deck-outline {
        margin: 0.65rem 0 0.5rem;
        padding: 0.65rem 0.85rem;
        border-radius: 12px;
        border: 1px solid light-dark(rgba(212, 175, 55, 0.28), rgba(212, 175, 55, 0.18));
        background: light-dark(rgba(255, 250, 240, 0.75), rgba(26, 26, 40, 0.55));
    }
    .saju-step1-deck-outline-kicker {
        margin: 0 0 0.35rem;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        color: light-dark(#7a5e12, #d4af37);
    }
    .saju-step1-deck-outline-list {
        margin: 0;
        padding-left: 1.1rem;
        font-size: 0.82rem;
        line-height: 1.45;
        color: light-dark(#4a4030, #c9c4b8);
    }
    .st-key-step1_revisit_auth {
        width: 100%;
        max-width: min(100%, 520px);
        margin: 0.2rem auto 0;
        box-sizing: border-box;
        overflow: hidden;
    }
    /* STEP1 CTA·재방문: 2열 고정 (모바일·PC, 인앱 WebView) */
    .st-key-step1_cta_row_briefing,
    .st-key-step1_cta_row_main,
    .st-key-step1_cta_row_free,
    .st-key-step1_revisit_pin_row {
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    .st-key-step1_cta_row_briefing [data-testid="stVerticalBlock"],
    .st-key-step1_cta_row_main [data-testid="stVerticalBlock"],
    .st-key-step1_revisit_pin_row [data-testid="stVerticalBlock"] {
        flex-wrap: nowrap !important;
        width: 100% !important;
    }
    .st-key-step1_cta_row_briefing [data-testid="stHorizontalBlock"],
    .st-key-step1_revisit_pin_row [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: stretch !important;
        gap: clamp(0.35rem, 2vw, 0.55rem) !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    .st-key-step1_cta_row_main [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: flex-end !important;
        gap: clamp(0.35rem, 2vw, 0.55rem) !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        position: relative !important;
        min-height: clamp(2.45rem, 11vw, 3rem) !important;
    }
    .st-key-step1_cta_row_briefing [data-testid="stHorizontalBlock"] > div,
    .st-key-step1_revisit_pin_row [data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0 !important;
        min-width: 0 !important;
        max-width: 50% !important;
        width: auto !important;
        overflow: hidden !important;
    }
    .st-key-step1_cta_row_main [data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0 !important;
        min-width: 0 !important;
        max-width: 50% !important;
        width: auto !important;
        overflow: visible !important;
        position: relative !important;
    }
    .st-key-step1_cta_row_briefing .stButton > button,
    .st-key-step1_cta_row_briefing .stLinkButton > a,
    .st-key-step1_cta_row_main .stButton > button,
    .st-key-step1_cta_row_main [data-testid="stFormSubmitButton"] > button,
    .st-key-step1_cta_row_main .stLinkButton > a,
    .st-key-step1_revisit_pin_row .stButton > button,
    .st-key-step1_revisit_pin_row [data-testid="stFormSubmitButton"] > button {
        width: 100% !important;
        max-width: 100% !important;
        min-height: clamp(2.45rem, 11vw, 3rem) !important;
        height: auto !important;
        padding: 0.42rem 0.28rem !important;
        font-size: clamp(10px, 2.85vw, 13px) !important;
        font-weight: 800 !important;
        line-height: 1.22 !important;
        letter-spacing: -0.045em !important;
        white-space: normal !important;
        word-break: keep-all !important;
        overflow-wrap: anywhere !important;
        border-radius: 12px !important;
        box-sizing: border-box !important;
    }
    .st-key-step1_cta_row_briefing .stButton > button,
    .st-key-step1_cta_row_briefing .stLinkButton > a {
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        color: light-dark(rgba(45, 38, 28, 0.9), rgba(235, 228, 210, 0.94)) !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: var(--saju-soft-radius) !important;
    }
    .st-key-step1_cta_row_main .stButton > button:disabled,
    .st-key-step1_cta_row_main [data-testid="stFormSubmitButton"] > button:disabled {
        background: light-dark(#f3f4f6, #2a2a36) !important;
        color: light-dark(rgba(45, 38, 28, 0.45), rgba(235, 228, 210, 0.45)) !important;
        border: none !important;
        box-shadow: none !important;
    }
    /* 재방문 — 연한 베이지 보조 버튼 (비밀번호 입력과 2열) */
    .st-key-step1_cta_row_main .stButton > button,
    .st-key-step1_cta_row_main [data-testid="stFormSubmitButton"] > button,
    .st-key-step1_cta_row_main .stLinkButton > a {
        width: 100% !important;
        max-width: 100% !important;
        min-height: clamp(2.45rem, 11vw, 3rem) !important;
        height: auto !important;
        padding: 0.42rem 0.65rem !important;
        font-size: clamp(11px, 3vw, 14px) !important;
        font-weight: 800 !important;
        line-height: 1.22 !important;
        letter-spacing: -0.03em !important;
        white-space: normal !important;
        word-break: keep-all !important;
        overflow-wrap: anywhere !important;
        border-radius: var(--saju-soft-radius) !important;
        box-sizing: border-box !important;
        border: none !important;
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        color: light-dark(rgba(45, 38, 28, 0.9), rgba(235, 228, 210, 0.94)) !important;
        box-shadow: none !important;
    }
    .st-key-step1_cta_row_main [data-testid="stForm"] {
        display: flex !important;
        flex-direction: column !important;
        gap: 0.45rem !important;
        width: 100% !important;
    }
    .st-key-step1_cta_row_main {
        display: block !important;
        position: relative !important;
        margin-bottom: 0.15rem !important;
        padding-bottom: 0.1rem !important;
        isolation: isolate !important;
    }
    .st-key-step1_revisit_pin_row .stTextInput label {
        font-size: clamp(11px, 3vw, 13px) !important;
    }
    .saju-revisit-pin-rule {
        margin: 0 0 0.35rem 0 !important;
        padding: 0 !important;
        font-size: clamp(10px, 2.8vw, 12px) !important;
        line-height: 1.35 !important;
        color: rgba(61, 47, 31, 0.78) !important;
        text-align: left !important;
    }
    .saju-revisit-pin-rule--compact {
        margin-bottom: 0.45rem !important;
    }
    .st-key-step1_cta_row_main .saju-revisit-pin-rule {
        margin-bottom: 0.28rem !important;
    }
    .st-key-step1_revisit_pin_in input[data-saju-revisit-pin="1"],
    .st-key-step1_cta_row_main input[data-saju-revisit-pin="1"],
    .st-key-step2_revisit_pin input[data-saju-revisit-pin="1"],
    .st-key-step2_revisit_pin_confirm input[data-saju-revisit-pin="1"],
    [class*="st-key-step2_revisit_pin"] input[data-saju-revisit-pin="1"] {
        -webkit-text-security: disc !important;
        text-security: disc !important;
    }
    .st-key-step1_revisit_pin_row .stTextInput > div > div > input,
    .st-key-step1_cta_row_main .stTextInput > div > div > input {
        min-height: clamp(2.45rem, 11vw, 3rem) !important;
        font-size: clamp(12px, 3.2vw, 14px) !important;
        padding: 0.4rem 0.55rem !important;
    }
    .st-key-step1_cta_row_free {
        width: 100% !important;
        max-width: 100% !important;
        margin-top: 0.75rem !important;
        margin-bottom: 0.35rem !important;
        box-sizing: border-box !important;
        position: relative !important;
        clear: both !important;
        display: block !important;
        isolation: isolate !important;
    }
    /* 메인 CTA — 골드 강조 */
    .st-key-step1_cta_row_free .stButton > button {
        width: 100% !important;
        min-height: clamp(2.65rem, 12vw, 3.2rem) !important;
        font-size: clamp(12px, 3.2vw, 15px) !important;
        font-weight: 800 !important;
        white-space: normal !important;
        word-break: keep-all !important;
        border-radius: var(--saju-soft-radius) !important;
        border: 1px solid rgba(139, 105, 20, 0.55) !important;
        background: linear-gradient(135deg, #f0d875 0%, #d4af37 42%, #b8922a 100%) !important;
        color: #1a1208 !important;
        box-shadow: 0 4px 14px rgba(201, 162, 39, 0.38) !important;
    }
    html.saju-dark-tone .st-key-step1_cta_row_free .stButton > button {
        background: linear-gradient(135deg, #e8c547 0%, #c9a227 50%, #9a7518 100%) !important;
        color: #1a1208 !important;
        border-color: rgba(212, 175, 55, 0.65) !important;
    }
    .st-key-step1_revisit_pin_row .stButton > button {
        border: none !important;
        background: light-dark(var(--saju-soft-fill-hover), var(--saju-soft-fill-dark-hover)) !important;
        color: light-dark(#8b6914, #f5e6a8) !important;
        box-shadow: none !important;
        border-radius: var(--saju-soft-radius) !important;
    }
    @media (max-width: 400px) {
        .st-key-step1_cta_row_briefing .stButton > button,
        .st-key-step1_cta_row_briefing .stLinkButton > a,
        .st-key-step1_cta_row_main .stButton > button,
        .st-key-step1_cta_row_main [data-testid="stFormSubmitButton"] > button,
        .st-key-step1_cta_row_main .stLinkButton > a {
            font-size: 10px !important;
            padding: 0.38rem 0.2rem !important;
            min-height: 2.35rem !important;
        }
    }
    /* STEP2 태어난 시간: 텍스트만 나열(배경·액자 없음) */
    /* STEP2 태어난 시간 아코디언: 액자·배경 제거, 글씨만 */
    .st-key-s2_self_time_acc [data-testid="stExpander"] details,
    .st-key-s2_opp_time_acc [data-testid="stExpander"] details {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
    }
    .st-key-s2_self_time_acc [data-testid="stExpander"] summary,
    .st-key-s2_opp_time_acc [data-testid="stExpander"] summary {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
        padding: 0.1rem 0 !important;
        font-weight: 600 !important;
        font-size: clamp(11px, 2.6vw, 13px) !important;
        list-style: none !important;
    }
    .st-key-s2_self_time_acc [data-testid="stExpander"] summary:hover,
    .st-key-s2_opp_time_acc [data-testid="stExpander"] summary:hover {
        color: light-dark(#8b6914, #f5e6a8) !important;
    }
    .st-key-s2_self_time_list .stButton > button,
    .st-key-s2_opp_time_list .stButton > button {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        min-height: auto !important;
        height: auto !important;
        padding: 0.06rem 0 !important;
        margin: 0 !important;
        white-space: nowrap !important;
        line-height: 1.28 !important;
        font-size: clamp(10px, 2.4vw, 12px) !important;
        letter-spacing: -0.04em !important;
        text-align: left !important;
        justify-content: flex-start !important;
        color: light-dark(rgba(45, 38, 28, 0.88), rgba(235, 228, 210, 0.92)) !important;
    }
    .st-key-s2_self_time_list .stButton > button[kind="primary"],
    .st-key-s2_self_time_list .stButton > button[data-testid="baseButton-primary"],
    .st-key-s2_opp_time_list .stButton > button[kind="primary"],
    .st-key-s2_opp_time_list .stButton > button[data-testid="baseButton-primary"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        font-weight: 700 !important;
        color: light-dark(#8b6914, #f5e6a8) !important;
    }
    .st-key-s2_self_time_list .stButton > button:hover,
    .st-key-s2_opp_time_list .stButton > button:hover {
        background: light-dark(rgba(212, 175, 55, 0.12), rgba(212, 175, 55, 0.08)) !important;
    }
    .st-key-s2_self_time_list .stButton,
    .st-key-s2_opp_time_list .stButton {
        margin-bottom: 0 !important;
    }
    /* STEP2 접이식(태어난 시간·성별·양력 등): 연한 피치 칩 */
    .st-key-step2_navertone_self [data-testid="stExpander"] .stButton > button,
    .st-key-step2_navertone_opp [data-testid="stExpander"] .stButton > button {
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        border: none !important;
        box-shadow: none !important;
        min-height: auto !important;
        height: auto !important;
        white-space: nowrap !important;
        line-height: 1.28 !important;
        font-size: clamp(12px, 2.85vw, 14px) !important;
        padding: 0.38rem 0.5rem !important;
        letter-spacing: -0.04em !important;
        border-radius: var(--saju-soft-radius) !important;
    }
    /* STEP1: 3열 메뉴는 접이식(expander) 안에서만 사용 */
    .st-key-step1_solar24 {
        max-width: min(100vw, 520px);
        margin-left: auto !important;
        margin-right: auto !important;
        padding: 0 clamp(0.35rem, 2vw, 1rem) !important;
        box-sizing: border-box;
    }
    .st-key-step1_solar24 [data-testid="stCustomComponentV1"],
    .st-key-step1_solar24 [data-testid="stCustomComponentV1"] iframe,
    .st-key-step1_solar24 iframe {
        width: 100% !important;
        max-width: 520px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        min-height: 500px !important;
        display: block !important;
        overflow: visible !important;
    }
    .st-key-step1_solar24 [data-testid="stCustomComponentV1"] {
        overflow: visible !important;
    }
    @media (max-width: 520px) {
        .st-key-step1_solar24 [data-testid="stCustomComponentV1"] iframe,
        .st-key-step1_solar24 iframe {
            min-height: 500px !important;
            max-height: none !important;
            height: auto !important;
        }
        html.saju-home-step1 .saju-landing-hero--face.saju-landing-hero--intense,
        html[data-saju-step="1"] .saju-landing-hero--face.saju-landing-hero--intense,
        html.saju-home-step1 .saju-landing-hero--luxe.saju-landing-hero--intense,
        html[data-saju-step="1"] .saju-landing-hero--luxe.saju-landing-hero--intense {
            padding: max(0.22rem, env(safe-area-inset-top, 0px)) 0.5rem 0.5rem !important;
            min-height: auto !important;
        }
        html.saju-home-step1 .st-key-saju_landing_stack,
        html[data-saju-step="1"] .st-key-saju_landing_stack {
            margin-top: 0 !important;
        }
    }
    /* 갤럭시·안드로이드·카카오 인앱 — 홈 배너 상단 빈 여백 제거 */
    @media (max-width: 768px) {
        html.saju-platform-android.saju-home-step1 .stApp [data-testid="stAppViewContainer"],
        html.saju-platform-android[data-saju-step="1"] .stApp [data-testid="stAppViewContainer"],
        html.saju-platform-kakao.saju-home-step1 .stApp [data-testid="stAppViewContainer"],
        html.saju-platform-kakao[data-saju-step="1"] .stApp [data-testid="stAppViewContainer"],
        html.saju-platform-inapp.saju-home-step1 .stApp [data-testid="stAppViewContainer"],
        html.saju-platform-inapp[data-saju-step="1"] .stApp [data-testid="stAppViewContainer"] {
            padding-top: 0 !important;
        }
        html.saju-platform-android.saju-home-step1 .main .block-container,
        html.saju-platform-android[data-saju-step="1"] .main .block-container {
            padding-top: 0 !important;
            padding-left: 0.35rem !important;
            padding-right: 0.35rem !important;
        }
        html.saju-platform-android.saju-home-step1 .st-key-saju_landing_stack,
        html.saju-platform-android[data-saju-step="1"] .st-key-saju_landing_stack {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        html.saju-platform-android.saju-home-step1 .st-key-saju_landing_stack [data-testid="stVerticalBlock"],
        html.saju-platform-android[data-saju-step="1"] .st-key-saju_landing_stack [data-testid="stVerticalBlock"] {
            gap: 0 !important;
            row-gap: 0 !important;
        }
        html.saju-platform-android.saju-home-step1 .st-key-saju_landing_stack [data-testid="stVerticalBlock"] > div,
        html.saju-platform-android[data-saju-step="1"] .st-key-saju_landing_stack [data-testid="stVerticalBlock"] > div {
            gap: 0 !important;
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        html.saju-platform-android.saju-home-step1 .st-key-saju_landing_hero [data-testid="stElementContainer"],
        html.saju-platform-android[data-saju-step="1"] .st-key-saju_landing_hero [data-testid="stElementContainer"],
        html.saju-platform-android.saju-home-step1 .st-key-saju_landing_stack [data-testid="stElementContainer"],
        html.saju-platform-android[data-saju-step="1"] .st-key-saju_landing_stack [data-testid="stElementContainer"] {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        html.saju-platform-android.saju-home-step1 .saju-landing-hero--luxe.saju-landing-hero--intense,
        html.saju-platform-android[data-saju-step="1"] .saju-landing-hero--luxe.saju-landing-hero--intense {
            padding-top: 0 !important;
            padding-bottom: 0.5rem !important;
            min-height: auto !important;
            justify-content: flex-start !important;
        }
        html.saju-platform-galaxy.saju-home-step1 .st-key-saju_landing_stack,
        html.saju-platform-galaxy[data-saju-step="1"] .st-key-saju_landing_stack,
        html.saju-platform-galaxy .st-key-saju_router_step_mount_01 .st-key-saju_landing_stack {
            margin-top: 0 !important;
            padding-top: 0 !important;
            transform: none !important;
        }
        html.saju-platform-galaxy.saju-home-step1 [data-testid="stAppViewContainer"],
        html.saju-platform-galaxy[data-saju-step="1"] [data-testid="stAppViewContainer"],
        html.saju-platform-galaxy [data-testid="stAppViewContainer"] {
            min-height: 0 !important;
            height: auto !important;
            justify-content: flex-start !important;
            align-items: stretch !important;
            padding-top: 0 !important;
        }
        html.saju-platform-galaxy.saju-home-step1 [data-testid="stMain"],
        html.saju-platform-galaxy[data-saju-step="1"] [data-testid="stMain"],
        html.saju-platform-galaxy [data-testid="stMain"],
        html.saju-platform-galaxy section.main {
            justify-content: flex-start !important;
            align-items: stretch !important;
            min-height: 0 !important;
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        html.saju-platform-galaxy.saju-home-step1 .main .block-container,
        html.saju-platform-galaxy[data-saju-step="1"] .main .block-container,
        html.saju-platform-galaxy .st-key-saju_router_step_mount_01 {
            padding-top: 0 !important;
            margin-top: 0 !important;
            min-height: 0 !important;
        }
        html.saju-platform-galaxy.saju-home-step1 .st-key-saju_landing_hero,
        html.saju-platform-galaxy[data-saju-step="1"] .st-key-saju_landing_hero,
        html.saju-platform-galaxy .st-key-saju_router_step_mount_01 .st-key-saju_landing_hero {
            order: 0 !important;
            flex: 0 0 auto !important;
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        html.saju-platform-galaxy.saju-home-step1 .st-key-step1_solar24,
        html.saju-platform-galaxy[data-saju-step="1"] .st-key-step1_solar24,
        html.saju-platform-galaxy .st-key-saju_router_step_mount_01 .st-key-step1_solar24 {
            order: 1 !important;
            margin-top: 0.1rem !important;
        }
        html.saju-platform-galaxy.saju-home-step1 .saju-landing-hero--luxe.saju-landing-hero--intense,
        html.saju-platform-galaxy[data-saju-step="1"] .saju-landing-hero--luxe.saju-landing-hero--intense,
        html.saju-platform-galaxy .st-key-saju_router_step_mount_01 #saju-home-hero-top:not(.saju-home-hero-banner),
        html.saju-platform-galaxy .st-key-saju_router_step_mount_01 .saju-landing-hero--nova {
            padding-top: max(0.06rem, env(safe-area-inset-top, 0px)) !important;
            padding-bottom: 0.5rem !important;
            min-height: 0 !important;
            max-height: min(40vh, 360px) !important;
            justify-content: flex-start !important;
            margin-top: 0 !important;
            position: relative !important;
            top: 0 !important;
            border-radius: 0 0 16px 16px !important;
        }
        html.saju-platform-galaxy .st-key-saju_router_step_mount_01 #saju-home-hero-top.saju-home-hero-banner,
        html.saju-platform-galaxy .st-key-saju_router_step_mount_01 .saju-home-hero-banner {
            max-height: none !important;
            min-height: 0 !important;
            margin-top: 0 !important;
            padding-top: max(0px, env(safe-area-inset-top, 0px)) !important;
        }
    }
    .saju-fg2-card {
        min-height: 9.25rem;
        box-sizing: border-box;
        padding: 0.9rem 0.8rem 1rem;
        border-radius: 14px;
        text-align: left;
        border: 1px solid light-dark(rgba(212, 175, 55, 0.42), rgba(212, 175, 55, 0.26));
        background-color: light-dark(#fffaf3, rgba(26, 26, 46, 0.94));
        background-image: linear-gradient(
            165deg,
            light-dark(rgba(255, 255, 255, 0.55), rgba(212, 175, 55, 0.07)) 0%,
            transparent 100%
        );
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.07);
    }
    .st-key-step1_menu_grid {
        max-width: min(100vw, 560px);
        margin: 0.35rem auto 0.15rem auto;
        padding: 0 clamp(0.45rem, 2.5vw, 1rem);
        box-sizing: border-box;
    }
    .st-key-step1_menu_grid .stButton > button {
        min-height: 3.15rem !important;
        font-size: max(13px, 2.8vw, 0.88rem) !important;
        font-weight: 700 !important;
        line-height: 1.22 !important;
        padding: 0.45rem 0.28rem !important;
        border-radius: 11px !important;
        white-space: normal !important;
    }
    @media (min-width: 400px) {
        .st-key-step1_menu_grid .stButton > button {
            min-height: 3.35rem !important;
            font-size: max(14px, 0.93rem) !important;
            padding: 0.5rem 0.35rem !important;
        }
    }
    .st-key-step1_menu_more_row {
        max-width: min(100vw, 540px);
        margin: 0 auto 0.35rem auto;
        padding: 0 clamp(0.65rem, 3.5vw, 1.1rem);
        box-sizing: border-box;
    }
    .st-key-step1_menu_more_row .stButton > button {
        min-height: 2.9rem !important;
        font-size: max(14px, 0.9rem) !important;
        font-weight: 650 !important;
        line-height: 1.25 !important;
        white-space: normal !important;
    }
    /* 홈: 최근 분석 기록 카드 띠 */
    .st-key-step1_recent_analysis_strip {
        margin-top: 0.65rem;
        margin-bottom: 0.25rem;
        max-width: min(100vw, 980px);
        margin-left: auto;
        margin-right: auto;
        padding: 0 clamp(0.45rem, 3vw, 1rem);
        box-sizing: border-box;
    }
    p.saju-recent-gj {
        margin: 0.2rem 0 0.45rem 0;
        font-size: clamp(0.98rem, 3vw, 1.22rem);
        font-weight: 800;
        letter-spacing: 0.1em;
        color: light-dark(#2a2620, rgba(245, 240, 230, 0.96));
        line-height: 1.4;
    }
    .saju-fortune-strip {
        width: 100vw;
        max-width: 100vw;
        margin-left: calc(50% - 50vw);
        margin-right: calc(50% - 50vw);
        box-sizing: border-box;
        padding: 1.1rem clamp(0.75rem, 3vw, 1.25rem) 1.35rem;
        background: light-dark(rgba(255, 252, 248, 0.92), rgba(15, 15, 26, 0.55));
        border-top: 1px solid light-dark(rgba(212, 175, 55, 0.2), rgba(212, 175, 55, 0.15));
    }
    .saju-fortune-heading {
        text-align: center;
        font-size: clamp(1.05rem, 3.5vw, 1.2rem);
        font-weight: 800;
        margin: 0 0 0.75rem 0;
        color: light-dark(#1a1a2e, #e5e5e5);
        letter-spacing: -0.02em;
    }
    .saju-fortune-scroll {
        display: flex;
        gap: 0.85rem;
        overflow-x: auto;
        scroll-snap-type: x mandatory;
        -webkit-overflow-scrolling: touch;
        padding: 0.25rem 0.15rem 0.6rem;
        scrollbar-width: thin;
    }
    .saju-fortune-scroll::-webkit-scrollbar {
        height: 6px;
    }
    .saju-fortune-scroll::-webkit-scrollbar-thumb {
        background: rgba(212, 175, 55, 0.45);
        border-radius: 99px;
    }
    .saju-fortune-card {
        flex: 0 0 min(82vw, 268px);
        scroll-snap-align: start;
        box-sizing: border-box;
        padding: 1rem 1.05rem 1.1rem;
        border-radius: 16px;
        text-align: left;
        border: 1px solid light-dark(rgba(212, 175, 55, 0.45), rgba(212, 175, 55, 0.28));
        background-color: light-dark(#fff9f0, rgba(26, 26, 46, 0.94));
        background-image: linear-gradient(
            165deg,
            light-dark(rgba(255, 255, 255, 0.55), rgba(212, 175, 55, 0.07)) 0%,
            transparent 100%
        );
        box-shadow: 0 6px 22px rgba(0, 0, 0, 0.08);
    }
    .saju-fc-k {
        font-size: max(15px, 0.95rem);
        font-weight: 800;
        margin: 0 0 0.45rem 0;
        color: light-dark(#6b5420, #e8b923);
        letter-spacing: -0.02em;
    }
    .saju-fc-t {
        font-size: max(15px, 0.95rem);
        line-height: 1.5;
        margin: 0.45rem 0 0 0;
        padding: 0.72rem 0.78rem 0.78rem;
        position: relative;
        border-radius: 13px;
        color: light-dark(rgba(26, 26, 46, 0.9), rgba(248, 244, 232, 0.94));
        border: 1px solid light-dark(rgba(212, 175, 55, 0.42), rgba(232, 185, 35, 0.3));
        background:
            radial-gradient(circle at 12% 18%, light-dark(rgba(212, 175, 55, 0.16), rgba(232, 185, 35, 0.12)) 0 2px, transparent 3px),
            linear-gradient(
                145deg,
                light-dark(rgba(255, 255, 255, 0.72), rgba(255, 255, 255, 0.08)) 0%,
                light-dark(rgba(255, 247, 229, 0.9), rgba(212, 175, 55, 0.08)) 100%
            );
        box-shadow:
            inset 0 0 0 1px light-dark(rgba(255, 255, 255, 0.55), rgba(255, 255, 255, 0.08)),
            0 6px 18px light-dark(rgba(138, 109, 26, 0.12), rgba(0, 0, 0, 0.22));
    }
    .saju-fc-t::before {
        content: "";
        position: absolute;
        inset: 0.28rem;
        border-radius: 10px;
        border: 1px solid light-dark(rgba(212, 175, 55, 0.26), rgba(232, 185, 35, 0.18));
        pointer-events: none;
    }
    .saju-fc-t::after {
        content: "✦";
        position: absolute;
        right: 0.58rem;
        top: -0.48rem;
        font-size: 0.85rem;
        color: light-dark(rgba(180, 135, 28, 0.7), rgba(232, 185, 35, 0.82));
        text-shadow: 0 0 10px rgba(212, 175, 55, 0.35);
    }

    /* 하단 단계 네비: 라이트=성공 그린 CTA, 다크=골드 CTA + 인앱 WebView 가로 고정 */
    [data-testid="stMarkdownContainer"] .naver-bottom-nav,
    .naver-bottom-nav {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: stretch !important;
        justify-content: space-between !important;
        gap: 8px !important;
        width: 100% !important;
        box-sizing: border-box !important;
        margin: 0.35rem 0 0.75rem 0 !important;
        padding-bottom: env(safe-area-inset-bottom, 0px) !important;
    }
    [data-testid="stMarkdownContainer"] .naver-bottom-nav .nbn-pill,
    .naver-bottom-nav .nbn-pill {
        flex: 1 1 0 !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 3.35rem !important;
        padding: 0.55rem 0.4rem !important;
        border-radius: 12px !important;
        font-size: max(16px, 1.02rem) !important;
        font-weight: 700 !important;
        text-align: center !important;
        text-decoration: none !important;
        line-height: 1.25 !important;
        -webkit-tap-highlight-color: transparent !important;
        touch-action: manipulation !important;
    }
    .naver-bottom-nav a.nbn-outline {
        border: 1px solid light-dark(#dadce0, rgba(212, 175, 55, 0.35)) !important;
        background: light-dark(#ffffff, #1a1a2e) !important;
        color: light-dark(#222222, #e5e5e5) !important;
    }
    .naver-bottom-nav a.nbn-outline:active {
        background: light-dark(#f7f8fa, rgba(26, 26, 46, 0.95)) !important;
    }
    .naver-bottom-nav a.nbn-primary {
        border: 1px solid light-dark(#16a34a, #c9a227) !important;
        background: light-dark(#22c55e, #d4af37) !important;
        color: light-dark(#ffffff, #0f0f1a) !important;
    }
    .naver-bottom-nav a.nbn-primary:active {
        filter: brightness(0.95);
    }
    .naver-bottom-nav .nbn-muted {
        border: 1px solid light-dark(#eceef1, rgba(212, 175, 55, 0.12)) !important;
        background: light-dark(#fafbfc, rgba(26, 26, 46, 0.55)) !important;
        color: light-dark(#b0b4bb, #b8b8c8) !important;
        cursor: not-allowed !important;
        pointer-events: none !important;
    }

    /* (안정화) 내부 레이아웃 블록의 display를 강제로 바꾸면 WebView에서 insertBefore/removeChild 오류가 날 수 있어 제거합니다. */
    .st-key-step2_form_pairs [data-testid="column"] > div,
    .st-key-step2_form_pairs [data-testid="stColumn"] > div,
    .st-key-step2_form_pairs div.stColumn > div,
    .stApp .main [data-testid="stForm"] .st-key-step2_form_pairs [data-testid="column"] > div,
    .stApp .main .stForm .st-key-step2_form_pairs [data-testid="column"] > div {
        padding-left: 2px !important;
        padding-right: 2px !important;
    }

    /* 모바일에서는 좌우 여백만 축소(레이아웃은 동일 유지) */
    @media (max-width: 768px) {
        .stApp .main .block-container {
            padding: 0 0.45rem 0.85rem !important;
            max-width: 100% !important;
        }
        .stApp .main [data-testid="stForm"] .stTextInput > div > div,
        .stApp .main [data-testid="stForm"] .stNumberInput > div > div,
        .stApp .main [data-testid="stForm"] .stSelectbox > div > div {
            border: none !important;
            box-shadow: none !important;
        }
        .stApp .main [data-testid="stForm"] .stTextInput > div > div > input,
        .stApp .main [data-testid="stForm"] .stNumberInput input,
        .stApp .main [data-testid="stForm"] .stDateInput input {
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }
        .stApp .main [data-testid="stForm"] .stSelectbox [data-baseweb="select"] > div,
        .stApp .main [data-testid="stForm"] .stSelectbox [data-baseweb="select"] {
            border: none !important;
            box-shadow: none !important;
        }
        .stApp .main [data-testid="stForm"] .stNumberInput button {
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }
    }

    /* ===== STEP2 정보입력: 카드 + 세그먼트 + 생일 date ===== */
    .st-key-s2_card_self,
    .st-key-s2_card_opp,
    .st-key-s2_card_contact {
        border: 1px solid light-dark(rgba(26, 26, 46, 0.1), rgba(212, 175, 55, 0.2));
        border-radius: 18px;
        padding: 1rem 1.15rem 1.3rem;
        margin-bottom: 1rem;
        background-color: light-dark(#ffffff, rgba(26, 26, 46, 0.52));
        box-shadow: 0 10px 32px rgba(0, 0, 0, 0.07);
    }
    .st-key-s2_card_self h5,
    .st-key-s2_card_opp h5,
    .st-key-s2_card_contact h5 {
        margin-top: 0 !important;
        margin-bottom: 0.35rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
    }
    .st-key-s2_card_self [data-testid="stCaption"],
    .st-key-s2_card_opp [data-testid="stCaption"] {
        margin-top: 0 !important;
        margin-bottom: 0.75rem !important;
    }
    .st-key-s2self_date_ring,
    .st-key-s2opp_date_ring {
        position: relative;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: min(72vw, 280px);
        margin: 0.25rem 0 0.75rem;
    }
    .st-key-s2self_date_ring::before,
    .st-key-s2opp_date_ring::before {
        content: "";
        position: absolute;
        width: min(88vw, 300px);
        height: min(88vw, 300px);
        max-width: 300px;
        max-height: 300px;
        border: 2px solid light-dark(rgba(201, 162, 39, 0.45), rgba(212, 175, 55, 0.35));
        border-radius: 50%;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        pointer-events: none;
        z-index: 0;
        box-shadow: inset 0 0 40px rgba(212, 175, 55, 0.06);
    }
    .st-key-s2self_date_ring > div,
    .st-key-s2opp_date_ring > div {
        position: relative;
        z-index: 1;
        width: min(100%, 300px);
    }
    .st-key-s2self_date_ring .stDateInput label,
    .st-key-s2opp_date_ring .stDateInput label {
        font-weight: 700 !important;
        font-size: max(15px, 0.95rem) !important;
    }
    .st-key-s2self_date_ring .stDateInput [data-baseweb="input"] input,
    .st-key-s2opp_date_ring .stDateInput [data-baseweb="input"] input {
        font-size: max(18px, 1.12rem) !important;
        font-weight: 650 !important;
        text-align: center !important;
        min-height: 3.5rem !important;
        border-radius: 999px !important;
    }
    .st-key-s2_card_self [data-testid="stVerticalBlock"] [data-testid="stElementContainer"] button,
    .st-key-s2_card_opp [data-testid="stVerticalBlock"] [data-testid="stElementContainer"] button {
        font-weight: 650 !important;
    }

    /* STEP2 상단: 해·달 원형 달력 전환 */
    p.saju-step2-cal-hero-hint {
        text-align: center;
        font-size: max(13px, 0.88rem);
        font-weight: 600;
        margin: 0.15rem 0 0.5rem 0;
        color: light-dark(rgba(42, 38, 32, 0.72), rgba(210, 208, 220, 0.82));
        letter-spacing: -0.02em;
    }
    .st-key-step2_cal_orb_row {
        margin: 0.15rem auto 1rem auto;
        max-width: min(100vw, 420px);
    }
    .st-key-step2_cal_orb_row [data-testid="column"] {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .st-key-step2_cal_orb_row .stButton > button {
        border-radius: 50% !important;
        aspect-ratio: 1 !important;
        width: min(7.75rem, 36vw) !important;
        height: min(7.75rem, 36vw) !important;
        min-width: min(7.75rem, 36vw) !important;
        min-height: min(7.75rem, 36vw) !important;
        max-width: 8.5rem !important;
        max-height: 8.5rem !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding: 0.55rem 0.35rem !important;
        font-size: clamp(1rem, 3.8vw, 1.22rem) !important;
        font-weight: 800 !important;
        line-height: 1.22 !important;
        white-space: pre-line !important;
        box-sizing: border-box !important;
    }
    .st-key-step2_cal_orb_row .stButton > button[kind="primary"],
    .st-key-step2_cal_orb_row .stButton > button[data-testid="baseButton-primary"] {
        border: none !important;
        background: light-dark(var(--saju-soft-fill-hover), var(--saju-soft-fill-dark-hover)) !important;
        color: light-dark(#8b6914, #f5e6a8) !important;
        box-shadow: none !important;
    }
    .st-key-step2_cal_orb_row .stButton > button[kind="secondary"],
    .st-key-step2_cal_orb_row .stButton > button[data-testid="baseButton-secondary"] {
        border: none !important;
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        color: light-dark(rgba(45, 38, 28, 0.88), rgba(235, 228, 210, 0.92)) !important;
        box-shadow: none !important;
    }
    html.saju-dark-tone .st-key-step2_cal_orb_row .stButton > button[kind="secondary"],
    html.saju-dark-tone .st-key-step2_cal_orb_row .stButton > button[data-testid="baseButton-secondary"] {
        background: var(--saju-soft-fill-dark) !important;
        color: rgba(235, 228, 210, 0.92) !important;
    }

    /* STEP2: 저장·분석 시작(안내 클릭) */
    .st-key-step2_save_gold_wrap .stButton > button {
        min-height: auto !important;
        font-size: max(17px, 1.06rem) !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
        border-radius: var(--saju-soft-radius) !important;
        border: none !important;
        background: light-dark(var(--saju-soft-fill-hover), var(--saju-soft-fill-dark-hover)) !important;
        color: light-dark(#8b6914, #f5e6a8) !important;
        box-shadow: none !important;
    }
    .st-key-step2_save_gold_wrap .stButton > button:hover {
        background: light-dark(var(--saju-soft-fill-active), var(--saju-soft-fill-dark-hover)) !important;
        filter: none !important;
    }
    .st-key-step2_save_gold_wrap .stButton > button:active {
        transform: none !important;
        box-shadow: none !important;
    }
    html.saju-dark-tone .st-key-step2_save_gold_wrap .stButton > button {
        color: #f5e6a8 !important;
    }

    /* ===== 분석 카드 `.card` 스킨 (STEP3~10 — 채팅창은 별도 규칙) ===== */
    div[class*="st-key-saju_analysis_card"] {
        position: relative;
        overflow: visible;
        border-radius: 22px;
        padding: clamp(1.55rem, 3vw, 2.35rem);
        margin-bottom: 1.35rem;
        box-sizing: border-box;
        border: 1px solid light-dark(rgba(92, 62, 36, 0.2), rgba(212, 175, 55, 0.22));
        background: light-dark(
            linear-gradient(150deg, #fdfcfa 0%, #f8f5ef 48%, #f2ede5 100%),
            linear-gradient(135deg, #1a1a2e 0%, #16213e 52%, #141b2a 100%)
        );
        box-shadow: light-dark(
                0 12px 36px rgba(35, 26, 18, 0.1),
                0 16px 44px rgba(0, 0, 0, 0.48)
            ),
            inset 0 1px 0 light-dark(rgba(255, 255, 255, 0.42), rgba(255, 255, 255, 0.06));
        color: light-dark(#1a1208, var(--saju-text-body));
    }
    /* 분석 카드 상단 골드 그라데이션 바(::before) 제거 — 사용자 요청:
       STEP3~ 피처 화면 최상단에 보이던 '진한 색 선'이 이 3px 바였다.
       전 피처 STEP 에서 보이지 않도록 비표시 처리(레이아웃·기능 영향 없음). */
    div[class*="st-key-saju_analysis_card"]::before {
        content: none !important;
        display: none !important;
    }
    div[class*="st-key-saju_analysis_card"]::after {
        content: none !important;
        display: none !important;
    }
    div[class*="st-key-saju_analysis_card"] > div {
        position: relative;
        z-index: 2;
    }
    div[class*="st-key-saju_analysis_card"] h1,
    div[class*="st-key-saju_analysis_card"] h2,
    div[class*="st-key-saju_analysis_card"] h3,
    div[class*="st-key-saju_analysis_card"] h4,
    div[class*="st-key-saju_analysis_card"] h5,
    div[class*="st-key-saju_analysis_card"] h6 {
        color: light-dark(var(--saju-text-readable), #f2ece2) !important;
    }
    div[class*="st-key-saju_analysis_card"] [data-testid="stMarkdownContainer"] p,
    div[class*="st-key-saju_analysis_card"] [data-testid="stMarkdownContainer"] li,
    div[class*="st-key-saju_analysis_card"] [data-testid="stCaptionContainer"],
    div[class*="st-key-saju_analysis_card"] label {
        color: light-dark(#211c16, #ece8e0) !important;
        opacity: 1 !important;
    }
    div[class*="st-key-saju_analysis_card"] [data-testid="stExpander"] details {
        border: 1px solid light-dark(rgba(139, 105, 20, 0.28), rgba(212, 175, 55, 0.22)) !important;
        border-radius: 12px !important;
        background: light-dark(#fffdf8, rgba(22, 28, 48, 0.9)) !important;
    }
    div[class*="st-key-saju_analysis_card"] [data-testid="stExpander"] summary {
        font-weight: 750 !important;
        color: light-dark(#1a1208, #f2ece2) !important;
        background: light-dark(#fff6eb, rgba(30, 36, 56, 0.75)) !important;
        border-radius: 10px !important;
    }
    div[class*="st-key-saju_analysis_card"] [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
    div[class*="st-key-saju_analysis_card"] [data-testid="stExpander"] [data-testid="stMarkdownContainer"] li {
        color: light-dark(#211c16, rgba(236, 232, 224, 0.96)) !important;
    }
    div[class*="st-key-saju_analysis_card"] .stTextArea textarea,
    div[class*="st-key-saju_analysis_card"] [data-testid="stTextArea"] textarea {
        background: light-dark(#ffffff, rgba(26, 26, 46, 0.92)) !important;
        color: light-dark(#1a1208, #ece8e0) !important;
        border: 1px solid light-dark(rgba(139, 105, 20, 0.22), rgba(212, 175, 55, 0.2)) !important;
    }

    .saju-section-title-badge {
        display: inline-block;
        padding: 0.48rem 0.9rem;
        margin: 0.15rem 0 0.7rem;
        border-radius: 12px;
        font-size: clamp(1rem, 3.8vw, 1.12rem);
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.35;
        background: light-dark(rgba(212, 175, 55, 0.24), rgba(212, 175, 55, 0.16));
        border: 1px solid light-dark(rgba(139, 90, 43, 0.38), rgba(212, 175, 55, 0.38));
        color: light-dark(#2a2218, #f5e6a8);
        box-shadow: light-dark(
            0 2px 10px rgba(35, 26, 18, 0.06),
            0 2px 12px rgba(0, 0, 0, 0.22)
        );
    }
    .saju-section-title-badge--center {
        display: block;
        width: fit-content;
        max-width: 100%;
        margin-left: auto;
        margin-right: auto;
        text-align: center;
    }

    .saju-roadmap-decades-frame,
    .st-key-step9_roadmap_decades,
    .st-key-step9_roadmap_current {
        border-radius: 16px !important;
        padding: 0.85rem 1rem !important;
        margin: 0.55rem 0 0.75rem !important;
        box-sizing: border-box !important;
        line-height: 1.55;
        font-size: max(14px, 0.92rem);
    }
    .saju-roadmap-decades-frame,
    .st-key-step9_roadmap_decades {
        border: 1px solid light-dark(rgba(139, 105, 20, 0.32), rgba(212, 175, 55, 0.28)) !important;
        background: light-dark(rgba(255, 252, 245, 0.96), rgba(26, 26, 46, 0.78)) !important;
    }
    .saju-roadmap-current-frame,
    .st-key-step9_roadmap_current {
        border: 1px solid light-dark(rgba(59, 130, 246, 0.28), rgba(96, 165, 250, 0.32)) !important;
        background: light-dark(rgba(239, 246, 255, 0.92), rgba(22, 32, 56, 0.82)) !important;
    }

    div[class*="st-key-saju_analysis_card_step9"],
    div[class*="st-key-saju_analysis_card_step9"] > div {
        overflow: visible !important;
        max-height: none !important;
    }
    /* 레거시 대운 선택 UI(핵심 요약·라디오·칩·십성 카드) — 완전 숨김 */
    .st-key-step9_core_summary,
    .st-key-step9_daewoon_timeline,
    .st-key-step9_daewoon_timeline_pick,
    .st-key-step9_core_summary *,
    .st-key-step9_daewoon_timeline *,
    .st-key-step9_daewoon_timeline_pick *,
    div[class*="st-key-saju_premium_step9"] .saju-dw-timeline,
    div[class*="st-key-saju_premium_step9"] .saju-dw-detail-card {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        max-height: 0 !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
    }
    .st-key-step9_life_roadmap {
        overflow: visible !important;
        max-height: none !important;
    }
    .saju-dw-detail-card {
        box-sizing: border-box;
        padding: 0.72rem 0.82rem;
        border-radius: 14px;
        border: 1px solid light-dark(rgba(139, 105, 20, 0.28), rgba(212, 175, 55, 0.24));
        background: light-dark(rgba(255, 252, 245, 0.96), rgba(26, 26, 46, 0.72));
        box-shadow: light-dark(0 2px 10px rgba(35, 26, 18, 0.06), 0 2px 12px rgba(0, 0, 0, 0.22));
    }
    .saju-dw-detail-label {
        font-size: 0.78rem;
        font-weight: 700;
        color: light-dark(rgba(74, 55, 16, 0.72), rgba(220, 210, 180, 0.78));
        margin-bottom: 0.28rem;
    }
    .saju-dw-detail-value {
        font-size: clamp(1rem, 3.2vw, 1.12rem);
        font-weight: 850;
        color: light-dark(#2a2218, #f5e6a8);
        letter-spacing: 0.04em;
    }
    .saju-dw-detail-card--interp {
        border-color: light-dark(rgba(59, 130, 246, 0.28), rgba(96, 165, 250, 0.32));
        background: light-dark(rgba(239, 246, 255, 0.94), rgba(22, 32, 56, 0.82));
    }
    .saju-dw-detail-card--interp p {
        margin: 0;
        line-height: 1.62;
        font-size: clamp(0.92rem, 3vw, 1rem);
        color: light-dark(#1e293b, rgba(245, 245, 248, 0.94));
    }
    .saju-step9-consult-frame {
        box-sizing: border-box;
        margin-top: 0.85rem;
        padding: 0.95rem 1rem 1.05rem;
        border-radius: 16px;
        border: 1.5px solid light-dark(rgba(139, 105, 20, 0.34), rgba(212, 175, 55, 0.3));
        background: light-dark(
            linear-gradient(155deg, rgba(255, 251, 240, 0.98), rgba(248, 236, 210, 0.94)),
            linear-gradient(155deg, rgba(34, 31, 42, 0.97), rgba(24, 28, 44, 0.95))
        );
        box-shadow:
            0 0 0 1px light-dark(rgba(255, 255, 255, 0.72), rgba(255, 255, 255, 0.06)) inset,
            0 8px 24px light-dark(rgba(98, 79, 39, 0.12), rgba(0, 0, 0, 0.28));
    }
    .saju-step9-consult-title {
        margin: 0 0 0.62rem;
        font-size: clamp(0.98rem, 3.1vw, 1.06rem);
        font-weight: 850;
        color: light-dark(#4a3710, #f5e6a8);
        letter-spacing: -0.02em;
    }
    .saju-step9-consult-body {
        line-height: 1.68;
        font-size: clamp(0.92rem, 3vw, 1rem);
        color: light-dark(#211c16, rgba(245, 245, 248, 0.94));
        word-break: keep-all;
        overflow-wrap: anywhere;
    }

    /* ===== STEP11/12 채팅 — 내부 스크롤(React DOM 건드리지 않음) ===== */
    :is(div[class*="st-key-step11_hanji_chat"], div[class*="st-key-step12_hanji_chat"]) {
        margin-bottom: 1rem !important;
    }
    .saju-chat-viewport {
        display: block;
        box-sizing: border-box;
        width: 100%;
        max-height: min(58dvh, 520px);
        min-height: 220px;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        -webkit-overflow-scrolling: touch;
        overscroll-behavior-y: contain;
        padding: 12px 14px;
        scrollbar-width: thin;
        scrollbar-color: light-dark(rgba(92, 62, 36, 0.45), rgba(212, 175, 55, 0.35)) transparent;
        background: light-dark(rgba(248, 244, 236, 0.55), rgba(10, 14, 24, 0.35));
        border-radius: 12px;
    }
    .saju-chat-viewport::-webkit-scrollbar {
        width: 8px;
    }
    .saju-chat-viewport::-webkit-scrollbar-thumb {
        border-radius: 8px;
        background: light-dark(rgba(92, 62, 36, 0.35), rgba(212, 175, 55, 0.4));
    }
    .saju-chat-thread {
        display: block;
        width: 100%;
    }
    .saju-chat-msg,
    :is(div[class*="st-key-step11_hanji_chat"], div[class*="st-key-step12_hanji_chat"]) .saju-chat-msg {
        display: block;
        max-width: 100% !important;
        width: 100% !important;
        box-sizing: border-box !important;
        position: relative !important;
        margin: 10px 0 !important;
        overflow: hidden;
    }
    .saju-chat-msg--user {
        display: flex !important;
        justify-content: flex-end !important;
    }
    .saju-chat-bubble {
        max-width: min(92%, 520px) !important;
        box-sizing: border-box !important;
        position: relative !important;
        overflow-wrap: anywhere;
        word-break: break-word;
    }
    .saju-chat-bubble--ai,
    .saju-chat-bubble--expert {
        max-width: 100% !important;
        width: 100% !important;
    }

    /* ===== STEP3 사주 팔자 — 한지 질감 4카드 (데스크톱 1×4 · 모바일 2×2) ===== */
    div[class*="st-key-step3_hanji_card"] {
        position: relative;
        text-align: center;
        padding: 0.85rem 0.4rem 1.05rem;
        border-radius: 16px;
        box-sizing: border-box;
        overflow: hidden;
        background-color: light-dark(#f5efe4, #1a1a2e);
        background-image: light-dark(
            linear-gradient(165deg, rgba(255, 252, 246, 0.95) 0%, #efe6d4 38%, #e5dac4 100%),
            linear-gradient(135deg, rgba(30, 28, 38, 0.97) 0%, #1a1a2e 48%, #16213e 100%)
        );
        border: 1px solid light-dark(rgba(139, 90, 43, 0.28), rgba(212, 175, 55, 0.22));
        box-shadow: light-dark(
            inset 0 1px 0 rgba(255, 255, 255, 0.55),
            inset 0 1px 0 rgba(255, 255, 255, 0.06)
        ), 0 4px 16px rgba(0, 0, 0, 0.07);
    }
    div[class*="st-key-step3_hanji_card"]::before {
        content: "";
        position: absolute;
        inset: 0;
        pointer-events: none;
        opacity: light-dark(0.06, 0.09);
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='72' height='72'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
        mix-blend-mode: multiply;
        border-radius: inherit;
    }
    div[class*="st-key-step3_hanji_card"]::after {
        content: "";
        position: absolute;
        inset: 0;
        pointer-events: none;
        border-radius: inherit;
        background: repeating-linear-gradient(
            95deg,
            transparent 0px,
            transparent 5px,
            rgba(212, 175, 55, 0.04) 5px,
            rgba(212, 175, 55, 0.04) 6px
        );
    }
    div[class*="st-key-step3_hanji_card"] [data-testid="stMarkdownContainer"],
    div[class*="st-key-step3_hanji_card"] [data-testid="stCaptionContainer"],
    div[class*="st-key-step3_hanji_card"] h3 {
        position: relative;
        z-index: 1;
    }
    p.saju-step3-pillar-emoji {
        position: relative;
        z-index: 1;
        text-align: center;
        font-size: clamp(1.25rem, 3.8vw, 1.65rem);
        line-height: 1.2;
        margin: 0 0 0.15rem 0;
        letter-spacing: 0.03em;
        user-select: none;
    }
    div[class*="st-key-step3_hanji_card"] [data-testid="stCaptionContainer"] {
        font-weight: 700 !important;
        letter-spacing: 0.12em !important;
        opacity: 0.85 !important;
    }
    div[class*="st-key-step3_hanji_card"] h3 {
        font-size: clamp(1.5rem, 3.8vw, 2.05rem) !important;
        font-weight: 800 !important;
        margin: 0.1rem 0 0 !important;
        letter-spacing: 0.08em !important;
    }
    /* 일주: 가장 크게 + 금색 테두리 */
    div[class*="st-key-step3_hanji_card_day"] {
        padding: 1rem 0.5rem 1.25rem !important;
        border: 2px solid rgba(212, 175, 55, 0.72) !important;
        box-shadow:
            light-dark(inset 0 1px 0 rgba(255, 255, 255, 0.65), inset 0 1px 0 rgba(255, 255, 255, 0.08)),
            0 0 0 1px rgba(184, 137, 43, 0.25),
            0 8px 28px rgba(212, 175, 55, 0.22),
            0 6px 20px rgba(0, 0, 0, 0.1) !important;
    }
    html.saju-dark-tone div[class*="st-key-step3_hanji_card_day"] {
        border-color: rgba(232, 201, 71, 0.55) !important;
        box-shadow:
            inset 0 1px 0 rgba(255, 255, 255, 0.06),
            0 0 0 1px rgba(212, 175, 55, 0.2),
            0 8px 32px rgba(0, 0, 0, 0.45),
            0 0 24px rgba(212, 175, 55, 0.12) !important;
    }
    div[class*="st-key-step3_hanji_card_day"] p.saju-step3-pillar-emoji {
        font-size: clamp(1.45rem, 4.5vw, 1.95rem) !important;
    }
    div[class*="st-key-step3_hanji_card_day"] h3 {
        font-size: clamp(1.85rem, 5.5vw, 2.65rem) !important;
        margin-top: 0.2rem !important;
    }
    html.saju-dark-tone div[class*="st-key-step3_hanji_card"]::before {
        mix-blend-mode: soft-light;
        opacity: 0.075;
    }
    @media (max-width: 900px) {
        div[class*="st-key-step3_pillars_grid"] [data-testid="stHorizontalBlock"] {
            flex-wrap: wrap !important;
            gap: 10px !important;
        }
        div[class*="st-key-step3_pillars_grid"] [data-testid="column"] {
            flex: 1 1 calc(50% - 8px) !important;
            min-width: calc(50% - 8px) !important;
            max-width: calc(50% - 4px) !important;
        }
    }

    /* ===== STEP4 궁합 — 좌우 인물 + 중앙 금색 연결 ===== */
    div[class*="st-key-step4_bridge_row"] [data-testid="column"]:nth-of-type(2) {
        display: flex !important;
        align-items: stretch !important;
        justify-content: center !important;
        min-width: 2.5rem !important;
    }
    .step4-gold-bridge {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 7rem;
        width: 100%;
        padding: 0.25rem 0;
    }
    .step4-gold-bridge .step4-gold-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, #f0e6c8, #d4af37 52%, #7a5e12);
        box-shadow: 0 0 10px rgba(212, 175, 55, 0.38);
    }
    .step4-gold-bridge .step4-gold-line {
        flex: 1 1 auto;
        width: 4px;
        min-height: 2.5rem;
        margin: 6px 0;
        border-radius: 99px;
        background: linear-gradient(
            180deg,
            rgba(212, 175, 55, 0.12) 0%,
            #d4af37 28%,
            #e8b923 72%,
            rgba(212, 175, 55, 0.12) 100%
        );
        box-shadow: 0 0 8px rgba(232, 185, 35, 0.22);
    }
    /* STEP4 입체 궁합 소제목: 이모지+문구 한 줄(좁은 폭은 가로 스크롤) */
    .step4-gunghap-title {
        white-space: nowrap;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        font-size: clamp(1.05rem, 3.8vw, 1.45rem);
        font-weight: 600;
        font-family: ui-serif, "Apple SD Gothic Neo", "Noto Serif KR", serif;
        color: #4a3a22;
        letter-spacing: -0.02em;
        margin: 0.35rem 0 0.75rem 0;
        line-height: 1.35;
    }
    html.saju-dark-tone .step4-gunghap-title {
        color: #e8d9b4;
    }
    .step4-pair-banner {
        display: inline-block;
        max-width: 100%;
        padding: 0.72rem 1.05rem;
        border-radius: 14px;
        font-size: clamp(0.84rem, 2.9vw, 0.96rem);
        line-height: 1.65;
        text-align: center;
        color: #f8fafc;
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid rgba(148, 163, 184, 0.45);
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.28);
    }
    .step4-pair-banner b {
        color: #fde68a;
        font-weight: 800;
    }
    .step4-pair-banner .step4-pair-pillars {
        color: #e2e8f0;
        font-weight: 600;
    }
    html.saju-dark-tone .step4-pair-banner {
        color: #f1f5f9;
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
        border-color: rgba(148, 163, 184, 0.35);
    }
    .step4-metric-frame-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.65rem;
        width: min(100%, 780px);
        margin: 0.75rem auto 1.15rem;
        box-sizing: border-box;
    }
    .step4-metric-frame {
        box-sizing: border-box;
        padding: 0.9rem 0.72rem;
        border-radius: 17px;
        text-align: center;
        border: 1.5px solid color-mix(in srgb, var(--step4-tone) 52%, transparent);
        background: light-dark(
            linear-gradient(155deg, rgba(255, 252, 244, 0.96), rgba(244, 236, 219, 0.92)),
            linear-gradient(155deg, rgba(34, 31, 42, 0.97), rgba(18, 24, 40, 0.95))
        );
        box-shadow:
            0 0 0 1px light-dark(rgba(255, 255, 255, 0.64), rgba(255, 255, 255, 0.06)) inset,
            0 8px 24px light-dark(rgba(98, 79, 39, 0.12), rgba(0, 0, 0, 0.32));
    }
    .step4-metric-title {
        color: light-dark(rgba(55, 48, 38, 0.8), rgba(220, 226, 236, 0.86));
        font-size: clamp(0.82rem, 2.8vw, 0.96rem);
        font-weight: 750;
        margin-bottom: 0.38rem;
    }
    .step4-metric-value {
        color: light-dark(#1a1a2e, rgba(255, 249, 225, 0.98));
        font-size: clamp(1.02rem, 3.35vw, 1.18rem);
        font-weight: 850;
        line-height: 1.28;
        letter-spacing: -0.03em;
    }
    .step4-person-pair {
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(3.2rem, 0.28fr) minmax(0, 1fr);
        gap: 0.75rem;
        align-items: center;
        width: min(100%, 860px);
        margin: 0.65rem auto 1rem;
        box-sizing: border-box;
    }
    .step4-person-card {
        padding: 1rem 1.05rem;
        border-radius: 18px;
        border: 1.5px solid light-dark(rgba(212, 175, 55, 0.32), rgba(212, 175, 55, 0.22));
        background: light-dark(rgba(255, 252, 244, 0.9), rgba(26, 26, 46, 0.76));
        box-shadow: 0 8px 24px light-dark(rgba(98, 79, 39, 0.1), rgba(0, 0, 0, 0.3));
        min-width: 0;
    }
    .step4-person-name {
        display: flex;
        align-items: center;
        gap: 0.46rem;
        color: light-dark(#1a1a2e, rgba(245, 245, 248, 0.96));
        font-size: clamp(1rem, 3.4vw, 1.16rem);
        font-weight: 850;
        margin-bottom: 0.78rem;
    }
    .step4-person-dot {
        width: 1.05rem;
        height: 1.05rem;
        border-radius: 999px;
        flex: 0 0 auto;
        background: #3b82f6;
    }
    .step4-person-partner .step4-person-dot {
        background: #f43f5e;
    }
    .step4-person-body {
        color: light-dark(#211c16, rgba(235, 235, 240, 0.92));
        line-height: 1.7;
        font-size: clamp(0.9rem, 2.95vw, 1rem);
    }
    .step4-person-link {
        text-align: center;
        color: light-dark(#6b5a2a, rgba(212, 175, 55, 0.88));
        font-size: clamp(0.9rem, 3vw, 1.08rem);
        font-weight: 850;
        letter-spacing: 0.16em;
        white-space: nowrap;
    }
    @media (max-width: 720px) {
        .step4-metric-frame-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.42rem;
        }
    }
    @media (max-width: 520px) {
        .step4-metric-frame {
            padding: 0.75rem 0.35rem;
        }
        .step4-person-pair {
            grid-template-columns: minmax(0, 1fr) minmax(2.6rem, 0.22fr) minmax(0, 1fr);
            gap: 0.42rem;
        }
        .step4-person-card {
            padding: 0.82rem 0.62rem;
        }
        .step4-person-body {
            font-size: clamp(0.76rem, 2.75vw, 0.92rem);
            line-height: 1.58;
        }
    }

    /* ===== STEP9 대운 — 수평 스크롤 타임라인 + 세부 레일 ===== */
    @keyframes sajuDwPulseGlow {
        0%,
        100% {
            box-shadow:
                0 0 0 2px rgba(212, 175, 55, 0.45),
                0 4px 20px rgba(212, 175, 55, 0.28),
                inset 0 1px 0 rgba(255, 255, 255, 0.35);
        }
        50% {
            box-shadow:
                0 0 0 5px rgba(212, 175, 55, 0.35),
                0 8px 32px rgba(212, 175, 55, 0.48),
                inset 0 1px 0 rgba(255, 255, 255, 0.45);
        }
    }
    div[class*="st-key-step9_timeline_hscroll"] {
        margin: 0.15rem 0 1rem 0;
        width: 100%;
        max-width: min(100vw, 960px);
        margin-left: auto;
        margin-right: auto;
        box-sizing: border-box;
    }
    div[class*="st-key-step9_timeline_hscroll"] [data-testid="stMarkdownContainer"] {
        margin-bottom: 0 !important;
    }
    .saju-dw-hrail {
        width: 100%;
        box-sizing: border-box;
    }
    .saju-dw-hrail-scroll {
        display: flex;
        flex-direction: row;
        flex-wrap: nowrap;
        gap: 0.65rem;
        overflow-x: auto;
        overflow-y: hidden;
        scroll-snap-type: x proximity;
        -webkit-overflow-scrolling: touch;
        padding: 0.45rem 0.2rem 0.85rem;
        scrollbar-width: thin;
    }
    .saju-dw-hrail-scroll::-webkit-scrollbar {
        height: 7px;
    }
    .saju-dw-hrail-scroll::-webkit-scrollbar-thumb {
        background: rgba(212, 175, 55, 0.45);
        border-radius: 99px;
    }
    .saju-dw-chip {
        flex: 0 0 auto;
        scroll-snap-align: start;
        min-width: 6.75rem;
        max-width: 9.5rem;
        padding: 0.55rem 0.6rem 0.65rem;
        border-radius: 14px;
        box-sizing: border-box;
        text-align: center;
        border: 1px solid light-dark(rgba(139, 90, 43, 0.22), rgba(212, 175, 55, 0.2));
        background: light-dark(
            linear-gradient(165deg, #fdf9f2 0%, #efe6d4 55%, #e8dcc8 100%),
            linear-gradient(145deg, #252836 0%, #1a1a2e 55%, #16213e 100%)
        );
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
    }
    .saju-dw-chip-gj {
        font-size: clamp(1.05rem, 3.2vw, 1.35rem);
        font-weight: 800;
        letter-spacing: 0.06em;
        color: light-dark(#2a2218, #f5f0e6);
        line-height: 1.2;
    }
    .saju-dw-chip-yr {
        font-size: max(12px, 0.78rem);
        font-weight: 650;
        margin-top: 0.2rem;
        color: light-dark(rgba(42, 34, 24, 0.78), rgba(220, 218, 230, 0.85));
        letter-spacing: -0.02em;
    }
    .saju-dw-chip-age {
        font-size: max(11px, 0.72rem);
        font-weight: 600;
        margin-top: 0.08rem;
        color: light-dark(rgba(90, 72, 48, 0.75), rgba(200, 198, 215, 0.72));
    }
    .saju-dw-chip.is-current {
        border: 2px solid rgba(212, 175, 55, 0.85) !important;
        background: light-dark(
            linear-gradient(165deg, #fffaf0 0%, #f3e6c8 40%, #ebd4a8 100%),
            linear-gradient(145deg, #2e2a42 0%, #252a3e 50%, #1e2438 100%)
        ) !important;
    }
    @keyframes sajuDwPulseGlowDark {
        0%,
        100% {
            box-shadow:
                0 0 0 2px rgba(232, 201, 71, 0.38),
                0 4px 18px rgba(0, 0, 0, 0.5),
                0 0 16px rgba(212, 175, 55, 0.18);
        }
        50% {
            box-shadow:
                0 0 0 6px rgba(212, 175, 55, 0.26),
                0 8px 32px rgba(0, 0, 0, 0.58),
                0 0 30px rgba(232, 201, 71, 0.28);
        }
    }
    @media (prefers-reduced-motion: no-preference) {
        .saju-dw-chip.is-current {
            animation: sajuDwPulseGlow 2.4s ease-in-out infinite;
        }
        html.saju-dark-tone .saju-dw-chip.is-current {
            animation: sajuDwPulseGlowDark 2.4s ease-in-out infinite;
        }
    }
    @media (prefers-reduced-motion: reduce) {
        .saju-dw-chip.is-current {
            animation: none;
        }
    }
    div[class*="st-key-step9_timeline_rail"] {
        border-left: 4px solid rgba(212, 175, 55, 0.38);
        padding-left: 1rem;
        margin-left: 0.35rem;
        box-sizing: border-box;
    }

    /* STEP9 모바일 세로 카드(Plotly 대체) */
    .s9-summary-card {
        border-radius: 16px;
        padding: 0.85rem 1rem;
        margin: 0 0 0.85rem;
        border: 1px solid light-dark(rgba(139, 105, 20, 0.28), rgba(212, 175, 55, 0.28));
        background: light-dark(rgba(255, 252, 245, 0.92), rgba(26, 26, 46, 0.72));
        box-sizing: border-box;
    }
    .s9-summary-card.is-highlight {
        border-width: 2px;
        border-color: rgba(212, 175, 55, 0.75);
        box-shadow: 0 4px 18px rgba(212, 175, 55, 0.18);
    }
    .s9-summary-card p {
        margin: 0.35rem 0 0;
        font-size: max(13px, 0.88rem);
        line-height: 1.5;
        color: light-dark(#334155, #e2e8f0);
    }
    .s9-year-stack {
        display: flex;
        flex-direction: column;
        gap: 0.45rem;
        width: 100%;
        max-width: 100%;
        box-sizing: border-box;
    }
    .s9-dae-band {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.35rem 0.55rem;
        padding: 0.5rem 0.65rem;
        margin: 0.35rem 0 0.15rem;
        border-radius: 12px;
        background: light-dark(rgba(212, 175, 55, 0.12), rgba(212, 175, 55, 0.1));
        border: 1px dashed light-dark(rgba(139, 105, 20, 0.35), rgba(212, 175, 55, 0.35));
        font-size: max(12px, 0.8rem);
    }
    .s9-dae-band-pillar {
        font-weight: 800;
        letter-spacing: 0.04em;
    }
    .s9-year-row {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto minmax(0, 1.1fr);
        gap: 0.45rem 0.5rem;
        align-items: start;
        padding: 0.55rem 0.65rem;
        border-radius: 14px;
        border: 1px solid light-dark(rgba(148, 163, 184, 0.28), rgba(212, 175, 55, 0.18));
        background: light-dark(#fff, rgba(22, 22, 38, 0.65));
        box-sizing: border-box;
    }
    .s9-year-row.is-current {
        border: 2px solid rgba(212, 175, 55, 0.8);
        background: light-dark(#fffaf0, rgba(36, 32, 48, 0.85));
    }
    .s9-year-period {
        font-weight: 800;
        font-size: max(14px, 0.95rem);
        color: light-dark(#1e293b, #f1f5f9);
    }
    .s9-year-sub {
        font-size: max(11px, 0.72rem);
        color: light-dark(#64748b, #94a3b8);
        margin-top: 0.12rem;
        line-height: 1.35;
    }
    .s9-ten-badge {
        display: inline-block;
        padding: 0.2rem 0.45rem;
        border-radius: 999px;
        font-size: max(11px, 0.72rem);
        font-weight: 700;
        white-space: nowrap;
        color: #0f172a;
        background: color-mix(in srgb, var(--s9-badge, #94a3b8) 35%, transparent);
        border: 1px solid var(--s9-badge, #94a3b8);
    }
    .s9-year-right {
        text-align: right;
        min-width: 0;
    }
    .s9-grade {
        display: inline-block;
        font-size: max(11px, 0.75rem);
        font-weight: 800;
        padding: 0.1rem 0.35rem;
        border-radius: 6px;
        margin-right: 0.25rem;
    }
    .s9-grade-a { background: rgba(34, 197, 94, 0.2); color: #15803d; }
    .s9-grade-b { background: rgba(96, 165, 250, 0.2); color: #1d4ed8; }
    .s9-grade-c { background: rgba(148, 163, 184, 0.25); color: #475569; }
    .s9-grade-d { background: rgba(251, 191, 36, 0.25); color: #b45309; }
    .s9-grade-e { background: rgba(248, 113, 113, 0.2); color: #b91c1c; }
    html.saju-dark-tone .s9-grade-a { color: #86efac; }
    html.saju-dark-tone .s9-grade-b { color: #93c5fd; }
    html.saju-dark-tone .s9-grade-c { color: #cbd5e1; }
    html.saju-dark-tone .s9-grade-d { color: #fcd34d; }
    html.saju-dark-tone .s9-grade-e { color: #fca5a5; }
    .s9-dots {
        font-size: 0.65rem;
        letter-spacing: 0.06em;
        color: light-dark(#64748b, #94a3b8);
    }
    .s9-year-detail {
        font-size: max(11px, 0.74rem);
        line-height: 1.4;
        color: light-dark(#475569, #cbd5e1);
        margin-top: 0.2rem;
    }
    .s9-year-extra {
        font-size: max(10px, 0.68rem);
        color: light-dark(#8b6914, #d4af37);
        margin-top: 0.15rem;
    }

    /* STEP9: 행동 타이밍 탭 제목 4개를 스크롤 없이 한 줄 고정 */
    .st-key-step9_action_timing .stTabs [data-baseweb="tab-list"] {
        display: grid !important;
        grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
        gap: 0.25rem !important;
        overflow: visible !important;
        width: 100% !important;
    }
    .st-key-step9_action_timing .stTabs [data-baseweb="tab"] {
        min-width: 0 !important;
        width: 100% !important;
        padding: 0.4rem 0.04rem !important;
        justify-content: center !important;
        text-align: center !important;
        white-space: nowrap !important;
        font-size: clamp(11px, 2.75vw, 14px) !important;
        letter-spacing: -0.085em !important;
    }
    .st-key-step9_action_timing .stTabs [data-baseweb="tab"] p {
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: clip !important;
        letter-spacing: -0.085em !important;
        font-size: inherit !important;
    }

    /* STEP9: 이사·이직·결혼·임신 탭 해석 */
    div[class*="st-key-step9_action_"] {
        border-color: light-dark(rgba(212, 175, 55, 0.35), rgba(212, 175, 55, 0.22)) !important;
    }
    .saju-step9-action-frame {
        box-sizing: border-box;
        margin: 0.55rem 0 0.85rem;
        padding: 1rem 1.05rem 1.05rem;
        border-radius: 18px;
        border: 1.5px solid color-mix(in srgb, var(--step9-action-tone) 55%, transparent);
        background: light-dark(
            linear-gradient(155deg, rgba(255, 252, 244, 0.96), rgba(244, 236, 219, 0.92)),
            linear-gradient(155deg, rgba(34, 31, 42, 0.97), rgba(18, 24, 40, 0.95))
        );
        box-shadow:
            0 0 0 1px light-dark(rgba(255, 255, 255, 0.68), rgba(255, 255, 255, 0.06)) inset,
            0 10px 28px light-dark(rgba(98, 79, 39, 0.13), rgba(0, 0, 0, 0.34));
    }
    .saju-step9-action-title {
        display: inline-flex;
        margin-bottom: 0.7rem;
        padding: 0.28rem 0.72rem;
        border-radius: 999px;
        background: color-mix(in srgb, var(--step9-action-tone) 18%, transparent);
        color: light-dark(#4a3710, #f8e7b8);
        font-weight: 850;
        font-size: clamp(0.92rem, 3vw, 1.02rem);
        letter-spacing: -0.02em;
    }
    .saju-step9-action-verdict {
        display: flex;
        align-items: center;
        gap: 0.45rem;
        margin-bottom: 0.62rem;
        color: light-dark(#1a1a2e, rgba(245, 245, 248, 0.96));
        font-weight: 800;
        font-size: clamp(0.98rem, 3.2vw, 1.08rem);
    }
    .saju-step9-action-verdict span {
        font-size: 1.15em;
    }
    .saju-step9-action-message {
        padding: 0.82rem 0.9rem;
        border-radius: 14px;
        background: light-dark(rgba(255, 255, 255, 0.48), rgba(255, 255, 255, 0.07));
        border: 1px solid color-mix(in srgb, var(--step9-action-tone) 24%, transparent);
        color: light-dark(#211c16, rgba(245, 245, 248, 0.94));
        line-height: 1.68;
        font-size: clamp(0.94rem, 3vw, 1.02rem);
    }
    .saju-step9-action-note {
        margin-top: 0.75rem;
        color: light-dark(rgba(55, 48, 38, 0.82), rgba(220, 226, 236, 0.86));
        font-size: clamp(0.86rem, 2.8vw, 0.95rem);
        line-height: 1.55;
    }
    .saju-step9-action-caution {
        margin-top: 0.8rem;
        padding: 0.78rem 0.88rem;
        border-radius: 13px;
        border: 1px solid light-dark(rgba(245, 158, 11, 0.34), rgba(251, 191, 36, 0.24));
        background: light-dark(rgba(255, 247, 237, 0.82), rgba(245, 158, 11, 0.1));
        color: light-dark(#7c2d12, #fde68a);
        line-height: 1.58;
        font-weight: 650;
    }

    /* ===== STEP10 총평 — 단일 리포트 시트 느낌 ===== */
    div[class*="st-key-step10_report_sheet"] {
        max-width: 760px;
        margin: 0 auto 1rem;
        padding: 1.35rem 1.2rem 1.5rem;
        border-radius: 14px;
        box-sizing: border-box;
        background: light-dark(
            linear-gradient(180deg, rgba(255, 255, 255, 0.55), rgba(253, 249, 243, 0.35)),
            linear-gradient(135deg, rgba(26, 26, 46, 0.72), rgba(22, 33, 62, 0.45))
        );
        border: 1px solid light-dark(rgba(212, 175, 55, 0.18), rgba(212, 175, 55, 0.12));
        box-shadow: light-dark(
            0 2px 14px rgba(0, 0, 0, 0.04),
            0 2px 18px rgba(0, 0, 0, 0.25)
        );
    }
    div[class*="st-key-step10_export_bar"] {
        max-width: 760px;
        margin: 0 auto 0.75rem;
    }

    /* STEP10 오행 요약 막대(도넛 차트 대체) */
    .s9-oheng-summary {
        display: flex;
        flex-direction: column;
        gap: 0.55rem;
        margin: 0.5rem 0 1rem;
        padding: 0.85rem 1rem;
        border-radius: 14px;
        border: 1px solid light-dark(rgba(139, 105, 20, 0.22), rgba(212, 175, 55, 0.22));
        background: light-dark(rgba(255, 252, 245, 0.92), rgba(26, 26, 46, 0.65));
        box-sizing: border-box;
    }
    .s9-oheng-row {
        display: grid;
        grid-template-columns: 4.5rem 3.2rem 1fr;
        align-items: center;
        gap: 0.5rem;
    }
    .s9-oheng-lbl {
        font-weight: 700;
        font-size: max(12px, 0.82rem);
        color: light-dark(#334155, #e2e8f0);
    }
    .s9-oheng-pct {
        font-size: max(12px, 0.8rem);
        font-weight: 650;
        text-align: right;
        color: light-dark(#64748b, #94a3b8);
    }
    .s9-oheng-bar {
        display: block;
        height: 10px;
        border-radius: 999px;
        background: linear-gradient(90deg, #d4af37, #fbbf24);
        width: var(--w, 0%);
        max-width: 100%;
        box-shadow: 0 0 10px rgba(212, 175, 55, 0.25);
    }
    .step10-exec-card {
        box-sizing: border-box;
        width: 100%;
        margin: 0.65rem 0 1rem;
        padding: 1rem 1.05rem 1.08rem;
        border-radius: 18px;
        border: 1.5px solid color-mix(in srgb, var(--step10-tone) 54%, transparent);
        background: light-dark(
            linear-gradient(155deg, rgba(255, 252, 244, 0.96), rgba(244, 236, 219, 0.92)),
            linear-gradient(155deg, rgba(34, 31, 42, 0.97), rgba(18, 24, 40, 0.95))
        );
        box-shadow:
            0 0 0 1px light-dark(rgba(255, 255, 255, 0.66), rgba(255, 255, 255, 0.06)) inset,
            0 10px 28px light-dark(rgba(98, 79, 39, 0.13), rgba(0, 0, 0, 0.34));
    }
    .step10-exec-title {
        display: inline-flex;
        margin-bottom: 0.5rem;
        padding: 0.28rem 0.72rem;
        border-radius: 999px;
        background: color-mix(in srgb, var(--step10-tone) 18%, transparent);
        color: light-dark(#4a3710, #f8e7b8);
        font-weight: 850;
        font-size: clamp(0.96rem, 3.1vw, 1.08rem);
        letter-spacing: -0.02em;
    }
    .step10-exec-subtitle {
        margin-bottom: 0.75rem;
        color: light-dark(rgba(55, 48, 38, 0.78), rgba(220, 226, 236, 0.84));
        font-size: clamp(0.84rem, 2.75vw, 0.94rem);
        line-height: 1.45;
    }
    .step10-exec-body {
        color: light-dark(#211c16, rgba(245, 245, 248, 0.94));
        line-height: 1.78;
        font-size: clamp(0.94rem, 3vw, 1.02rem);
        text-align: left;
    }

    /* STEP10 건강 카드 — 라이트: 밝은 배경·진한 글씨 / 다크: 기존 톤 */
    div[class*="st-key-step10_health_fortune"] .saju-step10-health-card {
        box-sizing: border-box;
        border-radius: 18px;
        padding: 1.1rem 1.05rem 1.15rem;
        border: 2px solid light-dark(#f472b6, rgba(244, 114, 182, 0.55));
        background: light-dark(
            linear-gradient(165deg, #ffffff 0%, #fff5f7 52%, #ffe4e6 100%),
            linear-gradient(165deg, #1a1020 0%, #121828 100%)
        );
        color: light-dark(#1f2937, #e2e8f0);
    }
    div[class*="st-key-step10_health_fortune"] .saju-step10-health-head {
        color: light-dark(#be123c, #f472b6);
        font-size: 1.35rem;
        font-weight: 800;
    }
    div[class*="st-key-step10_health_fortune"] .saju-step10-health-sub,
    div[class*="st-key-step10_health_fortune"] .saju-step10-health-meta,
    div[class*="st-key-step10_health_fortune"] .saju-step10-age-band,
    div[class*="st-key-step10_health_fortune"] .saju-step10-risk-label {
        color: light-dark(#334155, #f8fafc) !important;
        font-size: 0.95rem;
        font-weight: 650;
        opacity: 1 !important;
    }
    div[class*="st-key-step10_health_fortune"] .saju-step10-age-band {
        margin-bottom: 8px;
    }
    div[class*="st-key-step10_health_fortune"] .saju-step10-risk-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
        font-weight: 700;
        flex-wrap: wrap;
        gap: 8px;
    }
    div[class*="st-key-step10_health_fortune"] .saju-step10-health-card .saju-step10-risk-block {
        color: light-dark(#334155, #f8fafc) !important;
    }
    div[class*="st-key-step10_health_fortune"] .saju-step10-health-card .saju-step10-risk-block span:not(.saju-step10-risk-score):not(.saju-step10-risk-label) {
        color: inherit !important;
    }
    div[class*="st-key-step10_health_fortune"] .saju-step10-health-yong {
        padding: 1rem 1.05rem;
        border-radius: 14px;
        margin-bottom: 1rem;
        background: light-dark(rgba(244, 114, 182, 0.12), rgba(244, 114, 182, 0.09));
        color: light-dark(#9f1239, #fbcfe8);
        font-weight: 650;
    }
    div[class*="st-key-step10_health_fortune"] .saju-step10-health-weak {
        padding: 1rem 1.05rem;
        border-radius: 14px;
        line-height: 1.75;
        margin-bottom: 1rem;
        background: light-dark(#fffefb, #1f2937);
        color: light-dark(#1e293b, #e5e7eb);
        font-size: 0.98rem;
        border: 1px solid light-dark(rgba(139, 105, 20, 0.16), rgba(148, 163, 184, 0.22));
    }
    div[class*="st-key-step10_health_fortune"] .saju-step10-health-card .saju-step10-risk-score {
        font-weight: 800;
    }
    div[class*="st-key-step10_health_fortune"] .saju-health-tips {
        margin-top: 0.25rem;
        padding: 1rem 1.05rem;
        border-radius: 12px;
        font-size: max(13px, 0.92rem);
        line-height: 1.65;
        background: light-dark(#fff7ed, rgba(15, 23, 42, 0.55));
        border: 1px solid light-dark(rgba(190, 24, 93, 0.22), rgba(244, 114, 182, 0.35));
        box-sizing: border-box;
        color: light-dark(#1e293b, #f1f5f9) !important;
    }
    div[class*="st-key-step10_health_fortune"] .saju-health-tips * {
        color: inherit !important;
    }
    div[class*="st-key-step10_health_fortune"] .saju-health-tips b {
        color: light-dark(#be123c, #f9a8d4) !important;
    }

    /* STEP10 건강 카드 — 앱 다크 톤(html.saju-dark-tone) 가독성 (light-dark와 OS 불일치 보정) */
    html.saju-dark-tone div[class*="st-key-step10_health_fortune"] .saju-step10-health-card {
        background: linear-gradient(165deg, #1a1020 0%, #121828 100%) !important;
        color: #f1f5f9 !important;
        border-color: rgba(244, 114, 182, 0.55) !important;
    }
    html.saju-dark-tone div[class*="st-key-step10_health_fortune"] .saju-step10-health-head {
        color: #fb7185 !important;
    }
    html.saju-dark-tone div[class*="st-key-step10_health_fortune"] .saju-step10-health-sub,
    html.saju-dark-tone div[class*="st-key-step10_health_fortune"] .saju-step10-health-meta,
    html.saju-dark-tone div[class*="st-key-step10_health_fortune"] .saju-step10-age-band,
    html.saju-dark-tone div[class*="st-key-step10_health_fortune"] .saju-step10-risk-label {
        color: #f8fafc !important;
        opacity: 1 !important;
    }
    html.saju-dark-tone div[class*="st-key-step10_health_fortune"] .saju-step10-health-yong {
        background: rgba(244, 114, 182, 0.16) !important;
        color: #fce7f3 !important;
        border: 1px solid rgba(244, 114, 182, 0.28);
    }
    html.saju-dark-tone div[class*="st-key-step10_health_fortune"] .saju-step10-health-yong b,
    html.saju-dark-tone div[class*="st-key-step10_health_fortune"] .saju-step10-health-yong span {
        color: #fdf2f8 !important;
    }
    html.saju-dark-tone div[class*="st-key-step10_health_fortune"] .saju-step10-health-weak {
        background: rgba(15, 23, 42, 0.78) !important;
        color: #f1f5f9 !important;
        border-color: rgba(148, 163, 184, 0.3) !important;
    }
    html.saju-dark-tone div[class*="st-key-step10_health_fortune"] .saju-step10-risk-block {
        color: #f8fafc !important;
    }
    html.saju-dark-tone div[class*="st-key-step10_health_fortune"] .saju-step10-risk-block span:not(.saju-step10-risk-score):not(.saju-step10-risk-label) {
        color: #f8fafc !important;
    }
    html.saju-dark-tone div[class*="st-key-step10_health_fortune"] .saju-health-tips {
        background: rgba(15, 23, 42, 0.62) !important;
        color: #f8fafc !important;
        border-color: rgba(244, 114, 182, 0.38) !important;
    }
    html.saju-dark-tone div[class*="st-key-step10_health_fortune"] .saju-health-tips * {
        color: inherit !important;
    }
    html.saju-dark-tone div[class*="st-key-step10_health_fortune"] .saju-health-tips b {
        color: #f9a8d4 !important;
    }

    /* Streamlit 다크 테마 — OS 라이트와 light-dark() 불일치 시 건강 카드 보조 문구 */
    [data-theme="dark"] div[class*="st-key-step10_health_fortune"] .saju-step10-health-card,
    .stApp[data-theme="dark"] div[class*="st-key-step10_health_fortune"] .saju-step10-health-card {
        background: linear-gradient(165deg, #1a1020 0%, #121828 100%) !important;
        color: #f1f5f9 !important;
    }
    [data-theme="dark"] div[class*="st-key-step10_health_fortune"] .saju-step10-health-sub,
    [data-theme="dark"] div[class*="st-key-step10_health_fortune"] .saju-step10-health-meta,
    [data-theme="dark"] div[class*="st-key-step10_health_fortune"] .saju-step10-age-band,
    [data-theme="dark"] div[class*="st-key-step10_health_fortune"] .saju-step10-risk-block,
    [data-theme="dark"] div[class*="st-key-step10_health_fortune"] .saju-step10-risk-label,
    .stApp[data-theme="dark"] div[class*="st-key-step10_health_fortune"] .saju-step10-health-sub,
    .stApp[data-theme="dark"] div[class*="st-key-step10_health_fortune"] .saju-step10-health-meta,
    .stApp[data-theme="dark"] div[class*="st-key-step10_health_fortune"] .saju-step10-age-band,
    .stApp[data-theme="dark"] div[class*="st-key-step10_health_fortune"] .saju-step10-risk-block,
    .stApp[data-theme="dark"] div[class*="st-key-step10_health_fortune"] .saju-step10-risk-label {
        color: #f8fafc !important;
        opacity: 1 !important;
    }
    @media (prefers-color-scheme: dark) {
        div[class*="st-key-step10_health_fortune"] .saju-step10-health-sub,
        div[class*="st-key-step10_health_fortune"] .saju-step10-health-meta,
        div[class*="st-key-step10_health_fortune"] .saju-step10-age-band,
        div[class*="st-key-step10_health_fortune"] .saju-step10-risk-block,
        div[class*="st-key-step10_health_fortune"] .saju-step10-risk-label {
            color: #f8fafc !important;
            opacity: 1 !important;
        }
    }

    html.saju-dark-tone .step10-exec-card {
        color: #f1f5f9;
    }
    html.saju-dark-tone .step10-exec-subtitle {
        color: #cbd5e1 !important;
    }
    html.saju-dark-tone .step10-exec-body {
        color: #f1f5f9 !important;
    }
    html.saju-dark-tone div[class*="st-key-step10_report_sheet"] {
        color: #ece8e0;
    }
    html.saju-dark-tone div[class*="st-key-step10_report_sheet"] .stMarkdown,
    html.saju-dark-tone div[class*="st-key-step10_report_sheet"] p {
        color: rgba(235, 228, 210, 0.94) !important;
    }

    /* ===== 구조화 해석 블록(STEP3·STEP6 등) ===== */
    .saju-ix-donut-wrap {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 0.25rem 0;
    }
    .saju-ix-donut-num {
        fill: light-dark(#1a1a2e, #f5f5f5);
    }
    .saju-ix-donut-wrap svg text {
        fill: light-dark(#1a1a2e, #f0f0f0);
    }
    .saju-ix-one-liner {
        font-size: clamp(1.02rem, 0.95rem + 0.35vw, 1.2rem);
        font-weight: 750;
        line-height: 1.45;
        margin: 0 0 0.65rem 0;
        padding: 0.55rem 0.65rem;
        border-radius: 12px;
        background: linear-gradient(
            105deg,
            rgba(212, 175, 55, 0.14) 0%,
            rgba(251, 191, 36, 0.08) 45%,
            transparent 100%
        );
        border-left: 4px solid #d4af37;
        box-decoration-break: clone;
        color: light-dark(#1a1a2e, rgba(245, 245, 245, 0.96));
    }
    .saju-ix-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 2px;
    }
    .saju-ix-tag {
        display: inline-block;
        font-size: 0.82rem;
        font-weight: 650;
        padding: 0.28rem 0.65rem;
        border-radius: 999px;
        background: light-dark(
            rgba(212, 175, 55, 0.12),
            rgba(212, 175, 55, 0.16)
        );
        border: 1px solid light-dark(rgba(212, 175, 55, 0.35), rgba(251, 191, 36, 0.25));
        color: light-dark(#3d3428, rgba(235, 235, 235, 0.95));
    }
    div[class*="st-key-saju_ix_"][class*="detail"] .stMarkdown p {
        line-height: 1.65 !important;
        margin-bottom: 0.75rem !important;
        font-size: max(15px, 0.96rem) !important;
        color: light-dark(rgba(26, 26, 46, 0.92), rgba(230, 230, 230, 0.9)) !important;
    }
    .saju-ix-detail-frame {
        box-sizing: border-box;
        width: 100%;
        margin: 0.62rem 0 0.9rem;
        padding: 0.95rem 1.02rem;
        border-radius: 17px;
        border: 1.5px solid color-mix(in srgb, var(--saju-ix-tone) 52%, transparent);
        background: light-dark(
            linear-gradient(155deg, rgba(255, 252, 244, 0.96), rgba(244, 236, 219, 0.92)),
            linear-gradient(155deg, rgba(34, 31, 42, 0.97), rgba(18, 24, 40, 0.95))
        );
        box-shadow:
            0 0 0 1px light-dark(rgba(255, 255, 255, 0.64), rgba(255, 255, 255, 0.06)) inset,
            0 8px 24px light-dark(rgba(98, 79, 39, 0.12), rgba(0, 0, 0, 0.32));
    }
    .saju-ix-detail-body {
        color: light-dark(#211c16, rgba(245, 245, 248, 0.94));
        line-height: 1.78;
        font-size: clamp(0.94rem, 3vw, 1.03rem);
        text-align: left;
    }
    .saju-ix-detail-title {
        font-weight: 850;
        font-size: clamp(0.98rem, 3.2vw, 1.06rem);
        margin-bottom: 0.55rem;
        color: light-dark(#5c4510, #f4d179);
    }
    .saju-ix-detail-body b {
        color: light-dark(#5c4510, #f4d179);
        font-weight: 850;
    }
    .saju-ix-advice-line {
        margin: 0.35rem 0 0.35rem 0;
        padding: 0.45rem 0.55rem 0.45rem 0.5rem;
        border-radius: 10px;
        background: light-dark(rgba(99, 102, 241, 0.05), rgba(99, 102, 241, 0.1));
        border-left: 3px solid rgba(99, 102, 241, 0.45);
        font-size: max(15px, 0.95rem);
        line-height: 1.5;
        color: light-dark(#1a1a2e, rgba(235, 235, 235, 0.94));
    }

    /* ===== 오행 에너지 바 · 용신 히어로 · 십성 스트립 ===== */
    .saju-yongshin-hero {
        text-align: center;
        padding: 1rem 0.75rem 1.15rem;
        margin: 0 0 1rem 0;
        border-radius: 18px;
        background: radial-gradient(
            ellipse 120% 80% at 50% 0%,
            rgba(212, 175, 55, 0.22) 0%,
            rgba(212, 175, 55, 0.06) 42%,
            transparent 72%
        );
        border: 1px solid light-dark(rgba(212, 175, 55, 0.35), rgba(232, 185, 35, 0.22));
    }
    .saju-yongshin-label {
        display: block;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.35em;
        color: light-dark(rgba(180, 140, 50, 0.95), rgba(212, 175, 55, 0.88));
        margin-bottom: 0.35rem;
    }
    .saju-yongshin-core {
        display: inline-block;
        font-size: clamp(2.35rem, 5.5vw, 3.2rem);
        font-weight: 900;
        line-height: 1.1;
        letter-spacing: 0.06em;
        color: light-dark(#1a1a2e, #e8e8ec);
        animation: sajuyong-pulse 2.6s ease-in-out infinite;
    }
    .saju-yongshin-core.is-muted {
        font-size: clamp(1.2rem, 3vw, 1.5rem);
        animation: none;
        opacity: 0.85;
    }
    .saju-yongshin-ko {
        display: block;
        font-size: 1.05rem;
        font-weight: 750;
        margin-top: 0.25rem;
        color: light-dark(#3d3428, var(--saju-text-body));
    }
    .saju-yongshin-sub {
        display: block;
        font-size: 0.82rem;
        font-weight: 600;
        margin-top: 0.35rem;
        opacity: 0.78;
        color: light-dark(#4a4a5c, var(--saju-text-accent));
    }
    @keyframes sajuyong-pulse {
        0%,
        100% {
            text-shadow: 0 0 10px rgba(212, 175, 55, 0.4), 0 0 26px rgba(232, 185, 35, 0.22),
                0 0 40px rgba(212, 175, 55, 0.1);
            filter: drop-shadow(0 0 6px rgba(232, 185, 35, 0.28));
        }
        50% {
            text-shadow: 0 0 16px rgba(232, 185, 35, 0.5), 0 0 34px rgba(212, 175, 55, 0.32),
                0 0 52px rgba(232, 185, 35, 0.14);
            filter: drop-shadow(0 0 10px rgba(212, 175, 55, 0.42));
        }
    }

    .saju-oheng-bars {
        display: flex;
        flex-direction: column;
        gap: 10px;
        margin: 0.25rem 0 1rem 0;
    }
    .saju-elbar {
        display: grid;
        grid-template-columns: 3.2rem 1fr 2.6rem;
        align-items: center;
        gap: 10px;
    }
    .saju-elbar-label {
        font-weight: 800;
        font-size: 0.88rem;
        white-space: nowrap;
    }
    .saju-elbar-label .ko {
        margin-right: 4px;
        color: light-dark(#2d2a26, rgba(235, 235, 235, 0.92));
    }
    .saju-elbar-label .han {
        font-size: 0.78rem;
        opacity: 0.72;
    }
    .saju-elbar-track {
        height: 14px;
        border-radius: 999px;
        background: light-dark(rgba(0, 0, 0, 0.055), rgba(255, 255, 255, 0.07));
        overflow: hidden;
        box-shadow: inset 0 1px 4px rgba(0, 0, 0, 0.14),
            0 0 0 1px light-dark(rgba(212, 175, 55, 0.22), rgba(212, 175, 55, 0.12));
    }
    .saju-elbar-fill {
        height: 100%;
        border-radius: 999px;
        min-width: 0;
        transition: width 0.45s cubic-bezier(0.22, 1, 0.36, 1);
        box-shadow: 0 0 16px rgba(0, 0, 0, 0.12);
    }
    .saju-elbar-fill.is-yongshin {
        box-shadow: 0 0 18px var(--saju-glow), 0 0 32px rgba(212, 175, 55, 0.22);
        outline: 1px solid rgba(232, 185, 35, 0.5);
        outline-offset: 1px;
    }
    .saju-elbar-fill[data-el="wood"] {
        background: linear-gradient(90deg, #14532d, #4ade80 48%, #86efac);
    }
    .saju-elbar-fill[data-el="fire"] {
        background: linear-gradient(90deg, #7f1d1d, #f87171 48%, #fecaca);
    }
    .saju-elbar-fill[data-el="earth"] {
        background: linear-gradient(90deg, #713f12, #facc15 46%, #fef08a);
    }
    .saju-elbar-fill[data-el="metal"] {
        background: linear-gradient(90deg, #1e293b, #94a3b8 40%, #cbd5e1 70%, #e2e8f0);
    }
    .saju-elbar-fill[data-el="water"] {
        background: linear-gradient(90deg, #0c4a6e, #60a5fa 46%, #93c5fd);
    }
    .saju-elbar-pct {
        font-size: 0.8rem;
        font-weight: 750;
        text-align: right;
        opacity: 0.88;
        font-variant-numeric: tabular-nums;
    }

    .saju-tenstrip {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: center;
        margin-top: 0.35rem;
    }
    .saju-tenchip {
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 4.5rem;
        padding: 0.45rem 0.5rem 0.4rem;
        border-radius: 14px;
        background: light-dark(
            linear-gradient(165deg, rgba(255, 255, 255, 0.7), rgba(253, 249, 243, 0.5)),
            linear-gradient(165deg, rgba(35, 35, 55, 0.55), rgba(22, 33, 62, 0.35))
        );
        border: 1px solid light-dark(rgba(212, 175, 55, 0.22), rgba(212, 175, 55, 0.18));
    }
    .saju-ten-ic {
        font-size: 1.35rem;
        line-height: 1.2;
    }
    .saju-ten-name {
        font-size: 0.82rem;
        font-weight: 800;
        margin-top: 0.15rem;
        color: light-dark(#1a1a2e, rgba(240, 240, 245, 0.95));
    }
    .saju-ten-pill {
        font-size: 0.65rem;
        font-weight: 700;
        margin-top: 0.2rem;
        padding: 0.12rem 0.4rem;
        border-radius: 999px;
        background: rgba(212, 175, 55, 0.15);
        color: light-dark(#5c4d2a, rgba(250, 240, 210, 0.9));
    }
    .saju-ten-mini {
        margin: 0;
        font-size: 1.05rem;
        font-weight: 700;
    }

    /* ===== STEP11 AI 챗봇 — 말풍선·역할 (뷰포트 스크롤은 위 `step11_hanji_chat` 규칙) ===== */
    .step11-legend-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 12px;
        justify-content: center;
    }
    .step11-legend-card {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 8px 12px 10px;
        border-radius: 14px;
        max-width: min(100%, 280px);
        border: 1px solid transparent;
    }
    .step11-legend-ai {
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.14), rgba(99, 102, 241, 0.06));
        border-color: rgba(212, 175, 55, 0.32);
    }
    .step11-legend-expert {
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.18), rgba(251, 191, 36, 0.08));
        border-color: rgba(212, 175, 55, 0.35);
    }
    .step11-legend-ic {
        font-size: 1.25rem;
        line-height: 1.2;
        opacity: 0.9;
    }
    .step11-legend-title {
        font-weight: 800;
        font-size: 0.88rem;
        margin-bottom: 2px;
        color: light-dark(#1a1a2e, rgba(245, 245, 245, 0.96));
    }
    .step11-legend-desc {
        font-size: 0.72rem;
        line-height: 1.35;
        opacity: 0.82;
        color: light-dark(#3d3428, rgba(220, 220, 230, 0.88));
    }
    .step11-msg-row {
        margin-bottom: 10px;
    }
    .step11-msg-user {
        display: flex;
        justify-content: flex-end;
    }
    .step11-msg-assistant {
        display: flex;
        justify-content: flex-start;
    }
    .step11-bubble {
        max-width: min(100%, 640px);
        border-radius: 16px 16px 16px 6px;
        padding: 11px 14px 12px;
        box-sizing: border-box;
        border: 1px solid light-dark(rgba(0, 0, 0, 0.07), rgba(255, 255, 255, 0.1));
        box-shadow: 0 2px 14px rgba(0, 0, 0, 0.06);
    }
    .step11-msg-user .step11-bubble {
        border-radius: 16px 16px 6px 16px;
        max-width: min(92%, 520px);
    }
    .step11-bubble-user {
        background: linear-gradient(
            155deg,
            #1e3a5f 0%,
            #1e2a4a 42%,
            #172554 100%
        );
        border: 1px solid rgba(30, 58, 138, 0.55) !important;
        box-shadow: 0 4px 18px rgba(15, 23, 42, 0.25);
    }
    .step11-bubble-user .step11-bubble-body,
    .step11-bubble-user .step11-role-pill {
        color: #e8eefc !important;
    }
    .step11-bubble-user .step11-role-user {
        background: rgba(255, 255, 255, 0.12) !important;
        color: #dbeafe !important;
        border: 1px solid rgba(147, 197, 253, 0.35) !important;
    }
    .step11-bubble-ai {
        background: light-dark(
            linear-gradient(165deg, rgba(255, 255, 255, 0.82), rgba(253, 248, 238, 0.62)),
            linear-gradient(165deg, rgba(36, 34, 48, 0.88), rgba(22, 26, 38, 0.78))
        );
        border: 2px solid light-dark(rgba(201, 162, 39, 0.65), rgba(232, 201, 71, 0.5)) !important;
        box-shadow: 0 0 0 1px rgba(212, 175, 55, 0.12), 0 4px 22px rgba(212, 175, 55, 0.12);
    }
    .step11-bubble-expert {
        background: light-dark(
            linear-gradient(165deg, rgba(255, 251, 235, 0.95), rgba(254, 243, 199, 0.45)),
            linear-gradient(165deg, rgba(55, 40, 20, 0.85), rgba(35, 28, 18, 0.9))
        );
        border: 1px solid rgba(212, 175, 55, 0.45);
        box-shadow: 0 0 0 1px rgba(251, 191, 36, 0.12), 0 4px 18px rgba(212, 175, 55, 0.12);
    }
    .step11-role-row {
        margin-bottom: 6px;
    }
    .step11-role-pill {
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.02em;
        padding: 0.22rem 0.55rem;
        border-radius: 999px;
    }
    .step11-role-user {
        background: rgba(59, 130, 246, 0.15);
        color: #1e40af;
    }
    .step11-role-ai {
        background: linear-gradient(90deg, rgba(212, 175, 55, 0.22), rgba(99, 102, 241, 0.12));
        color: light-dark(#5c4510, #fef9c3);
        border: 1px solid rgba(212, 175, 55, 0.35);
    }
    .step11-role-expert {
        background: linear-gradient(90deg, rgba(212, 175, 55, 0.28), rgba(251, 191, 36, 0.12));
        color: light-dark(#5c4510, #fef3c7);
        border: 1px solid rgba(180, 130, 40, 0.45);
    }
    .step11-bubble-body {
        font-size: max(15px, 0.94rem);
        line-height: 1.55;
        color: light-dark(#1a1a2e, rgba(235, 235, 240, 0.94));
    }
    .step11-ai-deco {
        display: flex;
        align-items: center;
        gap: 6px;
        margin: 4px 0 8px;
        opacity: 0.95;
    }
    .step11-deco-svg {
        flex-shrink: 0;
        filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.12));
    }
    .step11-expert-deco {
        margin: 4px 0 8px;
        text-align: left;
    }
    .step11-seal {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2.1rem;
        height: 2.1rem;
        border-radius: 6px;
        font-size: 1.1rem;
        font-weight: 900;
        color: #7f1d1d;
        background: linear-gradient(145deg, #fecaca, #fca5a5);
        border: 2px solid rgba(185, 28, 28, 0.35);
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
    }
    p.step12-global-sync-line {
        font-size: max(13px, 0.84rem);
        line-height: 1.45;
        margin: 0.2rem 0 0.45rem 0;
        padding: 0.35rem 0.45rem;
        border-radius: 8px;
        background: light-dark(rgba(248, 250, 252, 0.9), rgba(26, 26, 46, 0.55));
        border: 1px solid light-dark(rgba(226, 232, 240, 0.95), rgba(212, 175, 55, 0.12));
        color: light-dark(#1e293b, rgba(235, 235, 240, 0.92));
    }

    /* ===== STEP2 레이아웃 ===== */
    .input-title { font-size: clamp(1.0625rem, 1rem + 0.4vw, 1.4rem); font-weight: 700; margin-bottom: 5px; }
    .stRadio > div { gap: 12px; }
    .stRadio label { font-size: max(16px, 1.1rem) !important; }
    [data-testid="column"] > div { padding: 8px 0; }
    .mini-label {
        font-size: max(16px, 1rem);
        font-weight: 800;
        margin: 0 0 6px 2px;
        line-height: 1.25;
        opacity: 0.92;
    }

    /*
     * STEP2(정보입력) 2열 고정 — DOM display를 grid로 바꾸지 않고,
     * horizontal container의 "wrap"만 막아 1열로 무너지는 현상을 방지합니다.
     * (네이버 인앱 WebView에서 자주 발생)
     */
    .st-key-s2self_r1 [data-testid="stVerticalBlock"],
    .st-key-s2self_r2 [data-testid="stVerticalBlock"],
    .st-key-s2self_r3 [data-testid="stVerticalBlock"],
    .st-key-s2self_r4 [data-testid="stVerticalBlock"],
    .st-key-s2opp_r1 [data-testid="stVerticalBlock"],
    .st-key-s2opp_r2 [data-testid="stVerticalBlock"],
    .st-key-s2opp_r3 [data-testid="stVerticalBlock"],
    .st-key-s2opp_r4 [data-testid="stVerticalBlock"] {
        flex-wrap: nowrap !important;
        gap: 10px !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    /* Streamlit 버전/렌더 경로에 따라 horizontal row가 stHorizontalBlock으로 나오는 경우도 있어 함께 고정 */
    .st-key-s2self_r1 [data-testid="stHorizontalBlock"],
    .st-key-s2self_r2 [data-testid="stHorizontalBlock"],
    .st-key-s2self_r3 [data-testid="stHorizontalBlock"],
    .st-key-s2self_r4 [data-testid="stHorizontalBlock"],
    .st-key-s2opp_r1 [data-testid="stHorizontalBlock"],
    .st-key-s2opp_r2 [data-testid="stHorizontalBlock"],
    .st-key-s2opp_r3 [data-testid="stHorizontalBlock"],
    .st-key-s2opp_r4 [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
        gap: 10px !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    /* st.columns(2)로 그린 row도 nowrap 강제 */
    .st-key-s2self_r1 [data-testid="stHorizontalBlock"],
    .st-key-s2self_r2 [data-testid="stHorizontalBlock"],
    .st-key-s2self_r3 [data-testid="stHorizontalBlock"],
    .st-key-s2self_r4 [data-testid="stHorizontalBlock"],
    .st-key-s2opp_r1 [data-testid="stHorizontalBlock"],
    .st-key-s2opp_r2 [data-testid="stHorizontalBlock"],
    .st-key-s2opp_r3 [data-testid="stHorizontalBlock"],
    .st-key-s2opp_r4 [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important;
    }
    .st-key-s2self_r1 [data-testid="stVerticalBlock"] > div,
    .st-key-s2self_r2 [data-testid="stVerticalBlock"] > div,
    .st-key-s2self_r3 [data-testid="stVerticalBlock"] > div,
    .st-key-s2self_r4 [data-testid="stVerticalBlock"] > div,
    .st-key-s2opp_r1 [data-testid="stVerticalBlock"] > div,
    .st-key-s2opp_r2 [data-testid="stVerticalBlock"] > div,
    .st-key-s2opp_r3 [data-testid="stVerticalBlock"] > div,
    .st-key-s2opp_r4 [data-testid="stVerticalBlock"] > div {
        flex: 1 1 0 !important;
        min-width: 0 !important;
    }
    .st-key-s2self_r1 [data-testid="stHorizontalBlock"] > div,
    .st-key-s2self_r2 [data-testid="stHorizontalBlock"] > div,
    .st-key-s2self_r3 [data-testid="stHorizontalBlock"] > div,
    .st-key-s2self_r4 [data-testid="stHorizontalBlock"] > div,
    .st-key-s2opp_r1 [data-testid="stHorizontalBlock"] > div,
    .st-key-s2opp_r2 [data-testid="stHorizontalBlock"] > div,
    .st-key-s2opp_r3 [data-testid="stHorizontalBlock"] > div,
    .st-key-s2opp_r4 [data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0 !important;
        min-width: 0 !important;
    }
    /* (안정화) STEP2 2열 강제 grid 제거 — Streamlit 기본 레이아웃 사용 */

    /*
     * STEP2 네이버 모바일형: 연한 크림 배경의 입력 칸·큰 라운드·은은한 테두리
     * (본인/상대 세로 배치 — `step2_navertone_self` / `step2_navertone_opp` 컨테이너)
     */
    .st-key-step2_section_stack {
        display: flex !important;
        flex-direction: column !important;
        gap: 0.25rem !important;
        width: 100% !important;
    }
    .st-key-s2v3_stack {
        display: flex !important;
        flex-direction: column !important;
        gap: 0.25rem !important;
        width: 100% !important;
    }
    .st-key-in4_stack {
        display: flex !important;
        flex-direction: column !important;
        gap: 0.25rem !important;
        width: 100% !important;
    }
    .st-key-saju_router_step_mount:has(.st-key-in4_stack) [data-testid="stTabs"],
    .st-key-saju_router_step_mount:has(.st-key-s2v3_stack) [data-testid="stTabs"],
    .st-key-saju_router_step_mount:has(.st-key-step2_section_stack) [data-testid="stTabs"] {
        display: none !important;
    }
    .st-key-in4_self .stTextInput > div > div,
    .st-key-in4_self .stNumberInput > div > div,
    .st-key-in4_self [data-baseweb="select"] > div,
    .st-key-in4_opp .stTextInput > div > div,
    .st-key-in4_opp .stNumberInput > div > div,
    .st-key-in4_opp [data-baseweb="select"] > div,
    .st-key-s2v3_self .stTextInput > div > div,
    .st-key-s2v3_self .stNumberInput > div > div,
    .st-key-s2v3_self [data-baseweb="select"] > div,
    .st-key-s2v3_opp .stTextInput > div > div,
    .st-key-s2v3_opp .stNumberInput > div > div,
    .st-key-s2v3_opp [data-baseweb="select"] > div,
    /* STEP2: 연한 피치 칩(성함·년·월·일·연락처) — 테두리 없음 */
    .st-key-step2_navertone_self .stTextInput > div > div,
    .st-key-step2_navertone_opp .stTextInput > div > div,
    .st-key-step2_save_actions .stTextInput > div > div,
    .st-key-step2_navertone_self .stNumberInput > div > div,
    .st-key-step2_navertone_self .stNumberInput [data-testid="stNumberInputContainer"],
    .st-key-step2_navertone_opp .stNumberInput > div > div,
    .st-key-step2_navertone_opp .stNumberInput [data-testid="stNumberInputContainer"],
    .st-key-step2_navertone_self .stTextInput > div > div:focus-within,
    .st-key-step2_navertone_opp .stTextInput > div > div:focus-within,
    .st-key-step2_save_actions .stTextInput > div > div:focus-within,
    .st-key-step2_navertone_self .stNumberInput [data-testid="stNumberInputContainer"].focused,
    .st-key-step2_navertone_opp .stNumberInput [data-testid="stNumberInputContainer"].focused,
    .st-key-step2_navertone_self .stNumberInput [data-testid="stNumberInputContainer"]:focus-within,
    .st-key-step2_navertone_opp .stNumberInput [data-testid="stNumberInputContainer"]:focus-within {
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        border-radius: var(--saju-soft-radius) !important;
    }
    .st-key-step2_navertone_self .stTextInput > div > div:focus-within,
    .st-key-step2_navertone_opp .stTextInput > div > div:focus-within,
    .st-key-step2_save_actions .stTextInput > div > div:focus-within {
        background: light-dark(var(--saju-soft-fill-hover), var(--saju-soft-fill-dark-hover)) !important;
    }
    .st-key-step2_navertone_self [data-baseweb="select"] > div,
    .st-key-step2_navertone_opp [data-baseweb="select"] > div {
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: var(--saju-soft-radius) !important;
    }
    /* STEP2 정보입력: 3행×2열 — 성함|성별 · 생년월일|달력 · 시간|연락처 */
    .st-key-step2_self_row1_name_gender [data-testid="stHorizontalBlock"],
    .st-key-step2_self_row2_bdate_cal [data-testid="stHorizontalBlock"],
    .st-key-step2_self_row3_time_contact [data-testid="stHorizontalBlock"],
    .st-key-step2_opp_row1_name_gender [data-testid="stHorizontalBlock"],
    .st-key-step2_opp_row2_bdate_cal [data-testid="stHorizontalBlock"],
    .st-key-step2_opp_row3_time_contact [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 10px !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    .st-key-step2_self_row1_name_gender [data-testid="stHorizontalBlock"] > div,
    .st-key-step2_self_row2_bdate_cal [data-testid="stHorizontalBlock"] > div,
    .st-key-step2_self_row3_time_contact [data-testid="stHorizontalBlock"] > div,
    .st-key-step2_opp_row1_name_gender [data-testid="stHorizontalBlock"] > div,
    .st-key-step2_opp_row2_bdate_cal [data-testid="stHorizontalBlock"] > div,
    .st-key-step2_opp_row3_time_contact [data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0 !important;
        min-width: 0 !important;
        max-width: 50% !important;
        width: 50% !important;
        box-sizing: border-box !important;
    }
    @media (min-width: 769px) {
        .st-key-step2_self_row1_name_gender [data-testid="stHorizontalBlock"],
        .st-key-step2_self_row2_bdate_cal [data-testid="stHorizontalBlock"],
        .st-key-step2_self_row3_time_contact [data-testid="stHorizontalBlock"],
        .st-key-step2_opp_row1_name_gender [data-testid="stHorizontalBlock"],
        .st-key-step2_opp_row2_bdate_cal [data-testid="stHorizontalBlock"],
        .st-key-step2_opp_row3_time_contact [data-testid="stHorizontalBlock"] {
            gap: 12px !important;
        }
        .st-key-step2_navertone_self,
        .st-key-step2_navertone_opp {
            max-width: min(100%, 42rem) !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }
    }
    .st-key-step2_self_row1_name_gender,
    .st-key-step2_self_row2_bdate_cal,
    .st-key-step2_self_row3_time_contact,
    .st-key-step2_opp_row1_name_gender,
    .st-key-step2_opp_row2_bdate_cal,
    .st-key-step2_opp_row3_time_contact {
        margin-bottom: 0.35rem !important;
    }
    .st-key-step2_self_row1_name_gender [data-testid="column"],
    .st-key-step2_self_row2_bdate_cal [data-testid="column"],
    .st-key-step2_self_row3_time_contact [data-testid="column"],
    .st-key-step2_opp_row1_name_gender [data-testid="column"],
    .st-key-step2_opp_row2_bdate_cal [data-testid="column"],
    .st-key-step2_opp_row3_time_contact [data-testid="column"] {
        min-width: 0 !important;
    }
    /* STEP2 모바일: 2열 가로 유지 (wrap으로 1열 무너짐 방지) */
    @media (max-width: 768px) {
        .st-key-step2_self_row1_name_gender [data-testid="stHorizontalBlock"],
        .st-key-step2_self_row2_bdate_cal [data-testid="stHorizontalBlock"],
        .st-key-step2_self_row3_time_contact [data-testid="stHorizontalBlock"],
        .st-key-step2_opp_row1_name_gender [data-testid="stHorizontalBlock"],
        .st-key-step2_opp_row2_bdate_cal [data-testid="stHorizontalBlock"],
        .st-key-step2_opp_row3_time_contact [data-testid="stHorizontalBlock"] {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            gap: 8px !important;
            width: 100% !important;
            box-sizing: border-box !important;
        }
        .st-key-step2_self_row1_name_gender [data-testid="stHorizontalBlock"] > div,
        .st-key-step2_self_row2_bdate_cal [data-testid="stHorizontalBlock"] > div,
        .st-key-step2_self_row3_time_contact [data-testid="stHorizontalBlock"] > div,
        .st-key-step2_opp_row1_name_gender [data-testid="stHorizontalBlock"] > div,
        .st-key-step2_opp_row2_bdate_cal [data-testid="stHorizontalBlock"] > div,
        .st-key-step2_opp_row3_time_contact [data-testid="stHorizontalBlock"] > div {
            flex: 1 1 0 !important;
            min-width: 0 !important;
            max-width: 50% !important;
            width: 50% !important;
            box-sizing: border-box !important;
        }
        .st-key-step2_navertone_self .stDateInput,
        .st-key-step2_navertone_opp .stDateInput {
            width: 100% !important;
        }
        .st-key-step2_navertone_self .stDateInput [data-baseweb="input"] input,
        .st-key-step2_navertone_opp .stDateInput [data-baseweb="input"] input {
            font-size: max(14px, 0.9rem) !important;
            min-height: 2.85rem !important;
            padding-left: 0.35rem !important;
            padding-right: 0.35rem !important;
        }
        .st-key-step2_navertone_self .st-key-step2_u_time_wrap [data-baseweb="select"] > div,
        .st-key-step2_navertone_opp .st-key-step2_p_time_wrap [data-baseweb="select"] > div,
        .st-key-step2_navertone_self .st-key-step2_u_time_wrap .stSelectbox > div > div,
        .st-key-step2_navertone_opp .st-key-step2_p_time_wrap .stSelectbox > div > div {
            min-height: 2.85rem !important;
        }
    }
    /* STEP2 생년월일: 달력 없이 텍스트 직접 입력 (YYYY/MM/DD) */
    .st-key-step2_u_bdate_wrap .stTextInput,
    .st-key-step2_p_bdate_wrap .stTextInput {
        width: 100% !important;
    }
    .st-key-step2_u_bdate_wrap [data-testid="stWidgetLabel"] label,
    .st-key-step2_p_bdate_wrap [data-testid="stWidgetLabel"] label {
        font-weight: 700 !important;
        font-size: max(15px, 0.95rem) !important;
    }
    .st-key-step2_u_bdate_wrap .stTextInput > div > div,
    .st-key-step2_p_bdate_wrap .stTextInput > div > div,
    .st-key-step2_navertone_self .st-key-step2_u_bdate_wrap .stTextInput > div > div,
    .st-key-step2_navertone_opp .st-key-step2_p_bdate_wrap .stTextInput > div > div {
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: var(--saju-soft-radius) !important;
        min-height: 2.85rem !important;
        width: 100% !important;
    }
    .st-key-step2_u_bdate_wrap .stTextInput input,
    .st-key-step2_p_bdate_wrap .stTextInput input,
    .st-key-step2_navertone_self .st-key-step2_u_bdate_wrap .stTextInput input,
    .st-key-step2_navertone_opp .st-key-step2_p_bdate_wrap .stTextInput input {
        font-size: max(15px, 0.95rem) !important;
        font-weight: 650 !important;
        text-align: left !important;
        min-height: 2.85rem !important;
        padding-left: 0.55rem !important;
        padding-right: 0.55rem !important;
        letter-spacing: 0.02em !important;
        font-variant-numeric: tabular-nums !important;
    }
    .st-key-step2_u_bdate_wrap [data-baseweb="calendar"],
    .st-key-step2_p_bdate_wrap [data-baseweb="calendar"],
    .st-key-step2_u_bdate_wrap .stDateInput,
    .st-key-step2_p_bdate_wrap .stDateInput {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        overflow: hidden !important;
        pointer-events: none !important;
    }
    /* 예전 년·월·일 3칸 레이아웃 잔여물 숨김 */
    .st-key-step2_u_bdate_wrap .stNumberInput,
    .st-key-step2_p_bdate_wrap .stNumberInput {
        display: none !important;
    }
    /* STEP2 태어난 시간: 생년월일 칩과 동일 연한 피치 */
    .st-key-step2_u_time_wrap .stSelectbox,
    .st-key-step2_p_time_wrap .stSelectbox {
        width: 100% !important;
    }
    .st-key-step2_u_time_wrap [data-baseweb="select"],
    .st-key-step2_p_time_wrap [data-baseweb="select"],
    .st-key-step2_u_time_wrap [role="combobox"],
    .st-key-step2_p_time_wrap [role="combobox"],
    .st-key-step2_u_time_wrap [data-baseweb="popover"],
    .st-key-step2_p_time_wrap [data-baseweb="popover"],
    .st-key-step2_u_time_wrap [data-baseweb="select-dropdown"],
    .st-key-step2_p_time_wrap [data-baseweb="select-dropdown"],
    .st-key-step2_u_time_wrap [role="option"],
    .st-key-step2_p_time_wrap [role="option"] {
        pointer-events: auto !important;
        touch-action: manipulation !important;
    }
    /* ── 셀렉트 드롭다운 z-index 보강 (모바일 '태어난 시간 → 모름' 고정 버그) ──
       모바일 좁은 화면에서 BaseWeb 셀렉트 드롭다운이 하단 '기능 바로가기'
       크롬(summary z-index:6)과 같은 쌓임 맥락에서 그 아래로 깔려, 목록 하단
       옵션(유·술·해 등 저녁 시진)을 탭하면 하단 버튼이 탭을 가로채 선택이
       커밋되지 않고 '모름'으로 남았다. 상단(자·축 등)만 정상 동작.
       드롭다운 레이어/팝오버를 항상 최상단으로 올려 전 옵션을 탭 가능하게 한다. */
    [data-baseweb="layer"]:has([role="listbox"]),
    [data-baseweb="layer"]:has([role="option"]),
    div[data-baseweb="popover"]:has([role="listbox"]),
    div[data-baseweb="popover"]:has([role="option"]),
    div[data-baseweb="popover"]:has([data-testid="stSelectboxVirtualDropdown"]) {
        z-index: 2147483600 !important;
    }
    @media (max-width: 768px) {
        .st-key-step2_u_time_wrap [data-baseweb="popover"],
        .st-key-step2_p_time_wrap [data-baseweb="popover"],
        .st-key-step2_u_time_wrap [data-baseweb="select-dropdown"],
        .st-key-step2_p_time_wrap [data-baseweb="select-dropdown"] {
            min-width: min(100vw - 1.5rem, 22rem) !important;
            max-width: min(100vw - 1rem, 24rem) !important;
        }
        .st-key-step2_u_time_wrap [role="option"],
        .st-key-step2_p_time_wrap [role="option"],
        .st-key-step2_u_time_wrap [data-baseweb="option"],
        .st-key-step2_p_time_wrap [data-baseweb="option"] {
            white-space: nowrap !important;
            font-size: max(14px, 0.88rem) !important;
            padding-left: 0.65rem !important;
            padding-right: 0.65rem !important;
        }
    }
    .st-key-step2_u_time_wrap [data-testid="stWidgetLabel"] label,
    .st-key-step2_p_time_wrap [data-testid="stWidgetLabel"] label,
    .st-key-step2_u_time_wrap .stSelectbox label,
    .st-key-step2_p_time_wrap .stSelectbox label {
        font-weight: 700 !important;
        font-size: max(15px, 0.95rem) !important;
    }
    .st-key-step2_navertone_self .st-key-step2_u_time_wrap .stSelectbox > div > div,
    .st-key-step2_navertone_opp .st-key-step2_p_time_wrap .stSelectbox > div > div,
    .st-key-step2_navertone_self .st-key-step2_u_time_wrap [data-baseweb="select"] > div,
    .st-key-step2_navertone_opp .st-key-step2_p_time_wrap [data-baseweb="select"] > div,
    .st-key-step2_navertone_self .st-key-step2_u_time_wrap .stSelectbox [data-baseweb="select"],
    .st-key-step2_navertone_opp .st-key-step2_p_time_wrap .stSelectbox [data-baseweb="select"] {
        width: 100% !important;
        min-height: 2.85rem !important;
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: var(--saju-soft-radius) !important;
        padding-left: 0.55rem !important;
        padding-right: 0.55rem !important;
        display: flex !important;
        align-items: center !important;
        box-sizing: border-box !important;
    }
    .st-key-step2_navertone_self .st-key-step2_u_time_wrap [data-baseweb="select"] > div > div,
    .st-key-step2_navertone_opp .st-key-step2_p_time_wrap [data-baseweb="select"] > div > div,
    .st-key-step2_navertone_self .st-key-step2_u_time_wrap [data-baseweb="select"] span,
    .st-key-step2_navertone_opp .st-key-step2_p_time_wrap [data-baseweb="select"] span,
    .st-key-step2_navertone_self .st-key-step2_u_time_wrap [data-baseweb="select"] input,
    .st-key-step2_navertone_opp .st-key-step2_p_time_wrap [data-baseweb="select"] input {
        font-size: max(14px, 0.9rem) !important;
        font-weight: 650 !important;
        letter-spacing: -0.02em !important;
        color: light-dark(var(--saju-text-readable), rgba(235, 228, 210, 0.94)) !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    .st-key-step2_navertone_self .st-key-step2_u_time_wrap [data-baseweb="select"] > div > div,
    .st-key-step2_navertone_opp .st-key-step2_p_time_wrap [data-baseweb="select"] > div > div {
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        white-space: nowrap !important;
        flex: 1 1 auto !important;
        min-width: 0 !important;
    }
    .st-key-step2_navertone_self .st-key-step2_u_time_wrap [data-baseweb="select"]:focus-within > div,
    .st-key-step2_navertone_opp .st-key-step2_p_time_wrap [data-baseweb="select"]:focus-within > div {
        background: light-dark(var(--saju-soft-fill-hover), var(--saju-soft-fill-dark-hover)) !important;
        outline: none !important;
        box-shadow: none !important;
    }
    .st-key-step2_navertone_self .stTextInput [data-baseweb="input"],
    .st-key-step2_navertone_opp .stTextInput [data-baseweb="input"],
    .st-key-step2_navertone_self .stTextInput [data-baseweb="input"] > div,
    .st-key-step2_navertone_opp .stTextInput [data-baseweb="input"] > div,
    .st-key-step2_save_actions .stTextInput [data-baseweb="input"],
    .st-key-step2_save_actions .stTextInput [data-baseweb="input"] > div,
    .st-key-step2_navertone_self .stTextInput [data-baseweb="base-input"],
    .st-key-step2_navertone_opp .stTextInput [data-baseweb="base-input"] {
        border: 0 !important;
        box-shadow: none !important;
        outline: none !important;
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        border-radius: var(--saju-soft-radius) !important;
    }
    .saju-privacy-disclosure {
        margin: 0.4rem 0 0.9rem;
        padding: 0.9rem 1rem;
        border-radius: 16px;
        border: 1px solid light-dark(rgba(212, 175, 55, 0.34), rgba(212, 175, 55, 0.24));
        background: light-dark(rgba(255, 250, 240, 0.86), rgba(37, 32, 24, 0.74));
        color: light-dark(#2f2718, rgba(245, 239, 226, 0.94));
        line-height: 1.64;
        font-size: clamp(0.86rem, 2.8vw, 0.98rem);
    }
    .saju-privacy-disclosure b {
        color: light-dark(#6d4f0f, #f4d179);
        font-size: 1.04em;
    }
    .st-key-step2_navertone_self .stTextInput > div > div > input,
    .st-key-step2_navertone_self .stTextInput input,
    .st-key-step2_navertone_self .stNumberInput input,
    .st-key-step2_navertone_opp .stTextInput > div > div > input,
    .st-key-step2_navertone_opp .stTextInput input,
    .st-key-step2_navertone_opp .stNumberInput input,
    .st-key-step2_save_actions .stTextInput > div > div > input,
    .st-key-step2_save_actions .stTextInput input {
        border-radius: var(--saju-soft-radius) !important;
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        border: 0 !important;
        box-shadow: none !important;
        font-size: clamp(13px, 3.2vw, 15px) !important;
        line-height: 1.18 !important;
        letter-spacing: -0.035em !important;
        color: light-dark(var(--saju-text-readable), rgba(235, 228, 210, 0.94)) !important;
        pointer-events: auto !important;
        position: relative !important;
        z-index: 2 !important;
        cursor: text !important;
    }
    /* BaseWeb 래퍼가 클릭·캐럿 이동을 가로채지 않도록 */
    .st-key-step2_navertone_self .stTextInput [data-baseweb="input"],
    .st-key-step2_navertone_self .stTextInput [data-baseweb="input"] > div,
    .st-key-step2_navertone_opp .stTextInput [data-baseweb="input"],
    .st-key-step2_navertone_opp .stTextInput [data-baseweb="input"] > div,
    .st-key-step2_save_actions .stTextInput [data-baseweb="input"],
    .st-key-step2_save_actions .stTextInput [data-baseweb="input"] > div {
        pointer-events: none !important;
    }
    .st-key-step2_navertone_self .stNumberInput input,
    .st-key-step2_navertone_opp .stNumberInput input {
        pointer-events: auto !important;
        position: relative !important;
        z-index: 2 !important;
        cursor: text !important;
    }
    .st-key-step2_navertone_self .stTextInput input:-webkit-autofill,
    .st-key-step2_navertone_self .stTextInput input:-webkit-autofill:hover,
    .st-key-step2_navertone_self .stTextInput input:-webkit-autofill:focus,
    .st-key-step2_navertone_opp .stTextInput input:-webkit-autofill,
    .st-key-step2_navertone_opp .stTextInput input:-webkit-autofill:hover,
    .st-key-step2_navertone_opp .stTextInput input:-webkit-autofill:focus,
    .st-key-step2_save_actions .stTextInput input:-webkit-autofill,
    .st-key-step2_save_actions .stTextInput input:-webkit-autofill:hover,
    .st-key-step2_save_actions .stTextInput input:-webkit-autofill:focus {
        -webkit-text-fill-color: light-dark(var(--saju-text-readable), rgba(235, 228, 210, 0.94)) !important;
        -webkit-box-shadow: 0 0 0 1000px #fff5ee inset !important;
        box-shadow: 0 0 0 1000px #fff5ee inset !important;
        transition: background-color 99999s ease-out 0s !important;
    }
    .st-key-in4_self .stTextInput > div > div > input,
    .st-key-in4_self .stNumberInput input,
    .st-key-in4_opp .stTextInput > div > div > input,
    .st-key-in4_opp .stNumberInput input,
    .st-key-s2v3_self .stTextInput > div > div > input,
    .st-key-s2v3_self .stNumberInput input,
    .st-key-s2v3_opp .stTextInput > div > div > input,
    .st-key-s2v3_opp .stNumberInput input {
        border-radius: 14px !important;
        background: transparent !important;
        border: 0 !important;
        font-size: clamp(13px, 3.2vw, 15px) !important;
        line-height: 1.18 !important;
        letter-spacing: -0.035em !important;
    }
    .st-key-step2_navertone_self .stTextInput input:focus,
    .st-key-step2_navertone_self .stTextInput input:focus-visible,
    .st-key-step2_navertone_opp .stTextInput input:focus,
    .st-key-step2_navertone_opp .stTextInput input:focus-visible,
    .st-key-step2_save_actions .stTextInput input:focus,
    .st-key-step2_save_actions .stTextInput input:focus-visible,
    .st-key-step2_navertone_self .stNumberInput input:focus,
    .st-key-step2_navertone_self .stNumberInput input:focus-visible,
    .st-key-step2_navertone_opp .stNumberInput input:focus,
    .st-key-step2_navertone_opp .stNumberInput input:focus-visible {
        outline: none !important;
        outline-offset: 0 !important;
        box-shadow: none !important;
        border: 0 !important;
    }
    .st-key-step2_navertone_self .stNumberInput button,
    .st-key-step2_navertone_opp .stNumberInput button {
        border-radius: 6px !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: light-dark(#6d5a3a, #c9b896) !important;
        font-size: clamp(13px, 3.2vw, 15px) !important;
        font-weight: 700 !important;
        min-width: 1.75rem !important;
    }
    /* STEP2: Streamlit "Press Enter to apply" → 한글 안내(엔터를 눌러 신청하세요) 숨김 */
    .st-key-step2_navertone_self [data-testid="InputInstructions"],
    .st-key-step2_navertone_opp [data-testid="InputInstructions"],
    .st-key-step2_save_actions [data-testid="InputInstructions"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }
    /* STEP2 라디오: 네이버 모바일처럼 세로 나열 (가로로 붙어 버튼처럼 보이는 현상 방지) */
    .st-key-step2_navertone_self .stRadio > div,
    .st-key-step2_navertone_opp .stRadio > div {
        flex-direction: column !important;
        align-items: flex-start !important;
        flex-wrap: nowrap !important;
        gap: 8px !important;
    }
    .st-key-step2_navertone_self .stRadio [role="radiogroup"],
    .st-key-step2_navertone_opp .stRadio [role="radiogroup"] {
        flex-direction: column !important;
        align-items: flex-start !important;
        gap: 8px !important;
    }
    .st-key-step2_navertone_self .stRadio label,
    .st-key-step2_navertone_opp .stRadio label {
        padding: 0.15rem 0 !important;
        width: 100%;
        max-width: 100%;
        box-sizing: border-box;
    }

    .st-key-step2_navertone_self [data-testid="stExpander"] details,
    .st-key-step2_navertone_opp [data-testid="stExpander"] details {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 0 !important;
    }
    .st-key-step2_navertone_self [data-testid="stExpander"] summary,
    .st-key-step2_navertone_opp [data-testid="stExpander"] summary {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 0 !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
        padding: 0 !important;
    }
    .st-key-step2_navertone_self [data-testid="stExpander"] summary p,
    .st-key-step2_navertone_opp [data-testid="stExpander"] summary p {
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: clip !important;
        font-size: clamp(13px, 3.2vw, 15px) !important;
        line-height: 1.18 !important;
        letter-spacing: -0.035em !important;
    }
    .st-key-step2_navertone_self [data-testid="stExpander"] [data-baseweb="select"] > div,
    .st-key-step2_navertone_opp [data-testid="stExpander"] [data-baseweb="select"] > div,
    .st-key-step2_navertone_self [data-testid="stExpander"] .stSelectbox > div > div,
    .st-key-step2_navertone_opp [data-testid="stExpander"] .stSelectbox > div > div {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 0 !important;
    }

    /* ===== STEP3 사주 네 칸 ===== */
    .saju-four-wrap { width: 100%; margin: 6px 0 14px 0; box-sizing: border-box; }
    .saju-four-row {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 6px;
        text-align: center;
        align-items: start;
    }
    .saju-four-row .saju-lab {
        font-weight: 700;
        font-size: max(16px, 1rem);
        margin: 0 0 6px 0;
        display: block;
        opacity: 0.92;
    }
    .saju-four-row .saju-gj {
        font-size: clamp(1.35rem, 4.8vw, 2.35rem);
        font-weight: 800;
        font-family: "Playfair Display", "Noto Serif KR", "Apple SD Gothic Neo", "Malgun Gothic",
            Georgia, "Microsoft YaHei", serif;
        letter-spacing: 2px;
        line-height: 1.2;
        padding: 10px 2px;
        border-radius: 12px;
        background: #f8fafc;
        background: light-dark(#f4f1ea, rgba(26, 26, 46, 0.85));
        border: 1px solid rgba(0, 0, 0, 0.08);
        border: 1px solid light-dark(rgba(0, 0, 0, 0.08), rgba(255, 255, 255, 0.12));
    }

    /* STEP3 메인 사주 차트(iframe): 내부 스크롤 없이 전체 높이 표시 */
    .st-key-step3_gapja_chart,
    .st-key-step3_gapja_chart [data-testid="stVerticalBlock"],
    .st-key-step3_gapja_chart [data-testid="stCustomComponentV1"],
    .st-key-step3_gapja_chart [data-testid="stCustomComponentV1"] iframe,
    .st-key-step3_gapja_chart iframe {
        width: 100% !important;
        max-width: 100% !important;
        min-height: 620px !important;
        max-height: none !important;
        height: auto !important;
        overflow: visible !important;
    }
    @media (max-width: 520px) {
        .st-key-step3_gapja_chart [data-testid="stCustomComponentV1"] iframe,
        .st-key-step3_gapja_chart iframe {
            min-height: 640px !important;
        }
    }

    /* STEP3 사주 원국(구 2×2 카드 — 미사용, CSS 유지) */
    .st-key-step3_gapja_kingdom .saju-wonguk-wrap {
        width: 100%;
        max-width: 100%;
        box-sizing: border-box;
    }
    .st-key-step3_gapja_kingdom .saju-wonguk-labels-row {
        display: grid !important;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.45rem 0.55rem;
        margin-bottom: 0.35rem;
    }
    .st-key-step3_gapja_kingdom .saju-wonguk-label {
        text-align: center;
        font-size: clamp(12px, 3.1vw, 0.9rem);
        font-weight: 800;
        letter-spacing: 0.08em;
        color: light-dark(#5c4510, #e8dcc0);
        padding: 0.2rem 0.1rem;
    }
    .st-key-step3_gapja_kingdom .saju-wonguk-label--day {
        color: light-dark(#4c1d95, #f5e6ff);
        text-shadow: 0 1px 0 light-dark(rgba(255,255,255,0.55), rgba(0,0,0,0.35));
    }
    .st-key-step3_gapja_kingdom .saju-wonguk-card {
        box-sizing: border-box;
        text-align: center;
        padding: 0.85rem 0.65rem 1rem;
        margin: 0 0 0.65rem 0;
        border-radius: 14px;
        border: 1px solid light-dark(rgba(212, 175, 55, 0.42), rgba(212, 175, 55, 0.28));
        background: light-dark(
            linear-gradient(165deg, #faf7f0 0%, #efe8dc 100%),
            linear-gradient(165deg, rgba(28, 28, 42, 0.96), rgba(22, 33, 62, 0.94))
        );
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.07);
    }
    .st-key-step3_gapja_kingdom .saju-wonguk-card--day {
        border-width: 2px;
        border-color: light-dark(#7c3aed, #c4b5fd);
        background: light-dark(
            linear-gradient(145deg, #f5f0ff 0%, #e9d5ff 38%, #ddd6fe 72%, #c4b5fd 100%),
            linear-gradient(145deg, rgba(76, 29, 149, 0.92) 0%, rgba(91, 33, 182, 0.9) 45%, rgba(30, 27, 75, 0.95) 100%)
        );
        box-shadow:
            0 1px 0 light-dark(rgba(255,255,255,0.85), rgba(255,255,255,0.12)) inset,
            0 -2px 0 light-dark(rgba(124,58,237,0.25), rgba(0,0,0,0.45)) inset,
            0 10px 26px light-dark(rgba(124, 58, 237, 0.28), rgba(0, 0, 0, 0.45)),
            0 0 0 1px light-dark(rgba(124, 58, 237, 0.35), rgba(196, 181, 253, 0.35));
        transform: translateY(-2px);
    }
    .st-key-step3_gapja_kingdom .saju-wonguk-pillar-inner--day {
        padding: 0.35rem 0.2rem 0.5rem;
        border-radius: 12px;
        background: light-dark(
            linear-gradient(180deg, rgba(255,255,255,0.72) 0%, rgba(233,213,255,0.35) 100%),
            linear-gradient(180deg, rgba(255,255,255,0.14) 0%, rgba(0,0,0,0.22) 100%)
        );
        box-shadow:
            0 2px 6px light-dark(rgba(124,58,237,0.22), rgba(0,0,0,0.35)),
            0 1px 0 light-dark(rgba(255,255,255,0.9), rgba(255,255,255,0.18)) inset;
    }
    .st-key-step3_gapja_kingdom .saju-wonguk-meta {
        font-size: max(13px, 0.86rem);
        font-weight: 800;
        color: light-dark(#5c4510, #f0e6c8);
        margin-bottom: 0.2rem;
    }
    .st-key-step3_gapja_kingdom .saju-wonguk-meta--day {
        color: light-dark(#6b4e12, #ffe9b3);
    }
    .st-key-step3_gapja_kingdom .saju-wonguk-sub {
        font-size: max(11px, 0.74rem);
        color: light-dark(rgba(42, 38, 32, 0.68), rgba(229, 229, 235, 0.72));
        margin-bottom: 0.55rem;
        line-height: 1.38;
    }
    .st-key-step3_gapja_kingdom .saju-wonguk-pillar,
    .st-key-step3_gapja_kingdom .saju-wonguk-pillar-unknown {
        font-family: "Noto Serif SC", "Noto Serif TC", "Noto Serif JP", "Noto Serif KR",
            "Source Han Serif KR", "Apple SD Gothic Neo", "Malgun Gothic", serif;
        font-weight: 800;
        letter-spacing: 0.12em;
        line-height: 1.12;
        margin: 0 auto;
        color: light-dark(#120f0c, #faf3e0);
    }
    .st-key-step3_gapja_kingdom .saju-wonguk-stem {
        display: block;
        font-size: clamp(1.95rem, 5.5vw, 2.55rem);
        color: light-dark(#2a1810, #fff8ec);
    }
    .st-key-step3_gapja_kingdom .saju-wonguk-branch {
        display: block;
        font-size: clamp(1.95rem, 5.5vw, 2.55rem);
        margin-top: 0.06rem;
        color: light-dark(#4a3018, #f5e0b8);
    }
    .st-key-step3_gapja_kingdom .saju-wonguk-pillar--day .saju-wonguk-stem,
    .st-key-step3_gapja_kingdom .saju-wonguk-pillar--day .saju-wonguk-branch {
        font-size: clamp(2.12rem, 6vw, 2.9rem);
        background: linear-gradient(
            180deg,
            light-dark(#5b21b6, #faf5ff) 0%,
            light-dark(#7c3aed, #e9d5ff) 45%,
            light-dark(#4c1d95, #c4b5fd) 100%
        );
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        filter: drop-shadow(0 2px 2px light-dark(rgba(91,33,182,0.25), rgba(0,0,0,0.45)));
    }
    .st-key-step3_gapja_kingdom .saju-wonguk-pillar-unknown {
        letter-spacing: 0;
        font-size: max(14px, 0.92rem);
        color: light-dark(#92400e, #fcd34d);
        font-weight: 700;
    }

    /* 사주 원국: 모바일·네이버 인앱 등에서 Streamlit column stack을 우회해 2×2 고정 */
    .st-key-step3_gapja_kingdom .saju-wonguk-grid2 {
        display: grid !important;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.45rem 0.55rem;
        width: 100%;
        max-width: 100%;
        box-sizing: border-box;
        align-items: stretch;
    }
    .st-key-step3_gapja_kingdom .saju-wonguk-grid2 .saju-wonguk-card {
        margin-bottom: 0;
        min-width: 0;
    }
    .st-key-step3_gapja_kingdom .saju-wonguk-grid2 .saju-wonguk-meta {
        font-size: clamp(11px, 2.9vw, 0.86rem);
    }
    .st-key-step3_gapja_kingdom .saju-wonguk-grid2 .saju-wonguk-sub {
        font-size: clamp(10px, 2.6vw, 0.74rem);
    }
    .st-key-step3_gapja_kingdom .saju-wonguk-grid2 .saju-wonguk-stem,
    .st-key-step3_gapja_kingdom .saju-wonguk-grid2 .saju-wonguk-branch {
        font-size: clamp(1.35rem, 5.2vw, 2.55rem);
    }
    .st-key-step3_gapja_kingdom .saju-wonguk-grid2 .saju-wonguk-pillar--day .saju-wonguk-stem,
    .st-key-step3_gapja_kingdom .saju-wonguk-grid2 .saju-wonguk-pillar--day .saju-wonguk-branch {
        font-size: clamp(1.45rem, 5.6vw, 2.9rem);
    }

    /* 인생 핵심 운세 제목: 이모지 없이 한 줄(좁은 인앱 대응) */
    .st-key-step3_life_core [data-testid="stExpander"] {
        margin: 0.2rem 0 !important;
        border-radius: 12px !important;
    }
    .st-key-step3_life_core [data-testid="stExpander"] details {
        border: 1px solid light-dark(rgba(212, 175, 55, 0.28), rgba(212, 175, 55, 0.22)) !important;
        border-radius: 12px !important;
        background: light-dark(rgba(255, 252, 245, 0.92), rgba(22, 28, 48, 0.88)) !important;
    }
    .st-key-step3_life_core [data-testid="stExpander"] summary {
        font-weight: 700 !important;
        font-size: clamp(0.92rem, 3.6vw, 1.05rem) !important;
        padding: 0.45rem 0.55rem !important;
    }
    .st-key-step3_life_core [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p {
        font-size: max(15px, 0.94rem) !important;
        line-height: 1.55 !important;
        margin: 0.15rem 0 !important;
    }
    .st-key-step3_life_core .saju-step3-life-core-h {
        font-weight: 800;
        font-size: clamp(11px, 3.35vw, 1.22rem);
        letter-spacing: -0.03em;
        margin: 0 0 0.45rem 0;
        line-height: 1.2;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        color: light-dark(#0f172a, #f1f5f9);
    }

    /* 인생 핵심 운세: 2×2(재물·혼인·커리어·원국 체질 힌트). 전역 .saju-card margin 제거 */
    .saju-life-core-grid2 .saju-life-core-score {
        color: light-dark(#0f172a, #f1f5f9) !important;
    }
    .saju-life-core-grid2 .saju-life-core-desc,
    .saju-life-core-grid2 .saju-life-core-health-tip {
        color: light-dark(#334155, #e2e8f0) !important;
        font-size: clamp(0.68rem, 2.8vw, 0.82rem);
        line-height: 1.45;
        display: block;
        margin-top: 4px;
    }
    .saju-life-core-grid2 .saju-life-core-health-note {
        color: light-dark(#64748b, #94a3b8) !important;
        font-size: clamp(0.56rem, 2.35vw, 0.72rem);
    }
    .st-key-step3_life_core .saju-life-core-grid2 {
        display: grid !important;
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        grid-auto-flow: row;
        gap: 0.45rem 0.55rem;
        width: 100%;
        max-width: 100%;
        box-sizing: border-box;
        align-items: stretch;
    }
    .st-key-step3_life_core .saju-life-core-grid2 .saju-card {
        margin: 0 !important;
        width: 100%;
        max-width: 100%;
    }
    .st-key-step3_life_core .saju-life-core-cell {
        min-width: 0;
        box-sizing: border-box;
        padding: 0.55rem 0.45rem 0.65rem !important;
    }
    .st-key-step3_life_core .saju-life-core-cell--health .saju-life-core-ico {
        font-size: clamp(1.45rem, 6.2vw, 2.4rem);
    }
    .st-key-step3_life_core .saju-life-core-health-tip {
        color: #cbd5e1;
        font-size: clamp(0.62rem, 2.65vw, 0.82rem);
        line-height: 1.38;
        margin: 6px 0 4px 0;
        text-align: center;
    }
    .st-key-step3_life_core .saju-life-core-health-note {
        color: #94a3b8;
        font-size: clamp(0.56rem, 2.35vw, 0.72rem);
        line-height: 1.35;
        display: block;
        margin-top: 2px;
    }
    .st-key-step3_life_core .saju-life-core-ico {
        font-size: clamp(1.65rem, 7vw, 2.8rem);
        margin: 4px 0 6px 0;
        line-height: 1;
    }
    .st-key-step3_life_core .saju-life-core-score {
        font-size: clamp(1.05rem, 4.2vw, 1.6rem);
        font-weight: 700;
        margin: 6px 0;
    }
    .st-key-step3_life_core .saju-life-core-desc,
    .st-key-step3_life_core .saju-life-core-health-tip {
        color: light-dark(#334155, #e2e8f0) !important;
        font-size: clamp(0.68rem, 2.8vw, 0.82rem);
        line-height: 1.45;
        display: block;
        margin-top: 4px;
    }
    .st-key-step3_life_core .saju-card {
        color: light-dark(#334155, #e2e8f0);
    }
    /* STEP3 통합 브리핑 — iframe이 카드 안에서 꽉 차게 */
    .st-key-step3_integrated_briefing [data-testid="stCustomComponentV1"],
    .st-key-step3_integrated_briefing iframe {
        width: 100% !important;
        max-width: 100% !important;
        border: none !important;
        border-radius: 12px;
        min-height: 480px;
    }
    .saju-step3-section-rule {
        height: 1px;
        margin: 0.65rem 0 0.5rem;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(212, 175, 55, 0.45),
            transparent
        );
    }
    /* STEP3: 인생 핵심 운세 ↔ PDF 사이 — 빈 iframe·미디어 미리보기(파이썬 로고) 제거 */
    .st-key-step3_trailing_actions [data-testid="stCustomComponentV1"],
    .st-key-step3_trailing_actions [data-testid="stCustomComponentV1"] iframe,
    .st-key-step3_trailing_actions iframe,
    .st-key-step3_trailing_actions [data-testid="stImage"],
    .st-key-step3_export_bar [data-testid="stCustomComponentV1"],
    .st-key-step3_export_bar [data-testid="stCustomComponentV1"] iframe,
    .st-key-step3_export_bar iframe,
    .st-key-step3_export_bar [data-testid="stImage"] {
        display: none !important;
        height: 0 !important;
        max-height: 0 !important;
        min-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        border: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
        overflow: hidden !important;
    }
    .st-key-step3_export_bar [data-testid="stDownloadButton"],
    .st-key-step3_export_bar [data-testid="stDownloadButton"] button {
        display: inline-flex !important;
        visibility: visible !important;
        pointer-events: auto !important;
        height: auto !important;
        max-height: none !important;
        min-height: 2.75rem !important;
    }
    .st-key-step3_trailing_actions {
        margin-top: 0.35rem;
    }
    @media (max-width: 520px) {
        .st-key-step3_life_core + [data-testid="stVerticalBlock"] [data-testid="stCustomComponentV1"],
        .st-key-step3_life_core + [data-testid="stVerticalBlock"] [data-testid="stCustomComponentV1"] iframe,
        .st-key-step3_life_core + [data-testid="stVerticalBlock"] iframe,
        .st-key-step3_life_core + [data-testid="stVerticalBlock"] [data-testid="stImage"] {
            display: none !important;
            height: 0 !important;
            max-height: 0 !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            visibility: hidden !important;
            pointer-events: none !important;
            overflow: hidden !important;
        }
    }

    /* STEP3: 요약·상세 아코디언 2×2 */
    .st-key-step3_layer_row_top,
    .st-key-step3_layer_row_bottom {
        width: 100% !important;
        box-sizing: border-box !important;
        margin-bottom: 0.45rem !important;
    }
    .st-key-step3_layer_row_top [data-testid="stHorizontalBlock"],
    .st-key-step3_layer_row_bottom [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 0.55rem !important;
        width: 100% !important;
        box-sizing: border-box !important;
        align-items: flex-start !important;
    }
    .st-key-step3_layer_row_top [data-testid="stHorizontalBlock"] > div,
    .st-key-step3_layer_row_bottom [data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0 !important;
        min-width: 0 !important;
        width: 50% !important;
        max-width: 50% !important;
    }
    .st-key-step3_layered_stack [data-testid="stExpander"] summary p {
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: clip !important;
        font-size: clamp(11px, 2.8vw, 15px) !important;
        letter-spacing: -0.05em !important;
    }
    @media (max-width: 640px) {
        .st-key-step3_layer_row_top [data-testid="stHorizontalBlock"],
        .st-key-step3_layer_row_bottom [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            flex-wrap: nowrap !important;
            gap: 0.55rem !important;
        }
        .st-key-step3_layer_row_top [data-testid="stHorizontalBlock"] > div,
        .st-key-step3_layer_row_bottom [data-testid="stHorizontalBlock"] > div {
            width: 100% !important;
            max-width: 100% !important;
            flex-basis: auto !important;
        }
        .st-key-step3_layered_stack [data-testid="stExpander"] {
            width: 100% !important;
        }
    }

    /* STEP3: 접이식 해석 본문 액자 */
    .saju-step3-focus-frame {
        box-sizing: border-box;
        margin: 0.45rem 0 0.65rem;
        padding: 1rem 1.05rem;
        border-radius: 18px;
        border: 1.5px solid color-mix(in srgb, var(--step3-tone) 58%, transparent);
        background: light-dark(
            linear-gradient(155deg, rgba(255, 252, 244, 0.96), rgba(244, 236, 219, 0.92)),
            linear-gradient(155deg, rgba(35, 32, 42, 0.96), rgba(19, 25, 39, 0.94))
        );
        box-shadow:
            0 0 0 1px light-dark(rgba(255, 255, 255, 0.62), rgba(255, 255, 255, 0.06)) inset,
            0 10px 26px light-dark(rgba(98, 79, 39, 0.12), rgba(0, 0, 0, 0.32));
    }
    .saju-step3-focus-title {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        margin-bottom: 0.75rem;
        padding: 0.28rem 0.68rem;
        border-radius: 999px;
        background: color-mix(in srgb, var(--step3-tone) 18%, transparent);
        color: light-dark(#4a3710, #f8e7b8);
        font-weight: 850;
        font-size: clamp(0.9rem, 3vw, 1rem);
        letter-spacing: -0.02em;
    }
    .saju-step3-focus-body {
        color: light-dark(#211c16, rgba(245, 245, 248, 0.94));
        line-height: 1.68;
        font-size: clamp(0.93rem, 3vw, 1.02rem);
    }
    .saju-step3-focus-body p {
        margin: 0.2rem 0 0.55rem;
    }
    .saju-step3-focus-note {
        margin-top: 0.8rem;
        padding: 0.72rem 0.82rem;
        border-radius: 13px;
        background: color-mix(in srgb, var(--step3-tone) 14%, transparent);
        border: 1px solid color-mix(in srgb, var(--step3-tone) 30%, transparent);
        font-weight: 650;
    }
    .saju-step3-summary-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: grid;
        gap: 0.45rem;
    }
    .saju-step3-summary-list li {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.6rem;
        padding: 0.56rem 0.68rem;
        border-radius: 12px;
        background: light-dark(rgba(255, 255, 255, 0.48), rgba(255, 255, 255, 0.07));
        border: 1px solid color-mix(in srgb, var(--step3-tone) 20%, transparent);
    }
    .saju-step3-summary-list span {
        color: light-dark(rgba(55, 48, 38, 0.82), rgba(220, 226, 236, 0.86));
        font-size: clamp(0.82rem, 2.7vw, 0.95rem);
        white-space: nowrap;
    }
    .saju-step3-summary-list b {
        color: light-dark(#1a1a2e, rgba(255, 249, 225, 0.98));
        font-size: clamp(0.9rem, 2.9vw, 1rem);
        white-space: nowrap;
    }
    .saju-step3-element-row {
        margin: 0.55rem 0 0.85rem;
    }
    .saju-step3-element-label {
        display: flex;
        justify-content: space-between;
        gap: 0.75rem;
        margin-bottom: 0.32rem;
        color: light-dark(#1a1a2e, rgba(245, 245, 248, 0.96));
    }
    .saju-step3-element-track {
        height: 10px;
        overflow: hidden;
        border-radius: 999px;
        background: light-dark(rgba(255, 255, 255, 0.82), rgba(255, 255, 255, 0.16));
        box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.12);
    }
    .saju-step3-element-fill {
        height: 100%;
        border-radius: inherit;
        background: linear-gradient(90deg, #D4AF37, #F3D36B);
        box-shadow: 0 0 14px rgba(212, 175, 55, 0.24);
    }

    /* STEP5 주요 신살 의미 액자 */
    .step5-meaning-card {
        box-sizing: border-box;
        width: 100%;
        margin: 0.55rem 0 0.8rem;
        padding: 0.9rem 0.95rem;
        border-radius: 16px;
        border: 1.5px solid color-mix(in srgb, var(--step5-tone) 52%, transparent);
        background: light-dark(
            linear-gradient(155deg, rgba(255, 252, 244, 0.96), rgba(244, 236, 219, 0.92)),
            linear-gradient(155deg, rgba(34, 31, 42, 0.97), rgba(18, 24, 40, 0.95))
        );
        box-shadow:
            0 0 0 1px light-dark(rgba(255, 255, 255, 0.64), rgba(255, 255, 255, 0.06)) inset,
            0 8px 22px light-dark(rgba(98, 79, 39, 0.12), rgba(0, 0, 0, 0.32));
    }
    .step5-meaning-title {
        display: inline-flex;
        margin-bottom: 0.55rem;
        padding: 0.24rem 0.62rem;
        border-radius: 999px;
        background: light-dark(
            color-mix(in srgb, var(--step5-tone) 22%, #fffaf5),
            color-mix(in srgb, var(--step5-tone) 18%, transparent)
        );
        color: light-dark(#7f1d1d, #f8e7b8);
        font-weight: 850;
        font-size: clamp(0.9rem, 3vw, 1rem);
        letter-spacing: -0.02em;
    }
    .step5-meaning-body {
        color: light-dark(#211c16, rgba(245, 245, 248, 0.94));
        line-height: 1.68;
        font-size: clamp(0.9rem, 2.9vw, 1rem);
        text-align: left;
    }

    /* STEP6 오늘의 핵심 운세 액자 */
    .step6-daily-focus-card {
        box-sizing: border-box;
        width: 100%;
        margin: 0.6rem 0 0.85rem;
        padding: 0.95rem 1rem 1.02rem;
        border-radius: 17px;
        border: 1.5px solid color-mix(in srgb, var(--step6-tone) 52%, transparent);
        background: light-dark(
            linear-gradient(155deg, rgba(255, 252, 244, 0.96), rgba(244, 236, 219, 0.92)),
            linear-gradient(155deg, rgba(34, 31, 42, 0.97), rgba(18, 24, 40, 0.95))
        );
        box-shadow:
            0 0 0 1px light-dark(rgba(255, 255, 255, 0.64), rgba(255, 255, 255, 0.06)) inset,
            0 8px 24px light-dark(rgba(98, 79, 39, 0.12), rgba(0, 0, 0, 0.32));
    }
    .step6-daily-focus-title {
        display: inline-flex;
        margin-bottom: 0.58rem;
        padding: 0.25rem 0.64rem;
        border-radius: 999px;
        background: light-dark(
            color-mix(in srgb, var(--step6-tone) 22%, #fffaf5),
            color-mix(in srgb, var(--step6-tone) 18%, transparent)
        );
        color: light-dark(#9a3412, #f8e7b8);
        font-weight: 850;
        font-size: clamp(0.92rem, 3vw, 1.02rem);
        letter-spacing: -0.02em;
    }
    .step6-daily-focus-body {
        color: light-dark(#211c16, rgba(245, 245, 248, 0.94));
        line-height: 1.7;
        font-size: clamp(0.93rem, 3vw, 1.02rem);
        text-align: left;
    }

    /* STEP8 타로 해석 액자 */
    .tarot-interpret-frame {
        box-sizing: border-box;
        width: 100%;
        margin: 0.65rem 0 1rem;
        padding: 1rem 1.05rem 1.08rem;
        border-radius: 18px;
        border: 1.5px solid color-mix(in srgb, var(--tarot-tone) 54%, transparent);
        background: light-dark(
            linear-gradient(155deg, rgba(255, 252, 244, 0.96), rgba(244, 236, 219, 0.92)),
            linear-gradient(155deg, rgba(34, 31, 46, 0.98), rgba(18, 24, 40, 0.95))
        );
        box-shadow:
            0 0 0 1px light-dark(rgba(255, 255, 255, 0.66), rgba(255, 255, 255, 0.06)) inset,
            0 10px 28px light-dark(rgba(98, 79, 39, 0.13), rgba(0, 0, 0, 0.34));
    }
    .tarot-interpret-title {
        display: inline-flex;
        margin-bottom: 0.75rem;
        padding: 0.28rem 0.72rem;
        border-radius: 999px;
        background: color-mix(in srgb, var(--tarot-tone) 18%, transparent);
        color: light-dark(#4a3710, #f8e7b8);
        font-weight: 850;
        font-size: clamp(0.95rem, 3.1vw, 1.06rem);
        letter-spacing: -0.02em;
    }
    .tarot-interpret-body {
        color: light-dark(#211c16, rgba(245, 245, 248, 0.94));
        line-height: 1.78;
        font-size: clamp(0.94rem, 3vw, 1.02rem);
        text-align: left;
    }

    /* STEP3: 사주+MBTI 배너 (images/사주+MBTI.png) */
    .step3-mbti-banner {
        margin: 0.35rem auto 0.85rem;
    }
    .step3-mbti-banner img {
        width: min(100%, 720px);
        max-height: none;
        height: auto;
        object-fit: contain;
        margin: 0 auto;
        border-radius: 14px;
        filter: drop-shadow(0 8px 24px rgba(212, 175, 55, 0.18));
    }

    /* STEP3: MBTI 입력 — Enter 제출(별도 엔터 버튼 없음) */
    .st-key-step3_mbti_input_row,
    .st-key-step3_aptitude_mbti .st-key-step3_mbti_input_row {
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    .st-key-step3_mbti_input_row .step3-mbti-field-label,
    .st-key-step3_aptitude_mbti .step3-mbti-field-label {
        margin: 0 0 0.28rem 0;
        padding: 0;
        font-size: clamp(11px, 3vw, 13px);
        font-weight: 700;
        color: light-dark(#334155, #e5e5e5);
        line-height: 1.2;
    }
    .st-key-step3_mbti_input_row .stTextInput > div > div > input,
    .st-key-step3_aptitude_mbti .st-key-step3_mbti_input_row .stTextInput > div > div > input {
        min-height: clamp(2.45rem, 11vw, 3rem) !important;
        font-size: clamp(12px, 3.2vw, 14px) !important;
        text-transform: uppercase;
    }

    /* STEP12: 관리자 로그인 — Enter 제출(로그인 버튼 숨김) */
    .st-key-step12_admin_login_panel [data-testid="stForm"] {
        width: 100% !important;
        max-width: 100% !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    .st-key-step12_admin_login_panel [data-testid="stFormSubmitButton"],
    .st-key-step12_admin_login_panel .stFormSubmitButton {
        display: none !important;
        height: 0 !important;
        max-height: 0 !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
        pointer-events: none !important;
    }
    .st-key-step12_admin_login_panel [data-testid="InputInstructions"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }
    .st-key-step12_admin_login_panel input[data-saju-revisit-pin="1"],
    .st-key-step12_admin_pwd_input input[data-saju-revisit-pin="1"] {
        -webkit-text-security: disc !important;
        text-security: disc !important;
    }

    /* STEP3: 사주 × MBTI 적성(한지·금색 톤, 청록 테마 제거) */
    .saju-mbti-blend-card {
        box-sizing: border-box;
        padding: 1.05rem 1.1rem 1.2rem;
        margin: 0.65rem 0 1.05rem 0;
        border-radius: 18px;
        border: 1.5px solid light-dark(rgba(212, 175, 55, 0.62), rgba(232, 201, 71, 0.42));
        background: light-dark(
            linear-gradient(155deg, #fffaf0 0%, #efe1c6 100%),
            linear-gradient(155deg, rgba(36, 32, 44, 0.98), rgba(18, 24, 40, 0.96))
        );
        box-shadow:
            0 0 0 1px light-dark(rgba(255, 255, 255, 0.7), rgba(255, 255, 255, 0.06)) inset,
            0 12px 30px light-dark(rgba(98, 79, 39, 0.14), rgba(0, 0, 0, 0.36));
    }
    .saju-mbti-blend-head {
        margin-bottom: 0.85rem;
        padding-bottom: 0.65rem;
        border-bottom: 1px solid light-dark(rgba(212, 175, 55, 0.28), rgba(212, 175, 55, 0.2));
    }
    .saju-mbti-blend-title {
        font-size: max(1.05rem, 1.02rem + 0.25vw);
        font-weight: 800;
        color: light-dark(#5c4510, #f5e6c8);
        letter-spacing: -0.02em;
        line-height: 1.35;
    }
    .saju-mbti-blend-label {
        font-weight: 700;
        color: light-dark(#334155, #e2e8f0);
        font-size: 0.92em;
    }
    .saju-mbti-blend-type {
        margin-top: 0.35rem;
        font-size: max(0.95rem, 0.9rem);
        font-weight: 650;
        color: light-dark(#7a5a12, #e8c547);
    }
    .saju-mbti-blend-strength {
        background: light-dark(rgba(212, 175, 55, 0.16), rgba(212, 175, 55, 0.12));
        padding: 0.9rem 1rem;
        border-radius: 12px;
        margin: 0.65rem 0;
        color: light-dark(#1a1510, rgba(245, 240, 230, 0.95));
        line-height: 1.55;
    }
    .saju-mbti-blend-career {
        margin: 0.75rem 0;
        padding: 0.8rem 0.9rem;
        border-radius: 12px;
        background: light-dark(rgba(255, 255, 255, 0.42), rgba(255, 255, 255, 0.06));
        color: light-dark(#243044, rgba(229, 231, 235, 0.92));
        line-height: 1.55;
    }
    .saju-mbti-blend-advice {
        padding: 0.85rem 0.95rem;
        border-radius: 12px;
        border: 1px solid light-dark(rgba(212, 175, 55, 0.24), rgba(212, 175, 55, 0.18));
        background: light-dark(rgba(255, 251, 235, 0.55), rgba(212, 175, 55, 0.07));
        color: light-dark(rgba(36, 32, 28, 0.82), rgba(203, 213, 225, 0.9));
        font-size: max(14px, 0.94rem);
        line-height: 1.62;
    }

    /* STEP7: 주역점 배너 (images/주역점.png) */
    .step7-iching-banner {
        display: block;
        width: min(100%, 720px);
        margin: 0.15rem auto 0.85rem;
        text-align: center;
        line-height: 0;
    }
    .step7-iching-banner img {
        width: min(100%, 720px) !important;
        max-height: none !important;
        height: auto !important;
        object-fit: contain;
        margin: 0 auto;
        border-radius: 14px;
        filter: drop-shadow(0 8px 24px rgba(212, 175, 55, 0.18));
    }

    /* STEP7 주역: 오늘의 괘 뽑기 / 다시뽑기 가로 2열 (인앱 WebView 세로 스택 방지) */
    .st-key-step7_action_row [data-testid="stVerticalBlock"] {
        flex-wrap: nowrap !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    .st-key-step7_action_row [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 8px !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    .st-key-step7_action_row [data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0 !important;
        min-width: 0 !important;
    }
    .st-key-step7_action_row .stButton > button{
        font-size: max(16px, 1.02rem) !important;
        font-weight: 800 !important;
        border-radius: 16px !important;
    }

    /* STEP7 주역: 괘 선도 중앙·대형, 제목·해설 정렬 */
    .st-key-step7_hex_reveal .step7-hex-wrap {
        text-align: center;
        margin: 0.5rem auto 1.25rem;
        max-width: 100%;
    }
    .st-key-step7_hex_reveal .step7-hex-title {
        font-family: "Noto Serif KR", "Times New Roman", Georgia, serif;
        font-size: clamp(1.05rem, 3.8vw, 1.35rem);
        font-weight: 700;
        color: light-dark(#8b6914, #d4af37);
        letter-spacing: 0.02em;
        margin-bottom: 0.35rem;
        line-height: 1.35;
    }
    .st-key-step7_hex_reveal .step7-hex-hanja-line {
        font-family: "Noto Serif KR", "Times New Roman", Georgia, serif;
        font-size: clamp(0.95rem, 3.2vw, 1.12rem);
        font-weight: 600;
        color: light-dark(#4a3f2a, rgba(230, 220, 200, 0.9));
        margin-bottom: 0.2rem;
        line-height: 1.3;
    }
    .st-key-step7_hex_reveal .step7-hex-hangul-line {
        font-size: clamp(1rem, 3.4vw, 1.18rem);
        font-weight: 700;
        color: light-dark(#1a1510, rgba(245, 240, 230, 0.95));
        margin-bottom: 0.75rem;
        line-height: 1.35;
        letter-spacing: 0.06em;
    }
    .st-key-step7_hex_reveal .step7-hex-visual {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin: 0.35rem auto 1rem;
        padding: 0.85rem 1.1rem 1rem;
        max-width: 17rem;
        background: light-dark(rgba(255, 252, 245, 0.55), rgba(26, 26, 46, 0.45));
        border-radius: 18px;
        border: 1px solid light-dark(rgba(139, 105, 20, 0.22), rgba(212, 175, 55, 0.25));
        box-shadow: 0 6px 24px light-dark(rgba(0, 0, 0, 0.06), rgba(0, 0, 0, 0.35));
    }
    .st-key-step7_hex_reveal .step7-hex-glyph {
        font-family: "Noto Serif KR", "Times New Roman", Georgia, serif;
        font-size: clamp(2.4rem, 11vw, 3.6rem);
        line-height: 1;
        margin-bottom: 0.35rem;
        color: light-dark(#1a1510, rgba(245, 240, 230, 0.96));
    }
    .st-key-step7_hex_reveal .step7-hex-trigram-cap {
        font-size: clamp(0.78rem, 2.8vw, 0.92rem);
        color: light-dark(#6b5a2a, rgba(212, 175, 55, 0.82));
        margin-bottom: 0.15rem;
        letter-spacing: 0.04em;
    }
    .st-key-step7_hex_reveal .step7-hex-trigram-hangul {
        font-size: clamp(0.82rem, 2.9vw, 0.96rem);
        font-weight: 600;
        color: light-dark(#3d3528, rgba(230, 220, 200, 0.88));
        margin-bottom: 0.55rem;
        letter-spacing: 0.05em;
    }
    .st-key-step7_hex_reveal .step7-yao-stack {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.28rem;
        width: 100%;
    }
    .st-key-step7_hex_reveal .step7-trigram-gap {
        height: 0.45rem;
        width: 1px;
        margin: 0.1rem 0;
    }
    .st-key-step7_hex_reveal .step7-yao {
        width: min(9.5rem, 72vw);
        height: 0.42rem;
        display: flex;
        align-items: center;
        justify-content: center;
        box-sizing: border-box;
    }
    .st-key-step7_hex_reveal .step7-yao.yang span {
        display: block;
        width: 100%;
        height: 0.34rem;
        border-radius: 2px;
        background: light-dark(#1a1510, rgba(245, 240, 230, 0.92));
    }
    .st-key-step7_hex_reveal .step7-yao.yin span {
        display: block;
        position: relative;
        width: 100%;
        height: 0.34rem;
        background: transparent;
    }
    .st-key-step7_hex_reveal .step7-yao.yin span::before,
    .st-key-step7_hex_reveal .step7-yao.yin span::after {
        content: "";
        position: absolute;
        top: 0;
        width: 42%;
        height: 0.34rem;
        border-radius: 2px;
        background: light-dark(#1a1510, rgba(245, 240, 230, 0.92));
    }
    .st-key-step7_hex_reveal .step7-yao.yin span::before {
        left: 0;
    }
    .st-key-step7_hex_reveal .step7-yao.yin span::after {
        right: 0;
    }
    .st-key-step7_hex_reveal .step7-interpret-frame {
        box-sizing: border-box;
        width: 100%;
        margin: 0.65rem 0 1rem;
        padding: 1rem 1.05rem 1.08rem;
        border-radius: 18px;
        border: 1.5px solid color-mix(in srgb, var(--step7-tone) 54%, transparent);
        background: light-dark(
            linear-gradient(155deg, rgba(255, 252, 244, 0.96), rgba(244, 236, 219, 0.92)),
            linear-gradient(155deg, rgba(34, 31, 42, 0.97), rgba(18, 24, 40, 0.95))
        );
        box-shadow:
            0 0 0 1px light-dark(rgba(255, 255, 255, 0.66), rgba(255, 255, 255, 0.06)) inset,
            0 10px 28px light-dark(rgba(98, 79, 39, 0.13), rgba(0, 0, 0, 0.34));
    }
    .st-key-step7_hex_reveal .step7-interpret-title {
        display: inline-flex;
        margin-bottom: 0.75rem;
        padding: 0.28rem 0.72rem;
        border-radius: 999px;
        background: color-mix(in srgb, var(--step7-tone) 18%, transparent);
        color: light-dark(#4a3710, #f8e7b8);
        font-weight: 850;
        font-size: clamp(0.95rem, 3.1vw, 1.06rem);
        letter-spacing: -0.02em;
    }
    .st-key-step7_hex_reveal .step7-interpret-body {
        color: light-dark(#211c16, rgba(245, 245, 248, 0.94));
        line-height: 1.78;
        font-size: clamp(0.94rem, 3vw, 1.02rem);
        text-align: left;
    }
    .st-key-step7_hex_reveal .step7-interpret-body b {
        color: light-dark(#5c4510, #f4d179);
    }
    .st-key-step7_hex_reveal .step7-interpret-divider {
        margin: 0.95rem 0;
        height: 1px;
        background: color-mix(in srgb, var(--step7-tone) 24%, transparent);
    }
    .st-key-step7_hex_reveal [data-testid="column"] h5 {
        text-align: center;
        margin-top: 0.85rem !important;
        margin-bottom: 0.35rem !important;
        color: light-dark(#5c4a1a, rgba(212, 175, 55, 0.92));
    }
    .st-key-step7_hex_reveal [data-testid="column"] [data-testid="stMarkdownContainer"] p,
    .st-key-step7_hex_reveal [data-testid="column"] [data-testid="stMarkdownContainer"] li {
        text-align: center;
        line-height: 1.65;
    }

    /* (안정화) STEP6 항목 5열 강제 grid 제거 — Streamlit 기본 레이아웃 사용 */
    /* STEP6 오늘의 운세: 가로 5열 고정, 버튼 라벨은 이모지만 · 아래에 짧은 명칭(재물·연애…) */
    .st-key-step6_today_pick_row [data-testid="stVerticalBlock"] {
        flex-wrap: nowrap !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    .st-key-step6_today_pick_row [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    .st-key-step6_today_pick_row [data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0 !important;
        min-width: 0 !important;
    }
    .st-key-step6_today_pick_row .stButton > button{
        border-radius: var(--saju-soft-radius) !important;
        border: none !important;
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        box-shadow: none !important;
        padding: 0.38rem 0.1rem !important;
        min-height: 2.55rem !important;
        height: auto !important;
        max-height: none !important;
        white-space: nowrap !important;
        text-align: center !important;
        line-height: 1 !important;
        font-size: clamp(1.35rem, 5.4vw, 1.9rem) !important;
        font-weight: 750 !important;
    }
    .st-key-step6_today_pick_row .stButton > button::first-line{
        font-size: inherit !important;
        line-height: inherit !important;
        font-weight: inherit !important;
    }
    .st-key-step6_today_pick_row p.step6-pick-cap {
        margin: 0.22rem 0 0 !important;
        padding: 0 !important;
        font-size: max(11px, 0.74rem) !important;
        font-weight: 750 !important;
        text-align: center !important;
        color: light-dark(rgba(45, 38, 30, 0.92), rgba(229, 231, 235, 0.88)) !important;
        line-height: 1.2 !important;
        letter-spacing: -0.02em !important;
    }
    /* STEP6 오늘의 운세: 점수 막대(퍼센트는 막대 위, 별도 metric 카드 없음) */
    .saju-step6-score-bar {
        margin: 0.4rem 0 0.9rem;
        width: 100%;
        box-sizing: border-box;
    }
    .saju-step6-score-track {
        position: relative;
        height: 2.15rem;
        border-radius: 12px;
        overflow: hidden;
        background: light-dark(rgba(250, 246, 239, 0.96), rgba(255, 255, 255, 0.08));
        border: 1px solid light-dark(rgba(212, 175, 55, 0.28), rgba(212, 175, 55, 0.2));
        box-sizing: border-box;
    }
    .saju-step6-score-fill {
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: calc(var(--step6-pct, 0) * 1%);
        max-width: 100%;
        background: var(--step6-tone, #d4af37);
        border-radius: 12px 0 0 12px;
    }
    .saju-step6-score-label {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: clamp(1rem, 4vw, 1.15rem);
        font-weight: 800;
        color: light-dark(#1a1a2e, #f5f0e8);
        letter-spacing: -0.02em;
        z-index: 1;
        pointer-events: none;
    }

    /* STEP11: 상담 버튼 가로 3열 고정(모바일 인앱 세로 스택 방지) */
    div[class*="st-key-step11_consult_strip"] {
        margin-top: 0.35rem !important;
        margin-bottom: 0.25rem !important;
        width: 100% !important;
        max-width: 100% !important;
    }
    div[class*="st-key-step11_consult_strip"] [data-testid="stVerticalBlock"],
    div[class*="st-key-step11_consult_strip"] [data-testid="stVerticalBlockBorderWrapper"] {
        width: 100% !important;
        max-width: 100% !important;
    }
    div[class*="st-key-step11_consult_strip"] [data-testid="stHorizontalBlock"],
    div[class*="st-key-step11_consult_strip"] [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: stretch !important;
        gap: 6px !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    div[class*="st-key-step11_consult_strip"] [data-testid="stHorizontalBlock"] > div,
    div[class*="st-key-step11_consult_strip"] [data-testid="column"],
    div[class*="st-key-step11_consult_strip"] div.stColumn {
        flex: 1 1 0 !important;
        min-width: 0 !important;
        width: 33.333% !important;
        max-width: 33.333% !important;
        padding-left: 2px !important;
        padding-right: 2px !important;
    }
    div[class*="st-key-step11_consult_strip"] [data-testid="column"] > div,
    div[class*="st-key-step11_consult_strip"] div.stColumn > div {
        width: 100% !important;
        min-width: 0 !important;
    }
    div[class*="st-key-step11_consult_strip"] .stLinkButton,
    div[class*="st-key-step11_consult_strip"] .stLinkButton > a,
    div[class*="st-key-step11_consult_strip"] .stButton,
    div[class*="st-key-step11_consult_strip"] .stButton > button {
        width: 100% !important;
        max-width: 100% !important;
        min-height: auto !important;
        height: auto !important;
        padding: 0.28rem 0.1rem !important;
        font-size: clamp(10px, 2.85vw, 12px) !important;
        font-weight: 700 !important;
        white-space: pre-line !important;
        text-align: center !important;
        line-height: 1.2 !important;
        border-radius: var(--saju-soft-radius) !important;
        border: none !important;
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        box-shadow: none !important;
        box-sizing: border-box !important;
        color: light-dark(#8b6914, #f5e6a8) !important;
    }
    div[class*="st-key-step11_consult_strip"] .stLinkButton > a {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        text-decoration: none !important;
    }
    div[class*="st-key-step11_consult_strip"] .stMarkdown a.step11-consult-tile {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: auto !important;
        padding: 0.28rem 0.1rem !important;
        font-size: clamp(10px, 2.85vw, 12px) !important;
        line-height: 1.2 !important;
        white-space: pre-line !important;
        text-align: center !important;
        border-radius: var(--saju-soft-radius) !important;
        border: none !important;
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        box-shadow: none !important;
        box-sizing: border-box !important;
        color: light-dark(#8b6914, #f5e6a8) !important;
        text-decoration: none !important;
        width: 100% !important;
        cursor: pointer !important;
        -webkit-tap-highlight-color: transparent;
    }
    div[class*="st-key-step11_consult_strip"] .stMarkdown .step11-consult-tile--phone {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 0.2rem !important;
        min-height: auto !important;
        padding: 0.32rem 0.12rem 0.4rem !important;
        border-radius: var(--saju-soft-radius) !important;
        background: light-dark(#6b5b2a, #8b7355) !important;
        box-sizing: border-box !important;
        width: 100% !important;
    }
    div[class*="st-key-step11_consult_strip"] .step11-phone-label {
        display: block;
        font-size: clamp(10px, 2.75vw, 12px) !important;
        line-height: 1.2 !important;
        white-space: pre-line !important;
        text-align: center !important;
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    div[class*="st-key-step11_consult_strip"] a.step11-phone-num,
    div[class*="st-key-step11_consult_strip"] span.step11-phone-num {
        display: block;
        font-size: clamp(13px, 4.1vw, 17px) !important;
        line-height: 1.2 !important;
        letter-spacing: 0.04em;
        text-align: center !important;
        color: #fef9c3 !important;
        font-weight: 900 !important;
        word-break: keep-all;
    }
    div[class*="st-key-step11_consult_strip"] a.step11-phone-num {
        text-decoration: underline !important;
        text-underline-offset: 3px;
    }
    div[class*="st-key-step11_consult_strip"] span.step11-phone-num {
        user-select: all;
        -webkit-user-select: all;
    }
    /* PC(마우스): 번호만 표시 — tel 클릭 시 Chrome 팝업 방지 */
    @media (hover: hover) and (pointer: fine) {
        div[class*="st-key-step11_consult_strip"] a.step11-phone-num--mobile {
            display: none !important;
        }
        div[class*="st-key-step11_consult_strip"] span.step11-phone-num--desktop {
            display: block !important;
        }
    }
    /* 모바일(터치): 번호 탭 → 전화 앱 */
    @media (hover: none), (pointer: coarse) {
        div[class*="st-key-step11_consult_strip"] a.step11-phone-num--mobile {
            display: block !important;
        }
        div[class*="st-key-step11_consult_strip"] span.step11-phone-num--desktop {
            display: none !important;
        }
    }
    div[class*="st-key-step11_consult_strip"] a.step11-phone-num:active {
        opacity: 0.88;
    }
    @media (max-width: 420px) {
        div[class*="st-key-step11_consult_strip"] [data-testid="stHorizontalBlock"] {
            gap: 4px !important;
        }
        div[class*="st-key-step11_consult_strip"] .stLinkButton > a,
        div[class*="st-key-step11_consult_strip"] .stButton > button {
            min-height: 3.1rem !important;
            font-size: 10px !important;
            padding: 0.32rem 0.1rem !important;
        }
        div[class*="st-key-step11_consult_strip"] a.step11-phone-num,
        div[class*="st-key-step11_consult_strip"] span.step11-phone-num {
            font-size: clamp(12px, 3.6vw, 14px) !important;
        }
    }

    /* STEP11: 상담 연결 아래 이동 버튼(← 총평 / 관리자 이동 →) — 가로 2열 고정 */
    div[class*="st-key-saju_router_step_mount_11"] .st-key-saju_bottom_prev_next_row,
    div[class*="st-key-step11_inline_nav_row"] {
        margin-top: 0.55rem !important;
        margin-bottom: 0.35rem !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    div[class*="st-key-saju_router_step_mount_11"] .st-key-saju_bottom_prev_next_row [data-testid="stVerticalBlock"],
    div[class*="st-key-saju_router_step_mount_11"] .st-key-saju_bottom_prev_next_row [data-testid="stVerticalBlockBorderWrapper"],
    div[class*="st-key-step11_inline_nav_row"] [data-testid="stVerticalBlock"],
    div[class*="st-key-step11_inline_nav_row"] [data-testid="stVerticalBlockBorderWrapper"] {
        flex-wrap: nowrap !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    div[class*="st-key-saju_router_step_mount_11"] .st-key-saju_bottom_prev_next_row [data-testid="stHorizontalBlock"],
    div[class*="st-key-step11_inline_nav_row"] [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: stretch !important;
        gap: 8px !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    div[class*="st-key-saju_router_step_mount_11"] .st-key-saju_bottom_prev_next_row [data-testid="stHorizontalBlock"] > div,
    div[class*="st-key-saju_router_step_mount_11"] .st-key-saju_bottom_prev_next_row [data-testid="column"],
    div[class*="st-key-saju_router_step_mount_11"] .st-key-saju_bottom_prev_next_row div.stColumn,
    div[class*="st-key-step11_inline_nav_row"] [data-testid="stHorizontalBlock"] > div,
    div[class*="st-key-step11_inline_nav_row"] [data-testid="column"],
    div[class*="st-key-step11_inline_nav_row"] div.stColumn {
        flex: 1 1 0 !important;
        min-width: 0 !important;
        width: 50% !important;
        max-width: 50% !important;
        box-sizing: border-box !important;
    }
    div[class*="st-key-saju_router_step_mount_11"] .st-key-saju_bottom_prev_next_row [data-testid="column"] > div,
    div[class*="st-key-saju_router_step_mount_11"] .st-key-saju_bottom_prev_next_row div.stColumn > div,
    div[class*="st-key-step11_inline_nav_row"] [data-testid="column"] > div,
    div[class*="st-key-step11_inline_nav_row"] div.stColumn > div {
        width: 100% !important;
        min-width: 0 !important;
    }
    div[class*="st-key-saju_router_step_mount_11"] .st-key-saju_bottom_prev_next_row .stButton > button,
    div[class*="st-key-step11_inline_nav_row"] .stButton > button {
        width: 100% !important;
        min-height: 2.65rem !important;
        font-weight: 700 !important;
        border-radius: var(--saju-soft-radius) !important;
    }

    /* STEP11: 메모 내려받기 + 새로고침 — 모바일 가로 2열 */
    div[class*="st-key-step11_memo_download_panel"] [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 8px !important;
        width: 100% !important;
    }
    div[class*="st-key-step11_memo_download_panel"] [data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0 !important;
        min-width: 0 !important;
        width: 50% !important;
        max-width: 50% !important;
    }
    div[class*="st-key-step11_memo_download_panel"] .stDownloadButton > button,
    div[class*="st-key-step11_memo_download_panel"] .stDownloadButton > button[kind="primary"],
    div[class*="st-key-step11_memo_download_panel"] .stDownloadButton > button[kind="secondary"],
    div[class*="st-key-step11_memo_download_panel"] .stDownloadButton > button[data-testid="baseButton-primary"],
    div[class*="st-key-step11_memo_download_panel"] .stDownloadButton > button[data-testid="baseButton-secondary"],
    div[class*="st-key-step11_memo_download_panel"] .stButton > button {
        width: 100% !important;
        min-height: 2.75rem !important;
        font-size: max(12px, 0.82rem) !important;
        font-weight: 700 !important;
        white-space: normal !important;
        line-height: 1.28 !important;
        padding: 0.45rem 0.35rem !important;
        color: light-dark(#2a2218, #f2ebe0) !important;
        -webkit-text-fill-color: light-dark(#2a2218, #f2ebe0) !important;
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        border: 1px solid light-dark(rgba(139, 105, 20, 0.38), rgba(212, 175, 55, 0.32)) !important;
        box-shadow: light-dark(0 1px 0 rgba(255, 255, 255, 0.65), none) !important;
    }
    div[class*="st-key-step11_memo_download_panel"] .stDownloadButton > button p,
    div[class*="st-key-step11_memo_download_panel"] .stDownloadButton > button span,
    div[class*="st-key-step11_memo_download_panel"] .stDownloadButton > button div,
    div[class*="st-key-step11_memo_download_panel"] .stButton > button p,
    div[class*="st-key-step11_memo_download_panel"] .stButton > button span,
    div[class*="st-key-step11_memo_download_panel"] .stButton > button div {
        color: inherit !important;
        -webkit-text-fill-color: inherit !important;
        opacity: 1 !important;
    }

    /* ===== 글로벌: 이동·안내 클릭 버튼 — 연한 피치 칩(정보입력 년·월·일 톤) ===== */
    .stApp .stButton > button,
    .stApp .stButton > button[kind="primary"],
    .stApp .stButton > button[kind="secondary"],
    .stApp .stButton > button[data-testid="baseButton-primary"],
    .stApp .stButton > button[data-testid="baseButton-secondary"],
    .stApp [data-testid="stFormSubmitButton"] > button,
    .stApp .stFormSubmitButton > button,
    .stApp div[data-testid="stBaseButton-primary"],
    .stApp div[data-testid="stBaseButton-secondary"] {
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        filter: none !important;
        border-radius: var(--saju-soft-radius) !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        color: light-dark(rgba(45, 38, 28, 0.9), rgba(235, 228, 210, 0.94)) !important;
    }
    .stApp .stButton > button[kind="primary"],
    .stApp .stButton > button[data-testid="baseButton-primary"],
    .stApp div[data-testid="stBaseButton-primary"] {
        font-weight: 800 !important;
        color: light-dark(#8b6914, #f5e6a8) !important;
        background: light-dark(var(--saju-soft-fill-hover), var(--saju-soft-fill-dark-hover)) !important;
    }
    .stApp .stButton > button:hover,
    .stApp .stButton > button:focus,
    .stApp .stButton > button:focus-visible,
    .stApp [data-testid="stFormSubmitButton"] > button:hover,
    .stApp .stLinkButton > a:hover {
        background: light-dark(var(--saju-soft-fill-hover), var(--saju-soft-fill-dark-hover)) !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        filter: none !important;
    }
    .stApp .stButton > button:active {
        background: light-dark(var(--saju-soft-fill-active), var(--saju-soft-fill-dark-hover)) !important;
    }
    /* STEP 하단 독은 HTML 링크(.saju-dock-a) — 버튼과 동일하게 액자 없음 */
    .stCaption,
    div[data-testid="stCaption"] {
        color: light-dark(rgba(26, 26, 46, 0.72), rgba(229, 229, 235, 0.72)) !important;
    }
    .stApp a {
        color: light-dark(var(--saju-gold-deep), var(--saju-gold-bright)) !important;
        text-underline-offset: 3px;
    }
    .stApp a:hover {
        color: light-dark(#5c4510, #e8d9a8) !important;
    }
    .stLinkButton > a {
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: var(--saju-soft-radius) !important;
        padding: 0.42rem 0.65rem !important;
        font-weight: 700 !important;
        color: light-dark(#8b6914, #f5e6a8) !important;
    }
    .saju-fortune-card {
        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(212, 175, 55, 0.18) !important;
    }
    /* 마크다운 래퍼용: <div class="saju-card">…</div> */
    .saju-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border-radius: 20px;
        border: 1px solid rgba(212, 175, 55, 0.25);
        padding: 24px 20px;
        margin: 16px 0;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
    }
    [data-testid="stExpander"] details {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 0 !important;
    }
    [data-testid="stExpander"] summary {
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        border: none !important;
        border-bottom: none !important;
        box-shadow: none !important;
        border-radius: var(--saju-soft-radius) !important;
        padding: 0.42rem 0.55rem !important;
    }
    /* STEP2 접이식(태어난 시간·성별·양력): 글로벌 expander/버튼 테두리보다 뒤에서 덮어씀 */
    .stApp .st-key-step2_navertone_self [data-testid="stExpander"] details,
    .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] details {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 0 !important;
    }
    .stApp .st-key-step2_navertone_self [data-testid="stExpander"] summary,
    .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] summary {
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        border: none !important;
        border-bottom: none !important;
        box-shadow: none !important;
        border-radius: var(--saju-soft-radius) !important;
        padding: 0.42rem 0.55rem !important;
        list-style: none !important;
    }
    .stApp .st-key-step2_navertone_self [data-testid="stExpander"] summary::marker,
    .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] summary::marker {
        content: "" !important;
    }
    .stApp .st-key-step2_navertone_self [data-testid="stExpander"] .stButton > button,
    .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] .stButton > button,
    .stApp .st-key-step2_navertone_self [data-testid="stExpander"] .stButton > button[kind="primary"],
    .stApp .st-key-step2_navertone_self [data-testid="stExpander"] .stButton > button[kind="secondary"],
    .stApp .st-key-step2_navertone_self [data-testid="stExpander"] .stButton > button[data-testid="baseButton-primary"],
    .stApp .st-key-step2_navertone_self [data-testid="stExpander"] .stButton > button[data-testid="baseButton-secondary"],
    .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] .stButton > button[kind="primary"],
    .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] .stButton > button[kind="secondary"],
    .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] .stButton > button[data-testid="baseButton-primary"],
    .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] .stButton > button[data-testid="baseButton-secondary"] {
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        border-radius: var(--saju-soft-radius) !important;
        min-height: auto !important;
        height: auto !important;
        margin: 0.12rem 0 !important;
        padding: 0.38rem 0.5rem !important;
        font-size: clamp(12px, 2.85vw, 14px) !important;
        line-height: 1.28 !important;
        letter-spacing: -0.04em !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
    }
    .stApp .st-key-step2_navertone_self [data-testid="stExpander"] .stButton > button[kind="primary"],
    .stApp .st-key-step2_navertone_self [data-testid="stExpander"] .stButton > button[data-testid="baseButton-primary"],
    .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] .stButton > button[kind="primary"],
    .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] .stButton > button[data-testid="baseButton-primary"] {
        background: light-dark(var(--saju-soft-fill-hover), var(--saju-soft-fill-dark-hover)) !important;
        border: none !important;
        box-shadow: none !important;
        font-weight: 700 !important;
        color: light-dark(#8b6914, #f5e6a8) !important;
    }
    .stApp .st-key-step2_navertone_self [data-testid="stExpander"] .stButton > button[kind="secondary"],
    .stApp .st-key-step2_navertone_self [data-testid="stExpander"] .stButton > button[data-testid="baseButton-secondary"],
    .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] .stButton > button[kind="secondary"],
    .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] .stButton > button[data-testid="baseButton-secondary"] {
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        border: none !important;
        box-shadow: none !important;
        color: light-dark(rgba(45, 38, 28, 0.88), rgba(235, 228, 210, 0.92)) !important;
    }
    .stApp .st-key-step2_navertone_self [data-testid="stExpander"] .stButton > button:hover,
    .stApp .st-key-step2_navertone_self [data-testid="stExpander"] .stButton > button:focus,
    .stApp .st-key-step2_navertone_self [data-testid="stExpander"] .stButton > button:focus-visible,
    .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] .stButton > button:hover,
    .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] .stButton > button:focus,
    .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] .stButton > button:focus-visible {
        background: light-dark(var(--saju-soft-fill-hover), var(--saju-soft-fill-dark-hover)) !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    /* 태어난 시간 목록: 왼쪽 정렬·세로 텍스트 목록 */
    .stApp .st-key-step2_navertone_self [data-testid="stExpander"] .stButton > button,
    .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] .stButton > button {
        width: 100% !important;
        justify-content: flex-start !important;
        text-align: left !important;
    }

    /*
     * 다크 모드(``html.saju-dark-tone``): config.toml 팔레트와 동기.
     * 링크는 인디고(#A5B4FC), 본문은 #E5E5E5, 악센트는 골드 변수 유지.
     */
    html.saju-dark-tone {
        color-scheme: dark;
        --saju-bg-deep: #05050c;
        --saju-bg-mid: #0a0a14;
        --saju-bg-elevated: #16213e;
        --saju-bg-card-a: #1a1a2e;
        --saju-bg-card-b: #16213e;
        --saju-gold: #d4af37;
        --saju-gold-bright: #e8b923;
        --saju-gold-soft: #c9a227;
        --saju-gold-deep: #7a5e12;
        --saju-glow: rgba(212, 175, 55, 0.34);
        --saju-text-body: #e5e5e5;
        --saju-text-accent: #a5b4fc;
        --saju-soft-fill: rgba(40, 36, 32, 0.88);
        --saju-soft-fill-hover: rgba(50, 44, 38, 0.94);
        --saju-soft-fill-active: rgba(56, 48, 42, 0.96);
        --saju-soft-fill-dark: rgba(40, 36, 32, 0.88);
        --saju-soft-fill-dark-hover: rgba(50, 44, 38, 0.94);
    }
    html.saju-dark-tone .main .block-container::before {
        opacity: 0.35 !important;
        filter: none !important;
    }
    html.saju-dark-tone .stApp {
        background-color: var(--saju-bg-canvas-dark) !important;
        background-image:
            radial-gradient(ellipse 95% 68% at 50% -18%, rgba(212, 175, 55, 0.1), transparent 56%),
            linear-gradient(168deg, #0a0a12 0%, #0e0e18 54%, #12121f 100%) !important;
    }
    [data-theme="dark"] .stApp,
    .stApp[data-theme="dark"] {
        background-color: var(--saju-bg-canvas-dark) !important;
        background-image:
            radial-gradient(ellipse 95% 68% at 50% -18%, rgba(212, 175, 55, 0.1), transparent 56%),
            linear-gradient(168deg, #0a0a12 0%, #0e0e18 54%, #12121f 100%) !important;
    }
    [data-theme="light"] .stApp,
    .stApp[data-theme="light"] {
        background-color: var(--saju-bg-canvas-light) !important;
        background-image:
            radial-gradient(ellipse 110% 72% at 50% -16%, rgba(201, 162, 39, 0.07), transparent 54%),
            linear-gradient(
                168deg,
                var(--saju-bg-canvas-light) 0%,
                var(--saju-bg-canvas-light-mid) 46%,
                var(--saju-bg-canvas-light-deep) 100%
            ) !important;
    }
    /* iPhone Safari — feTurbulence·mix-blend 노이즈 번짐 방지, 단색 그라데이션만 */
    @supports (-webkit-touch-callout: none) {
        .stApp {
            background-image: light-dark(
                linear-gradient(180deg, #fcfaf7 0%, #f3efe8 100%),
                linear-gradient(180deg, #0c0c16 0%, #0a0a12 100%)
            ) !important;
        }
        .main .block-container::before {
            display: none !important;
        }
        div[class*="st-key-saju_analysis_card"]::after,
        div[class*="st-key-step3_hanji_card"]::before {
            content: none !important;
            display: none !important;
        }
    }
    html.saju-dark-tone *:focus-visible {
        outline-color: rgba(165, 180, 252, 0.55) !important;
    }
    html.saju-dark-tone .stButton > button:focus-visible,
    html.saju-dark-tone .stTextInput input:focus-visible,
    html.saju-dark-tone .stSelectbox div[data-baseweb="select"]:focus-within,
    html.saju-dark-tone .stCheckbox input:focus-visible,
    html.saju-dark-tone .stRadio input:focus-visible,
    html.saju-dark-tone .stNumberInput input:focus-visible,
    html.saju-dark-tone [data-testid="stChatInput"] textarea:focus-visible,
    html.saju-dark-tone .stTextArea textarea:focus-visible,
    html.saju-dark-tone .stLinkButton > a:focus-visible {
        outline: 3px solid rgba(212, 175, 55, 0.55) !important;
    }
    html.saju-dark-tone .stApp a {
        color: var(--saju-text-accent) !important;
    }
    html.saju-dark-tone .stApp a:hover {
        color: #c7d2fe !important;
    }
    html.saju-dark-tone .stApp .stButton > button,
    html.saju-dark-tone .stApp .stButton > button[kind="primary"],
    html.saju-dark-tone .stApp .stButton > button[kind="secondary"],
    html.saju-dark-tone .stApp div[data-testid="stBaseButton-primary"],
    html.saju-dark-tone .stApp div[data-testid="stBaseButton-secondary"],
    html.saju-dark-tone .stApp [data-testid="stFormSubmitButton"] > button,
    html.saju-dark-tone .stApp .stLinkButton > a {
        filter: none !important;
        border: none !important;
        box-shadow: none !important;
        background: var(--saju-soft-fill-dark) !important;
    }
    html.saju-dark-tone .stApp .stButton > button[kind="primary"],
    html.saju-dark-tone .stApp div[data-testid="stBaseButton-primary"] {
        color: #f5e6a8 !important;
    }
    html.saju-dark-tone .stApp .stButton > button[kind="primary"]:hover,
    html.saju-dark-tone .stApp div[data-testid="stBaseButton-primary"]:hover,
    html.saju-dark-tone .stApp .stButton > button:hover,
    html.saju-dark-tone .stApp .stLinkButton > a:hover {
        background: var(--saju-soft-fill-dark-hover) !important;
    }
    html.saju-dark-tone .stApp .st-key-step2_navertone_self [data-testid="stExpander"] details,
    html.saju-dark-tone .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] details,
    html.saju-dark-tone .stApp .st-key-step2_navertone_self [data-testid="stExpander"] summary,
    html.saju-dark-tone .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] summary {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }
    html.saju-dark-tone .stApp .st-key-step2_navertone_self [data-testid="stExpander"] .stButton > button,
    html.saju-dark-tone .stApp .st-key-step2_navertone_self [data-testid="stExpander"] .stButton > button[kind="primary"],
    html.saju-dark-tone .stApp .st-key-step2_navertone_self [data-testid="stExpander"] .stButton > button[kind="secondary"],
    html.saju-dark-tone .stApp .st-key-step2_navertone_self [data-testid="stExpander"] .stButton > button[data-testid="baseButton-primary"],
    html.saju-dark-tone .stApp .st-key-step2_navertone_self [data-testid="stExpander"] .stButton > button[data-testid="baseButton-secondary"],
    html.saju-dark-tone .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] .stButton > button,
    html.saju-dark-tone .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] .stButton > button[kind="primary"],
    html.saju-dark-tone .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] .stButton > button[kind="secondary"],
    html.saju-dark-tone .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] .stButton > button[data-testid="baseButton-primary"],
    html.saju-dark-tone .stApp .st-key-step2_navertone_opp [data-testid="stExpander"] .stButton > button[data-testid="baseButton-secondary"] {
        border: none !important;
        box-shadow: none !important;
        background: var(--saju-soft-fill-dark) !important;
        filter: none !important;
    }
    html.saju-dark-tone .st-key-step6_today_pick_row .stButton > button {
        border: none !important;
        background: var(--saju-soft-fill-dark) !important;
        box-shadow: none !important;
    }
    html.saju-dark-tone .stCaption,
    html.saju-dark-tone div[data-testid="stCaption"] {
        color: rgba(229, 229, 229, 0.72) !important;
    }
    html.saju-dark-tone .stMarkdown strong,
    html.saju-dark-tone [data-testid="stMarkdownContainer"] strong {
        color: #ececf1 !important;
    }
    /* 폼 컨트롤·버튼 터치/가독성 (STEP2 등 입력 화면) */
    .stNumberInput input,
    .stTextInput input,
    .stSelectbox select {
        font-size: 1.1rem !important;
        padding: 12px !important;
    }
    .stButton button {
        height: 58px !important;
        font-size: 1.1rem !important;
        font-weight: 600;
    }
    /* STEP6 운세 5아이콘 행: 전역 버튼 높이 고정 해제(가로 5열·이모지 단독) */
    .st-key-step6_today_pick_row .stButton > button {
        height: auto !important;
        min-height: 2.55rem !important;
    }

    /* 브리핑 슬라이드 · 대운 타임라인 (P1) */
    .saju-briefing-fortune-card {
        border-radius: 18px;
        border: 1px solid color-mix(in srgb, var(--fc, #d4af37) 55%, transparent);
        background: linear-gradient(145deg, rgba(0,0,0,0.35), rgba(255,255,255,0.04));
        padding: 1rem 0.85rem;
        text-align: center;
        min-height: 11rem;
    }
    .saju-briefing-fortune-emoji { font-size: 2.2rem; line-height: 1; }
    .saju-briefing-fortune-title { font-weight: 800; margin-top: 0.35rem; color: var(--fc, #d4af37); }
    .saju-briefing-fortune-score { font-size: 2rem; font-weight: 900; color: #fff8ec; margin: 0.25rem 0; }
    .saju-briefing-fortune-score span { font-size: 1rem; opacity: 0.7; }
    .saju-briefing-fortune-sum { font-size: 0.82rem; line-height: 1.45; opacity: 0.88; margin: 0; }
    /* STEP3 통합 분석 — 3D 덱과 동일 항목(네이티브) */
    .saju-unified-deck-section {
        margin: 0.55rem 0 0.85rem;
        padding: 0.75rem 0.85rem;
        border-radius: 12px;
        background: light-dark(#fffdf8, rgba(15, 23, 42, 0.55));
        border: 1px solid light-dark(rgba(212, 175, 55, 0.35), rgba(148, 163, 184, 0.2));
    }
    .saju-unified-deck-kicker {
        font-size: 0.72rem;
        font-weight: 700;
        color: #d97706;
        margin: 0 0 0.25rem;
        letter-spacing: 0.04em;
    }
    .saju-unified-deck-title {
        font-size: clamp(1rem, 4vw, 1.2rem);
        font-weight: 800;
        margin: 0 0 0.35rem;
        color: light-dark(#1e293b, #f8fafc);
    }
    .saju-unified-deck-purpose,
    .saju-unified-deck-body {
        font-size: 0.84rem;
        line-height: 1.5;
        color: light-dark(#334155, #cbd5e1);
        margin: 0.25rem 0;
    }
    .saju-unified-dm-block { text-align: center; margin: 0.65rem 0; }
    .saju-unified-dm-label { font-size: 0.7rem; color: #d97706; margin: 0; }
    .saju-unified-dm-char { font-size: 2.4rem; font-weight: 900; margin: 0.15rem 0; color: light-dark(#0f172a, #fff); }
    .saju-unified-dm-el { font-size: 0.95rem; margin: 0; opacity: 0.85; }
    .saju-unified-kw-list { list-style: none; padding: 0; margin: 0.5rem 0 0; }
    .saju-unified-kw-item {
        padding: 0.45rem 0.55rem;
        margin-bottom: 0.35rem;
        border-radius: 8px;
        background: light-dark(rgba(0,0,0,0.04), rgba(255,255,255,0.06));
    }
    .saju-unified-kw-item b { color: #fbbf24; display: block; }
    .saju-unified-kw-item span { font-size: 0.8rem; color: light-dark(#64748b, #94a3b8); }
    .saju-unified-kw-chips { display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.45rem; }
    .saju-unified-kw-chip {
        padding: 0.25rem 0.55rem;
        border-radius: 999px;
        border: 1px solid rgba(251, 191, 36, 0.45);
        font-size: 0.78rem;
        color: #b45309;
    }
    .saju-unified-balance-box {
        margin-top: 0.55rem;
        padding: 0.55rem 0.65rem;
        border-radius: 8px;
        background: light-dark(rgba(251, 191, 36, 0.12), rgba(251, 191, 36, 0.08));
        font-size: 0.82rem;
        line-height: 1.45;
    }
    .saju-unified-tg-chart { margin-top: 0.45rem; }
    .saju-unified-tg-row {
        display: grid;
        grid-template-columns: 3.2rem 1fr 1.5rem;
        align-items: center;
        gap: 0.35rem;
        margin-bottom: 0.35rem;
        font-size: 0.8rem;
    }
    .saju-unified-tg-bar {
        display: block;
        height: 8px;
        border-radius: 4px;
        background: linear-gradient(90deg, #f59e0b, #fbbf24);
        min-width: 8px;
    }
    .saju-unified-tg-val { text-align: right; font-weight: 700; }
    .saju-briefing-rec-card {
        border-radius: 14px;
        border: 1px solid rgba(212,175,55,0.35);
        background: rgba(0,0,0,0.25);
        padding: 0.85rem 1rem;
        margin-bottom: 0.55rem;
    }
    .saju-briefing-rec-title { font-weight: 700; color: #d4af37; }
    .saju-briefing-rec-desc { margin: 0.35rem 0 0; font-size: 0.9rem; line-height: 1.5; opacity: 0.9; }
    .saju-match-slide {
        border-radius: 14px;
        border: 1px solid color-mix(in srgb, var(--ms-tone, #d4af37) 45%, #e2e8f0);
        padding: 0.75rem 0.55rem;
        min-height: 6.5rem;
        background: light-dark(#fffefb, rgba(15, 23, 42, 0.55));
    }
    .saju-match-slide-label {
        font-weight: 800;
        font-size: 0.9rem;
        color: light-dark(#9f1239, var(--ms-tone, #d4af37));
    }
    .saju-match-slide-body {
        font-size: 0.78rem;
        line-height: 1.45;
        margin: 0.35rem 0 0;
        color: light-dark(#334155, rgba(226, 232, 240, 0.92));
        opacity: 1;
    }
    .saju-match-hero-score { text-align: center; margin: 0.5rem 0 0.75rem; }
    .saju-match-hero-num { font-size: 2.4rem; font-weight: 900; color: #fbbf24; }
    .saju-dw-timeline {
        display: flex; flex-wrap: wrap; gap: 0.35rem;
        margin: 0.5rem 0 1rem; padding: 0.35rem 0;
    }
    .saju-dw-chip {
        display: inline-flex; flex-direction: column; align-items: center;
        padding: 0.35rem 0.5rem; border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.15);
        font-size: 0.85rem; font-weight: 700;
        background: rgba(0,0,0,0.25);
    }
    .saju-dw-chip small { font-size: 0.65rem; font-weight: 500; opacity: 0.75; }
    .saju-dw-chip--now { border-color: #d4af37; box-shadow: 0 0 0 1px rgba(212,175,55,0.35); }
    .saju-dw-chip--sel {
        background: light-dark(rgba(212, 175, 55, 0.22), rgba(212, 175, 55, 0.18));
        color: light-dark(#2a2218, #f5e6a8);
        border-color: light-dark(rgba(139, 90, 43, 0.45), rgba(212, 175, 55, 0.55));
    }

    .saju-landing-mini-slide {
        border-radius: 16px; border: 1px solid rgba(212,175,55,0.35);
        padding: 0.85rem 1rem; margin-bottom: 0.65rem;
        background: linear-gradient(135deg, rgba(212,175,55,0.12), rgba(0,0,0,0.2));
    }
    .saju-landing-mini-kicker { font-size: 0.72rem; letter-spacing: 0.12em; color: #d4af37; margin: 0; }
    .saju-landing-mini-title { font-size: 1.35rem; margin: 0.25rem 0; color: #f5e6a8; }
    .saju-landing-mini-body, .saju-landing-mini-prep { font-size: 0.88rem; line-height: 1.45; opacity: 0.9; margin: 0.2rem 0; }
    .saju-step2-oheng-preview {
        display: flex; align-items: center; gap: 0.5rem;
        padding: 0.5rem 0.75rem; border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.12); margin: 0.5rem 0 0.75rem;
    }
    .saju-step2-oheng-dot { width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; }
    .saju-sinsal-flip-card {
        border-radius: 18px;
        border: 1px solid light-dark(rgba(185, 28, 28, 0.28), rgba(212, 175, 55, 0.4));
        padding: 1.1rem;
        margin: 0.5rem 0 1rem;
        background: light-dark(
            linear-gradient(165deg, #fffafb 0%, #fff1f2 55%, #ffe4e6 100%),
            rgba(0, 0, 0, 0.25)
        );
    }
    .saju-sinsal-flip-front {
        font-size: 1.5rem;
        font-weight: 800;
        color: light-dark(#b91c1c, #d4af37);
    }
    .saju-sinsal-flip-back {
        margin: 0.65rem 0 0;
        line-height: 1.55;
        font-size: 0.92rem;
        color: light-dark(#1f2937, rgba(245, 245, 248, 0.94));
        opacity: 1;
    }
    .saju-s11-kw-rail { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.35rem 0 0.85rem; }
    .saju-s11-kw-chip {
        padding: 0.35rem 0.65rem; border-radius: 999px;
        border: 1px solid rgba(212,175,55,0.45); font-size: 0.82rem; color: #f5e6a8;
    }
    .step7-hex-wrap--reveal .step7-yao-stack .step7-yao {
        animation: sajuYaoFade 0.55s ease both;
    }
    .step7-hex-wrap--reveal .step7-yao-stack .step7-yao:nth-child(2) { animation-delay: 0.08s; }
    .step7-hex-wrap--reveal .step7-yao-stack .step7-yao:nth-child(3) { animation-delay: 0.16s; }
    .step7-hex-wrap--reveal .step7-yao-stack .step7-yao:nth-child(4) { animation-delay: 0.24s; }
    .step7-hex-wrap--reveal .step7-yao-stack .step7-yao:nth-child(5) { animation-delay: 0.32s; }
    .step7-hex-wrap--reveal .step7-yao-stack .step7-yao:nth-child(6) { animation-delay: 0.4s; }
    .step7-hex-wrap--reveal .step7-yao-stack .step7-yao:nth-child(7) { animation-delay: 0.48s; }
    @keyframes sajuYaoFade {
        from { opacity: 0; transform: translateY(6px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .step8-synth-lead { font-size: 1rem; line-height: 1.55; opacity: 0.92; margin: 0.5rem 0; }
    .step8-tarot-banner {
        display: block;
        width: min(100%, 720px);
        margin: 0.15rem auto 0.85rem;
        text-align: center;
    }
    .step8-tarot-banner__row {
        display: flex;
        flex-direction: row;
        flex-wrap: nowrap;
        justify-content: center;
        align-items: flex-end;
        gap: clamp(6px, 2vw, 14px);
        width: 100%;
    }
    .step8-tarot-banner__row img {
        flex: 1 1 0;
        min-width: 0;
        width: 33.333%;
        max-width: 220px;
        height: auto;
        margin: 0;
        border-radius: 20px;
        box-shadow: 0 0 30px rgba(160, 100, 255, 0.4);
        object-fit: contain;
    }

    /* ===== 밝은 한지 톤 · 모바일 가독성 (글자색 묻힘 방지) ===== */
    .main [data-testid="stMarkdownContainer"] p,
    .main [data-testid="stMarkdownContainer"] li,
    .main [data-testid="stMarkdownContainer"] span,
    .main [data-testid="stMarkdownContainer"] label {
        color: light-dark(var(--saju-text-readable), #ece8e0);
    }
    .main [data-testid="stMarkdownContainer"] h1,
    .main [data-testid="stMarkdownContainer"] h2,
    .main [data-testid="stMarkdownContainer"] h3,
    .main [data-testid="stMarkdownContainer"] h4,
    .main [data-testid="stMarkdownContainer"] h5,
    .main [data-testid="stMarkdownContainer"] h6 {
        color: light-dark(#14100c, #f5f0e8) !important;
        font-weight: 800 !important;
    }
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p {
        color: light-dark(#3d3428, #d8d4cc) !important;
        opacity: 1 !important;
    }
    .saju-step7-question-guide {
        display: block;
        margin: 0.35rem 0 0.75rem;
        padding: 0.9rem 1rem;
        border-radius: 16px;
        border: 1px solid light-dark(rgba(212, 175, 55, 0.38), rgba(212, 175, 55, 0.28));
        background: light-dark(
            linear-gradient(135deg, #fffefb 0%, #fff6e8 55%, #ffefd6 100%),
            linear-gradient(135deg, rgba(32, 30, 48, 0.96) 0%, rgba(22, 22, 40, 0.94) 100%)
        );
        color: light-dark(var(--saju-text-readable), #ece8e0);
        font-size: max(15px, 0.95rem);
        line-height: 1.62;
        box-shadow: light-dark(0 6px 20px rgba(35, 26, 18, 0.06), 0 8px 24px rgba(0, 0, 0, 0.28));
    }
    .saju-step7-question-guide .saju-guide-warn {
        color: light-dark(#b91c1c, #fbbf24);
        font-weight: 800;
    }
    .saju-privacy-disclosure {
        background: light-dark(
            linear-gradient(135deg, rgba(255, 254, 251, 0.98) 0%, rgba(255, 248, 236, 0.96) 100%),
            rgba(37, 32, 24, 0.82)
        ) !important;
        color: light-dark(var(--saju-text-readable), rgba(245, 239, 226, 0.96)) !important;
    }
    @media (max-width: 768px) {
        .stApp {
            background-color: light-dark(var(--saju-bg-canvas-light), var(--saju-bg-canvas-dark)) !important;
            background-image: light-dark(
                linear-gradient(180deg, #fcfaf7 0%, #f5f1ea 52%, #efeae2 100%),
                linear-gradient(180deg, #0c0c16 0%, #0a0a12 100%)
            ) !important;
        }
        .main .block-container::before {
            display: none !important;
        }
        div[class*="st-key-saju_analysis_card"]::after {
            opacity: 0 !important;
        }
        div[class*="st-key-saju_analysis_card"] {
            background: light-dark(
                linear-gradient(160deg, #fdfcfa 0%, #f6f2eb 100%),
                linear-gradient(135deg, #1c1c30 0%, #141b2a 100%)
            ) !important;
            color: light-dark(var(--saju-text-readable), #ece8e0) !important;
        }
        .main [data-testid="stMarkdownContainer"] p,
        .main [data-testid="stMarkdownContainer"] li,
        .main [data-testid="stMarkdownContainer"] span {
            color: light-dark(#1a1208, #f0ece4) !important;
            text-shadow: light-dark(0 1px 0 rgba(255, 255, 255, 0.35), none);
        }
        .stTextArea textarea {
            background: light-dark(#ffffff, rgba(30, 30, 48, 0.95)) !important;
        }
    }

    /* ===== 전역 최종 우선: 이동·안내 버튼 — 연한 피치 칩 ===== */
    .stApp .stButton > button,
    .stApp .stButton > button[kind="primary"],
    .stApp .stButton > button[kind="secondary"],
    .stApp .stButton > button[data-testid="baseButton-primary"],
    .stApp .stButton > button[data-testid="baseButton-secondary"],
    .stApp [data-testid="stFormSubmitButton"] > button,
    .stApp .stFormSubmitButton > button,
    .stApp .stLinkButton > a,
    .stApp .stDownloadButton > button,
    .stApp .stDownloadButton > button[kind="primary"],
    .stApp .stDownloadButton > button[kind="secondary"],
    .stApp .stDownloadButton > button[data-testid="baseButton-primary"],
    .stApp .stDownloadButton > button[data-testid="baseButton-secondary"],
    .stApp div[data-testid="stBaseButton-primary"],
    .stApp div[data-testid="stBaseButton-secondary"],
    .st-key-saju_bottom_prev_next_row .stButton > button,
    .st-key-saju_bottom_quick_menu_panel .stButton > button,
    .st-key-saju_global_bottom_chrome [data-testid="stExpander"] .stButton > button,
    .st-key-step1_menu_grid .stButton > button,
    .st-key-step1_menu_more_row .stButton > button,
    .st-key-step1_cta_row_briefing .stButton > button,
    .st-key-step1_cta_row_main .stButton > button,
    .st-key-step1_cta_row_free .stButton > button,
    .st-key-step1_revisit_pin_row .stButton > button,
    .st-key-step3_mbti_input_row .stButton > button,
    .st-key-step7_action_row .stButton > button,
    .st-key-step6_today_pick_row .stButton > button,
    .st-key-step2_save_gold_wrap .stButton > button,
    .st-key-step2_cal_orb_row .stButton > button,
    div[class*="st-key-step11_consult_strip"] .stButton > button,
    div[class*="st-key-step11_consult_strip"] .stLinkButton > a {
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        filter: none !important;
        border-radius: var(--saju-soft-radius) !important;
        color: light-dark(rgba(45, 38, 28, 0.92), rgba(235, 228, 210, 0.94)) !important;
        -webkit-text-fill-color: light-dark(rgba(45, 38, 28, 0.92), rgba(235, 228, 210, 0.94)) !important;
    }
    .stApp .stDownloadButton > button p,
    .stApp .stDownloadButton > button span,
    .stApp .stDownloadButton > button div {
        color: inherit !important;
        -webkit-text-fill-color: inherit !important;
        opacity: 1 !important;
    }
    .stApp .stButton > button[kind="primary"],
    .stApp .stButton > button[data-testid="baseButton-primary"] {
        background: light-dark(var(--saju-soft-fill-hover), var(--saju-soft-fill-dark-hover)) !important;
    }
    .stApp .stDownloadButton > button[kind="primary"],
    .stApp .stDownloadButton > button[data-testid="baseButton-primary"] {
        background: light-dark(var(--saju-soft-fill-hover), var(--saju-soft-fill-dark-hover)) !important;
        color: light-dark(#6b520f, #f5e6a8) !important;
        -webkit-text-fill-color: light-dark(#6b520f, #f5e6a8) !important;
    }
    .stApp .stButton > button[kind="primary"]:hover,
    .stApp .stButton > button[kind="secondary"]:hover,
    .stApp .stButton > button[data-testid="baseButton-primary"]:hover,
    .stApp .stButton > button[data-testid="baseButton-secondary"]:hover,
    .stApp .stLinkButton > a:hover,
    .stApp .stDownloadButton > button:hover {
        background: light-dark(var(--saju-soft-fill-hover), var(--saju-soft-fill-dark-hover)) !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        color: light-dark(#2a2218, #f5f0e6) !important;
        -webkit-text-fill-color: light-dark(#2a2218, #f5f0e6) !important;
    }
    html.saju-dark-tone .stApp .stButton > button,
    html.saju-dark-tone .stApp .stButton > button[kind="primary"],
    html.saju-dark-tone .stApp .stButton > button[kind="secondary"],
    html.saju-dark-tone .stApp .stLinkButton > a,
    html.saju-dark-tone .stApp .stDownloadButton > button {
        border: none !important;
        box-shadow: none !important;
        background: var(--saju-soft-fill-dark) !important;
        filter: none !important;
    }
    [data-testid="stExpander"] summary,
    .st-key-saju_global_bottom_chrome [data-testid="stExpander"] summary {
        border: none !important;
        border-bottom: none !important;
        box-shadow: none !important;
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        border-radius: var(--saju-soft-radius) !important;
    }
    [data-testid="stExpander"] details,
    .st-key-saju_global_bottom_chrome [data-testid="stExpander"] details {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }
    .saju-step-dock-html .saju-dock-a {
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: var(--saju-soft-radius) !important;
    }
    .saju-step-dock-html,
    .st-key-saju_global_prev_next {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }

    /*
     * 하단 「기능 바로가기」 — 사주분석·궁합·살풀이·오늘의 운세·주역점·타로·대운·총평(STEP3~10)
     * 적색 라벨 가독: 연한 장미/버건디 배경 + 진한 적색 글씨
     */
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_3_"] .stButton > button,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_4_"] .stButton > button,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_5_"] .stButton > button,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_6_"] .stButton > button,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_7_"] .stButton > button,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_8_"] .stButton > button,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_9_"] .stButton > button,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_10_"] .stButton > button {
        background: linear-gradient(
            165deg,
            #fff8f8 0%,
            #ffe8ea 42%,
            #ffd6da 100%
        ) !important;
        border: 1px solid rgba(185, 28, 28, 0.28) !important;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.65) inset !important;
        color: #b91c1c !important;
        -webkit-text-fill-color: #b91c1c !important;
        font-weight: 800 !important;
    }
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_3_"] .stButton > button p,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_4_"] .stButton > button p,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_5_"] .stButton > button p,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_6_"] .stButton > button p,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_7_"] .stButton > button p,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_8_"] .stButton > button p,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_9_"] .stButton > button p,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_10_"] .stButton > button p,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_3_"] .stButton > button span,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_4_"] .stButton > button span,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_5_"] .stButton > button span,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_6_"] .stButton > button span,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_7_"] .stButton > button span,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_8_"] .stButton > button span,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_9_"] .stButton > button span,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_10_"] .stButton > button span {
        color: inherit !important;
        -webkit-text-fill-color: inherit !important;
        opacity: 1 !important;
    }
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_3_"] .stButton > button[kind="primary"],
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_4_"] .stButton > button[kind="primary"],
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_5_"] .stButton > button[kind="primary"],
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_6_"] .stButton > button[kind="primary"],
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_7_"] .stButton > button[kind="primary"],
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_8_"] .stButton > button[kind="primary"],
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_9_"] .stButton > button[kind="primary"],
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_10_"] .stButton > button[kind="primary"],
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_3_"] .stButton > button[data-testid="baseButton-primary"],
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_4_"] .stButton > button[data-testid="baseButton-primary"],
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_5_"] .stButton > button[data-testid="baseButton-primary"],
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_6_"] .stButton > button[data-testid="baseButton-primary"],
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_7_"] .stButton > button[data-testid="baseButton-primary"],
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_8_"] .stButton > button[data-testid="baseButton-primary"],
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_9_"] .stButton > button[data-testid="baseButton-primary"],
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_10_"] .stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(
            165deg,
            #fecdd3 0%,
            #fda4af 55%,
            #fb7185 100%
        ) !important;
        border-color: rgba(127, 29, 29, 0.45) !important;
        color: #7f1d1d !important;
        -webkit-text-fill-color: #7f1d1d !important;
    }
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_3_"] .stButton > button:hover,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_4_"] .stButton > button:hover,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_5_"] .stButton > button:hover,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_6_"] .stButton > button:hover,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_7_"] .stButton > button:hover,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_8_"] .stButton > button:hover,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_9_"] .stButton > button:hover,
    .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_10_"] .stButton > button:hover {
        background: linear-gradient(
            165deg,
            #ffe4e6 0%,
            #fecdd3 100%
        ) !important;
        color: #991b1b !important;
        -webkit-text-fill-color: #991b1b !important;
    }
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_3_"] .stButton > button,
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_4_"] .stButton > button,
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_5_"] .stButton > button,
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_6_"] .stButton > button,
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_7_"] .stButton > button,
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_8_"] .stButton > button,
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_9_"] .stButton > button,
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_10_"] .stButton > button {
        background: linear-gradient(
            165deg,
            #4a1820 0%,
            #351016 52%,
            #280c12 100%
        ) !important;
        border-color: rgba(252, 165, 165, 0.32) !important;
        box-shadow: 0 1px 0 rgba(255, 255, 255, 0.06) inset !important;
        color: #fecaca !important;
        -webkit-text-fill-color: #fecaca !important;
    }
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_3_"] .stButton > button[kind="primary"],
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_4_"] .stButton > button[kind="primary"],
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_5_"] .stButton > button[kind="primary"],
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_6_"] .stButton > button[kind="primary"],
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_7_"] .stButton > button[kind="primary"],
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_8_"] .stButton > button[kind="primary"],
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_9_"] .stButton > button[kind="primary"],
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_10_"] .stButton > button[kind="primary"],
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_3_"] .stButton > button[data-testid="baseButton-primary"],
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_4_"] .stButton > button[data-testid="baseButton-primary"],
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_5_"] .stButton > button[data-testid="baseButton-primary"],
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_6_"] .stButton > button[data-testid="baseButton-primary"],
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_7_"] .stButton > button[data-testid="baseButton-primary"],
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_8_"] .stButton > button[data-testid="baseButton-primary"],
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_9_"] .stButton > button[data-testid="baseButton-primary"],
    html.saju-dark-tone .st-key-saju_bottom_quick_grid_2col [class*="st-key-saju_bottom_nav_10_"] .stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(
            165deg,
            #6b1d2a 0%,
            #5c1a22 55%,
            #451318 100%
        ) !important;
        border-color: rgba(254, 202, 202, 0.42) !important;
        color: #fff1f2 !important;
        -webkit-text-fill-color: #fff1f2 !important;
    }

    /* STEP2 성함·연락처: 년·월·일과 동일 연한 피치(내부 input·baseweb 포함) */
    .stApp .st-key-step2_navertone_self .stTextInput > div > div,
    .stApp .st-key-step2_navertone_opp .stTextInput > div > div,
    .stApp .st-key-step2_navertone_self .stTextInput [data-baseweb="input"],
    .stApp .st-key-step2_navertone_opp .stTextInput [data-baseweb="input"],
    .stApp .st-key-step2_navertone_self .stTextInput [data-baseweb="input"] > div,
    .stApp .st-key-step2_navertone_opp .stTextInput [data-baseweb="input"] > div,
    .stApp .st-key-step2_navertone_self .stTextInput [data-baseweb="base-input"],
    .stApp .st-key-step2_navertone_opp .stTextInput [data-baseweb="base-input"],
    .stApp .st-key-step2_navertone_self .stTextInput input,
    .stApp .st-key-step2_navertone_opp .stTextInput input,
    .stApp .st-key-step2_navertone_self [data-testid="stTextInputRootElement"],
    .stApp .st-key-step2_navertone_opp [data-testid="stTextInputRootElement"] {
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: var(--saju-soft-radius) !important;
    }
    html.saju-dark-tone .stApp .st-key-step2_navertone_self .stTextInput input:-webkit-autofill,
    html.saju-dark-tone .stApp .st-key-step2_navertone_opp .stTextInput input:-webkit-autofill {
        -webkit-box-shadow: 0 0 0 1000px rgba(40, 36, 32, 0.88) inset !important;
        box-shadow: 0 0 0 1000px rgba(40, 36, 32, 0.88) inset !important;
    }
    /* 성함·연락처 위젯 키(컨테이너 밖 클래스에도 동일 적용) */
    .stApp .st-key-step2_self_name_input .stTextInput > div > div,
    .stApp .st-key-step2_self_name_input .stTextInput [data-baseweb="input"],
    .stApp .st-key-step2_self_name_input .stTextInput [data-baseweb="input"] > div,
    .stApp .st-key-step2_self_name_input .stTextInput [data-baseweb="base-input"],
    .stApp .st-key-step2_self_name_input .stTextInput input,
    .stApp .st-key-u_contact .stTextInput > div > div,
    .stApp .st-key-u_contact .stTextInput [data-baseweb="input"],
    .stApp .st-key-u_contact .stTextInput [data-baseweb="input"] > div,
    .stApp .st-key-u_contact .stTextInput [data-baseweb="base-input"],
    .stApp .st-key-u_contact .stTextInput input,
    .stApp .st-key-p_name .stTextInput > div > div,
    .stApp .st-key-p_name .stTextInput input {
        background: light-dark(var(--saju-soft-fill), var(--saju-soft-fill-dark)) !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: var(--saju-soft-radius) !important;
    }
    .stApp .st-key-step2_self_name_input .stTextInput > div > div,
    .stApp .st-key-u_contact .stTextInput > div > div {
        min-height: 3.3rem !important;
        padding-left: 0.55rem !important;
        padding-right: 0.55rem !important;
    }

    /* Streamlit date_input 달력: 요일 Su~Sa · 월 1월~12월 (JS + CSS 이중 고정) */
    [data-baseweb="popover"] [data-baseweb="calendar"],
    [data-baseweb="datepicker"] [data-baseweb="calendar"],
    body > div [data-baseweb="calendar"] {
        font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif !important;
        letter-spacing: 0 !important;
        word-spacing: 0 !important;
    }
    [data-baseweb="calendar"] [role="grid"] [role="row"]:first-child {
        display: grid !important;
        grid-template-columns: repeat(7, minmax(2.1rem, 1fr)) !important;
        gap: 0 !important;
    }
    [data-baseweb="calendar"] [data-baseweb="calendar-header"] > div,
    [data-baseweb="calendar"] [role="grid"] [role="row"]:first-child [role="columnheader"] {
        position: relative !important;
        box-sizing: border-box !important;
        min-width: 2.1rem !important;
        padding: 0.1rem 0 !important;
        margin: 0 !important;
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
        content: "" !important;
        display: block !important;
        font-size: 0.72rem !important;
        line-height: 1.25 !important;
        font-weight: 600 !important;
        color: light-dark(#334155, #e2e8f0) !important;
        text-indent: 0 !important;
        text-align: center !important;
        letter-spacing: 0 !important;
        white-space: nowrap !important;
    }
    [data-baseweb="calendar"] [data-baseweb="calendar-header"] > div:nth-child(1)::after,
    [data-baseweb="calendar"] [role="grid"] [role="row"]:first-child [role="columnheader"]:nth-child(1)::after {
        content: "Su" !important;
    }
    [data-baseweb="calendar"] [data-baseweb="calendar-header"] > div:nth-child(2)::after,
    [data-baseweb="calendar"] [role="grid"] [role="row"]:first-child [role="columnheader"]:nth-child(2)::after {
        content: "Mo" !important;
    }
    [data-baseweb="calendar"] [data-baseweb="calendar-header"] > div:nth-child(3)::after,
    [data-baseweb="calendar"] [role="grid"] [role="row"]:first-child [role="columnheader"]:nth-child(3)::after {
        content: "Tu" !important;
    }
    [data-baseweb="calendar"] [data-baseweb="calendar-header"] > div:nth-child(4)::after,
    [data-baseweb="calendar"] [role="grid"] [role="row"]:first-child [role="columnheader"]:nth-child(4)::after {
        content: "We" !important;
    }
    [data-baseweb="calendar"] [data-baseweb="calendar-header"] > div:nth-child(5)::after,
    [data-baseweb="calendar"] [role="grid"] [role="row"]:first-child [role="columnheader"]:nth-child(5)::after {
        content: "Th" !important;
    }
    [data-baseweb="calendar"] [data-baseweb="calendar-header"] > div:nth-child(6)::after,
    [data-baseweb="calendar"] [role="grid"] [role="row"]:first-child [role="columnheader"]:nth-child(6)::after {
        content: "Fr" !important;
    }
    [data-baseweb="calendar"] [data-baseweb="calendar-header"] > div:nth-child(7)::after,
    [data-baseweb="calendar"] [role="grid"] [role="row"]:first-child [role="columnheader"]:nth-child(7)::after {
        content: "Sa" !important;
    }
    [data-baseweb="calendar"] [data-saju-weekday]::after {
        content: attr(data-saju-weekday) !important;
    }
    [data-baseweb="popover"] [role="option"][data-saju-month-num],
    [data-baseweb="select-dropdown"] [role="option"][data-saju-month-num],
    [data-baseweb="option"][data-saju-month-num],
    li[data-baseweb="option"][data-saju-month-num] {
        font-size: 0 !important;
        line-height: 0 !important;
        color: transparent !important;
        position: relative !important;
        min-height: 1.35rem !important;
    }
    [data-baseweb="popover"] [role="option"][data-saju-month-num]::after,
    [data-baseweb="select-dropdown"] [role="option"][data-saju-month-num]::after,
    [data-baseweb="option"][data-saju-month-num]::after,
    li[data-baseweb="option"][data-saju-month-num]::after {
        display: block !important;
        font-size: 0.88rem !important;
        line-height: 1.35 !important;
        font-weight: 500 !important;
        color: light-dark(#334155, #e2e8f0) !important;
        text-align: center !important;
        text-indent: 0 !important;
        letter-spacing: 0 !important;
        white-space: nowrap !important;
    }
    [role="option"][data-saju-month-num="1"]::after,
    [data-baseweb="option"][data-saju-month-num="1"]::after { content: "1월" !important; }
    [role="option"][data-saju-month-num="2"]::after,
    [data-baseweb="option"][data-saju-month-num="2"]::after { content: "2월" !important; }
    [role="option"][data-saju-month-num="3"]::after,
    [data-baseweb="option"][data-saju-month-num="3"]::after { content: "3월" !important; }
    [role="option"][data-saju-month-num="4"]::after,
    [data-baseweb="option"][data-saju-month-num="4"]::after { content: "4월" !important; }
    [role="option"][data-saju-month-num="5"]::after,
    [data-baseweb="option"][data-saju-month-num="5"]::after { content: "5월" !important; }
    [role="option"][data-saju-month-num="6"]::after,
    [data-baseweb="option"][data-saju-month-num="6"]::after { content: "6월" !important; }
    [role="option"][data-saju-month-num="7"]::after,
    [data-baseweb="option"][data-saju-month-num="7"]::after { content: "7월" !important; }
    [role="option"][data-saju-month-num="8"]::after,
    [data-baseweb="option"][data-saju-month-num="8"]::after { content: "8월" !important; }
    [role="option"][data-saju-month-num="9"]::after,
    [data-baseweb="option"][data-saju-month-num="9"]::after { content: "9월" !important; }
    [role="option"][data-saju-month-num="10"]::after,
    [data-baseweb="option"][data-saju-month-num="10"]::after { content: "10월" !important; }
    [role="option"][data-saju-month-num="11"]::after,
    [data-baseweb="option"][data-saju-month-num="11"]::after { content: "11월" !important; }
    [role="option"][data-saju-month-num="12"]::after,
    [data-baseweb="option"][data-saju-month-num="12"]::after { content: "12월" !important; }
    [data-baseweb="calendar"] [data-baseweb="day"] {
        letter-spacing: 0 !important;
    }

    /* 모바일 STEP1 홈 — 사진2: 히어로 최상단 + 절기 카드(상단 빈 여백·겹침 방지) */
    @media (max-width: 768px) {
        /* STEP2~: 홈 마운트·랜딩 잔존 시 사진1(겹침·빈 여백) 차단 */
        html.saju-not-step1 .st-key-saju_router_step_mount_01,
        html[data-saju-step]:not([data-saju-step="1"]) .st-key-saju_router_step_mount_01,
        html.saju-not-step1 .st-key-saju_landing_stack,
        html.saju-not-step1 .st-key-saju_landing_hero,
        html.saju-not-step1 .st-key-step1_solar24,
        html.saju-not-step1 .saju-landing-hero,
        html[data-saju-step]:not([data-saju-step="1"]) .st-key-saju_landing_stack,
        html[data-saju-step]:not([data-saju-step="1"]) .st-key-saju_landing_hero,
        html[data-saju-step]:not([data-saju-step="1"]) .st-key-step1_solar24,
        html[data-saju-step]:not([data-saju-step="1"]) .saju-landing-hero {
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
        html.saju-home-step1,
        html[data-saju-step="1"] {
            scroll-padding-top: 0 !important;
        }
        html.saju-home-step1 [data-testid="stAppViewContainer"],
        html[data-saju-step="1"] [data-testid="stAppViewContainer"] {
            overflow-y: auto !important;
            -webkit-overflow-scrolling: touch !important;
            touch-action: pan-y !important;
        }
        html.saju-home-step1 [data-testid="stAppViewContainer"],
        html[data-saju-step="1"] [data-testid="stAppViewContainer"],
        html.saju-home-step1 [data-testid="stMain"],
        html[data-saju-step="1"] [data-testid="stMain"],
        html.saju-home-step1 section.main,
        html[data-saju-step="1"] section.main {
            scroll-padding-top: 0 !important;
        }
        html.saju-home-step1 .main .block-container,
        html[data-saju-step="1"] .main .block-container {
            padding-top: 0 !important;
            margin-top: 0 !important;
            min-height: 0 !important;
        }
        html.saju-home-step1 .st-key-saju_router_step_mount_01,
        html[data-saju-step="1"] .st-key-saju_router_step_mount_01 {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        html.saju-home-step1 #saju-step-top-anchor,
        html[data-saju-step="1"] #saju-step-top-anchor {
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        html.saju-home-step1 .st-key-saju_landing_stack,
        html[data-saju-step="1"] .st-key-saju_landing_stack {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        html.saju-home-step1 .st-key-saju_landing_hero,
        html[data-saju-step="1"] .st-key-saju_landing_hero {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        html.saju-home-step1 .saju-landing-hero.saju-landing-hero--nova,
        html[data-saju-step="1"] .saju-landing-hero.saju-landing-hero--nova {
            display: flex !important;
            flex-direction: column !important;
            justify-content: flex-start !important;
            max-height: min(38vh, 340px) !important;
            min-height: 0 !important;
            overflow: hidden !important;
            margin-top: 0 !important;
            padding-top: max(0.35rem, env(safe-area-inset-top, 0px)) !important;
        }
        html.saju-home-step1 .st-key-step1_solar24,
        html[data-saju-step="1"] .st-key-step1_solar24 {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            margin-top: 0.15rem !important;
            overflow: visible !important;
            position: relative !important;
            left: auto !important;
            height: auto !important;
        }
        html.saju-home-step1 .st-key-step1_solar24 [data-testid="stHtml"],
        html[data-saju-step="1"] .st-key-step1_solar24 [data-testid="stHtml"],
        html.saju-home-step1 .st-key-step1_solar24 iframe,
        html[data-saju-step="1"] .st-key-step1_solar24 iframe {
            min-height: 600px !important;
            max-height: none !important;
            height: auto !important;
            overflow: visible !important;
        }
        html.saju-home-step1 .st-key-step1_solar24 [data-testid="stCustomComponentV1"],
        html[data-saju-step="1"] .st-key-step1_solar24 [data-testid="stCustomComponentV1"] {
            min-height: 600px !important;
            overflow: visible !important;
        }
        /* 사진2 고정 — html STEP 동기화 전에도 STEP1 마운트 기준(외부 모바일·Cloud) */
        .st-key-saju_router_step_mount_01 .saju-landing-hero.saju-landing-hero--nova,
        .st-key-saju_router_step_mount_01 .saju-landing-hero--luxe.saju-landing-hero--intense {
            display: flex !important;
            flex-direction: column !important;
            justify-content: flex-start !important;
            max-height: min(38vh, 340px) !important;
            min-height: 0 !important;
            overflow: hidden !important;
            margin-top: 0 !important;
            padding-top: max(0.35rem, env(safe-area-inset-top, 0px)) !important;
        }
        .st-key-saju_router_step_mount_01 .st-key-step1_solar24 {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: relative !important;
            left: auto !important;
            top: auto !important;
            height: auto !important;
            margin-top: 0.12rem !important;
            overflow: visible !important;
            pointer-events: auto !important;
        }
        .st-key-saju_router_step_mount_01 .st-key-step1_solar24 iframe,
        .st-key-saju_router_step_mount_01 .st-key-step1_solar24 [data-testid="stHtml"],
        .st-key-saju_router_step_mount_01 .st-key-step1_solar24 [data-testid="stCustomComponentV1"] {
            display: block !important;
            visibility: visible !important;
            min-height: 580px !important;
            max-height: none !important;
            height: auto !important;
            overflow: visible !important;
        }
        /* 사진2: 히어로 배너를 뷰포트 최상단에 밀착(상단 빈 여백 제거) */
        html.saju-home-step1 #saju-step-top-anchor,
        html[data-saju-step="1"] #saju-step-top-anchor,
        html.saju-home-step1 #saju-step-active-top,
        html[data-saju-step="1"] #saju-step-active-top,
        .st-key-saju_router_step_mount_01 #saju-step-active-top {
            display: none !important;
            height: 0 !important;
            max-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
            scroll-margin: 0 !important;
        }
        html.saju-home-step1 .st-key-saju_landing_hero .saju-landing-hero,
        html[data-saju-step="1"] .st-key-saju_landing_hero .saju-landing-hero,
        .st-key-saju_router_step_mount_01 .saju-landing-hero--nova {
            justify-content: flex-start !important;
            align-items: center !important;
            min-height: 0 !important;
            margin-top: 0 !important;
            padding-top: max(0.1rem, env(safe-area-inset-top, 0px)) !important;
        }
        html.saju-home-step1 .main .block-container:has(.st-key-saju_landing_hero),
        html[data-saju-step="1"] .main .block-container:has(.st-key-saju_landing_hero) {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        html.saju-home-step1 .st-key-saju_landing_hero [data-testid="stElementContainer"],
        html[data-saju-step="1"] .st-key-saju_landing_hero [data-testid="stElementContainer"],
        html.saju-home-step1 .st-key-saju_landing_hero [data-testid="stVerticalBlock"],
        html[data-saju-step="1"] .st-key-saju_landing_hero [data-testid="stVerticalBlock"],
        html.saju-home-step1 .st-key-saju_landing_hero [data-testid="stMarkdownContainer"],
        html[data-saju-step="1"] .st-key-saju_landing_hero [data-testid="stMarkdownContainer"] {
            margin-top: 0 !important;
            padding-top: 0 !important;
            min-height: 0 !important;
        }
    }
    /*
     * 모바일 홈 배너 최상단 — :has()·플랫폼 클래스 없이 STEP1 마운트만으로 적용
     * (삼성 인터넷 등 :has 미지원·세로 중앙정렬 시 상단 대량 여백 방지)
     */
    @media (max-width: 768px) {
        .st-key-saju_step_top_anchor,
        .st-key-saju_step_top_anchor [data-testid="stElementContainer"],
        .st-key-saju_step_top_anchor [data-testid="stVerticalBlock"] {
            display: none !important;
            height: 0 !important;
            max-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
            visibility: hidden !important;
        }
        html.saju-home-step1 .st-key-saju_step_top_anchor,
        html[data-saju-step="1"] .st-key-saju_step_top_anchor {
            display: none !important;
        }
        .stApp [data-testid="stAppViewContainer"],
        .stApp [data-testid="stAppViewContainer"] > .main,
        .stApp section.main,
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"] {
            display: flex !important;
            flex-direction: column !important;
            justify-content: flex-start !important;
            align-items: stretch !important;
            align-content: flex-start !important;
            min-height: 0 !important;
            height: auto !important;
            max-height: none !important;
            margin-top: 0 !important;
            padding-top: 0 !important;
            flex: none !important;
        }
        .stApp [data-testid="stAppViewContainer"] {
            display: block !important;
            flex: none !important;
            overflow-y: auto !important;
        }
        .st-key-saju_router_step_mount_01 .st-key-saju_landing_hero {
            display: block !important;
            order: 0 !important;
            margin-top: 0 !important;
            padding-top: 0 !important;
            transform: none !important;
        }
        .st-key-saju_router_step_mount_01 .st-key-saju_landing_stack {
            display: block !important;
            order: 1 !important;
            margin-top: 0 !important;
            padding-top: 0 !important;
            transform: none !important;
        }
        .st-key-saju_router_step_mount_01 [data-testid="stVerticalBlock"] {
            display: flex !important;
            flex-direction: column !important;
            justify-content: flex-start !important;
            align-items: stretch !important;
            min-height: 0 !important;
        }
        .stApp .main .block-container {
            padding-top: 0 !important;
            margin-top: 0 !important;
            min-height: 0 !important;
        }
        /* mount 이전 유틸 iframe·동기화 블록 — 상단 빈 공간 방지 */
        .main .block-container [data-testid="stElementContainer"]:has(
            [class*="st-key-saju_browser_"]
        ),
        .main .block-container [data-testid="stElementContainer"]:has(
            [class*="st-key-saju_step_html_sync"]
        ),
        .main .block-container [data-testid="stElementContainer"]:has(
            [class*="st-key-saju_scroll_"]
        ),
        .main .block-container [data-testid="stElementContainer"]:has(
            [class*="st-key-saju_home_"]
        ) {
            display: none !important;
            height: 0 !important;
            max-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
            visibility: hidden !important;
        }
        .st-key-saju_router_step_mount_01,
        .st-key-saju_router_step_mount_01 [data-testid="stVerticalBlock"],
        .st-key-saju_router_step_mount_01 [data-testid="stElementContainer"] {
            margin-top: 0 !important;
            padding-top: 0 !important;
            gap: 0 !important;
            row-gap: 0 !important;
        }
        .st-key-saju_router_step_mount_01 .st-key-saju_landing_stack,
        .st-key-saju_router_step_mount_01 .st-key-saju_landing_stack [data-testid="stVerticalBlock"],
        .st-key-saju_router_step_mount_01 .st-key-saju_landing_stack [data-testid="stElementContainer"],
        .st-key-saju_router_step_mount_01 .st-key-saju_landing_stack [data-testid="stMarkdownContainer"] {
            margin-top: 0 !important;
            padding-top: 0 !important;
            min-height: 0 !important;
        }
        #saju-home-hero-top:not(.saju-home-hero-banner),
        .st-key-saju_router_step_mount_01 .saju-landing-hero--nova,
        .st-key-saju_router_step_mount_01 .saju-landing-hero--luxe {
            box-sizing: border-box !important;
            justify-content: flex-start !important;
            align-items: center !important;
            min-height: 0 !important;
            max-height: min(40vh, 360px) !important;
            margin-top: 0 !important;
            margin-left: -0.45rem !important;
            margin-right: -0.45rem !important;
            width: calc(100% + 0.9rem) !important;
            max-width: none !important;
            padding-top: max(0.06rem, env(safe-area-inset-top, 0px)) !important;
            padding-bottom: 0.5rem !important;
            border-radius: 0 0 clamp(16px, 4.5vw, 20px) clamp(16px, 4.5vw, 20px) !important;
        }
        .st-key-saju_router_step_mount_01 .saju-landing-hero {
            justify-content: flex-start !important;
            min-height: 0 !important;
        }
    }
    /* 모바일 안정화 — 과한 애니메이션·스크롤 튐 방지 */
    html.saju-mobile-stable .saju-landing-hero--nova,
    html.saju-mobile-stable .saju-landing-hero--nova *,
    html.saju-mobile-stable .saju-landing-hero--luxe {
        animation: none !important;
        transition: none !important;
    }
    html.saju-mobile-stable [data-testid="stAppViewContainer"],
    html.saju-mobile-stable [data-testid="stMain"],
    html.saju-mobile-stable section.main {
        scroll-behavior: auto !important;
        overscroll-behavior-y: auto !important;
    }

    /* 홈 STEP1 — PC: 사진 배너 전체 표시 (잘림 방지) */
    @media (min-width: 769px) {
        .st-key-saju_router_step_mount_01 .saju-home-hero-banner.saju-landing-hero--photo,
        .st-key-saju_router_step_mount_01 #saju-home-hero-top.saju-home-hero-banner {
            max-height: none !important;
            overflow: visible !important;
        }
        .st-key-saju_router_step_mount_01 .saju-home-hero-banner.saju-landing-hero--photo,
        .st-key-saju_router_step_mount_01 #saju-home-hero-top.saju-home-hero-banner {
            width: 100% !important;
            max-width: min(100%, 560px) !important;
            margin-left: auto !important;
            margin-right: auto !important;
        }
        .st-key-saju_router_step_mount_01 .saju-home-hero-banner.saju-landing-hero--photo img,
        #saju-home-hero-top.saju-home-hero-banner img {
            width: 100% !important;
            max-width: 560px !important;
            height: auto !important;
            max-height: min(52vh, 520px) !important;
            object-fit: contain !important;
            object-position: center center !important;
            margin: 0 auto !important;
            border-radius: clamp(16px, 2vw, 22px) !important;
        }
    }

    /* 홈 STEP1 — 사진2: 배너 최상단 (flex-center·100vh 밀림 방지, 최종 우선) */
    @media (max-width: 768px) {
        .st-key-saju_router_step_mount_01 {
            display: block !important;
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        .st-key-saju_router_step_mount_01 .st-key-saju_landing_hero,
        .st-key-saju_router_step_mount_01 #saju-home-hero-top,
        .st-key-saju_router_step_mount_01 .saju-home-hero-banner {
            display: block !important;
            position: relative !important;
            top: 0 !important;
            margin-top: 0 !important;
            padding-top: max(0.06rem, env(safe-area-inset-top, 0px)) !important;
            transform: none !important;
        }
        /* 배너를 아래 24절기 카드 폭에 맞추고(좌우 패딩 동일), 가로·세로로 키운다 */
        .st-key-saju_router_step_mount_01 .saju-home-hero-banner.saju-landing-hero--photo,
        .st-key-saju_router_step_mount_01 #saju-home-hero-top.saju-home-hero-banner,
        .st-key-saju_router_step_mount_01 .saju-home-hero-banner__figure {
            width: 100% !important;
            max-width: min(100vw, 520px) !important;
            margin-left: auto !important;
            margin-right: auto !important;
            padding: 0 clamp(0.35rem, 2vw, 1rem) !important;
            overflow: visible !important;
            box-sizing: border-box !important;
        }
        .st-key-saju_router_step_mount_01 .saju-home-hero-banner.saju-landing-hero--photo img,
        #saju-home-hero-top.saju-home-hero-banner img {
            display: block !important;
            width: 100% !important;
            max-width: 520px !important;
            height: auto !important;
            max-height: min(48vh, 320px) !important;
            object-fit: cover !important;
            object-position: center center !important;
            margin: 0 auto !important;
            vertical-align: top !important;
            /* 아래 카드처럼 4면 모두 둥글게 */
            border-radius: clamp(16px, 4.5vw, 20px) !important;
        }
        .st-key-saju_router_step_mount_01 .st-key-saju_landing_stack {
            margin-top: 0 !important;
            padding-top: 0 !important;
            transform: none !important;
        }
    }

    /* 홈 STEP1 — Chrome·삼성·카카오·PC 공통: 상단 빈 여백 제거(세로 가운데 정렬 차단) */
    html.saju-home-step1,
    html[data-saju-step="1"] {
        scroll-padding-top: 0 !important;
    }
    html.saju-home-step1 body,
    html[data-saju-step="1"] body {
        display: block !important;
        min-height: 0 !important;
        height: auto !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    html.saju-home-step1,
    html[data-saju-step="1"] {
        min-height: 0 !important;
        height: auto !important;
    }
    html.saju-home-step1 .stApp,
    html[data-saju-step="1"] .stApp,
    html.saju-home-step1 [data-testid="stAppViewContainer"],
    html[data-saju-step="1"] [data-testid="stAppViewContainer"],
    html.saju-home-step1 [data-testid="stAppViewContainer"] > .main,
    html[data-saju-step="1"] [data-testid="stAppViewContainer"] > .main,
    html.saju-home-step1 section.main,
    html[data-saju-step="1"] section.main,
    html.saju-home-step1 [data-testid="stMain"],
    html[data-saju-step="1"] [data-testid="stMain"],
    html.saju-home-step1 [data-testid="stMainBlockContainer"],
    html[data-saju-step="1"] [data-testid="stMainBlockContainer"],
    html.saju-home-step1 .main .block-container,
    html[data-saju-step="1"] .main .block-container,
    html.saju-home-step1 .st-key-saju_router_step_mount_01,
    html[data-saju-step="1"] .st-key-saju_router_step_mount_01 {
        display: block !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
        align-content: flex-start !important;
        min-height: 0 !important;
        height: auto !important;
        max-height: none !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
        flex: none !important;
    }
    html.saju-home-step1 .st-key-saju_router_step_mount_01 [data-testid="stVerticalBlock"],
    html[data-saju-step="1"] .st-key-saju_router_step_mount_01 [data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
        align-content: flex-start !important;
        min-height: 0 !important;
        height: auto !important;
        max-height: none !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
        flex: 0 0 auto !important;
        gap: 0 !important;
        row-gap: 0 !important;
    }
    /*
     * STEP1 — 홈 상단 공백 제거(배너+24절기 함께 스크롤)
     * 모바일 WebView(카카오/삼성)에서 inline <script>가 막히면 html class/data-saju-step가 안 붙을 수 있어
     * :has(.st-key-saju_router_step_mount_01) 기반으로도 동일 규칙을 강제합니다.
     */
    .st-key-saju_router_step_mount_01 {
        margin-top: 0 !important;
        padding-top: 0 !important;
        align-self: stretch !important;
        width: 100% !important;
        min-height: 0 !important;
    }
    .stApp:has(.st-key-saju_router_step_mount_01) .main .block-container,
    [data-testid="stAppViewContainer"]:has(.st-key-saju_router_step_mount_01) .main .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
        min-height: 0 !important;
    }
    [data-testid="stAppViewContainer"]:has(.st-key-saju_router_step_mount_01),
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"] {
        display: block !important;
        min-height: 0 !important;
        height: auto !important;
        max-height: none !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"] > .main,
    [data-testid="stAppViewContainer"]:has(.st-key-saju_router_step_mount_01) > .main {
        display: block !important;
        min-height: 0 !important;
        height: auto !important;
        max-height: none !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    .stApp:has(.st-key-saju_router_step_mount_01) section.main,
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stMain"],
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewContainer"]:has(.st-key-saju_router_step_mount_01) section.main,
    [data-testid="stAppViewContainer"]:has(.st-key-saju_router_step_mount_01) [data-testid="stMain"],
    [data-testid="stAppViewContainer"]:has(.st-key-saju_router_step_mount_01) [data-testid="stMainBlockContainer"] {
        display: block !important;
        min-height: 0 !important;
        height: auto !important;
        max-height: none !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
        padding-top: 0 !important;
        margin-top: 0 !important;
        flex: none !important;
    }
    .st-key-saju_router_step_mount_01 .st-key-saju_landing_hero {
        order: 0 !important;
        flex: 0 0 auto !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    .st-key-saju_router_step_mount_01 .st-key-saju_landing_stack {
        order: 1 !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stVerticalBlock"],
    [data-testid="stAppViewContainer"]:has(.st-key-saju_router_step_mount_01) [data-testid="stVerticalBlock"],
    .st-key-saju_router_step_mount_01 [data-testid="stElementContainer"] {
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
        align-content: flex-start !important;
        min-height: 0 !important;
        height: auto !important;
        max-height: none !important;
        flex-grow: 0 !important;
    }
    .main .block-container[data-saju-home-pulled="1"] {
        transform: none !important;
    }
    .st-key-saju_router_step_mount_01 #saju-home-hero-top.saju-home-hero-banner {
        margin-top: 0 !important;
        padding-top: max(0px, env(safe-area-inset-top, 0px)) !important;
        max-height: none !important;
        min-height: 0 !important;
    }
    html.saju-home-step1 .st-key-saju_landing_hero,
    html[data-saju-step="1"] .st-key-saju_landing_hero,
    html.saju-home-step1 #saju-home-hero-top,
    html[data-saju-step="1"] #saju-home-hero-top {
        order: 0 !important;
        margin-top: 0 !important;
        padding-top: max(0px, env(safe-area-inset-top, 0px)) !important;
    }
    html.saju-platform-kakao.saju-home-step1 .stApp,
    html.saju-platform-inapp.saju-home-step1 .stApp,
    html.saju-platform-kakao[data-saju-step="1"] .stApp,
    html.saju-platform-inapp[data-saju-step="1"] .stApp,
    html.saju-platform-android.saju-home-step1 .stApp,
    html.saju-platform-android[data-saju-step="1"] .stApp {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    /* 홈 당김 잔여(margin/transform) 제거 — 데스크톱 하단 밀림·모바일 백화 방지 */
    html.saju-home-step1 .main .block-container,
    html[data-saju-step="1"] .main .block-container,
    .st-key-saju_router_step_mount_01,
    .main .block-container[data-saju-home-pulled="1"] {
        margin-top: 0 !important;
        transform: none !important;
    }
    /* 홈 최상단 잠금 — main 체인은 block(100vh flex-center 차단), mount 내부만 column flex */
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"],
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"] > .main,
    .stApp:has(.st-key-saju_router_step_mount_01) section.main,
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stMain"],
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stMainBlockContainer"],
    .stApp:has(.st-key-saju_router_step_mount_01) .main .block-container,
    .st-key-saju_router_step_mount_01 {
        display: block !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
        align-content: flex-start !important;
        min-height: 0 !important;
        height: auto !important;
        max-height: none !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
        transform: none !important;
        flex: none !important;
    }
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"] {
        overflow-y: auto !important;
        overflow-x: hidden !important;
    }
    .st-key-saju_router_step_mount_01 [data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
        flex: 0 0 auto !important;
        min-height: 0 !important;
        order: 0 !important;
    }
    .st-key-saju_router_step_mount_01 .st-key-saju_landing_hero {
        order: 0 !important;
        flex: 0 0 auto !important;
    }
    .st-key-saju_router_step_mount_01 .st-key-saju_landing_stack {
        order: 1 !important;
        flex: 0 0 auto !important;
    }
    /* 홈 본문 표시 — landing_stack 컨테이너는 :has(.st-key-saju_landing_stack)에 자기 자신이 안 잡혀 숨김되던 문제 방지 */
    .stApp:has(.st-key-saju_router_step_mount_01) .st-key-saju_landing_hero,
    .stApp:has(.st-key-saju_router_step_mount_01) .st-key-saju_landing_stack,
    html.saju-home-step1 .st-key-saju_landing_stack,
    html[data-saju-step="1"] .st-key-saju_landing_stack,
    html.saju-home-step1 .st-key-step1_solar24,
    html[data-saju-step="1"] .st-key-step1_solar24,
    html.saju-home-step1 .st-key-step1_cta_row_main,
    html[data-saju-step="1"] .st-key-step1_cta_row_main,
    html.saju-home-step1 .st-key-step1_cta_row_free,
    html[data-saju-step="1"] .st-key-step1_cta_row_free,
    html.saju-home-step1 .st-key-saju_landing_cta,
    html[data-saju-step="1"] .st-key-saju_landing_cta {
        display: block !important;
        visibility: visible !important;
        height: auto !important;
        max-height: none !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        overflow: visible !important;
    }
    .stApp:has(.st-key-saju_router_step_mount_01) .st-key-step1_solar24 iframe {
        display: block !important;
        visibility: visible !important;
        min-height: 520px !important;
        height: auto !important;
        max-height: none !important;
        opacity: 1 !important;
    }
    html.saju-platform-galaxy .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"],
    html.saju-platform-android.saju-home-step1 [data-testid="stAppViewContainer"],
    html.saju-platform-android[data-saju-step="1"] [data-testid="stAppViewContainer"] {
        flex: none !important;
        min-height: 0 !important;
        height: auto !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
    }
    /* ===== 사진2: 배너·24절기 화면 최상단 (상단 빈 flex·mount 이전 위젯 제거) ===== */
    .stApp:has(.st-key-saju_router_step_mount_01) .main .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
        min-height: 0 !important;
        height: auto !important;
        display: block !important;
    }
    /* Streamlit: block-container > stVerticalBlock > stElementContainer (직계 EC 선택자는 무효) */
    .stApp:has(.st-key-saju_router_step_mount_01) .main .block-container > [data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
        align-content: flex-start !important;
        min-height: 0 !important;
        height: auto !important;
        gap: 0 !important;
        row-gap: 0 !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    .stApp:has(.st-key-saju_router_step_mount_01) .main .block-container
        > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:not(:has(.st-key-saju_router_step_mount_01)):not(:has(.st-key-saju_global_bottom_chrome)) {
        display: none !important;
        height: 0 !important;
        max-height: 0 !important;
        min-height: 0 !important;
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
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stMainBlockContainer"] {
        display: block !important;
        flex: none !important;
        flex-grow: 0 !important;
        min-height: 0 !important;
        height: auto !important;
        max-height: none !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
        align-content: flex-start !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    .stApp:has(.st-key-saju_router_step_mount_01) .st-key-saju_router_step_mount_01,
    .stApp:has(.st-key-saju_router_step_mount_01) .st-key-saju_landing_hero,
    .stApp:has(.st-key-saju_router_step_mount_01) .st-key-saju_landing_stack {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    /* PC·모바일 — .stApp 자체도 flex 세로 가운데 정렬 차단 */
    html:has(.st-key-saju_router_step_mount_01) .stApp,
    .stApp:has(.st-key-saju_router_step_mount_01) {
        display: block !important;
        min-height: 0 !important;
        height: auto !important;
        max-height: none !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
    }
    .stApp:has(.st-key-saju_router_step_mount_01) .main .block-container[data-saju-home-flush="1"],
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"][data-saju-home-flush="1"],
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"] > .main[data-saju-home-flush="1"] {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    /* PC·모바일 공통 — Streamlit flex 세로 가운데 정렬 차단 (상단 백화) */
    html:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"],
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"] {
        min-height: 0 !important;
        display: block !important;
        flex: none !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
        align-content: flex-start !important;
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    html:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"] > .main,
    html:has(.st-key-saju_router_step_mount_01) section.main,
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"] > .main,
    .stApp:has(.st-key-saju_router_step_mount_01) section.main,
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stMain"],
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stMainBlockContainer"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
        min-height: 0 !important;
        height: auto !important;
        max-height: none !important;
        display: block !important;
        flex: none !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
        align-content: flex-start !important;
    }
    .stApp:has(.st-key-saju_router_step_mount_01) .main .block-container[data-saju-home-flush="1"],
    .stApp:has(.st-key-saju_router_step_mount_01) .main .block-container > [data-testid="stVerticalBlock"][data-saju-home-flush="1"] {
        transform: none !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    /* 사진2 최종 — 100vh·세로 가운데 정렬로 인한 상단 백화(사진1) 차단 */
    html:has(.st-key-saju_router_step_mount_01),
    html:has(.st-key-saju_router_step_mount_01) body {
        min-height: 0 !important;
        height: auto !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    html:has(.st-key-saju_router_step_mount_01) .stApp {
        height: 100vh !important;
        height: 100dvh !important;
        max-height: 100dvh !important;
        overflow: hidden !important;
    }
    html:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"] {
        height: 100vh !important;
        height: 100dvh !important;
        max-height: 100dvh !important;
        min-height: 0 !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
    }
    html:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"] > .main,
    html:has(.st-key-saju_router_step_mount_01) section.main,
    html:has(.st-key-saju_router_step_mount_01) [data-testid="stMain"],
    html:has(.st-key-saju_router_step_mount_01) [data-testid="stMainBlockContainer"],
    .stApp:has(.st-key-saju_router_step_mount_01) .main .block-container {
        display: block !important;
        flex: none !important;
        flex-grow: 0 !important;
        min-height: 0 !important;
        height: auto !important;
        max-height: none !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
        align-content: flex-start !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    .stApp:has(.st-key-saju_router_step_mount_01) .main .block-container {
        padding-left: 0 !important;
        padding-right: 0 !important;
        max-width: 100% !important;
    }
    html:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"] {
        overflow-y: auto !important;
        overflow-x: hidden !important;
    }
    /* 사진2 최종 잠금 — block-container 세로 가운데 정렬·100vh 밀림 제거 */
    .stApp:has(.st-key-saju_router_step_mount_01) .main .block-container,
    .stApp:has(.st-key-saju_router_step_mount_01) .main .block-container > [data-testid="stVerticalBlock"],
    .stApp:has(.st-key-saju_router_step_mount_01) .main .block-container > [data-testid="stVerticalBlockBorderWrapper"],
    .st-key-saju_router_step_mount_01,
    .st-key-saju_router_step_mount_01 .st-key-saju_landing_hero,
    .st-key-saju_router_step_mount_01 .st-key-saju_landing_stack {
        min-height: 0 !important;
        height: auto !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
        justify-content: flex-start !important;
        align-content: flex-start !important;
    }
    .st-key-saju_router_step_mount_01 .st-key-saju_landing_stack {
        margin-top: 0 !important;
        padding-top: 0 !important;
        gap: 0 !important;
    }
    /* 홈 — 라우터 뒤에 붙는 browser/privacy iframe 이 레이아웃 높이를 만들지 않게 */
    .st-key-saju_browser_nav_check,
    .st-key-saju_browser_privacy_client_v2,
    [class*="st-key-saju_home_viewport_lock_"] {
        position: absolute !important;
        left: -99999px !important;
        top: 0 !important;
        width: 0 !important;
        height: 0 !important;
        max-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
        visibility: hidden !important;
        pointer-events: none !important;
        opacity: 0 !important;
    }
    /* 사진2 — 배너 위 빈 여백 제거(핵심).
       마운트 '이전'에 렌더되는 bootstrap util 블록(<style>/<script> 전용 st.markdown)은
       보이지 않아도 block-container 의 flex 슬롯·row-gap 을 차지해 배너를 아래로 밀어낸다.
       해당 util element container 만 flow 에서 제거하고, 루트 수직 블록 gap 을 0 으로 잠근다. */
    .stApp:has(.st-key-saju_router_step_mount_01) .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(style),
    .stApp:has(.st-key-saju_router_step_mount_01) .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(script),
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(style),
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(script) {
        display: none !important;
        height: 0 !important;
        max-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
        visibility: hidden !important;
    }
    .stApp:has(.st-key-saju_router_step_mount_01) .main .block-container > [data-testid="stVerticalBlock"],
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {
        gap: 0 !important;
        row-gap: 0 !important;
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    /* 전체 STEP 공통 — 상단 공백 제거.
       모든 STEP 마운트(st-key-saju_router_step_mount_NN)에서 세로 가운데 정렬·100vh 밀림,
       마운트 이전 util(<style>/<script>) 블록의 flex 슬롯·row-gap 을 제거해
       콘텐츠가 항상 화면 상단에서 시작하도록 잠근다. */
    .stApp:has([class*="st-key-saju_router_step_mount_"]) [data-testid="stAppViewContainer"],
    .stApp:has([class*="st-key-saju_router_step_mount_"]) [data-testid="stAppViewContainer"] > .main,
    .stApp:has([class*="st-key-saju_router_step_mount_"]) section.main,
    .stApp:has([class*="st-key-saju_router_step_mount_"]) [data-testid="stMain"],
    .stApp:has([class*="st-key-saju_router_step_mount_"]) [data-testid="stMainBlockContainer"],
    .stApp:has([class*="st-key-saju_router_step_mount_"]) .main .block-container {
        display: block !important;
        min-height: 0 !important;
        height: auto !important;
        max-height: none !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
        align-content: flex-start !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
        flex: none !important;
    }
    .stApp:has([class*="st-key-saju_router_step_mount_"]) .main .block-container > [data-testid="stVerticalBlock"],
    .stApp:has([class*="st-key-saju_router_step_mount_"]) [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {
        gap: 0 !important;
        row-gap: 0 !important;
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    .stApp:has([class*="st-key-saju_router_step_mount_"]) .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(style),
    .stApp:has([class*="st-key-saju_router_step_mount_"]) .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(script),
    .stApp:has([class*="st-key-saju_router_step_mount_"]) [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(style),
    .stApp:has([class*="st-key-saju_router_step_mount_"]) [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(script) {
        display: none !important;
        height: 0 !important;
        max-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
        visibility: hidden !important;
    }
    /* 브라우저 scroll-anchoring 비활성화.
       오늘의 운세(STEP6)·주역(STEP7)·총평(STEP10)처럼 iframe/AI 결과가 늦게 붙는 STEP 은
       최상단 스크롤 직후 콘텐츠가 로드되며 브라우저가 스크롤을 아래로 끌어내려(anchoring)
       상단 포커스가 풀리는데, overflow-anchor:none 으로 이 현상을 막는다. */
    html:has([class*="st-key-saju_router_step_mount_"]),
    html:has([class*="st-key-saju_router_step_mount_"]) body,
    .stApp:has([class*="st-key-saju_router_step_mount_"]) [data-testid="stAppViewContainer"],
    .stApp:has([class*="st-key-saju_router_step_mount_"]) [data-testid="stMain"],
    .stApp:has([class*="st-key-saju_router_step_mount_"]) section.main,
    .stApp:has([class*="st-key-saju_router_step_mount_"]) [data-testid="stMainBlockContainer"],
    .stApp:has([class*="st-key-saju_router_step_mount_"]) .main .block-container,
    .stApp:has([class*="st-key-saju_router_step_mount_"]) .main .block-container > [data-testid="stVerticalBlock"] {
        overflow-anchor: none !important;
    }

    /* ===== 전 STEP 상단 공백 최소화 — 화면을 위로 올림(사용자 요청) =====
       홈~관리자까지 모든 STEP 공통. 게이트(data-saju-step) 없이 항상 적용되도록
       메인 CSS 맨 끝(최후위)에 배치해 권위 있게 덮어쓴다. */
    [data-testid="stMainBlockContainer"],
    .main .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    /* 분석 카드(STEP3~10) 상단 패딩 축소 — 카드 안 첫 요소(즐겨찾기)가 위로 */
    div[class*="st-key-saju_analysis_card"] {
        padding-top: clamp(0.8rem, 1.8vw, 1.15rem) !important;
    }
    /* 카드/마운트 안 첫 요소의 윗여백 제거(누적 gap·margin 차단) */
    div[class*="st-key-saju_analysis_card"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:first-child,
    div[class*="st-key-saju_analysis_card"] > [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"]:first-child,
    [class*="st-key-saju_router_step_mount_"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    /* 홈 랜딩도 동일하게 상단 밀착 */
    .st-key-saju_landing_stack,
    .st-key-saju_landing_hero {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    /* ===== 전 STEP 상단 공백 제거(핵심) =====
       라우터가 STEP 마운트 '내부' 첫 요소로 주입하는 마운트 가시성 <style>
       (inject_router_step_mount_visibility_css: id=saju-router-mount-visibility-N)는
       화면에 아무것도 그리지 않지만 element-container 가 세로 약 48px 슬롯을 차지해
       배너·본문을 아래로 밀어낸다(모든 STEP 공통, 사진의 배너 위 공백 원인).
       기존 빈 <style> 숨김 규칙은 block-container 직계 수직블록만 대상이라 마운트
       내부의 이 컨테이너를 못 잡으므로, id 기준으로 정확히(콘텐츠 카드는 건드리지 않음)
       흐름에서 제거한다. */
    [data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] style[id^="saju-router-mount-visibility"]),
    [data-testid="stElementContainer"]:has(style[id^="saju-router-mount-visibility"]) {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }
    /* 순수 <style>/<script> 전용 마크다운 element-container 제거(전역).
       st.markdown("<style>…")·st.markdown("<script>…") 처럼 보이는 출력이 없는
       주입 블록은 마크다운 컨테이너의 '유일한 자식'이 style/script 다. 이런 EC 는
       화면에 아무것도 안 그리면서 세로 슬롯(약 48px)만 차지해 본문을 아래로 민다.
       (콘텐츠 카드는 style 옆에 div/p 등 형제가 있어 :only-child 가 아니므로 안전) */
    [data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] > [data-testid="stMarkdownContainer"] > style:only-child),
    [data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] > [data-testid="stMarkdownContainer"] > script:only-child),
    [data-testid="stElementContainer"]:has([data-testid="stMarkdownContainer"] > style:only-child),
    [data-testid="stElementContainer"]:has([data-testid="stMarkdownContainer"] > script:only-child) {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }
    /* 더 견고한 보강: Streamlit 이 style/script 옆에 빈 래퍼(<p>·<div>)를 끼워
       :only-child 가 깨지는 경우까지 잡는다. "EC 안에 style/script 와 마크다운 래퍼
       (stMarkdown/stMarkdownContainer) 외의 '다른 요소'가 전혀 없는" EC = 순수 주입.
       콘텐츠 카드는 div/p/img 등 다른 요소가 있어 :has(*:not(...)) 가 참 → 제외(안전). */
    [data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] style):not(:has(> [data-testid="stMarkdown"] > [data-testid="stMarkdownContainer"] > *:not(style):not(script))),
    [data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] script):not(:has(> [data-testid="stMarkdown"] > [data-testid="stMarkdownContainer"] > *:not(style):not(script))) {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }
    /* ===== 전 STEP 상단 밀착(핵심) — JS(data-saju-step) 비의존 =====
       문제: 홈(STEP1)은 ``:has(.st-key-saju_router_step_mount_01)`` 기반 flush 가 있어
       block-container/main/app 상단 패딩이 0 이지만, 비홈 STEP 은 상단 패딩 0 규칙이
       ``html[data-saju-step]`` / ``html.saju-not-step1`` (JS 로 늦게 세팅되는 클래스)에
       의존해, 클래스 미적용 순간 기본 패딩(약 40px)이 그대로 남아 본문이 아래로 밀렸다.
       모든 STEP 마운트는 항상 존재하므로 ``:has(마운트)`` 로 JS 와 무관하게 즉시 적용한다. */
    .stApp [data-testid="stMainBlockContainer"]:has([class*="st-key-saju_router_step_mount_"]),
    .stApp .main .block-container:has([class*="st-key-saju_router_step_mount_"]) {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    .stApp [data-testid="stAppViewContainer"]:has([class*="st-key-saju_router_step_mount_"]) > .main,
    .stApp section.main:has([class*="st-key-saju_router_step_mount_"]) {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    .stApp [data-testid="stAppViewContainer"]:has([class*="st-key-saju_router_step_mount_"]) {
        padding-top: 0 !important;
    }
    /* ===== 전 STEP 마운트 내부 상단 밀착 =====
       마운트(st-key-saju_router_step_mount_NN)는 그 자체가 수직블록이며, 홈(_01) 외
       STEP 은 위 여백·세로 슬롯(row-gap) 잠금 규칙이 없어 콘텐츠(카드 등)가 마운트 위에서
       내려와 있었다. 모든 STEP 마운트에 동일 잠금을 적용한다.
       (마운트 직계 자식은 보통 콘텐츠 컨테이너 1개뿐이라 row-gap:0 이 카드 내부 간격엔
       영향을 주지 않는다. 카드 안쪽 간격은 카드 자신의 수직블록이 따로 관리.) */
    [class*="st-key-saju_router_step_mount_"] {
        margin-top: 0 !important;
        padding-top: 0 !important;
        gap: 0 !important;
        row-gap: 0 !important;
    }
    /* 마운트 안 콘텐츠(분석 카드 등) 위 잔여 여백 제거 — 카드 래퍼 margin-top 차단 */
    [class*="st-key-saju_router_step_mount_"] > [data-testid="stVerticalBlockBorderWrapper"],
    [class*="st-key-saju_router_step_mount_"] > [data-testid="stElementContainer"],
    div[class*="st-key-saju_analysis_card"] {
        margin-top: 0 !important;
    }
    /* 마운트 안 'st.markdown(<script>) 주입 전용' 컨테이너 제거(전 STEP).
       saju_step_html_sync_* 는 내부 <script> 가 Streamlit 에 제거돼 '빈 컨테이너'가
       되지만 세로 flex 슬롯을 차지한다(홈 런타임 JS 가 숨기던 것을 CSS 로 상시화).
       (functional components.html iframe(스크롤·동기화 등)은 건드리지 않는다.) */
    [class*="st-key-saju_step_html_sync"] {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }
    /* 배너 figure 기본 여백 제거 — 브라우저 기본 <figure>{margin:1em 40px} 가 배너 위
       공백을 만든다. 홈 배너(.saju-home-hero-banner)와 일반 figure 모두 0 으로. */
    .saju-home-hero-banner,
    .saju-home-hero-banner__figure,
    [class*="st-key-saju_router_step_mount_"] figure,
    div[class*="st-key-saju_analysis_card"] figure {
        margin: 0 !important;
        padding-top: 0 !important;
    }
    /* 홈 히어로 컨테이너 안 '첫 마크다운/요소' 위 여백 제거 —
       마운트 위 공백의 원인(컨테이너→수직블록→첫 EC 의 누적 margin/gap)을 차단.
       (히어로는 배너 1개뿐이라 gap:0 안전) */
    .st-key-saju_landing_hero [data-testid="stMarkdownContainer"],
    .st-key-saju_landing_hero > [data-testid="stVerticalBlock"],
    .st-key-saju_landing_hero [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
        gap: 0 !important;
        row-gap: 0 !important;
    }
    /* 분석 카드: '위 패딩/여백'만 0 으로(섹션 사이 gap 은 유지해 카드 내부 레이아웃 보존). */
    div[class*="st-key-saju_analysis_card"] > [data-testid="stVerticalBlock"] {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    div[class*="st-key-saju_analysis_card"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    /* ===== 본문(메인 수직블록) 최상단 'head 주입 전용' element-container 제거 =====
       문제: 라우터 마운트 앞에, 화면에 아무것도 안 그리는 주입 컨테이너
       (viewport meta · 조기 step style/script 등)가 직계 형제로 3개 가량 쌓여
       각자 세로 flex 슬롯(+row-gap)을 차지해 STEP 본문(분석 카드 등) 위에 약 50px
       공백을 만들었다. 이들은 style/script/meta/link '만' 담은 비시각 요소이므로
       흐름에서 제거한다.
       안전장치: 마크다운 컨테이너에 head 태그(style·script·meta·link) 외의 '다른
       요소'(div·p·img·표 등 보이는 콘텐츠)가 하나라도 있으면 :not(:has(...)) 로
       제외 → 인라인 <style> 를 함께 쓰는 콘텐츠 카드는 절대 숨기지 않는다.
       범위: 블록컨테이너의 '메인 수직블록 직계 자식'으로 한정(카드/마운트 내부 불간섭). */
    [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] :is(style, script, meta, link)):not(:has(> [data-testid="stMarkdown"] > [data-testid="stMarkdownContainer"] > *:not(style):not(script):not(meta):not(link))),
    .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] :is(style, script, meta, link)):not(:has(> [data-testid="stMarkdown"] > [data-testid="stMarkdownContainer"] > *:not(style):not(script):not(meta):not(link))) {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }
    /* ===== STEP 이동(rerun) stale — 이전 DOM 겹침(배너·버튼 이중 표시) 제거 =====
       Streamlit 은 rerun 중 이전 위젯에 data-stale 을 붙인다.
       opacity:1 강제는 stale·fresh 가 동시에 보여 배너·CTA 가 겹치므로,
       stale element-container 는 레이아웃에서 완전히 제거한다. */
    [data-testid="stElementContainer"][data-stale="true"],
    [data-testid="stVerticalBlockBorderWrapper"][data-stale="true"],
    .element-container[data-stale="true"] {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
        visibility: hidden !important;
        pointer-events: none !important;
        opacity: 0 !important;
        transition: none !important;
    }
    /* 배너 id 중복(stale 잔존) — 첫 번째만 표시 */
    #saju-home-hero-top ~ #saju-home-hero-top,
    .saju-home-hero-banner ~ .saju-home-hero-banner {
        display: none !important;
        height: 0 !important;
        overflow: hidden !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }
    /* STEP1 홈 — 섹션 세로 간격(CTA·재방문 겹침 방지) */
    .st-key-saju_landing_stack > [data-testid="stVerticalBlock"] {
        display: flex !important;
        flex-direction: column !important;
        gap: 0.55rem !important;
        row-gap: 0.55rem !important;
    }
    .st-key-saju_landing_stack .st-key-step1_solar24,
    .st-key-saju_landing_stack .st-key-step1_revisit_auth,
    .st-key-saju_landing_stack .st-key-step1_cta_row_main,
    .st-key-saju_landing_stack .st-key-step1_cta_row_free,
    .st-key-saju_landing_stack .st-key-saju_landing_cta {
        position: relative !important;
        display: block !important;
        width: 100% !important;
        height: auto !important;
        min-height: 0 !important;
        overflow: visible !important;
        flex: 0 0 auto !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
    .st-key-step1_cta_row_main [data-testid="stForm"],
    .st-key-step1_cta_row_main form {
        margin-bottom: 0 !important;
    }
    /* STEP1 CTA — 모바일 WebView gap:0 덮어쓰기(버튼 겹침 방지) */
    html.saju-platform-android .st-key-saju_landing_stack .st-key-step1_cta_row_main,
    html.saju-platform-android .st-key-saju_landing_stack .st-key-step1_cta_row_free,
    html.saju-platform-kakao .st-key-saju_landing_stack .st-key-step1_cta_row_main,
    html.saju-platform-kakao .st-key-saju_landing_stack .st-key-step1_cta_row_free,
    html.saju-platform-inapp .st-key-saju_landing_stack .st-key-step1_cta_row_main,
    html.saju-platform-inapp .st-key-saju_landing_stack .st-key-step1_cta_row_free {
        margin-top: 0.5rem !important;
        margin-bottom: 0.45rem !important;
        position: relative !important;
        display: block !important;
        height: auto !important;
        min-height: 0 !important;
        overflow: visible !important;
    }
    html.saju-platform-android .st-key-step1_cta_row_free,
    html.saju-platform-kakao .st-key-step1_cta_row_free,
    html.saju-platform-inapp .st-key-step1_cta_row_free {
        margin-top: 0.85rem !important;
    }
    /* ===== 비활성 STEP 마운트 래퍼(EC) — flex gap 상단 대공백 제거(핵심) =====
       마운트 내부만 display:none 해도 ElementContainer 가 flex 슬롯을 차지해
       현재 STEP 위에 빈 여백이 쌓인다. 현재 data-saju-step 과 일치하지 않는
       마운트를 담은 EC 는 통째로 접는다(전환 pending 중엔 출발 STEP 유지). */
    html[data-saju-step="1"]:not([data-saju-nav-pending="1"]) .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has([class*="st-key-saju_router_step_mount_"]):not(:has(.st-key-saju_router_step_mount_01)):not(:has(.st-key-saju_global_bottom_chrome)),
    html[data-saju-step="2"]:not([data-saju-nav-pending="1"]) .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has([class*="st-key-saju_router_step_mount_"]):not(:has(.st-key-saju_router_step_mount_02)):not(:has(.st-key-saju_global_bottom_chrome)),
    html[data-saju-step="3"]:not([data-saju-nav-pending="1"]) .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has([class*="st-key-saju_router_step_mount_"]):not(:has(.st-key-saju_router_step_mount_03)):not(:has(.st-key-saju_global_bottom_chrome)),
    html[data-saju-step="4"]:not([data-saju-nav-pending="1"]) .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has([class*="st-key-saju_router_step_mount_"]):not(:has(.st-key-saju_router_step_mount_04)):not(:has(.st-key-saju_global_bottom_chrome)),
    html[data-saju-step="5"]:not([data-saju-nav-pending="1"]) .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has([class*="st-key-saju_router_step_mount_"]):not(:has(.st-key-saju_router_step_mount_05)):not(:has(.st-key-saju_global_bottom_chrome)),
    html[data-saju-step="6"]:not([data-saju-nav-pending="1"]) .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has([class*="st-key-saju_router_step_mount_"]):not(:has(.st-key-saju_router_step_mount_06)):not(:has(.st-key-saju_global_bottom_chrome)),
    html[data-saju-step="7"]:not([data-saju-nav-pending="1"]) .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has([class*="st-key-saju_router_step_mount_"]):not(:has(.st-key-saju_router_step_mount_07)):not(:has(.st-key-saju_global_bottom_chrome)),
    html[data-saju-step="8"]:not([data-saju-nav-pending="1"]) .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has([class*="st-key-saju_router_step_mount_"]):not(:has(.st-key-saju_router_step_mount_08)):not(:has(.st-key-saju_global_bottom_chrome)),
    html[data-saju-step="9"]:not([data-saju-nav-pending="1"]) .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has([class*="st-key-saju_router_step_mount_"]):not(:has(.st-key-saju_router_step_mount_09)):not(:has(.st-key-saju_global_bottom_chrome)),
    html[data-saju-step="10"]:not([data-saju-nav-pending="1"]) .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has([class*="st-key-saju_router_step_mount_"]):not(:has(.st-key-saju_router_step_mount_10)):not(:has(.st-key-saju_global_bottom_chrome)),
    html[data-saju-step="11"]:not([data-saju-nav-pending="1"]) .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has([class*="st-key-saju_router_step_mount_"]):not(:has(.st-key-saju_router_step_mount_11)):not(:has(.st-key-saju_global_bottom_chrome)),
    html[data-saju-step="12"]:not([data-saju-nav-pending="1"]) .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has([class*="st-key-saju_router_step_mount_"]):not(:has(.st-key-saju_router_step_mount_12)):not(:has(.st-key-saju_global_bottom_chrome)) {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        max-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
        visibility: hidden !important;
        pointer-events: none !important;
        opacity: 0 !important;
        position: absolute !important;
        left: -99999px !important;
        width: 0 !important;
    }
    /* STEP 전환·스크롤 유틸 iframe 컨테이너 — 본문 위 flex 슬롯 제거 */
    [class*="st-key-saju_nav_pending_flag"],
    [class*="st-key-saju_nav_scroll_tail"],
    .st-key-saju_step_top_anchor,
    [class*="st-key-saju_nav_pending_flag"] [data-testid="stCustomComponentV1"],
    [class*="st-key-saju_nav_scroll_tail"] [data-testid="stCustomComponentV1"] {
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
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
    .stApp:has([class*="st-key-saju_router_step_mount_"]) .main .block-container > [data-testid="stVerticalBlock"] {
        gap: 0 !important;
        row-gap: 0 !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    /* rerun 진행 표시(상단 러닝바·스피너)도 STEP 이동 깜빡임으로 보이므로 숨김 */
    [data-testid="stStatusWidget"],
    .stApp > div[data-testid="stStatusWidget"] {
        display: none !important;
    }

    /* STEP3(사주분석) — 단일 스크롤 컨테이너·튐(overscroll bounce) 완화 */
    html:has(.st-key-saju_router_step_mount_03) [data-testid="stMain"],
    html:has(.st-key-saju_router_step_mount_03) section.main,
    html:has(.st-key-saju_router_step_mount_03) [data-testid="stMainBlockContainer"] {
        overflow: visible !important;
        overscroll-behavior-y: auto !important;
        -webkit-overflow-scrolling: auto !important;
    }
    html:has(.st-key-saju_router_step_mount_03) [data-testid="stAppViewContainer"] {
        overflow-y: auto !important;
        overflow-x: hidden !important;
        overscroll-behavior-y: auto !important;
        -webkit-overflow-scrolling: touch !important;
        scroll-behavior: auto !important;
    }
    html:has(.st-key-saju_router_step_mount_03) .st-key-step3_gapja_chart iframe,
    html:has(.st-key-saju_router_step_mount_03) .st-key-step3_gapja_chart [data-testid="stCustomComponentV1"] {
        overflow: visible !important;
        pointer-events: auto !important;
    }

    /* ===== 스크롤 복구 (Streamlit Cloud · 최종 우선) =====
       height:auto + overflow-y:auto 는 컨테이너가 콘텐츠만큼 늘어나 스크롤바가 생기지 않고,
       .stApp(100dvh·overflow:hidden) 안에서 하단이 잘린다. 뷰포트 고정 스크롤 루트를 복원한다.
       (상단 flex-center 차단은 justify-content:flex-start 유지) */
    html body .stApp,
    html:has([class*="st-key-saju_router_step_mount_"]) .stApp,
    html:has(.st-key-saju_router_step_mount_01) .stApp {
        height: 100vh !important;
        height: 100dvh !important;
        max-height: 100dvh !important;
        overflow: hidden !important;
    }
    html body [data-testid="stAppViewContainer"],
    html:has([class*="st-key-saju_router_step_mount_"]) [data-testid="stAppViewContainer"],
    html:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"],
    html.saju-home-step1 [data-testid="stAppViewContainer"],
    html[data-saju-step="1"] [data-testid="stAppViewContainer"],
    html[data-saju-step] [data-testid="stAppViewContainer"],
    .stApp:has([class*="st-key-saju_router_step_mount_"]) [data-testid="stAppViewContainer"],
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"] {
        height: 100vh !important;
        height: 100dvh !important;
        max-height: 100dvh !important;
        min-height: 0 !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        -webkit-overflow-scrolling: touch !important;
        overscroll-behavior-y: auto !important;
        touch-action: pan-y !important;
        display: block !important;
        justify-content: flex-start !important;
        align-items: stretch !important;
    }
    html body [data-testid="stAppViewContainer"] > .main,
    html body section.main,
    html body [data-testid="stMain"],
    html body [data-testid="stMainBlockContainer"],
    html body .main .block-container {
        height: auto !important;
        max-height: none !important;
        overflow: visible !important;
    }

    /* ===== 홈 배너 최상단 밀착 (Cloud·JS/html class 지연 무관, 최종 우선) =====
       Streamlit Cloud: toolbar(stHeader) + block-container 기본 padding-top 이
       배너 위 공백을 만든다. :has(히어로) 로 html class 없이도 즉시 적용. */
    .stApp:has(.st-key-saju_landing_hero) .main .block-container,
    .stApp:has(#saju-home-hero-top) .main .block-container,
    .stApp:has(.saju-home-hero-banner) .main .block-container,
    .stApp:has(.st-key-saju_router_step_mount_01) .main .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
        scroll-padding-top: 0 !important;
    }
    .stApp:has(.st-key-saju_landing_hero) [data-testid="stAppViewContainer"],
    .stApp:has(.st-key-saju_landing_hero) [data-testid="stAppViewContainer"] > .main,
    .stApp:has(.st-key-saju_landing_hero) [data-testid="stMain"],
    .stApp:has(.st-key-saju_landing_hero) [data-testid="stMainBlockContainer"],
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stAppViewContainer"],
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stMainBlockContainer"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    .stApp:has(.st-key-saju_landing_hero) header[data-testid="stHeader"],
    .stApp:has(.st-key-saju_router_step_mount_01) header[data-testid="stHeader"],
    .stApp:has(.st-key-saju_landing_hero) > header,
    .stApp:has(.st-key-saju_router_step_mount_01) > header,
    .stApp:has(.st-key-saju_landing_hero) [data-testid="stToolbar"],
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stToolbar"],
    .stApp:has(.st-key-saju_landing_hero) [data-testid="stDecoration"],
    .stApp:has(.st-key-saju_router_step_mount_01) [data-testid="stDecoration"] {
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
        top: 0 !important;
        left: 0 !important;
        width: 0 !important;
        z-index: -1 !important;
    }
    .stApp:has(.st-key-saju_landing_hero) .st-key-saju_router_step_mount_01,
    .stApp:has(.st-key-saju_landing_hero) .st-key-saju_landing_hero,
    .stApp:has(.st-key-saju_landing_hero) #saju-home-hero-top,
    .stApp:has(.st-key-saju_landing_hero) .saju-home-hero-banner,
    .stApp:has(.st-key-saju_landing_hero) .saju-home-hero-banner__figure {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    .stApp:has(.st-key-saju_landing_hero) .main .block-container > [data-testid="stVerticalBlock"] {
        gap: 0 !important;
        row-gap: 0 !important;
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    .stApp:has(.st-key-saju_landing_hero) .main .block-container > [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:first-child {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
</style>
<script>
(function () {
    const pw = window.parent && window.parent !== window ? window.parent : window;
    if (pw.__sajuBootstrapNavScrollV15) return;
    pw.__sajuBootstrapNavScrollV15 = true;
    pw.__sajuBootstrapNavScrollV14 = true;
    pw.__sajuBootstrapNavScrollV13 = true;
    pw.__sajuBootstrapNavScrollV12 = true;
    pw.__sajuBootstrapNavScrollV11 = true;
    pw.__sajuBootstrapNavScrollV10 = true;
    pw.__sajuBootstrapNavScrollV9 = true;
    pw.__sajuBootstrapNavScrollV8 = true;
    pw.__sajuBootstrapNavScrollV7 = true;
    pw.__sajuBootstrapNavScrollV6 = true;
    const pinHomeHeroIfNeeded = function () {
        const doc = pw.document || document;
        if (!doc) return;
        const root = doc.documentElement;
        const step = root
            ? String(root.getAttribute("data-saju-step") || "1")
            : "1";
        const onHome =
            step === "1" ||
            (root && root.classList.contains("saju-home-step1")) ||
            !!doc.querySelector(
                ".st-key-saju_router_step_mount_01 .st-key-saju_landing_hero, #saju-home-hero-top"
            );
        if (!onHome) return;
        let scrollOff = 0;
        try {
            const main =
                doc.querySelector('[data-testid="stAppViewContainer"]') ||
                doc.scrollingElement;
            scrollOff = Math.max(
                main ? main.scrollTop || 0 : 0,
                pw.scrollY || 0,
                doc.documentElement.scrollTop || 0
            );
        } catch (eOff) {}
        if (scrollOff > 48 || pw.__sajuUserIsScrolling) {
            return;
        }
        if (typeof pw.__sajuPhoto2SnapTop === "function") {
            pw.__sajuPhoto2SnapTop();
        }
    };
    try {
        pinHomeHeroIfNeeded();
        pw.requestAnimationFrame(pinHomeHeroIfNeeded);
        [120, 400].forEach(function (ms) {
            pw.setTimeout(pinHomeHeroIfNeeded, ms);
        });
        if (typeof pw.__sajuDetectMobilePlatform === "function") {
            pw.__sajuDetectMobilePlatform();
        }
    } catch (ePin) {}
    /* STEP 이동 스크롤은 app.py finalize 1회만 — 여기서 스크롤하면 본문 렌더 전 멈춤·이중 스냅 발생 */
    const syncStepAttrOnly = function () {
        const doc = pw.document || document;
        if (!doc) return;
        const root = doc.documentElement;
        if (!root) return;
        const nodes = doc.querySelectorAll(".saju-live-step-beacon");
        const b = nodes.length ? nodes[nodes.length - 1] : null;
        const step = b
            ? String(b.getAttribute("data-saju-step") || "1")
            : String(root.getAttribute("data-saju-step") || "1");
        if (String(root.getAttribute("data-saju-step") || "") !== step) {
            root.setAttribute("data-saju-step", step);
        }
    };
    try {
        const doc = pw.document;
        if (doc && doc.documentElement) {
            new MutationObserver(function (muts) {
                for (let i = 0; i < muts.length; i++) {
                    if (muts[i].attributeName === "data-saju-step") {
                        syncStepAttrOnly();
                        return;
                    }
                }
            }).observe(doc.documentElement, {
                attributes: true,
                attributeFilter: ["data-saju-step"],
            });
        }
    } catch (e4) {}
})();
</script>
"""
    )
    _inject_bootstrap_global_css(_saju_bootstrap_head_html)
    try:
        from saju_app.ui.element_theme import inject_element_theme_styles

        inject_element_theme_styles()
    except Exception:
        pass
    try:
        from saju_app.ui.extras_integration import apply_global_streamlit_extras

        apply_global_streamlit_extras()
    except Exception:
        pass
    try:
        from saju_app.ui.execution import (
            inject_calendar_weekday_en_once,
            inject_step2_tab_manager_global_once,
            inject_step_nav_click_guard_once,
            inject_step_scroll_manager_once,
        )
        # 8502 관리자 앱에서는 전역 DOM 보정(JS)이 React removeChild 오류를 유발할 수 있어 최소화합니다.
        try:
            from saju_app.ui import components as _saju_nav

            is_admin_build = bool(_saju_nav.admin_panel_enabled())
        except Exception:
            is_admin_build = False

        inject_step_scroll_manager_once()
        if not is_admin_build:
            inject_step_nav_click_guard_once()
            inject_step2_tab_manager_global_once()
            inject_calendar_weekday_en_once()
            from saju_app.ui.execution import inject_home_photo2_layout_css

            inject_home_photo2_layout_css()
    except Exception:
        pass
    try:
        from saju_app.ui import components as _saju_nav

        _saju_nav.inject_global_input_autofill_guard()
    except Exception:
        pass
