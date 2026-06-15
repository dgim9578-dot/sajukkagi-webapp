"""STEP 4 — 궁합 분석."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from saju.core.engine import get_element_scores
from saju.core.gapja_utils import (
    day_pillar_from_gapja,
    format_day_branch_rel_label,
    ilju_parts_from_gapja,
)

from saju_app.ui import analysis_favorite_memo as AFM
from saju_app.ui import consulting_corpus as CC
from saju_app.ui import components as M
from saju_app.ui import pdf_utils
from saju_app.ui import step4_match_analysis as M4
from saju_app.ui.execution import rerun_full_app


def _step4_pdf_plain(
    *,
    u_name: str,
    p_name: str,
    u_ilju: str,
    p_ilju: str,
    u_strength: str,
    p_strength: str,
    u_max_el: str,
    u_min_el: str,
    p_max_el: str,
    p_min_el: str,
    u_yong: str,
    p_yong: str,
    day_branch_rel: str,
    u_day_branch: str | None,
    p_day_branch: str | None,
    u_next_3: list[str],
    p_next_3: list[str],
    match_pct: int,
) -> str:
    u_nb = str(u_day_branch or "")
    p_nb = str(p_day_branch or "")
    u3 = ", ".join(u_next_3)
    p3 = ", ".join(p_next_3)
    return (
        f"{u_name}님 · {p_name}님 궁합 분석 (STEP4)\n\n"
        f"정밀 궁합 핵심 스코어: 종합 {match_pct}% (0~100)\n"
        "핵심 기준: 일주/일지(합·충)\n\n"
        f"[본인] {u_name}\n"
        f"일주 {u_ilju} · 강약 {u_strength}\n"
        f"강한 오행 {u_max_el} / 약한 {u_min_el} · 용신 {u_yong}\n\n"
        f"[상대] {p_name}\n"
        f"일주 {p_ilju} · 강약 {p_strength}\n"
        f"강한 오행 {p_max_el} / 약한 {p_min_el} · 용신 {p_yong}\n\n"
        f"일지 관계: {u_nb} ↔ {p_nb} ({day_branch_rel})\n\n"
        "--- 나의 인연과 맞는 유형(요약) ---\n\n"
        "만나기 좋은 흐름은 다음 대운 간지 흐름을 먼저 점검합니다.\n"
        f"{u_name}: {u3}\n"
        f"{p_name}: {p3}\n\n"
        "오행 방향은 배우자별(재성/관성) 관점에서 서로의 빈틈을 메우는 축을 참고합니다.\n\n"
        "--- 입체 궁합 해석 ---\n\n"
        "성격\n"
        f"성격은 일간·일주가 본체입니다. {u_name}({u_ilju})·{p_name}({p_ilju})의 기질이 비슷하면 편안하고, "
        "다르면 자극이 커집니다.\n\n"
        "감정\n"
        f"감정 흐름은 일지(배우자 자리) 영향이 큽니다. {u_nb}↔{p_nb}는 {day_branch_rel}로, "
        "합이면 정서적 결속이 쉬우며 충이면 오해·타이밍 이슈를 관리해야 합니다.\n\n"
        "생활\n"
        "생활 방식은 오행 리듬이 좌우합니다. 강한 오행이 동일하면 생활패턴이 닮지만, 쏠림도 같이 커질 수 있어 "
        "약한 오행 보완이 중요합니다.\n\n"
        "돈\n"
        "돈 쓰는 방식은 재성(財) 성향이 드러납니다. 특히 남자에게는 재성, 여자에게는 관성이 배우자·책임으로 "
        "작동해 생활 재정의 기준점이 됩니다.\n\n"
        "갈등\n"
        f"갈등 처리는 충(沖) 여부와 강약 차이에서 터집니다. 일지 관계가 {day_branch_rel}이므로, "
        "충이면 규칙·합의(생활 룰)를 먼저 만들어두는 게 유리합니다.\n\n"
        "성적\n"
        "성적 에너지는 단일 지표로 단정하기 어렵고, 주로 일지·오행(화·수) 밸런스와 기복 리듬(대운·세운)으로 해석합니다.\n\n"
        "지속성\n"
        f"결혼 지속성은 용신을 함께 살리는가와 대운 리듬이 핵심입니다. 다음 3개 대운: {u_name} {u3}, {p_name} {p3}\n\n"
        "--- 결론 요약 ---\n\n"
        "핵심 강점\n"
        "일주·오행이 서로의 빈틈을 메우면 안정감이 빠르게 올라갑니다.\n\n"
        "주의 포인트\n"
        "일지 충·강약 차이가 크면, 감정 타이밍과 생활 규칙부터 조율해야 합니다.\n\n"
        "실행 포인트\n"
        f"서로의 용신 {u_yong} / {p_yong}을 생활 습관으로 만들면 궁합 체감이 가장 빠르게 좋아집니다.\n"
    ).strip()


def _render_step4_pdf_download(
    *,
    u_name: str,
    p_name: str,
    u_ilju: str,
    p_ilju: str,
    u_strength: str,
    p_strength: str,
    u_max_el: str,
    u_min_el: str,
    p_max_el: str,
    p_min_el: str,
    u_yong: str,
    p_yong: str,
    day_branch_rel: str,
    u_day_branch: str | None,
    p_day_branch: str | None,
    u_next_3: list[str],
    p_next_3: list[str],
    match_pct: int,
) -> None:
    _u = str(u_name or "").strip() or "본인"
    _p = str(p_name or "").strip() or "상대"
    slug = "".join(ch if ch.isalnum() else "_" for ch in f"{_u}_{_p}")[:48]
    stamp = datetime.now().strftime("%Y%m%d")
    title = f"{_u}님 · {_p}님 궁합 리포트"
    body = _step4_pdf_plain(
        u_name=_u,
        p_name=_p,
        u_ilju=u_ilju,
        p_ilju=p_ilju,
        u_strength=u_strength,
        p_strength=p_strength,
        u_max_el=u_max_el,
        u_min_el=u_min_el,
        p_max_el=p_max_el,
        p_min_el=p_min_el,
        u_yong=u_yong,
        p_yong=p_yong,
        day_branch_rel=day_branch_rel,
        u_day_branch=u_day_branch,
        p_day_branch=p_day_branch,
        u_next_3=list(u_next_3),
        p_next_3=list(p_next_3),
        match_pct=match_pct,
    )
    pdf_bytes = pdf_utils.build_report_pdf_bytes(title=title, body=body)
    if pdf_bytes:
        with st.container(key="step4_export_bar"):
            st.download_button(
                label="PDF 리포트 다운로드",
                data=pdf_bytes,
                file_name=f"saju_step4_{slug}_{stamp}.pdf",
                mime="application/pdf",
                key="step4_dl_pdf",
                use_container_width=True,
            )


def _render_match_focus_box(title: str, body: str, *, tone: str = "gold") -> str:
    """궁합 카드 HTML 조각(배치 렌더용)."""
    tones = {
        "gold": ("#D4AF37", "rgba(212, 175, 55, 0.18)"),
        "blue": ("#60A5FA", "rgba(96, 165, 250, 0.16)"),
        "rose": ("#F472B6", "rgba(244, 114, 182, 0.16)"),
        "amber": ("#FBBF24", "rgba(251, 191, 36, 0.18)"),
        "green": ("#34D399", "rgba(52, 211, 153, 0.14)"),
        "purple": ("#A78BFA", "rgba(167, 139, 250, 0.15)"),
    }
    accent, wash = tones.get(tone, tones["gold"])
    return f"""
