"""STEP 5 — 12신살."""

from __future__ import annotations

import streamlit as st

from saju_app.ui import analysis_favorite_memo as AFM
from saju_app.ui import consulting_corpus as CC
from saju_app.ui import briefing_slides as BSlides
from saju_app.ui import components as M


SINSAL_ORDER = [
    "겁살",
    "재살",
    "천살",
    "지살",
    "년살",
    "월살",
    "망신",
    "장성",
    "반안",
    "역마",
    "육해",
    "화개",
]

SINSAL_ALIASES = {"년살": "년살(도화)"}

SINSAL_MEANINGS = {
    "겁살": "빼앗김·경쟁·돌발 변수의 기운입니다. 무리한 확장보다 손실 관리가 중요합니다.",
    "재살": "재물·기회·거래가 반복되는 기운입니다. 기회는 있으나 판단이 성급하면 손실도 커집니다.",
    "천살": "윗사람·제도·환경의 압박을 받기 쉬운 기운입니다. 원칙과 명분을 지키면 안정됩니다.",
    "지살": "이동·현장·생활 반경 변화의 기운입니다. 배움과 실무 경험으로 운이 열립니다.",
    "년살": "도화살로도 보며, 인연·매력·주목성이 강해지는 기운입니다. 관계의 선을 분명히 해야 합니다.",
    "월살": "가려짐·정체·심리적 부담을 뜻합니다. 속도를 낮추고 준비 기간을 갖는 것이 좋습니다.",
    "망신": "말·평판·노출로 인한 구설을 조심해야 하는 기운입니다. 공개적 약속과 언행을 신중히 하세요.",
    "장성": "주도권·책임·리더십의 기운입니다. 강한 추진력을 독단으로 쓰지 않는 것이 핵심입니다.",
    "반안": "자리·명예·안정 기반이 붙는 기운입니다. 좋은 후원과 직함을 활용하기 좋습니다.",
    "역마": "이동·변화·출장·이직·확장의 기운입니다. 충동적 결정만 피하면 활동성이 장점이 됩니다.",
    "육해": "작은 방해·피로·인간관계 마찰의 기운입니다. 건강 루틴과 계약 확인이 필요합니다.",
    "화개": "예술·종교·철학·고독·몰입의 기운입니다. 전문성은 깊어지나 고립은 경계해야 합니다.",
}

SINSAL_WARNINGS = {
    "역마": "잦은 변화, 충동적 이동·이직 주의",
    "재살": "투자·거래 판단 신중",
    "망신": "말실수, 평판, 공개적 구설 주의",
    "육해": "인간관계 갈등과 건강 피로 관리",
    "겁살": "손실·경쟁·빼앗김에 대한 방어 필요",
    "년살": "도화성 인연, 감정 관계의 선 긋기 필요",
    "화개": "고립·우울감보다 창작·공부로 승화",
}


def _display_sinsal(name: str) -> str:
    return SINSAL_ALIASES.get(name, name)


def _collect_sins(sinsal_result: dict) -> list[str]:
    sins: list[str] = []
    for v in sinsal_result.values():
        if isinstance(v, dict):
            sins.append(str(v.get("연기준", "")))
            sins.append(str(v.get("일기준", "")))
        else:
            sins.append(str(v))
    return [s for s in sins if s and s != "없음"]


def _ordered_unique_sins(sins: list[str]) -> list[str]:
    seen = set(sins)
    ordered = [s for s in SINSAL_ORDER if s in seen]
    extras = [s for s in sins if s not in SINSAL_ORDER and s not in ordered]
    return ordered + extras


