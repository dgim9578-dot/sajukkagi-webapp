"""Streamlit 최초 설정: `set_page_config` + 전역 CSS.

다크/라이트 테마는 `.streamlit/config.toml`의 `[theme.light]` / `[theme.dark]`
(Deep Luxury Dark + Gold / 크림·골드 라이트) 및 앱 우상단 ⋮ → Settings → Theme 에서 전환합니다.
"""

from __future__ import annotations

import streamlit as st


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


def configure_application() -> None:
    st.set_page_config(
        page_title="사주까기 · 무료 사주풀이",
        page_icon="🔮",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    init_session_state()
    try:
        from saju_app.ui import share_meta as _share_meta

        _share_meta.inject_link_share_meta()
    except Exception:
        pass

    st.markdown(
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
        --saju-bg-paper: #faf6ef;
        --saju-gold: #d4af37;
        --saju-gold-bright: #e8b923;
        --saju-gold-soft: #c9a227;
        --saju-gold-deep: #7a5e12;
        --saju-ink: #120e0a;
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
    .stApp {
        font-size: 1rem;
        font-family: "Playfair Display", "Noto Serif KR", "Apple SD Gothic Neo", "Malgun Gothic",
            Georgia, "Times New Roman", "Noto Color Emoji", serif !important;
        /* 테마 배경과 맞춤: 다크 #0F0F1A / 라이트 크림 (config.toml 과 동조) */
        background-color: light-dark(var(--saju-bg-paper), var(--saju-bg-mid)) !important;
    }
    /* Streamlit Cloud 플랫폼 UI — 사주 앱 기능과 무관 (Fork·관리·Made with Streamlit 등) */
    header[data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    .stDeployButton,
    #MainMenu,
    footer {
        visibility: hidden !important;
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        overflow: hidden !important;
        pointer-events: none !important;
    }
    /* Cloud 하단 고정 버튼(빨간 왕관·관리) — 소유자 미리보기용 */
    iframe[title="streamlit"],
    a[href*="share.streamlit.io/manage"],
    a[href*="streamlit.app/manage"] {
        display: none !important;
        visibility: hidden !important;
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
    /* 럭셔리 워치 톤: 다크에서 은은한 골드 앰비언트(한지 위 금박 반사 느낌) */
    .main .block-container::before {
        content: "";
        position: absolute;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        opacity: 1;
        background:
            radial-gradient(ellipse 100% 52% at 50% -12%, rgba(212, 175, 55, 0.09), transparent 58%),
            radial-gradient(ellipse 55% 40% at 100% 18%, rgba(165, 180, 252, 0.04), transparent 50%),
            radial-gradient(ellipse 50% 38% at 0% 72%, rgba(212, 175, 55, 0.035), transparent 48%);
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
        color: light-dark(#334155, #e2e8f0);
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
            border: 1px solid rgba(26, 26, 46, 0.15);
            border: 1px solid light-dark(rgba(26, 26, 46, 0.12), rgba(212, 175, 55, 0.22));
            border-radius: 12px;
            box-shadow: light-dark(0 4px 18px rgba(26, 26, 46, 0.08), 0 4px 22px rgba(0, 0, 0, 0.45));
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
        border-radius: 14px !important;
        background: light-dark(rgba(250, 248, 243, 0.99), rgba(14, 14, 24, 0.96)) !important;
        border: 1px solid light-dark(rgba(26, 26, 46, 0.12), rgba(212, 175, 55, 0.22)) !important;
        box-shadow: light-dark(0 4px 18px rgba(15, 23, 42, 0.08), 0 6px 22px rgba(0, 0, 0, 0.42)) !important;
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

    /* ===== STEP1 랜딩: 한지·먹·금박 톤 히어로 ===== */
    .st-key-saju_landing_stack {
        margin-top: -2rem;
        margin-bottom: 0.1rem;
    }
    .st-key-saju_landing_stack [data-testid="stVerticalBlock"] > div {
        gap: 0.35rem !important;
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
        padding: clamp(1.15rem, 3.5vw, 2.25rem) clamp(1rem, 4vw, 2rem)
            clamp(1rem, 2.5vw, 1.65rem);
        min-height: 0;
        height: auto;
        overflow: visible;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        text-align: center;
        border-radius: 0 0 22px 22px;
        background-color: #e8dfd4;
        background-image:
            radial-gradient(ellipse 130% 85% at 50% -25%, rgba(22, 18, 14, 0.22) 0%, transparent 58%),
            radial-gradient(ellipse 90% 70% at 110% 35%, rgba(15, 15, 26, 0.09) 0%, transparent 48%),
            radial-gradient(ellipse 70% 55% at -10% 75%, rgba(15, 15, 26, 0.07) 0%, transparent 42%),
            repeating-linear-gradient(
                92deg,
                rgba(212, 175, 55, 0.04) 0px,
                rgba(212, 175, 55, 0.04) 1px,
                transparent 1px,
                transparent 7px
            ),
            linear-gradient(168deg, #f4eee4 0%, #ebe2d4 38%, #dfd2c2 100%),
            radial-gradient(ellipse 85% 70% at 0% 100%, rgba(62, 48, 32, 0.1), transparent 52%),
            radial-gradient(ellipse 80% 65% at 100% 0%, rgba(15, 15, 26, 0.06), transparent 48%);
        box-shadow:
            inset 0 0 100px rgba(15, 15, 26, 0.05),
            0 14px 48px rgba(0, 0, 0, 0.14);
        border-bottom: 1px solid rgba(201, 162, 39, 0.4);
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
        width: clamp(2.2rem, 8vw, 3.4rem);
        height: clamp(2.2rem, 8vw, 3.4rem);
        pointer-events: none;
        z-index: 2;
        opacity: 0.72;
        border-color: rgba(212, 175, 55, 0.75);
        border-style: solid;
    }
    .saju-landing-corner-tl {
        top: 0.65rem;
        left: 0.65rem;
        border-width: 2px 0 0 2px;
        border-radius: 12px 0 0 0;
    }
    .saju-landing-corner-tr {
        top: 0.65rem;
        right: 0.65rem;
        border-width: 2px 2px 0 0;
        border-radius: 0 12px 0 0;
    }
    .saju-landing-corner-bl {
        bottom: 0.65rem;
        left: 0.65rem;
        border-width: 0 0 2px 2px;
        border-radius: 0 0 0 12px;
    }
    .saju-landing-corner-br {
        bottom: 0.65rem;
        right: 0.65rem;
        border-width: 0 2px 2px 0;
        border-radius: 0 0 12px 0;
    }
    .saju-landing-illu-wrap {
        position: absolute;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0.52;
        overflow: hidden;
        border-radius: inherit;
    }
    .saju-landing-illus-svg {
        width: min(95%, 36rem);
        max-height: min(55%, 18rem);
        height: auto;
        flex-shrink: 0;
        filter: drop-shadow(0 0 28px rgba(212, 175, 55, 0.12));
    }
    @media (max-width: 768px) {
        .st-key-saju_landing_stack {
            margin-top: -2.35rem !important;
        }
        .main .block-container {
            padding-top: 0 !important;
            padding-left: 0.55rem !important;
            padding-right: 0.55rem !important;
        }
        [data-testid="stAppViewContainer"] > .main {
            padding-top: 0 !important;
        }
        header[data-testid="stHeader"] {
            background: transparent !important;
        }
        .saju-landing-hero {
            padding-top: clamp(0.95rem, 3vw, 1.35rem) !important;
            padding-bottom: clamp(0.85rem, 2.5vw, 1.15rem) !important;
            border-radius: 0 0 18px 18px;
        }
        .st-key-saju_landing_hero {
            display: block !important;
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
    .saju-landing-hero-inner {
        position: relative;
        z-index: 1;
        max-width: 40rem;
        width: 100%;
        padding-top: 0.15rem;
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
        opacity: 0.32;
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
        gap: 0.55rem;
        margin-bottom: 0.5rem;
    }
    @media (min-width: 520px) {
        .saju-landing-logo-row {
            flex-direction: row;
            justify-content: center;
            align-items: center;
            gap: 1.15rem;
        }
    }
    .saju-landing-seal-wrap {
        flex-shrink: 0;
        filter: drop-shadow(0 8px 26px rgba(138, 109, 26, 0.5));
    }
    .saju-landing-seal-svg {
        width: clamp(5.25rem, 17vw, 7.5rem);
        height: auto;
        display: block;
    }
    .saju-landing-brand-block {
        text-align: center;
    }
    .saju-landing-brand {
        font-family: "Playfair Display", "Noto Serif KR", "Apple SD Gothic Neo", "Malgun Gothic", Georgia, serif;
        font-size: clamp(2.2rem, 6.8vw, 3.95rem);
        font-weight: 800;
        letter-spacing: 0.1em;
        margin: 0 0 0.25rem 0;
        line-height: 1.1;
        background: linear-gradient(
            102deg,
            var(--saju-gold-deep) 0%,
            #b8892b 22%,
            #e8c547 38%,
            var(--saju-gold-soft) 48%,
            var(--saju-gold) 58%,
            #8a6d1a 100%
        );
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        filter: drop-shadow(0 2px 16px rgba(138, 109, 26, 0.48));
    }
    .saju-landing-kicker {
        font-family: "Playfair Display", Georgia, serif;
        font-size: clamp(0.58rem, 1.85vw, 0.72rem);
        font-weight: 600;
        letter-spacing: 0.38em;
        text-indent: 0.38em;
        margin: 0;
        color: rgba(90, 72, 40, 0.72);
        text-transform: uppercase;
    }
    .saju-landing-tagline {
        font-size: clamp(1.05rem, 3.4vw, 1.28rem);
        font-weight: 700;
        color: rgba(35, 30, 24, 0.88);
        margin: 0.85rem 0 0.35rem 0;
        line-height: 1.45;
        letter-spacing: -0.03em;
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
        margin: 0.35rem 0 0.45rem !important;
        padding: 0 0.25rem;
        font-size: clamp(1.05rem, 2.8vw, 1.2rem) !important;
        font-weight: 800 !important;
        color: light-dark(#7a5e12, #e8c547) !important;
        letter-spacing: 0.02em;
        text-align: center;
    }
    .st-key-step1_solar24 {
        margin: 0 0 0.35rem !important;
        isolation: isolate;
        display: block !important;
        min-height: 200px !important;
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
    .st-key-step1_cta_row_main [data-testid="stHorizontalBlock"],
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
    .st-key-step1_cta_row_briefing [data-testid="stHorizontalBlock"] > div,
    .st-key-step1_cta_row_main [data-testid="stHorizontalBlock"] > div,
    .st-key-step1_revisit_pin_row [data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0 !important;
        min-width: 0 !important;
        max-width: 50% !important;
        width: auto !important;
        overflow: hidden !important;
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
        background: light-dark(#ffffff, rgba(38, 38, 56, 0.95)) !important;
        color: light-dark(#334155, #e8e8f0) !important;
        border: 1px solid light-dark(#e5e7eb, rgba(212, 175, 55, 0.22)) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06) !important;
    }
    .st-key-step1_cta_row_main .stButton > button:disabled,
    .st-key-step1_cta_row_main [data-testid="stFormSubmitButton"] > button:disabled {
        background: rgba(184, 134, 11, 0.14) !important;
        color: #8a6d1a !important;
        border: 1px dashed rgba(184, 134, 11, 0.45) !important;
        box-shadow: none !important;
    }
    .st-key-step1_cta_row_main .stButton > button,
    .st-key-step1_cta_row_main [data-testid="stFormSubmitButton"] > button,
    .st-key-step1_cta_row_main .stLinkButton > a {
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
        border: 1px solid rgba(138, 109, 26, 0.55) !important;
        background: linear-gradient(180deg, #f0dc82 0%, #d4af37 38%, #b8892b 100%) !important;
        color: #0f0f1a !important;
        box-shadow: 0 3px 0 rgba(107, 84, 32, 0.32), 0 6px 16px rgba(0, 0, 0, 0.12) !important;
    }
    .st-key-step1_revisit_pin_row .stTextInput label {
        font-size: clamp(11px, 3vw, 13px) !important;
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
        margin-top: 0.35rem !important;
        box-sizing: border-box !important;
    }
    .st-key-step1_cta_row_free .stButton > button {
        width: 100% !important;
        min-height: clamp(2.55rem, 11vw, 3.05rem) !important;
        font-size: clamp(11px, 3vw, 14px) !important;
        font-weight: 800 !important;
        white-space: nowrap !important;
        border-radius: 12px !important;
        border: 1px solid rgba(138, 109, 26, 0.55) !important;
        background: linear-gradient(180deg, #f0dc82 0%, #d4af37 38%, #b8892b 100%) !important;
        color: #0f0f1a !important;
        box-shadow: 0 3px 0 rgba(107, 84, 32, 0.32), 0 6px 16px rgba(0, 0, 0, 0.12) !important;
    }
    .st-key-step1_revisit_pin_row .stButton > button {
        border: 1px solid rgba(138, 109, 26, 0.55) !important;
        background: linear-gradient(180deg, #f0dc82 0%, #d4af37 38%, #b8892b 100%) !important;
        color: #0f0f1a !important;
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
    /* STEP2 태어난 시간 아코디언: 긴 시간 범위가 모바일에서 겹치지 않도록 */
    .st-key-step2_navertone_self .stExpander .stButton > button,
    .st-key-step2_navertone_opp .stExpander .stButton > button {
        min-height: 2.6rem !important;
        height: auto !important;
        white-space: nowrap !important;
        line-height: 1.16 !important;
        font-size: clamp(12px, 2.85vw, 14px) !important;
        padding: 0.34rem 0.18rem !important;
        letter-spacing: -0.045em !important;
    }
    /* STEP1: 3열 메뉴는 접이식(expander) 안에서만 사용 */
    .st-key-step1_solar24 {
        max-width: min(100vw, 520px);
        margin: 0.35rem auto 0.15rem auto;
        padding: 0 clamp(0.45rem, 2.5vw, 1rem);
        box-sizing: border-box;
    }
    .st-key-step1_solar24 [data-testid="stCustomComponentV1"],
    .st-key-step1_solar24 [data-testid="stCustomComponentV1"] iframe,
    .st-key-step1_solar24 iframe {
        width: 100% !important;
        max-width: 520px !important;
        margin: 0 auto !important;
        min-height: 640px !important;
        display: block !important;
        overflow: visible !important;
    }
    .st-key-step1_solar24 [data-testid="stCustomComponentV1"] {
        overflow: visible !important;
    }
    @media (max-width: 520px) {
        .st-key-step1_solar24 [data-testid="stCustomComponentV1"] iframe,
        .st-key-step1_solar24 iframe {
            min-height: 660px !important;
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
    .st-key-step1_footer_ornament {
        max-width: min(100vw, 440px);
        margin: 0.1rem auto 1.1rem auto;
        padding: 0.35rem 0.75rem 0.85rem;
        box-sizing: border-box;
        text-align: center;
    }
    .saju-step1-footer-ornament svg {
        display: block;
        margin: 0 auto;
        max-width: 100%;
        height: auto;
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
            padding: 0.35rem 0.55rem 0.85rem !important;
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
        border: 1px solid rgba(138, 109, 26, 0.55) !important;
        background: linear-gradient(180deg, #f0dc82 0%, #d4af37 42%, #b8892b 100%) !important;
        color: #0f0f1a !important;
        box-shadow:
            0 3px 0 rgba(107, 84, 32, 0.32),
            0 10px 26px rgba(0, 0, 0, 0.14) !important;
    }
    .st-key-step2_cal_orb_row .stButton > button[kind="secondary"],
    .st-key-step2_cal_orb_row .stButton > button[data-testid="baseButton-secondary"] {
        border: 1px solid light-dark(rgba(201, 162, 39, 0.35), rgba(212, 175, 55, 0.25)) !important;
        background: light-dark(rgba(255, 252, 248, 0.85), rgba(26, 26, 46, 0.65)) !important;
        color: light-dark(#3a3428, #e8e6f0) !important;
    }
    html.saju-dark-tone .st-key-step2_cal_orb_row .stButton > button[kind="secondary"],
    html.saju-dark-tone .st-key-step2_cal_orb_row .stButton > button[data-testid="baseButton-secondary"] {
        background: rgba(22, 24, 40, 0.75) !important;
        color: rgba(232, 230, 245, 0.88) !important;
    }

    /* STEP2: 골드 저장 버튼 */
    .st-key-step2_save_gold_wrap .stButton > button {
        min-height: 3.65rem !important;
        font-size: max(17px, 1.06rem) !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
        border-radius: 14px !important;
        border: 1px solid rgba(138, 109, 26, 0.55) !important;
        background: linear-gradient(180deg, #f0dc82 0%, #d4af37 38%, #b8892b 100%) !important;
        color: #0f0f1a !important;
        box-shadow:
            0 4px 0 rgba(107, 84, 32, 0.35),
            0 10px 28px rgba(0, 0, 0, 0.18) !important;
    }
    .st-key-step2_save_gold_wrap .stButton > button:hover {
        filter: brightness(1.04) !important;
    }
    .st-key-step2_save_gold_wrap .stButton > button:active {
        transform: translateY(1px);
        box-shadow: 0 2px 0 rgba(107, 84, 32, 0.35), 0 6px 18px rgba(0, 0, 0, 0.16) !important;
    }
    html.saju-dark-tone .st-key-step2_save_gold_wrap .stButton > button {
        color: #0f0f1a !important;
    }

    /* ===== 분석 카드 `.card` 스킨 (STEP3~10 — 채팅창은 별도 규칙) ===== */
    div[class*="st-key-saju_analysis_card"] {
        position: relative;
        overflow: hidden;
        border-radius: 22px;
        padding: clamp(1.55rem, 3vw, 2.35rem);
        margin-bottom: 1.35rem;
        box-sizing: border-box;
        border: 1px solid light-dark(rgba(92, 62, 36, 0.2), rgba(212, 175, 55, 0.22));
        background: light-dark(
            linear-gradient(150deg, #fdf9f4 0%, #f1e9dc 48%, #e7dcc9 100%),
            linear-gradient(135deg, #1a1a2e 0%, #16213e 52%, #141b2a 100%)
        );
        box-shadow: light-dark(
                0 12px 36px rgba(35, 26, 18, 0.1),
                0 16px 44px rgba(0, 0, 0, 0.48)
            ),
            inset 0 1px 0 light-dark(rgba(255, 255, 255, 0.42), rgba(255, 255, 255, 0.06));
        color: light-dark(#1a1a2e, var(--saju-text-body));
    }
    div[class*="st-key-saju_analysis_card"]::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(
            90deg,
            transparent 0%,
            #7a5e12 10%,
            #d4af37 32%,
            #e8b923 50%,
            #d4af37 68%,
            #7a5e12 90%,
            transparent 100%
        );
        z-index: 3;
    }
    div[class*="st-key-saju_analysis_card"]::after {
        content: "";
        position: absolute;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        opacity: light-dark(0.07, 0.055);
        mix-blend-mode: multiply;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='96' height='96'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.88' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
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
        color: inherit;
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

    /* STEP10 건강 카드 — 다크 카드 위 본문·위험도·실천 포인트 가독 */
    div[class*="st-key-step10_health_fortune"] .saju-step10-health-card {
        color: #e2e8f0;
    }
    div[class*="st-key-step10_health_fortune"] .saju-step10-health-card .saju-step10-risk-block,
    div[class*="st-key-step10_health_fortune"] .saju-step10-health-card .saju-step10-risk-block * {
        color: #e0e7ff !important;
    }
    div[class*="st-key-step10_health_fortune"] .saju-step10-health-card .saju-step10-risk-score {
        font-weight: 700;
    }
    div[class*="st-key-step10_health_fortune"] .saju-health-tips,
    div[class*="st-key-step10_health_fortune"] .saju-health-tips * {
        color: #f1f5f9 !important;
    }
    div[class*="st-key-step10_health_fortune"] .saju-health-tips {
        margin-top: 0.25rem;
        padding: 1rem 1.05rem;
        border-radius: 12px;
        font-size: max(13px, 0.92rem);
        line-height: 1.65;
        background: rgba(15, 23, 42, 0.55);
        border: 1px solid rgba(244, 114, 182, 0.35);
        box-sizing: border-box;
    }
    div[class*="st-key-step10_health_fortune"] .saju-health-tips b {
        color: #f9a8d4 !important;
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
     * (본인/상대 탭 각각 `step2_navertone_self` / `step2_navertone_opp` 컨테이너)
     */
    .st-key-step2_navertone_self .stTextInput > div > div,
    .st-key-step2_navertone_self .stNumberInput > div > div,
    .st-key-step2_navertone_self [data-baseweb="select"] > div,
    .st-key-step2_navertone_opp .stTextInput > div > div,
    .st-key-step2_navertone_opp .stNumberInput > div > div,
    .st-key-step2_navertone_opp [data-baseweb="select"] > div {
        border-radius: 16px !important;
        background: light-dark(#f4efe6, #2a2620) !important;
        border: 1px solid light-dark(#e3dcc8, rgba(212, 175, 55, 0.22)) !important;
        box-shadow: none !important;
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
    .st-key-step2_navertone_self .stNumberInput input,
    .st-key-step2_navertone_opp .stTextInput > div > div > input,
    .st-key-step2_navertone_opp .stNumberInput input {
        border-radius: 14px !important;
        background: transparent !important;
        border: 0 !important;
        font-size: clamp(13px, 3.2vw, 15px) !important;
        line-height: 1.18 !important;
        letter-spacing: -0.035em !important;
    }
    .st-key-step2_navertone_self .stNumberInput button,
    .st-key-step2_navertone_opp .stNumberInput button {
        border-radius: 10px !important;
        background: light-dark(#e8dcc4, #3d3528) !important;
        border: 1px solid light-dark(#d4c4a8, rgba(212, 175, 55, 0.25)) !important;
        font-size: clamp(13px, 3.2vw, 15px) !important;
        font-weight: 800 !important;
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
        border-radius: 16px !important;
        background: light-dark(#f4efe6, #2a2620) !important;
        border: 1px solid light-dark(#e3dcc8, rgba(212, 175, 55, 0.22)) !important;
    }
    .st-key-step2_navertone_self [data-testid="stExpander"] summary,
    .st-key-step2_navertone_opp [data-testid="stExpander"] summary {
        border-radius: 14px !important;
        font-weight: 600 !important;
        white-space: nowrap !important;
        padding-left: 0.35rem !important;
        padding-right: 0.35rem !important;
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

    /* STEP3 메인 사주 차트(iframe): 모바일에서 하단 오행 막대까지 보이도록 */
    .st-key-step3_gapja_chart [data-testid="stCustomComponentV1"],
    .st-key-step3_gapja_chart [data-testid="stCustomComponentV1"] iframe,
    .st-key-step3_gapja_chart iframe {
        width: 100% !important;
        max-width: 100% !important;
        min-height: 420px !important;
        max-height: 560px !important;
        overflow: hidden !important;
    }
    @media (max-width: 520px) {
        .st-key-step3_gapja_chart [data-testid="stCustomComponentV1"] iframe,
        .st-key-step3_gapja_chart iframe {
            min-height: 440px !important;
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
        background: color-mix(in srgb, var(--step5-tone) 18%, transparent);
        color: light-dark(#4a3710, #f8e7b8);
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
        background: color-mix(in srgb, var(--step6-tone) 18%, transparent);
        color: light-dark(#4a3710, #f8e7b8);
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

    /* STEP3: MBTI 입력 + 엔터 — 모바일·PC 가로 2열 고정 */
    .st-key-step3_mbti_input_row,
    .st-key-step3_aptitude_mbti .st-key-step3_mbti_input_row {
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    .st-key-step3_mbti_input_row [data-testid="stVerticalBlock"],
    .st-key-step3_aptitude_mbti .st-key-step3_mbti_input_row [data-testid="stVerticalBlock"] {
        flex-wrap: nowrap !important;
        width: 100% !important;
    }
    .st-key-step3_mbti_input_row [data-testid="stHorizontalBlock"],
    .st-key-step3_aptitude_mbti .st-key-step3_mbti_input_row [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: flex-end !important;
        gap: clamp(0.35rem, 2vw, 0.55rem) !important;
        width: 100% !important;
    }
    .st-key-step3_mbti_input_row [data-testid="stHorizontalBlock"] > div,
    .st-key-step3_aptitude_mbti .st-key-step3_mbti_input_row [data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0 !important;
        min-width: 0 !important;
        width: auto !important;
    }
    .st-key-step3_mbti_input_row [data-testid="stHorizontalBlock"] > div:first-child,
    .st-key-step3_aptitude_mbti .st-key-step3_mbti_input_row [data-testid="stHorizontalBlock"] > div:first-child {
        flex: 1.55 1 0 !important;
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
    .st-key-step3_mbti_input_row .stButton > button,
    .st-key-step3_aptitude_mbti .st-key-step3_mbti_input_row .stButton > button {
        width: 100% !important;
        min-height: clamp(2.45rem, 11vw, 3rem) !important;
        font-size: clamp(12px, 3.2vw, 14px) !important;
        font-weight: 800 !important;
        border-radius: 12px !important;
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
        border-radius: 14px !important;
        border: 1px solid light-dark(rgba(148,163,184,0.25), rgba(212,175,55,0.2)) !important;
        background: light-dark(#ffffff, rgba(26,26,46,0.75)) !important;
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

    /* STEP11: 상담 버튼 가로 3열 고정(모바일 인앱 세로 스택 방지) + 질문창을 버튼 바로 아래 */
    div[class*="st-key-step11_consult_strip"] {
        margin-top: 0.5rem !important;
    }
    div[class*="st-key-step11_consult_strip"] [data-testid="stVerticalBlock"] {
        flex-wrap: nowrap !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    div[class*="st-key-step11_consult_strip"] [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 6px !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    div[class*="st-key-step11_consult_strip"] [data-testid="stHorizontalBlock"] > div {
        flex: 1 1 0 !important;
        min-width: 0 !important;
        width: 33.333% !important;
        max-width: 33.333% !important;
    }
    div[class*="st-key-step11_consult_strip"] [data-testid="column"] {
        flex: 1 1 0 !important;
        min-width: 0 !important;
    }
    div[class*="st-key-step11_consult_strip"] .stLinkButton > a,
    div[class*="st-key-step11_consult_strip"] .stButton > button {
        width: 100% !important;
        min-height: 2.75rem !important;
        height: auto !important;
        max-height: none !important;
        padding: 0.4rem 0.2rem !important;
        font-size: max(12px, 0.8rem) !important;
        white-space: nowrap !important;
        text-align: center !important;
        line-height: 1.15 !important;
    }
    div[class*="st-key-step11_consult_strip"] [data-testid="stChatInput"] {
        position: relative !important;
        bottom: auto !important;
        margin-top: 0.35rem !important;
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
    div[class*="st-key-step11_memo_download_panel"] .stButton > button {
        width: 100% !important;
        min-height: 2.75rem !important;
        font-size: max(11px, 0.78rem) !important;
        white-space: normal !important;
        line-height: 1.2 !important;
        padding: 0.45rem 0.35rem !important;
    }

    /* ===== Top5: 글로벌 프리미엄 크롬 (버튼·캡션·링크·운세 카드) ===== */
    .stApp .stButton > button[kind="primary"],
    .stApp div[data-testid="stBaseButton-primary"] {
        border-radius: 16px !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
        box-shadow: 0 4px 18px rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(212, 175, 55, 0.22) !important;
    }
    .stApp .stButton > button[kind="primary"]:hover,
    .stApp div[data-testid="stBaseButton-primary"]:hover {
        filter: brightness(1.05) saturate(1.05);
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.16), 0 0 0 1px rgba(232, 185, 35, 0.32) !important;
    }
    .stApp .stButton > button[kind="secondary"] {
        border-radius: 15px !important;
        font-weight: 700 !important;
        border: 1px solid light-dark(rgba(212, 175, 55, 0.35), rgba(212, 175, 55, 0.25)) !important;
    }
    /* STEP 하단 독은 HTML 링크(.saju-dock-a)로 렌더 — secondary 버튼 오버라이드 불필요 */
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
        border-radius: 12px !important;
        border: 1px solid light-dark(rgba(212, 175, 55, 0.35), rgba(212, 175, 55, 0.28)) !important;
        padding: 0.35rem 0.65rem !important;
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
        border-radius: 14px !important;
        border: 1px solid light-dark(rgba(212, 175, 55, 0.22), rgba(212, 175, 55, 0.18)) !important;
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
    }
    html.saju-dark-tone .main .block-container::before {
        opacity: 0.88 !important;
        filter: saturate(0.95) brightness(0.97) !important;
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
    html.saju-dark-tone .stApp .stButton > button[kind="primary"],
    html.saju-dark-tone .stApp div[data-testid="stBaseButton-primary"] {
        filter: none !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(212, 175, 55, 0.35) !important;
    }
    html.saju-dark-tone .stApp .stButton > button[kind="primary"]:hover,
    html.saju-dark-tone .stApp div[data-testid="stBaseButton-primary"]:hover {
        filter: brightness(1.06) saturate(1.05) !important;
        box-shadow: 0 6px 26px rgba(0, 0, 0, 0.48), 0 0 0 1px rgba(232, 185, 35, 0.42) !important;
    }
    html.saju-dark-tone .st-key-step6_today_pick_row .stButton > button {
        border-color: rgba(212, 175, 55, 0.28) !important;
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
        background: light-dark(rgba(255, 252, 245, 0.92), rgba(15, 23, 42, 0.55));
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
        color: light-dark(#475569, #cbd5e1);
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
        border: 1px solid color-mix(in srgb, var(--ms-tone, #d4af37) 50%, transparent);
        padding: 0.75rem 0.55rem;
        min-height: 6.5rem;
        background: rgba(0,0,0,0.2);
    }
    .saju-match-slide-label { font-weight: 800; font-size: 0.9rem; color: var(--ms-tone); }
    .saju-match-slide-body { font-size: 0.78rem; line-height: 1.4; margin: 0.35rem 0 0; opacity: 0.9; }
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
    .saju-dw-chip--sel { background: rgba(212,175,55,0.18); color: #f5e6a8; }

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
        border-radius: 18px; border: 1px solid rgba(212,175,55,0.4);
        padding: 1.1rem; background: rgba(0,0,0,0.25); margin: 0.5rem 0 1rem;
    }
    .saju-sinsal-flip-front { font-size: 1.5rem; font-weight: 800; color: #d4af37; }
    .saju-sinsal-flip-back { margin: 0.65rem 0 0; line-height: 1.55; font-size: 0.92rem; opacity: 0.92; }
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

</style>
""",
        unsafe_allow_html=True,
    )
    try:
        from saju_app.ui.element_theme import inject_element_theme_styles

        inject_element_theme_styles()
    except Exception:
        pass
    try:
        from saju_app.ui.premium_motion import inject_premium_motion_styles

        inject_premium_motion_styles()
    except Exception:
        pass
    try:
        from saju_app.ui.dark_theme_polish import inject_dark_theme_tone_class

        inject_dark_theme_tone_class()
    except Exception:
        pass
    try:
        from saju_app.ui.pwa_support import inject_pwa_manifest_and_sw

        inject_pwa_manifest_and_sw()
    except Exception:
        pass
    try:
        from saju_app.ui.extras_integration import apply_global_streamlit_extras

        apply_global_streamlit_extras()
    except Exception:
        pass
    try:
        from saju_app.ui import components as _saju_nav

        _saju_nav.try_restore_step2_from_disk_prefill_if_needed()
    except Exception:
        pass
