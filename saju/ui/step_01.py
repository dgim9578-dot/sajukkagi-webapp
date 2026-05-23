"""STEP 1 — 랜딩 / 메인 화면 (히어로·24절기·CTA). 하단 이동은 라우터 전역 바를 사용합니다."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from saju_app.ui import components as M
from saju_app.ui import revisit_auth as Revisit
from saju_app.ui import solar_terms_24 as ST24
from saju_app.ui import webapp_launch as W


def _step1_footer_ornament_html() -> str:
    """랜딩 하단 장식 — 골드 라인 전통 문양(SVG)."""
    return """
<div class="saju-step1-footer-ornament" aria-hidden="true">
  <svg viewBox="0 0 400 56" xmlns="http://www.w3.org/2000/svg" width="100%" height="56" preserveAspectRatio="xMidYMid meet">
    <defs>
      <linearGradient id="sajuFootOrnStroke" x1="0%" y1="0%" x2="100%" y2="0%">
        <stop offset="0%" stop-color="#a68b3a" stop-opacity="0.2"/>
        <stop offset="22%" stop-color="#d4af37" stop-opacity="0.95"/>
        <stop offset="50%" stop-color="#f0e0a8" stop-opacity="0.9"/>
        <stop offset="78%" stop-color="#d4af37" stop-opacity="0.95"/>
        <stop offset="100%" stop-color="#a68b3a" stop-opacity="0.2"/>
      </linearGradient>
    </defs>
    <g fill="none" stroke="url(#sajuFootOrnStroke)" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round">
      <path d="M8 30c18-22 52-22 70 0c10 12 10 28 0 40M78 30c-18-22-52-22-70 0"/>
      <path d="M322 30c18-22 52-22 70 0M392 30c-18-22-52-22-70 0c-10 12-10 28 0 40"/>
      <path d="M108 40h184"/>
      <circle cx="200" cy="28" r="7" stroke-opacity="0.9"/>
      <path d="M200 21v14M193 28h14" stroke-width="1"/>
    </g>
    <g fill="#d4af37" fill-opacity="0.35" stroke="none">
      <circle cx="200" cy="28" r="2.2"/>
    </g>
  </svg>
</div>
""".strip()


def _hero_html() -> str:
    # 인라인 SVG: 금박 링 + 먹 중심(브랜드 각인 느낌)
    _seal_svg = """
<svg class="saju-landing-seal-svg" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <defs>
    <linearGradient id="sajuSealGold" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#6b5420"/>
      <stop offset="38%" stop-color="#d4af37"/>
      <stop offset="55%" stop-color="#f5e6a8"/>
      <stop offset="72%" stop-color="#d4af37"/>
      <stop offset="100%" stop-color="#8a6d1a"/>
    </linearGradient>
    <radialGradient id="sajuSealInk" cx="50%" cy="45%" r="65%">
      <stop offset="0%" stop-color="#2a2218"/>
      <stop offset="100%" stop-color="#0f0c0a"/>
    </radialGradient>
  </defs>
  <circle cx="60" cy="60" r="56" fill="none" stroke="url(#sajuSealGold)" stroke-width="5"/>
  <circle cx="60" cy="60" r="46" fill="url(#sajuSealInk)" stroke="rgba(212,175,55,0.35)" stroke-width="1.2"/>
  <text x="60" y="68" text-anchor="middle" font-size="28" font-weight="800" fill="#e8d5a0" font-family="Noto Serif KR,serif">命</text>
</svg>
""".strip()
    # 금색 용·봉황 실루엣(장식, 낮은 대비)
    _illus_svg = """
