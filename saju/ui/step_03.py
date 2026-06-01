"""STEP 3 — 사주 분석 결과 (메인 차트 · 인생 핵심 운세)."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from saju_app.ui import analysis_favorite_memo as AFM
from saju_app.ui import components as M
from saju_app.ui import consulting_corpus as CC
from saju_app.ui import aptitude_mbti as APT
from saju_app.ui.briefing_life_sync import health_tip_from_engine
from saju_app.ui import element_theme as ElTheme
from saju_app.ui import gapja_master_chart as GapjaChart
from saju_app.ui import pdf_utils
from saju_app.ui.interpretation_layout import (
    StructuredInterpretation,
    build_step3_interpretation,
    format_structured_interpretation_for_pdf,
    render_structured_interpretation_block,
)


def _step3_health_tip_text(*, strength: str, max_el: str, min_el: str) -> str:
    """원국 기준 건강·체질 힌트."""
    return health_tip_from_engine(strength=strength, max_el=max_el, min_el=min_el)


def _step3_life_core_grid(
    engine: dict[str, object],
    *,
    strength: str,
    max_el: str,
    min_el: str,
) -> None:
    """재물·혼인·커리어·원국 체질 힌트 — 아코디언(접이식) 목록."""
    ws = str(engine.get("wealth_strength") or "5")
    wc = str(engine.get("wealth_comment") or "재물운 분석 중...")
    ms = str(engine.get("marriage_strength") or "5")
    mc = str(engine.get("marriage_comment") or "혼인운 분석 중...")
    cs = str(engine.get("career_strength") or "5")
    cc = str(engine.get("career_comment") or "커리어운 분석 중...")
    tip = _step3_health_tip_text(strength=strength, max_el=max_el, min_el=min_el)
    if not str(wc or "").strip():
        wc = "재물운 분석 중..."
    if not str(mc or "").strip():
        mc = "혼인운 분석 중..."
    if not str(cc or "").strip():
        cc = "커리어운 분석 중..."
    if not str(tip or "").strip():
        tip = "원국 오행 균형을 바탕으로 한 체질·생활 리듬 참고 문구입니다."

    scored_items = (
        ("step3_acc_wealth", "💰 재물운", ws, wc, True),
        ("step3_acc_marriage", "❤️ 혼인운", ms, mc, False),
        ("step3_acc_career", "💼 커리어운", cs, cc, False),
    )

    with st.container(key="step3_life_core"):
        st.markdown(
            '<div class="saju-step3-life-core-h saju-theme-accent">나의 인생 핵심 운세</div>',
            unsafe_allow_html=True,
        )
        st.caption("항목을 눌러 펼치면 상세 해석을 볼 수 있습니다.")
        for key, label, score, body, expanded in scored_items:
            with st.expander(f"{label} · {score}/10", expanded=expanded):
                st.markdown(body)
        with st.expander("🩺 원국 체질 힌트", expanded=False):
            st.markdown(tip)
            st.caption("의학적 진단·치료는 반드시 의료기관과 상의하세요.")


def _render_step3_focus_frame(*, title: str, body_html: str, tone: str = "#D4AF37") -> None:
    st.markdown(
        f"""
<div class="saju-step3-focus-frame" style="--step3-tone:{M._hx(tone)};">
    <div class="saju-step3-focus-title">{M._hx(title)}</div>
    <div class="saju-step3-focus-body">{body_html}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_step3_element_frame(el: dict[str, object]) -> None:
    rows: list[str] = []
    for han, ko in (("木", "목"), ("火", "화"), ("土", "토"), ("金", "금"), ("水", "수")):
        v = max(0, min(100, int(el.get(han, 0) or 0)))
        rows.append(
            f"""
<div class="saju-step3-element-row">
    <div class="saju-step3-element-label"><b>{M._hx(ko)}({M._hx(han)})</b> <span>{v}%</span></div>
    <div class="saju-step3-element-track"><div class="saju-step3-element-fill" style="width:{v}%;"></div></div>
</div>
"""
        )
    _render_step3_focus_frame(
        title="오행 비중",
        body_html="".join(rows),
        tone="#D4AF37",
    )