def _render_step5_frame(title: str, lines: list[str], *, tone: str = "#D4AF37") -> None:
    body = "<br><br>".join(str(line) for line in lines if str(line).strip())
    st.markdown(
        f"""
<div style="
    margin:0.7rem 0 1rem;
    padding:1rem 1.05rem;
    border-radius:16px;
    border:1px solid {tone};
    background:
        radial-gradient(circle at 12% 18%, {tone}24 0 3px, transparent 4px),
        linear-gradient(135deg, {tone}20 0%, rgba(255,255,255,0.06) 100%);
    box-shadow:0 10px 28px rgba(0,0,0,0.12), inset 0 0 0 1px rgba(255,255,255,0.08);
">
  <div style="font-weight:800;color:{tone};margin-bottom:0.55rem;">{M._hx(title)}</div>
  <div style="line-height:1.72;">{body}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def _render_step5_meaning_card(title: str, body: str, *, tone: str) -> None:
    st.markdown(
        f"""
<div class="step5-meaning-card" style="--step5-tone:{M._hx(str(tone))};">
  <div class="step5-meaning-title">{M._hx(title)}</div>
  <div class="step5-meaning-body">{M._hx(body)}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render() -> None:
    u_gapja = M._require_u_gapja_or_halt(
        message="사주 정보가 없습니다.",
        show_home_button=False,
    )
    u_name = str(st.session_state.get("u_name") or "").strip() or "회원"
    engine, _core = M.ensure_engine_and_core(u_gapja)

    strength = engine["strength"]
    yongshin = engine["yongshin"]
    day_el = engine.get("day_el", "")

    sinsal_result = M.calculate_sinsal(u_gapja)
    sins = _collect_sins(sinsal_result)
    unique_sins = _ordered_unique_sins(sins)

    has_yeokma = "역마" in sins
    has_jaesal = "재살" in sins
    has_dohwa = "도화" in sins or "년살" in sins
    has_hwagae = "화개" in sins

    with M.premium_analysis_shell(5):
        AFM.render_analysis_favorite_memo_band(step=5)
        st.markdown(f"## 🔥 {u_name}님의 12신살 분석")
        st.divider()

        with st.container(key="step5_sinsal_deck"):
            st.subheader("🧿 신살 카드 덱")
            BSlides.render_sinsal_card_deck(
                unique_sins,
                SINSAL_MEANINGS,
                display_fn=_display_sinsal,
            )
            with st.expander("12신살 전체 목록", expanded=False):
                for k, v in sinsal_result.items():
                    if isinstance(v, dict):
                        st.markdown(
                            f"• **{k}** — 연: {_display_sinsal(str(v.get('연기준', '없음')))} · "
                            f"일: {_display_sinsal(str(v.get('일기준', '없음')))}"
                        )
                    else:
                        st.markdown(f"• **{k}** → {_display_sinsal(str(v))}")

        with st.container(key="step5_layered_stack"):
            with st.container(key="step5_interpret_layers"):
                with st.expander("📜 종합 해석", expanded=True):
                    summary_lines = [
                        f"{u_name}님의 사주에서는 <b>{', '.join(_display_sinsal(s) for s in unique_sins)}</b> 흐름이 나타납니다."
                    ]
                    if has_yeokma:
                        summary_lines.append("역마살이 강해 이동과 변화가 많은 삶입니다.")
                    if has_jaesal:
                        summary_lines.append("재살이 있어 재물 기회가 반복됩니다.")
                    if has_dohwa:
                        summary_lines.append("도화살 영향으로 인연과 매력이 강합니다.")
                    if has_hwagae:
                        summary_lines.append("화개살이 있어 예술·정신적 성향이 깊습니다.")
                    if "신강" in str(strength):
                        summary_lines.append("신강한 구조로 추진력이 강합니다.")
                    else:
                        summary_lines.append("신약 구조로 환경 영향을 많이 받습니다.")
                    summary_lines.append(f"용신인 <b>{yongshin}</b> 기운을 활용하면 전체 운이 안정됩니다.")
                    if day_el:
                        summary_lines.append(
                            f"일간 오행은 <b>{day_el}</b> 입니다. 신살 해석은 일간·용신·대운과 함께 보아야 정확도가 높습니다."
                        )
                    _render_step5_frame("종합 해석", summary_lines, tone="#D4AF37")

                with st.expander("⚠️ 주의사항", expanded=False):
                    active_warnings = [
                        f"• <b>{_display_sinsal(sin)}</b> → {msg}"
                        for sin, msg in SINSAL_WARNINGS.items()
                        if sin in unique_sins
                    ]
                    if active_warnings:
                        warning_lines = active_warnings
                    else:
                        warning_lines = ["• 큰 충돌성 신살보다 기본 운의 균형 관리가 중요합니다."]
                    warning_lines.append(f"• 용신 <b>{yongshin}</b> 기운을 생활 속에서 보강하세요")
                    _render_step5_frame("주의사항", warning_lines, tone="#FBBF24")

                with st.expander("🧭 용신·신강약 메모", expanded=False):
                    _render_step5_frame(
                        "용신·신강약 메모",
                        [
                            f"신강약: <b>{strength}</b> · 용신: <b>{yongshin}</b>",
                            "신살은 ‘경향’이고, 실행은 용신·대운·선택이 함께 만듭니다. 위 주의사항은 상황별로 가중치를 달리해 읽으면 됩니다.",
                        ],
                        tone="#60A5FA",
                    )