<svg class="saju-landing-illus-svg" viewBox="0 0 420 200" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
  <defs>
    <linearGradient id="sajuIlluGoldStroke" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#6b5420" stop-opacity="0.55"/>
      <stop offset="45%" stop-color="#e8c547" stop-opacity="0.75"/>
      <stop offset="100%" stop-color="#8a6d1a" stop-opacity="0.5"/>
    </linearGradient>
  </defs>
  <g opacity="0.9" fill="none" stroke="url(#sajuIlluGoldStroke)" stroke-width="1.35" stroke-linecap="round" stroke-linejoin="round">
    <!-- 용(좌): S자 몸통·비늘 느낌 -->
    <path d="M48 148c-18-32-12-68 14-88 22-16 52-12 68 8 10 12 8 28-4 38-14 12-36 14-52 28-10 10-8 26 8 30 18 4 36-8 44-26 6-14 4-30-6-42"/>
    <path d="M58 72c12-6 28-4 40 4M70 96c8 10 20 14 34 10M52 118c10 18 28 26 48 20"/>
    <!-- 봉황(우): 날개·꼬리 곡선 -->
    <path d="M268 154c-6-38 8-72 36-88 22-12 48-10 64 8 14 16 12 40-6 52-16 10-40 8-56 22-12 12-10 32 10 38 22 6 44-6 54-28 8-18 6-40-8-56"/>
    <path d="M318 82c14 8 26 22 30 40M302 108c-6 14-4 32 8 44M338 124c12-4 24-2 34 6"/>
  </g>
</svg>
""".strip()
    return f"""
<div class="saju-landing-hero">
  <div class="saju-landing-illu-wrap" aria-hidden="true">{_illus_svg}</div>
  <div class="saju-landing-hero-inner">
    <div class="saju-landing-logo-row">
      <div class="saju-landing-seal-wrap">{_seal_svg}</div>
      <div class="saju-landing-brand-block">
        <div class="saju-landing-brand">사주까기</div>
        <p class="saju-landing-kicker">LUXURY SAJU INSIGHT</p>
      </div>
    </div>
    <p class="saju-landing-tagline">당신의 운명을 정밀하게 읽다</p>
  </div>
</div>
""".strip()


def render() -> None:
    def _go_step2() -> None:
        st.session_state._step2_force_blank = True
        M.navigate_to_step(2)

    with st.container(key="saju_landing_stack"):
        with st.container(key="saju_landing_hero"):
            st.markdown(_hero_html(), unsafe_allow_html=True)

        with st.container(key="step1_solar24"):
            components.html(
                ST24.solar_term_frame_html(),
                height=700,
                scrolling=True,
            )

        Revisit.render_revisit_home_header()

        # 비밀번호 입력 포커스 상태에서 일반 버튼을 누르면 첫 클릭이 blur만 처리되는 경우가 있어 form으로 묶습니다.
        with st.form("step1_revisit_login_form", clear_on_submit=False, border=False):
            with st.container(key="step1_cta_row_main"):
                try:
                    c_pin, c_load = st.columns(
                        2, gap="small", vertical_alignment="bottom"
                    )
                except TypeError:
                    c_pin, c_load = st.columns(2, gap="small")
                with c_pin:
                    revisit_pin = st.text_input(
                        "비밀번호",
                        type="password",
                        key="step1_revisit_pin_in",
                        placeholder="비밀번호*",
                        label_visibility="collapsed",
                    )
                with c_load:
                    load_submitted = st.form_submit_button(
                        "내 기록 불러오기",
                        type="primary",
                        use_container_width=True,
                    )
        if load_submitted:
            Revisit.process_revisit_login(
                str(revisit_pin or st.session_state.get("step1_revisit_pin_in") or "")
            )

        with st.container(key="step1_cta_row_free"):
            st.button(
                "지금 무료로 사주 보기",
                key="saju_landing_cta_main",
                type="primary",
                use_container_width=True,
                on_click=_go_step2,
            )

        with st.container(key="saju_landing_cta"):
            W.render_step1_premium_button(key="step1_premium_cta")
            W.render_step1_phone_caption()

    if not M.analysis_flow_unlocked():
        with st.container(key="step1_footer_ornament"):
            st.markdown(_step1_footer_ornament_html(), unsafe_allow_html=True)