<div class="step4-focus-box" style="
    margin:0.7rem 0 1rem;
    padding:1rem 1.05rem;
    border-radius:16px;
    border:1px solid {accent};
    background:
        linear-gradient(135deg, {wash} 0%, rgba(255,255,255,0.04) 100%);
    box-shadow:0 10px 28px rgba(0,0,0,0.12), inset 0 0 0 1px rgba(255,255,255,0.08);
">
  <div style="font-weight:800;color:{accent};margin-bottom:0.45rem;">{M._hx(title)}</div>
  <div style="line-height:1.72;">{M._match_body_html(body)}</div>
</div>
"""


def _render_match_sections_batch(sections: list[tuple[str, str, str]]) -> None:
    if not sections:
        return
    st.markdown(
        "".join(_render_match_focus_box(t, b, tone=tone) for t, b, tone in sections),
        unsafe_allow_html=True,
    )


def _navigate_step2_for_partner() -> None:
    M.prepare_step_change_ui()
    st.session_state._return_step_after_input = 4
    M.navigate_to_step(2)


def render() -> None:
    M._resync_user_gapja_from_u_data()
    if not M.partner_is_registered():
        M.reconcile_partner_registration()
    if not M.partner_is_registered():
        M.clear_partner_analysis_state()
    else:
        M.sync_partner_gapja_for_match_analysis()

    u_name = M.session_user_display_name() or "사주까기님"
    u_gapja = list(st.session_state.get("u_gapja") or [])
    p_gapja = list(st.session_state.get("p_gapja") or []) if M.partner_is_registered() else []
    u_gender = st.session_state.get("u_gender", "남자")
    p_gender = st.session_state.get("p_gender", "여자")

    if M.partner_is_registered() and p_gapja and not day_pillar_from_gapja(p_gapja):
        M.sync_partner_gapja_for_match_analysis()
        p_gapja = list(st.session_state.get("p_gapja") or [])

    if (
        M.partner_is_registered()
        and p_gapja
        and len(p_gapja) >= 3
        and not day_pillar_from_gapja(p_gapja)
    ):
        _pn_gate = str(
            st.session_state.get("partner_name_snapshot")
            or st.session_state.get("p_name")
            or "상대"
        ).strip()
        st.error(
            f"상대방 **{M._hx(_pn_gate)}** 일주(일지)를 계산하지 못했습니다. "
            "STEP2 **상대방정보**에서 생년월일·달력(양/음력)을 확인한 뒤 "
            "**저장하고 사주 분석 시작**을 다시 눌러 주세요."
        )
        st.button(
            "← 정보 입력(상대방)으로",
            use_container_width=True,
            key="step4_gate_partner_ilju",
            on_click=_navigate_step2_for_partner,
        )
        return

    if not u_gapja or len(u_gapja) < 3:
        _, mid, _ = st.columns([1, 3, 1])
        with mid:
            st.error(
                "궁합 분석을 하려면 **본인 사주**가 먼저 필요합니다. "
                "정보 입력(STEP2)에서 생년월일·시간을 저장한 뒤 다시 오시거나, 이미 입력하셨다면 **사주 분석(STEP3)**으로 이동해 주세요."
            )
            def _go_step2_then_back() -> None:
                M.prepare_step_change_ui()
                st.session_state._return_step_after_input = 4
                M.navigate_to_step(2)

            c1, c2 = st.columns(2)
            with c1:
                st.button(
                    "← 정보 입력으로",
                    use_container_width=True,
                    key="step4_gate_step2",
                    on_click=_go_step2_then_back,
                )
            with c2:
                st.button(
                    "← 사주 분석으로",
                    use_container_width=True,
                    key="step4_gate_step3",
                    on_click=M.navigate_to_step,
                    args=(3,),
                )
        st.stop()

    if not M.partner_is_registered() or not p_gapja or len(p_gapja) < 3:
        st.info(
            "궁합을 보려면 **상대방 생년월일·시간**이 필요합니다. "
            "STEP2 **상대방정보**에서 이름·생년월일을 입력한 뒤 "
            "**저장하고 사주 분석 시작**을 눌러 주세요."
        )
        def _go_step2_partner_birth() -> None:
            _navigate_step2_for_partner()

        st.button(
            "← 정보 입력(상대방)으로",
            use_container_width=True,
            key="step4_gate_partner_birth",
            on_click=_go_step2_partner_birth,
        )
        return

    _pn_raw = str(
        st.session_state.get("partner_name_snapshot")
        or st.session_state.get("p_name")
        or ""
    ).strip()
    if not _pn_raw:
        M.clear_partner_analysis_state()
        st.warning("상대방 정보가 없습니다. 먼저 정보 입력에서 상대방 이름·생년월일을 등록해 주세요.")
        def _go_step2_partner_name() -> None:
            M.prepare_step_change_ui()
            st.session_state._return_step_after_input = 4
            M.navigate_to_step(2)

        st.button(
            "← 정보 입력으로",
            use_container_width=True,
            key="step4_gate_partner_name",
            on_click=_go_step2_partner_name,
        )
        st.stop()

    p_name = _pn_raw

    if M.partner_gapja_same_as_user():
        st.error(
            "상대방 사주가 **본인과 동일한 간지**로 잡혀 있습니다. "
            "STEP2 **상대방정보**에서 상대 **생년월일·시간**을 본인과 다르게 입력한 뒤 "
            "**저장하고 사주 분석 시작**을 다시 눌러 주세요."
        )
        st.button(
            "← 정보 입력(상대방)으로",
            use_container_width=True,
            key="step4_gate_same_gapja",
            on_click=_go_step2_partner_birth,
        )
        st.stop()

    with M.premium_analysis_shell(4):
        AFM.render_analysis_favorite_memo_band(step=4)
        st.markdown(
            f"<h2 style='text-align:center; color:#F472B6;'>💞 {M._hx(u_name)}님과 {M._hx(p_name)}님의 입체 궁합</h2>",
            unsafe_allow_html=True,
        )
        M.render_mood_image("step04_hero", variant="hero", alt="궁합 분석")
        M.render_step_intro_banner(
            "연애·결혼·인연은 두 번째 핵심 축이에요",
            emoji="💞",
            accent="#f9a8d4",
        )
        u_engine, u_core = M.ensure_engine_and_core(u_gapja)
        p_engine, p_core = M.ensure_engine_and_core(
            p_gapja,
            birth_year=M._birth_year_from_record(st.session_state.get("p_data")),
            birth_record=st.session_state.get("p_data"),
            gender=st.session_state.get("p_gender", "여자"),
            cache_role="partner",
        )

        u_elements = u_engine.get("elements") or get_element_scores(u_gapja)
        p_elements = p_engine.get("elements") or get_element_scores(p_gapja)
        u_max_el, u_min_el = M.top_elements(u_elements)
        p_max_el, p_min_el = M.top_elements(p_elements)
        u_max_el = M.element_to_hanja(u_max_el) or u_max_el
        u_min_el = M.element_to_hanja(u_min_el) or u_min_el
        p_max_el = M.element_to_hanja(p_max_el) or p_max_el
        p_min_el = M.element_to_hanja(p_min_el) or p_min_el

        u_ilju, u_day_stem, u_day_branch = ilju_parts_from_gapja(u_gapja)
        p_ilju, p_day_stem, p_day_branch = ilju_parts_from_gapja(p_gapja)

        u_spouse_el = (
            M.element_i_control(u_engine.get("day_el", "木"))
            if u_gender == "남자"
            else M.element_controls_me(u_engine.get("day_el", "木"))
        )
        p_spouse_el = (
            M.element_i_control(p_engine.get("day_el", "木"))
            if p_gender == "남자"
            else M.element_controls_me(p_engine.get("day_el", "木"))
        )

        u_yong = M.element_to_hanja(str(u_engine.get("yongshin", ""))) or str(
            u_engine.get("yongshin", "") or ""
        ).strip()
        p_yong = M.element_to_hanja(str(p_engine.get("yongshin", ""))) or str(
            p_engine.get("yongshin", "") or ""
        ).strip()

        u_ys = u_gapja[0][0] if u_gapja and u_gapja[0] else "甲"
        p_ys = p_gapja[0][0] if p_gapja and p_gapja[0] else "甲"
        u_next_3 = M.next_daewoon_pillars(
            u_gapja[1] if len(u_gapja) > 1 else "丙寅",
            3,
            gender=u_gender,
            year_stem=u_ys,
        )
        p_next_3 = M.next_daewoon_pillars(
            p_gapja[1] if len(p_gapja) > 1 else "丙寅",
            3,
            gender=p_gender,
            year_stem=p_ys,
        )

        u_day_el = str(u_engine.get("day_el") or "木")
        p_day_el = str(p_engine.get("day_el") or "木")
        _mf = M4.compute_step4_match_factors(
            u_gapja=list(u_gapja),
            p_gapja=list(p_gapja),
            u_day_branch=u_day_branch,
            p_day_branch=p_day_branch,
            u_day_stem=u_day_stem,
            p_day_stem=p_day_stem,
            u_day_el=u_day_el,
            p_day_el=p_day_el,
            u_max_el=u_max_el,
            u_min_el=u_min_el,
            p_max_el=p_max_el,
            p_min_el=p_min_el,
            u_yong=u_yong,
            p_yong=p_yong,
            u_gender=str(u_gender),
            p_gender=str(p_gender),
            u_spouse_el=str(u_spouse_el),
            p_spouse_el=str(p_spouse_el),
            u_next_3=list(u_next_3),
            p_next_3=list(p_next_3),
            get_ten_fn=M.get_detailed_ten_stem,
        )
        day_branch_rel = _mf.day_branch_rel
        day_branch_rel_display = format_day_branch_rel_label(
            str(day_branch_rel), u_day_branch, p_day_branch
        )
        _ms = int(min(100, max(0, int(_mf.match_score))))
        _yong_harmony = (
            "강함"
            if (u_yong and p_yong and u_yong == p_yong)
            else (
                "보완"
                if (u_yong == p_max_el or p_yong == u_max_el)
                else "보통"
            )
        )
        _el_supplement = f"{u_max_el} ↔ {p_min_el}"
        _stem_he_label = (
            _mf.day_stem_he
            if _mf.day_stem_he.startswith("天干合")
            else "없음"
        )
        _mctx = M4.build_step4_match_context(
            u_name=u_name,
            p_name=p_name,
            u_gapja=list(u_gapja),
            p_gapja=list(p_gapja),
            u_engine=u_engine,
            p_engine=p_engine,
            u_max_el=u_max_el,
            u_min_el=u_min_el,
            p_max_el=p_max_el,
            p_min_el=p_min_el,
            u_yong=u_yong,
            p_yong=p_yong,
            u_gender=str(u_gender),
            p_gender=str(p_gender),
            day_branch_rel=str(day_branch_rel),
            day_branch_same=_mf.day_branch_same,
            day_stem_he=_mf.day_stem_he,
            mutual_sheng=_mf.mutual_sheng,
            pillar_harmony=_mf.pillar_harmony,
            pillar_conflict=_mf.pillar_conflict,
            yin_yang_day=_mf.yin_yang_day,
            u_spouse_el=str(u_spouse_el),
            p_spouse_el=str(p_spouse_el),
            u_next_3=list(u_next_3),
            p_next_3=list(p_next_3),
            match_score=_ms,
        )

        M.render_mood_image("step04_mid_score", variant="mid", alt="종합 궁합 지수")
        st.markdown(
            f"""
