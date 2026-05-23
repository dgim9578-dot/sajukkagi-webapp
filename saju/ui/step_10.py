"""STEP 10 — 심층 총평(오행 해석 통합)."""

from __future__ import annotations

import html
from datetime import datetime
from typing import Any

import streamlit as st

from saju.core.engine import STEM_ELEMENT
from saju_app.ui import analysis_favorite_memo as AFM
from saju_app.ui import consulting_corpus as CC
from saju_app.ui import components as M
from saju_app.ui import pdf_utils


_ORGAN_MAP: dict[str, str] = {
    "木": "간·담낭·눈·신경",
    "火": "심장·혈액·정신",
    "土": "비장·위·소화기",
    "金": "폐·대장·호흡기",
    "水": "신장·방광·생식기·뼈",
}


def _pick_current_daewoon_row(dae: dict[str, Any], current_age: int) -> dict[str, Any] | None:
    """현재 연령이 속한 대운 한 칸(``rows`` 원소)."""
    ca = max(0, int(current_age))
    for row in dae.get("rows") or []:
        try:
            a0 = int(row.get("age_start", 0))
            a1 = int(row.get("age_end", a0 + 9))
        except (TypeError, ValueError):
            continue
        if a0 <= ca <= a1:
            return row
    return None


def _element_pct(elements: dict[str, Any], el: str) -> float:
    try:
        return float(elements.get(el, 0) or 0)
    except (TypeError, ValueError):
        return 0.0


def _dae_health_risk_score(
    *,
    dae_el: str,
    yongshin: str,
    max_el: str,
    min_el: str,
) -> int:
    """대운 천간 오행 vs 용신·원국 강약 → 참고용 위험 점수(높을수록 관리 포인트)."""
    ys_raw = str(yongshin or "").strip()
    ys_ok = ys_raw not in ("", "판단 필요")
    mx_raw = str(max_el or "").strip()
    mn_raw = str(min_el or "").strip()
    de = str(dae_el or "").strip()
    if ys_ok and de == ys_raw:
        return 25
    if de == mx_raw:
        return 65
    if de == mn_raw:
        return 85
    return 45


def _risk_style(score: int) -> tuple[str, str]:
    if int(score) <= 35:
        return "#4ADE80", "🟢 낮음"
    if int(score) <= 60:
        return "#FACC15", "🟡 보통"
    return "#F87171", "🔴 높음"


def _health_weak_points_lines(
    *,
    day_el: str,
    strength: str,
    max_el: str,
    min_el: str,
    month_branch: str,
    elements: dict[str, Any],
    current_age: int | None = None,
) -> list[str]:
    """원국 기준 건강 취약 포인트(참고 문구, 리스트)."""
    weak: list[str] = []
    s = str(strength or "")
    mx = str(max_el or "").strip()
    mn = str(min_el or "").strip()
    de = str(day_el or "").strip()

    organ_mx = _ORGAN_MAP.get(mx, "전신")
    organ_mn = _ORGAN_MAP.get(mn, "전신")

    if "신강" in s:
        weak.append(
            f"• {mx} 기운이 과다해지기 쉬워 {organ_mx} 쪽에 열·당김이 쌓이기 쉽다고 읽을 수 있습니다."
        )
    elif "신약" in s:
        weak.append(
            f"• {mn} 기운이 상대적으로 부족해 {organ_mn} 보완이 생활에서 중요해집니다."
        )

    season = M.get_season_from_month_branch(month_branch) if month_branch else "미상"
    if season == "겨울" and de in ("木", "火"):
        weak.append(
            "• 월령이 한기에 가깝고 목·화 일간은 따뜻한 순환·보온 리듬을 챙기면 컨디션이 덜 흔들립니다."
        )
    elif season == "여름" and de in ("金", "水"):
        weak.append(
            "• 월령이 열기에 가깝고 금·수 일간은 수분·휴식으로 건조·열감을 다스리는 편이 좋습니다."
        )

    if _element_pct(elements, mx) > 35.0:
        weak.append(
            f"• {mx} 비중이 높게 잡혀 {organ_mx} 과부하에 유의하는 것이 좋습니다."
        )
    if _element_pct(elements, mn) < 12.0:
        weak.append(
            f"• {mn} 비중이 낮게 잡혀 {organ_mn} 쪽은 무리가 누적되지 않게 가볍게 관리하는 편이 좋습니다."
        )

    if current_age is not None and int(current_age) >= 33:
        weak.append(
            "• 30대 중반 이후에는 수면·소화·근골격 누적이 체감으로 드러나기 쉬워, 원국에서 약한 축을 미리 생활습관으로 보완하는 편이 유리합니다."
        )
        weak.append(
            "• 만성 질환 가족력이 있다면, 사주의 약한 오행 부위는 **정기 검진 우선순위를 정하는 참고**로만 쓰고, 진단·치료는 반드시 의료기관과 상의하세요."
        )

    return weak