def _render_step3_summary_frame(
    *,
    strength: str,
    yongshin: str,
    need_el_text: str,
    max_el: str,
) -> None:
    body_html = (
        '<ul class="saju-step3-summary-list">'
        f"<li><span>신강/신약</span><b>{M._hx(str(strength))}</b></li>"
        f"<li><span>용신</span><b>{M._hx(str(yongshin))}</b></li>"
        f"<li><span>조후 필요 기운</span><b>{M._hx(str(need_el_text))}</b></li>"
        f"<li><span>가장 강한 오행</span><b>{M._hx(str(max_el))}</b></li>"
        "</ul>"
        f'<div class="saju-step3-focus-note">결론: <b>{M._hx(str(yongshin))}</b> 중심 + 조후 보완이 핵심 전략</div>'
    )
    _render_step3_focus_frame(
        title="핵심 요약",
        body_html=body_html,
        tone="#D4AF37",
    )


def _step3_pdf_plain(
    *,
    u_name: str,
    u_gapja: list[str],
    ix3: StructuredInterpretation,
    strength: str,
    yongshin: str,
    max_el: str,
    need_el_text: str,
) -> str:
    g4 = " · ".join(str(g) for g in u_gapja[:4])
    ix_block = format_structured_interpretation_for_pdf(ix3)
    return (
        f"{u_name}님 사주 분석 (STEP3)\n\n"
        f"팔자(년·월·일·시): {g4}\n\n"
        f"{ix_block}\n\n"
        "체크리스트 요약\n"
        f"• 신강/신약: {strength}\n"
        f"• 용신: {yongshin}\n"
        f"• 조후 필요 기운: {need_el_text}\n"
        f"• 가장 강한 오행: {max_el}\n"
    ).strip()


def _render_step3_pdf_download(
    *,
    u_name: str,
    u_gapja: list[str],
    ix3: StructuredInterpretation,
    strength: str,
    yongshin: str,
    max_el: str,
    need_el_text: str,
) -> None:
    _uname = str(u_name or "").strip() or "고객"
    _slug = "".join(ch if ch.isalnum() else "_" for ch in _uname)[:40]
    _stamp = datetime.now().strftime("%Y%m%d")
    title = f"{_uname}님 사주 분석 리포트"
    body = _step3_pdf_plain(
        u_name=_uname,
        u_gapja=u_gapja,
        ix3=ix3,
        strength=strength,
        yongshin=yongshin,
        max_el=max_el,
        need_el_text=need_el_text,
    )
    pdf_bytes = pdf_utils.build_report_pdf_bytes(title=title, body=body)
    with st.container(key="step3_export_bar"):
        if pdf_bytes:
            pdf_utils.render_pdf_download_button(
                pdf_bytes=pdf_bytes,
                file_name=f"saju_step3_{_slug}_{_stamp}.pdf",
                label="PDF 리포트 다운로드",
                key="step3_dl_pdf",
                use_container_width=True,
            )
        else:
            st.caption(
                "PDF는 PC에서 한글 폰트가 인식될 때 제공됩니다. "
                "모바일에서는 아래 해석을 이용해 주세요."
            )