<div style="text-align:center; margin:20px 0;">
    <h3 style="color:#FBBF24; margin-bottom:8px;">종합 궁합 지수</h3>
    <div style="font-size:3.8rem; font-weight:700; color:#FBBF24;">{_ms}<span style="font-size:1.4rem;">점</span></div>
    <div style="font-size:0.85rem; color:#9CA3AF; margin-top:6px;">(동일 지표 PDF·내부 계산은 0~100 환산)</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.caption(
            "핵심 기준: ①일지(동일·육합·충) ②천간합 ③오행·재성/관성 ④용신·년월합·충 ⑤음양·대운"
        )

        st.markdown(
            f"""
<div class="step4-metric-frame-grid">
  <div class="step4-metric-frame" style="--step4-tone:#F472B6;">
    <div class="step4-metric-title">일지 궁합</div>
    <div class="step4-metric-value">{M._hx(str(day_branch_rel_display))}</div>
  </div>
  <div class="step4-metric-frame" style="--step4-tone:#A78BFA;">
    <div class="step4-metric-title">천간합</div>
    <div class="step4-metric-value">{M._hx(str(_stem_he_label))}</div>
  </div>
  <div class="step4-metric-frame" style="--step4-tone:#60A5FA;">
    <div class="step4-metric-title">용신 조화</div>
    <div class="step4-metric-value">{M._hx(str(_yong_harmony))}</div>
  </div>
  <div class="step4-metric-frame" style="--step4-tone:#D4AF37;">
    <div class="step4-metric-title">오행 보완</div>
    <div class="step4-metric-value">{M._hx(str(_el_supplement))}</div>
  </div>
</div>
<div class="step4-person-pair">
  <div class="step4-person-card step4-person-self">
    <div class="step4-person-name"><span class="step4-person-dot"></span>{M._hx(str(u_name))}</div>
    <div class="step4-person-body">일주 <b>{M._hx(str(u_ilju))}</b> · 강약 <b>{M._hx(str(u_engine.get('strength')))}</b><br>
    강 <b>{M._hx(str(u_max_el))}</b> / 약 <b>{M._hx(str(u_min_el))}</b> · 용신 <b>{M._hx(str(u_yong))}</b></div>
  </div>
  <div class="step4-person-link">◆ · · · ◆</div>
  <div class="step4-person-card step4-person-partner">
    <div class="step4-person-name"><span class="step4-person-dot"></span>{M._hx(str(p_name))}</div>
    <div class="step4-person-body">일주 <b>{M._hx(str(p_ilju))}</b> · 강약 <b>{M._hx(str(p_engine.get('strength')))}</b><br>
    강 <b>{M._hx(str(p_max_el))}</b> / 약 <b>{M._hx(str(p_min_el))}</b> · 용신 <b>{M._hx(str(p_yong))}</b></div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )

        st.divider()

        st.markdown(
            f"<div style='text-align:center;margin:0.4rem 0 1rem;'>"
            f"{M4.pair_analysis_banner(_mctx)}</div>",
            unsafe_allow_html=True,
        )
        st.caption(
            f"분석 조합: 본인 일주 **{u_ilju}** × 상대 일주 **{p_ilju}** · "
            f"상대 네 기둥 **{' · '.join(p_gapja[:4]) if len(p_gapja) >= 4 else p_ilju}** — "
            "상대 생년월일을 바꾸셨다면 STEP2 **저장** 후 이 화면을 새로고침하세요."
        )

        tab1, tab2, tab3, tab4 = st.tabs(
            ["💕 감정·인연", "💼 생활·커리어", "💰 재물", "⚠️ 주의점"]
        )

        with tab1:
            _render_match_sections_batch(
                M4.tab_love_sections(_mctx, get_ten_fn=M.get_detailed_ten_stem)
            )

        with tab2:
            _render_match_sections_batch(
                M4.tab_life_sections(_mctx, get_ten_fn=M.get_detailed_ten_stem)
            )

        with tab3:
            _render_match_sections_batch(M4.tab_wealth_sections(_mctx))

        with tab4:
            _render_match_sections_batch(M4.tab_caution_sections(_mctx))

        st.divider()

        CC.render_consulting_panel(
            CC.query_for_step("step4", topic="궁합", ilju=u_ilju),
            apply="step4",
            title="💬 현장 상담 참고 (연애·궁합)",
            expanded=False,
            container_key="step4_consulting_love",
        )

        st.subheader("🧭 결론 요약")
        c1, c2, c3 = st.columns(3)
        for col, section in zip(
            (c1, c2, c3),
            M4.conclusion_sections(_mctx, get_ten_fn=M.get_detailed_ten_stem),
        ):
            with col:
                _render_match_sections_batch([section])

        _render_step4_pdf_download(
            u_name=u_name,
            p_name=str(p_name),
            u_ilju=u_ilju,
            p_ilju=p_ilju,
            u_strength=str(u_engine.get("strength", "")),
            p_strength=str(p_engine.get("strength", "")),
            u_max_el=str(u_max_el),
            u_min_el=str(u_min_el),
            p_max_el=str(p_max_el),
            p_min_el=str(p_min_el),
            u_yong=u_yong,
            p_yong=p_yong,
            day_branch_rel=str(day_branch_rel),
            u_day_branch=u_day_branch,
            p_day_branch=p_day_branch,
            u_next_3=list(u_next_3),
            p_next_3=list(p_next_3),
            match_pct=_ms,
        )