def _health_fortune_html(
    *,
    day_el: str,
    strength: str,
    yongshin: str,
    max_el: str,
    min_el: str,
    month_branch: str,
    elements: dict[str, Any],
    dae_row: dict[str, Any] | None,
    current_age: int | None = None,
) -> str:
    """원국 체질 힌트 + 현재 대운 컨디션 관리 주의도 카드."""
    de = html.escape(str(day_el or "木"))
    stg = html.escape(str(strength or ""))
    ys = html.escape(str(yongshin or "판단 필요"))
    mx = html.escape(str(max_el or "木"))
    mn = html.escape(str(min_el or "水"))

    weak_lines = _health_weak_points_lines(
        day_el=str(day_el or "木"),
        strength=strength,
        max_el=str(max_el or "木"),
        min_el=str(min_el or "水"),
        month_branch=str(month_branch or ""),
        elements=elements if isinstance(elements, dict) else {},
        current_age=current_age,
    )
    if weak_lines:
        weak_block = "<br>".join(html.escape(line) for line in weak_lines)
    else:
        weak_block = html.escape("• 원국 구조가 비교적 균형 잡혀 있습니다.")

    dae_pillar = ""
    dae_el_s = ""
    age_band = ""
    if dae_row and isinstance(dae_row, dict):
        raw_p = str(dae_row.get("pillar", "") or "").strip()
        if len(raw_p) >= 2:
            dae_pillar = raw_p
            dae_stem = raw_p[0]
            dae_el_s = str(STEM_ELEMENT.get(dae_stem, "木"))
            try:
                a0 = int(dae_row.get("age_start", 0))
                a1 = int(dae_row.get("age_end", a0 + 9))
                age_band = f"{a0}–{a1}세 구간"
            except (TypeError, ValueError):
                age_band = ""

    mx_raw = str(max_el or "").strip()
    mn_raw = str(min_el or "").strip()

    risk_score = 50
    if dae_pillar and len(dae_pillar) >= 2:
        risk_score = _dae_health_risk_score(
            dae_el=dae_el_s,
            yongshin=str(yongshin or ""),
            max_el=mx_raw,
            min_el=mn_raw,
        )

    risk_color, risk_label = _risk_style(int(risk_score))

    risk_label_e = html.escape(risk_label)
    age_html = ""
    if age_band:
        age_html = f'<div style="font-size:0.88rem;color:#94A3B8;margin-bottom:8px;">{html.escape(age_band)}</div>'

    return f"""
<div class="saju-card saju-step10-health-card" style="border:2px solid #F472B6;">
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px;">
        <div style="font-size:3.5rem;" aria-hidden="true">🫀</div>
        <div>
            <div style="font-size:1.4rem;font-weight:700;color:#F472B6;">원국 건강 취약점</div>
            <div style="color:#E0E7FF;">{de} 일간 · {stg} 체질</div>
        </div>
    </div>
    <div style="background:rgba(244,114,182,0.09);padding:18px;border-radius:16px;margin-bottom:20px;">
        <b style="color:#F472B6;">용신 <span>{ys}</span> 기준으로 삼아 보강하면 좋은 건강 포인트</b>
    </div>
    <div style="background:#1F2937;padding:18px;border-radius:14px;line-height:1.75;margin-bottom:20px;color:#E5E7EB;font-size:0.98rem;">
        {weak_block}
    </div>
    <div class="saju-step10-risk-block" style="margin-bottom:20px;color:#E0E7FF;">
        {age_html}
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;font-weight:700;flex-wrap:wrap;gap:8px;color:#E0E7FF;">
            <span style="color:#E0E7FF;">📍 현재 대운 컨디션 관리 주의도</span>
            <span class="saju-step10-risk-score" style="color:{risk_color};">{int(risk_score)}% {risk_label_e}</span>
        </div>
    </div>
    <div class="saju-health-tips" style="color:#F1F5F9;">
        💡 <b>생활 속 실천 포인트</b><br>
        • 용신 <b>{ys}</b> 기운을 매일 챙기세요 (색상, 음식, 운동)<br>
        • 약한 오행({mn}) 관련 부위는 정기 검진·가벼운 점검을 검토해 보세요<br>
        • 과로, 스트레스, 불규칙한 생활을 줄이면 원국·대운 리듬을 덜 흔들립니다<br>
        • <b>부모님 건강</b>은 검진·진료가 1순위이며, 년주·월주는 가족 리듬 참고용입니다<br>
        • <b>노후(만 60세 이후)</b>에는 체력·정서 관리를 조금 더 촘촘히 하는 편이 좋습니다
    </div>
</div>
"""