def render() -> None:
    M._resync_user_gapja_from_u_data()
    u_gapja = st.session_state.get("u_gapja")
    u_name = M.session_user_display_name() or "사주까기님"

    if not u_gapja or len(u_gapja) < 3:
        st.error("사주 정보가 없습니다. 먼저 정보 입력을 진행해주세요.")
        st.button(
            "← 정보 입력으로",
            help="정보 입력(STEP2) 화면으로 돌아가 생년월일을 수정합니다.",
            use_container_width=True,
            on_click=M.navigate_to_step,
            args=(2,),
        )
        st.stop()

    engine, core = M.ensure_engine_and_core(u_gapja)

    _theme_meta: dict = {}
    try:
        import saju_storage as _storage

        _theme_meta = _storage.build_saju_theme_meta(list(u_gapja))
        _t0 = _theme_meta.get("theme") if isinstance(_theme_meta.get("theme"), dict) else {}
        ElTheme.apply_element_data_theme(str(_t0.get("slug") or _t0.get("dominant_element") or "土"))
    except Exception:
        pass

    with M.premium_analysis_shell(3):
        AFM.render_analysis_favorite_memo_band(step=3)
        M.render_mood_image("step03_hero", variant="hero", alt="사주 분석")

        _theme_emoji = ""
        _theme_vibe = ""
        _t = _theme_meta.get("theme") if isinstance(_theme_meta.get("theme"), dict) else {}
        _theme_emoji = str(_t.get("emoji") or "")
        _theme_vibe = str(_t.get("vibe") or "")
        st.markdown(
            f"<h2 class='saju-theme-accent' style='text-align:center;'>"
            f"🧬 {M._hx(u_name)}님의 사주 분석</h2>",
            unsafe_allow_html=True,
        )
        if _theme_vibe:
            st.markdown(
                f"<p class='saju-theme-accent' style='text-align:center;margin-top:-0.5rem;'>"
                f"{M._hx(_theme_emoji)} {M._hx(_theme_vibe)}</p>",
                unsafe_allow_html=True,
            )
        el = engine.get("elements", {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0})
        strength = engine.get("strength", "중화")
        yongshin = engine.get("yongshin", "판단 필요")
        max_el = engine.get("max_el", "木")
        min_el = str(core.get("min_el") or engine.get("min_el") or "水")

        month_branch = u_gapja[1][1] if len(u_gapja) > 1 and len(u_gapja[1]) >= 2 else None
        johu = M.get_johu_advice(month_branch) if month_branch else {"need_elements": []}
        need_el_text = ", ".join(johu.get("need_elements", [])) or "없음"
        ix3 = build_step3_interpretation(u_gapja=u_gapja, engine=engine, core=core)

        with st.container(key="step3_gapja_chart"):
            st.markdown("#### 📍 사주 원국")
            st.caption("기둥을 탭(클릭)하면 아래에 설명이 표시됩니다.")
            GapjaChart.render_gapja_master_chart(list(u_gapja), height=620)

        _step3_life_core_grid(
            engine if isinstance(engine, dict) else {},
            strength=str(strength),
            max_el=str(max_el),
            min_el=str(min_el),
        )

        with st.container(key="step3_trailing_actions"):
            st.markdown(
                '<div class="saju-step3-section-rule" aria-hidden="true"></div>',
                unsafe_allow_html=True,
            )
            _render_step3_pdf_download(
                u_name=u_name,
                u_gapja=list(u_gapja),
                ix3=ix3,
                strength=str(strength),
                yongshin=str(yongshin),
                max_el=str(max_el),
                need_el_text=need_el_text,
            )

        st.subheader("🌟 핵심 해석")
        render_structured_interpretation_block(ix3, container_key="saju_ix")
        st.subheader("📖 요약 · 상세 레이어")
        tab_sum, tab_oheng, tab_johu, tab_yong = st.tabs(
            ["📌 핵심 요약", "🔢 오행", "🌤️ 조후", "🧭 용신"]
        )
        with st.container(key="step3_layered_stack"):
            with tab_sum:
                _render_step3_summary_frame(
                    strength=str(strength),
                    yongshin=str(yongshin),
                    need_el_text=str(need_el_text),
                    max_el=str(max_el),
                )
            with tab_oheng:
                _render_step3_element_frame(el)
            with tab_johu:
                need_html = ""
                if johu.get("need_elements"):
                    need_html = (
                        '<div class="saju-step3-focus-note">'
                        f"보완에 유리한 기운: {M._hx(', '.join(johu.get('need_elements', [])))}"
                        "</div>"
                    )
                _render_step3_focus_frame(
                    title="조후 · 월지 흐름",
                    body_html=(
                        f"<p><b>계절권:</b> {M._hx(str(johu.get('season', '미상')))}</p>"
                        f"<p>{M._hx(str(johu.get('desc', '')))}</p>"
                        f"{need_html}"
                    ),
                    tone="#60A5FA",
                )
            with tab_yong:
                _render_step3_focus_frame(
                    title="용신 활용 팁",
                    body_html=(
                        f"<p>지금 구조(<b>{M._hx(str(strength))}</b>)에서는 "
                        f"<b>{M._hx(str(yongshin))}</b>을 생활 습관·색·환경에 녹이면 "
                        "결정과 체력의 밸런스가 함께 좋아지기 쉽습니다.</p>"
                    ),
                    tone="#FBBF24",
                )

        st.divider()
        with st.container(key="step3_aptitude_mbti"):
                APT.render_step3_aptitude_mbti_block(
                    u_name=str(u_name),
                    u_gapja=list(u_gapja),
                    strength=str(strength),
                    yongshin=str(yongshin),
                    max_el=str(max_el),
                    min_el=str(min_el),
                    ix3=ix3,
                    engine=engine,
                )
