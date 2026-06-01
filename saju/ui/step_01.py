"""STEP 1 — 랜딩 / 메인 화면 (히어로·24절기·CTA). 하단 이동은 라우터 전역 바를 사용합니다."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from saju_app.ui import components as M
from saju_app.ui import revisit_auth as Revisit
from saju_app.ui import solar_terms_24 as ST24
from saju_app.ui import webapp_launch as W
from saju.ui.home_hero_banner import (
    ensure_step01_hero_banner_file,
    step01_hero_banner_html,
)
from saju_app.ui.execution import inject_home_scroll_after_solar24


def _hero_html() -> str:
    _seal_svg = """
<svg class="saju-landing-seal-svg" viewBox="0 0 128 128" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <defs>
    <linearGradient id="sajuSealGold" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#5c4a18"/>
      <stop offset="28%" stop-color="#c9a227"/>
      <stop offset="48%" stop-color="#f8e9b8"/>
      <stop offset="62%" stop-color="#d4af37"/>
      <stop offset="100%" stop-color="#7a6020"/>
    </linearGradient>
    <radialGradient id="sajuSealInk" cx="50%" cy="42%" r="68%">
      <stop offset="0%" stop-color="#3a3028"/>
      <stop offset="72%" stop-color="#14110e"/>
      <stop offset="100%" stop-color="#080706"/>
    </radialGradient>
    <filter id="sajuSealGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="2" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <circle cx="64" cy="64" r="58" fill="none" stroke="url(#sajuSealGold)" stroke-width="3.5" opacity="0.45"/>
  <circle cx="64" cy="64" r="54" fill="none" stroke="url(#sajuSealGold)" stroke-width="6"/>
  <circle cx="64" cy="64" r="44" fill="url(#sajuSealInk)" stroke="rgba(232,201,113,0.42)" stroke-width="1.5"/>
  <text x="64" y="73" text-anchor="middle" font-size="30" font-weight="800" fill="#f0dfa8" font-family="'Noto Serif KR',Georgia,serif" filter="url(#sajuSealGlow)">命</text>
</svg>
""".strip()
    _pattern_svg = """
<svg class="saju-landing-pattern-svg" viewBox="0 0 800 320" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
  <defs>
    <linearGradient id="sajuPatGold" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#ffd86a" stop-opacity="0"/>
      <stop offset="35%" stop-color="#fff4c4" stop-opacity="0.55"/>
      <stop offset="50%" stop-color="#ffffff" stop-opacity="0.75"/>
      <stop offset="65%" stop-color="#ffd86a" stop-opacity="0.5"/>
      <stop offset="100%" stop-color="#c9a227" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="sajuPatSpot" cx="50%" cy="40%" r="65%">
      <stop offset="0%" stop-color="#ffe9a8" stop-opacity="0.5"/>
      <stop offset="55%" stop-color="#d4af37" stop-opacity="0.15"/>
      <stop offset="100%" stop-color="#7c5cff" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="800" height="320" fill="url(#sajuPatSpot)"/>
  <g fill="none" stroke="url(#sajuPatGold)" stroke-width="1.2" opacity="0.9">
    <path d="M-40 90 L840 40"/>
    <path d="M-20 160 Q200 60 400 150 T820 120"/>
    <path d="M0 230 Q260 120 400 210 T800 190"/>
    <ellipse cx="400" cy="150" rx="180" ry="52" opacity="0.35"/>
  </g>
  <g fill="url(#sajuPatGold)" opacity="0.35">
    <circle cx="120" cy="80" r="2"/><circle cx="680" cy="100" r="2.5"/>
    <circle cx="540" cy="240" r="2"/><circle cx="260" cy="200" r="1.8"/>
  </g>
</svg>
""".strip()
    _sparks = """
<div class="saju-landing-sparks" aria-hidden="true">
  <span class="saju-landing-spark"></span>
  <span class="saju-landing-spark"></span>
  <span class="saju-landing-spark"></span>
  <span class="saju-landing-spark"></span>
  <span class="saju-landing-spark"></span>
  <span class="saju-landing-spark"></span>
</div>
""".strip()
    _corners = """
<span class="saju-landing-corner saju-landing-corner-tl" aria-hidden="true"></span>
<span class="saju-landing-corner saju-landing-corner-tr" aria-hidden="true"></span>
<span class="saju-landing-corner saju-landing-corner-bl" aria-hidden="true"></span>
<span class="saju-landing-corner saju-landing-corner-br" aria-hidden="true"></span>
""".strip()
    # 홈 히어로 핀 고정 JS는 `inject_home_hero_pin_tail()`에서만 주입합니다.
    # (여기서 또 주입하면 중복 실행으로 인해 모바일 레이아웃이 흔들릴 수 있습니다.)
    _pin_script = ""
    return f"""
<div id="saju-home-hero-top" class="saju-landing-hero saju-landing-hero--intense saju-landing-hero--face saju-landing-hero--luxe saju-landing-hero--nova">
  <div class="saju-landing-hero-aurora" aria-hidden="true"></div>
  <div class="saju-landing-hero-mesh" aria-hidden="true"></div>
  <div class="saju-landing-hero-rays" aria-hidden="true"></div>
  <div class="saju-landing-hero-topline" aria-hidden="true"></div>
  <div class="saju-landing-hero-beam" aria-hidden="true"></div>
  <div class="saju-landing-hero-shimmer" aria-hidden="true"></div>
  {_corners}
  <div class="saju-landing-illu-wrap" aria-hidden="true">{_pattern_svg}</div>
  {_sparks}
  <div class="saju-landing-hero-glow" aria-hidden="true"></div>
  <div class="saju-landing-hero-inner">
    <div class="saju-landing-hero-stack">
      <p class="saju-landing-eyebrow">프리미엄 · 럭셔리 사주</p>
      <div class="saju-landing-logo-row saju-landing-logo-row--stacked">
        <div class="saju-landing-seal-wrap">{_seal_svg}</div>
        <div class="saju-landing-brand-block">
          <div class="saju-landing-brand">사주까기</div>
          <p class="saju-landing-kicker">럭셔리 사주 인사이트</p>
        </div>
      </div>
      <p class="saju-landing-tagline">
        당신의 <span class="saju-landing-tagline-accent">운명</span>을 정밀하게 읽다
      </p>
    </div>
  </div>
</div>
{_pin_script}
""".strip()


def render() -> None:
    if int(st.session_state.get("step", 1)) != 1:
        return

    def _go_step2() -> None:
        st.session_state["_step2_need_fresh_form"] = True
        M.navigate_to_step(2)

    ensure_step01_hero_banner_file(force=True)

    with st.container(key="saju_landing_hero"):
        banner_html = step01_hero_banner_html()
        st.markdown(
            banner_html if banner_html else _hero_html(),
            unsafe_allow_html=True,
        )

    with st.container(key="saju_landing_stack"):
        with st.container(key="step1_solar24"):
            components.html(
                ST24.solar_term_frame_html(),
                height=600,
                scrolling=False,
            )
            inject_home_scroll_after_solar24()

        Revisit.render_revisit_home_header()

        with st.container(key="step1_cta_row_main"):
            with st.form("step1_revisit_login_form", clear_on_submit=False, border=False):
                try:
                    c_pin, c_load = st.columns(
                        2, gap="small", vertical_alignment="bottom"
                    )
                except TypeError:
                    c_pin, c_load = st.columns(2, gap="small")
                with c_pin:
                    M.render_revisit_pin_rule_hint(home=True)
                    revisit_pin = M.revisit_pin_input_no_autofill(
                        "비밀번호",
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
            if int(st.session_state.get("step", 1)) != 1:
                st.stop()

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