def _exec_point_card(
    *,
    emoji: str,
    title: str,
    subtitle: str,
    accent: str,
    soft_bg: str,
    md_body: str,
) -> None:
    body = html.escape(str(md_body or "")).replace("\n", "<br>")
    st.markdown(
        f"""
<div class="step10-exec-card" style="--step10-tone:{html.escape(str(accent), quote=True)};">
  <div class="step10-exec-title">{html.escape(str(emoji))} {html.escape(str(title))}</div>
  <div class="step10-exec-subtitle">{html.escape(str(subtitle))}</div>
  <div class="step10-exec-body">{body}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def _total_review_frame(u_name: str, combined_md: str) -> None:
    st.subheader("📋 심층 총평 · 오행 통합")
    st.caption(f"{u_name}님을 위한 한 장 요약")
    st.write(combined_md)


def render() -> None:
    u_gapja = M._require_u_gapja_or_halt(
        message="사주 분석 데이터가 없습니다.",
        show_home_button=False,
    )

    u_name = st.session_state.get("u_name", "사주까기님")
    engine, core = M.ensure_engine_and_core(u_gapja)

    u_data = st.session_state.get("u_data", (2000, 1, 1))
    u_gender = st.session_state.get("u_gender", "남자")
    opt = st.session_state.get("saju_options", {}) or {}
    zi_boundary = str(opt.get("zi_boundary", "23:30"))
    birth_y = int(u_data[0]) if u_data else 2000
    cur_age = max(0, M.now_kst().year - birth_y)
    dae_sched = M.compute_daewoon_schedule(
        list(u_gapja),
        u_data,
        str(u_gender),
        birth_y,
        zi_boundary=zi_boundary,
        n_terms=12,
    )
    dae_row = _pick_current_daewoon_row(dae_sched, cur_age)

    el_percents = engine["elements"]
    max_el = core.get("max_el") or max(el_percents, key=el_percents.get)
    min_el = core.get("min_el") or min(el_percents, key=el_percents.get)
    yongshin = core.get("yongshin") or engine.get("yongshin", "판단 필요")
    day_el = str(engine.get("day_el", "木"))
    strength = str(engine.get("strength", "중화"))
    _t10a, _t10b, _t10c = M._step10_exec_point_texts(str(max_el), str(min_el), str(yongshin))

    with M.premium_analysis_shell(10):
        AFM.render_analysis_favorite_memo_band(step=10)
        st.markdown(f"## 📜 {u_name}님 심층 사주 분석 총평")
        st.markdown("### 🫀 건강·노후 참고 — 원국 체질 힌트 + 대운 컨디션 관리")
        st.caption(
            "이 항목은 건강에 관련된 치료를 판단하지 않으니 의료기관과 상의하세요."
        )
        month_branch = str(core.get("month_branch") or "").strip()
        if not month_branch and len(u_gapja) > 1 and len(str(u_gapja[1])) >= 2:
            month_branch = str(u_gapja[1])[1]
        with st.container(key="step10_health_fortune"):
            st.markdown(
                _health_fortune_html(
                    day_el=day_el,
                    strength=strength,
                    yongshin=str(yongshin),
                    max_el=str(max_el),
                    min_el=str(min_el),
                    month_branch=month_branch,
                    elements=dict(el_percents),
                    dae_row=dae_row,
                    current_age=int(cur_age),
                ),
                unsafe_allow_html=True,
            )

        st.divider()

        synopsis = ""
        if core.get("ok"):
            synopsis = str(core.get("interpretation_200", "") or "").strip()
        else:
            synopsis = "핵심 요약을 불러오지 못했습니다. STEP3 사주 분석을 먼저 확인해 주세요."

        oheng_md = M.step10_oheng_blend_markdown(el_percents, str(max_el), str(min_el))

        suffix = (
            "위 내용은 월주·일주를 중심으로 한 핵심 해석에 **오행 밸런스**를 이어 붙인 것입니다. 대운·세운이 겹치면 실제 체감은 달라질 수 있습니다. "
            "같은 팔자라도 선택과 습관이 쌓이는 방향이 다르면 결과는 크게 달라지니, 요약을 체크리스트처럼 하루 한 가지씩 실천에 옮겨 보시길 권합니다. "
            "더 구체적인 부분은 사주까기님 상담에서 선명하게 드러납니다."
        )
        combined = f"{synopsis}\n\n{oheng_md}\n\n{suffix}".strip()
        if len(combined) < 120:
            combined += (
                "\n\n운의 리듬은 시기마다 미세하게 변하므로, 중요한 결정은 여유를 두고 재점검한 뒤 실행하는 편이 안전합니다."
            )

        _uname = str(u_name or "").strip() or "고객"
        _slug = "".join(ch if ch.isalnum() else "_" for ch in _uname)[:40]
        _stamp = datetime.now().strftime("%Y%m%d")
        pdf_title = f"{_uname}님 심층 사주 분석 총평"
        pdf_body = (
            f"{combined}\n\n"
            "실행 포인트\n"
            f"강점: {_t10a}\n\n"
            f"보완: {_t10b}\n\n"
            f"용신: {_t10c}"
        )
        pdf_bytes = pdf_utils.build_report_pdf_bytes(title=pdf_title, body=pdf_body)

        if pdf_bytes:
            with st.container(key="step10_export_bar"):
                st.download_button(
                    label="PDF 리포트 다운로드",
                    data=pdf_bytes,
                    file_name=f"saju_step10_{_slug}_{_stamp}.pdf",
                    mime="application/pdf",
                    key="step10_dl_pdf",
                    use_container_width=True,
                )

        with st.container(key="step10_report_sheet"):
            _total_review_frame(_uname, combined)

            st.markdown("### 🧭 실행 포인트")
            st.caption("총평 본문에 오행 해석을 함께 묶었습니다. 카드는 실행 체크용입니다.")

            _exec_point_card(
                emoji="🌟",
                title="강점",
                subtitle="두드러지게 살아 있는 기운",
                accent="#d97706",
                soft_bg="#fffbeb",
                md_body=_t10a,
            )
            _exec_point_card(
                emoji="🛡️",
                title="보완",
                subtitle="부족한 기운을 다스리는 법",
                accent="#0284c7",
                soft_bg="#f0f9ff",
                md_body=_t10b,
            )
            _exec_point_card(
                emoji="🧭",
                title="용신",
                subtitle="선택과 타이밍의 기준",
                accent="#7c3aed",
                soft_bg="#f5f3ff",
                md_body=_t10c,
            )

