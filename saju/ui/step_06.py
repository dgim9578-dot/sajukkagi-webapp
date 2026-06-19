"""STEP 6 — 오늘의 운세."""

from __future__ import annotations

import html

import streamlit as st

from saju.core.daily_fortune import build_daily_fortune
from saju.core.engine import STEM_ELEMENT, _ten_strength_counts

from saju_app.ui import analysis_favorite_memo as AFM
from saju_app.ui import consulting_corpus as CC
from saju_app.ui import components as M
from saju_app.ui.interpretation_layout import (
    build_step6_today_interpretation,
    render_structured_interpretation_block,
)
from saju_app.ui.plain_language import to_plain_text
from saju_app.ui.step06_hero_banner import render_step06_hero_banner

_EL_KO = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}


def _el_ko(el: str) -> str:
    return _EL_KO.get(str(el or "").strip(), str(el or ""))


def _yongshin_card_body(*, strength: str, yongshin: str, day_el: str) -> str:
    ys = _el_ko(yongshin)
    de = _el_ko(day_el)
    if not yongshin or yongshin == "판단 필요":
        return "아직 핵심 기운 판단이 더 필요해요. 오늘은 큰 결정보다 루틴·환경부터 정리하세요."
    if strength == "신강":
        return (
            f"에너지가 강한 편(신강)이고 나(일간)는 {de}({day_el}) 타입이에요. "
            f"오늘은 핵심 보조 기운 {ys}({yongshin}) 쪽으로 일·대화·생활 리듬을 맞추면 "
            f"무리하지 않고 힘을 쓸 수 있어요."
        )
    if strength == "신약":
        return (
            f"에너지가 약한 편(신약)이고 나(일간)는 {de}({day_el}) 타입이에요. "
            f"오늘은 핵심 보조 기운 {ys}({yongshin})으로 컨디션을 먼저 채우는 선택이 "
            f"루틴·환경·대화에 도움이 돼요."
        )
    return (
        f"균형형(중화)이고 나(일간)는 {de}({day_el}) 타입이에요. "
        f"핵심 보조 기운 {ys}({yongshin})을 기준으로 과하지 않게 맞추면 "
        f"오늘 흐름이 안정적이에요."
    )


def _strength_card_body(
    *,
    strength: str,
    max_el: str,
    min_el: str,
    today_el: str,
    ten_detail: str,
) -> str:
    return (
        f"내 에너지는 {strength}이에요. 타고난 팔자에서는 {_el_ko(max_el)}({max_el})이 강하고 "
        f"{_el_ko(min_el)}({min_el})을 채우면 좋아요. "
        f"오늘은 {_el_ko(today_el)}({today_el})·{ten_detail} 기운이 더 눈에 띄는 날이에요."
    )


def _step6_score_bar_html(score: int, tone: str) -> str:
    """오늘의 운세 점수 막대 — 퍼센트를 막대 위에 표시."""
    pct = max(0, min(100, int(score)))
    tone_esc = html.escape(tone)
    return (
        f'<div class="saju-step6-score-bar" style="--step6-tone:{tone_esc};--step6-pct:{pct};" '
        f'role="progressbar" aria-valuenow="{pct}" aria-valuemin="0" aria-valuemax="100" '
        f'aria-label="점수 {pct}퍼센트">'
        '<div class="saju-step6-score-track">'
        '<div class="saju-step6-score-fill"></div>'
        f'<span class="saju-step6-score-label">{pct}%</span>'
        "</div></div>"
    )


def _render_step6_category_panel(
    cat: str,
    *,
    daily_scores: dict[str, int],
    daily_comments: dict[str, str],
    category_meta: dict[str, dict[str, str]],
    ten_detail: str,
    ten_group: str,
    day_branch_rel: str,
    yongshin: str,
) -> None:
    sc = int(daily_scores[cat])
    meta = category_meta[cat]
    msg = to_plain_text(daily_comments.get(cat, ""))
    tone = str(meta["tone"])
    st.subheader(f"{meta['icon']} {cat}")
    st.markdown(_step6_score_bar_html(sc, tone), unsafe_allow_html=True)
    st.markdown(
        f"""
<div style="
    margin:0.8rem 0 0.75rem;
    padding:1rem 1.05rem 1.05rem;
    border-radius:16px;
    border:1px solid {tone};
    background:
        radial-gradient(circle at 12% 18%, {tone}24 0 3px, transparent 4px),
        linear-gradient(135deg, {tone}22 0%, rgba(255,255,255,0.06) 100%);
    box-shadow:0 10px 28px rgba(0,0,0,0.12), inset 0 0 0 1px rgba(255,255,255,0.08);
">
  <div style="font-weight:800;color:{tone};margin-bottom:0.5rem;">{html.escape(str(cat))} 해석 포인트</div>
  <div style="line-height:1.72;">{html.escape(msg)}</div>
  <div style="
      margin-top:0.8rem;
      padding:0.62rem 0.72rem;
      border-radius:12px;
      background:rgba(255,255,255,0.08);
      border:1px solid rgba(148,163,184,0.22);
      font-size:0.92rem;
      line-height:1.55;
  ">
    체크포인트: 십성 {html.escape(str(ten_detail))}({html.escape(str(ten_group))}) · 일지 {html.escape(day_branch_rel or '무특별')} · 용신 {html.escape(str(yongshin))}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


@st.fragment
def _render_step6_category_tabs(
    *,
    cats: tuple[str, ...],
    category_meta: dict[str, dict[str, str]],
    daily_scores: dict[str, int],
    daily_comments: dict[str, str],
    ten_detail: str,
    ten_group: str,
    day_branch_rel: str,
    yongshin: str,
) -> None:
    """재물·연애 등 카테고리 탭 — fragment 로만 rerun 해 스크롤이 위로 튕기지 않게."""
    if "step6_today_pick" not in st.session_state:
        st.session_state.step6_today_pick = "재물"

    picked = str(st.session_state.get("step6_today_pick") or "재물")
    if picked not in cats:
        picked = cats[0]
        st.session_state.step6_today_pick = picked

    def _pick(cat: str):
        def _h():
            st.session_state.step6_today_pick = cat

        return _h

    with st.container(key="step6_today_pick_row"):
        pick_cols = M._columns_compat(len(cats))
        for i, cat in enumerate(cats):
            with pick_cols[i]:
                emo = category_meta[cat]["icon"]
                st.button(
                    emo,
                    key=f"step6_pick_{cat}",
                    on_click=_pick(cat),
                    use_container_width=True,
                    type="primary" if cat == picked else "secondary",
                    help=f"{cat}운 상세 보기",
                )
                st.markdown(
                    f'<p class="step6-pick-cap">{html.escape(cat)}</p>',
                    unsafe_allow_html=True,
                )

    st.divider()

    with st.container(key="step6_detail_panel"):
        _render_step6_category_panel(
            picked,
            daily_scores=daily_scores,
            daily_comments=daily_comments,
            category_meta=category_meta,
            ten_detail=ten_detail,
            ten_group=ten_group,
            day_branch_rel=day_branch_rel,
            yongshin=yongshin,
        )
        CC.render_consulting_panel(
            f"{CC.query_for_step('step6', topic=picked)} 오늘 운세 타이밍",
            apply="step6",
            title="📎 현장 상담 참고 (일반 사례)",
            expanded=False,
            container_key="step6_consulting",
        )


def render() -> None:
    M._resync_user_gapja_from_u_data()
    u_name = st.session_state.get("u_name", "사주까기님")
    u_gapja = st.session_state.get("u_gapja")

    if not u_gapja or len(u_gapja) < 3:
        st.warning("⚠️ 사주 정보가 없습니다. 먼저 사주 분석을 진행해주세요.")
        st.button(
            "← 사주 분석 결과로",
            use_container_width=True,
            help="STEP3 사주 분석 결과 화면으로 이동합니다.",
            on_click=M.navigate_to_step,
            args=(3,),
        )
        st.stop()

    engine, core = M.ensure_engine_and_core(u_gapja)

    with M.premium_analysis_shell(6):
        AFM.render_analysis_favorite_memo_band(step=6)
        now = M.now_kst()
        today_gapja = M.get_saju_data(now.year, now.month, now.day, 12, False, False)

        u_stem, u_branch = u_gapja[2][0], u_gapja[2][1]
        t_stem, t_branch = today_gapja[2][0], today_gapja[2][1]

        ten_detail = M.get_detailed_ten_stem(
            u_stem, t_stem
        )
        if ten_detail in ("비견", "겁재"):
            ten_group = "비겁"
        elif ten_detail in ("식신", "상관"):
            ten_group = "식상"
        elif ten_detail in ("정재", "편재"):
            ten_group = "재성"
        elif ten_detail in ("정관", "편관"):
            ten_group = "관성"
        else:
            ten_group = "인성"

        t_el = STEM_ELEMENT.get(t_stem, "木")
        yongshin = str(engine.get("yongshin", "판단 필요"))
        strength = str(engine.get("strength", "중화"))
        max_el = str(engine.get("max_el", "木"))
        min_el = str(engine.get("min_el", "水"))
        day_el = str(engine.get("day_el", STEM_ELEMENT.get(u_stem, "木")))
        gender = str(st.session_state.get("u_gender") or "남자")
        ten_counts = _ten_strength_counts(u_gapja)
        when = now.date()

        daily = build_daily_fortune(
            u_gapja=u_gapja,
            today_gapja=today_gapja,
            when=when,
            engine=engine,
            ten_counts=ten_counts,
            ten_detail=ten_detail,
            ten_group=ten_group,
            u_name=u_name,
            gender=gender,
            branch_pair_relation_fn=M.branch_pair_relation,
        )
        daily_scores = daily["scores"]
        daily_comments = daily["comments"]
        day_branch_rel = str(daily.get("day_branch_rel") or "")

        category_meta = {
            "직장": {"icon": "💼", "tone": "#60a5fa"},
            "연애": {"icon": "💖", "tone": "#fb7185"},
            "재물": {"icon": "💰", "tone": "#fbbf24"},
            "공부": {"icon": "📚", "tone": "#34d399"},
            "건강": {"icon": "🩺", "tone": "#a78bfa"},
        }

        render_step06_hero_banner()

        def _render_daily_focus_cards() -> None:
            cards = [
                (
                    "오늘의 중심 기운",
                    f"오늘 일진 {today_gapja[2]} × 본인 {u_gapja[2]} — "
                    f"{ten_detail}({ten_group}) · 일지 {day_branch_rel or '무특별'}",
                    "#D4AF37",
                ),
                (
                    "용신 활용",
                    _yongshin_card_body(strength=strength, yongshin=yongshin, day_el=day_el),
                    "#60A5FA",
                ),
                (
                    "신강약 메모",
                    _strength_card_body(
                        strength=strength,
                        max_el=max_el,
                        min_el=min_el,
                        today_el=t_el,
                        ten_detail=ten_detail,
                    ),
                    "#34D399",
                ),
            ]
            for title, body, tone in cards:
                st.markdown(
                    f"""
<div class="step6-daily-focus-card" style="--step6-tone:{html.escape(tone)};">
  <div class="step6-daily-focus-title">{html.escape(title)}</div>
  <div class="step6-daily-focus-body">{html.escape(body)}</div>
</div>
""",
                    unsafe_allow_html=True,
                )

        st.divider()

        core_box = (
            f"오늘 {daily.get('today_ilju', today_gapja[2])} · 본인 {daily.get('user_ilju', u_gapja[2])} · "
            f"일지 {day_branch_rel or '무특별'} · **{ten_detail}({ten_group})** 중심. "
            f"용신 **{yongshin}** 방향으로 루틴·환경을 맞추면 체감 운이 안정됩니다."
        )
        if len(core_box) > 160:
            core_box = core_box[:159] + "…"

        cats = ("재물", "연애", "직장", "건강", "공부")
        avg_today = int(daily.get("avg_score") or 0)

        st.subheader("오늘의 핵심 운세")
        _ix6 = build_step6_today_interpretation(
            ten_detail=ten_detail,
            ten_group=ten_group,
            yongshin=yongshin,
            strength=strength,
            max_el=max_el,
            min_el=min_el,
            today_el=t_el,
            day_el=day_el,
            base_msg=core_box.replace("**", ""),
            harmony_pct=avg_today,
        )
        render_structured_interpretation_block(_ix6, container_key="saju_ix_step6")
        _render_daily_focus_cards()

        st.divider()

        _render_step6_category_tabs(
            cats=cats,
            category_meta=category_meta,
            daily_scores=daily_scores,
            daily_comments=daily_comments,
            ten_detail=ten_detail,
            ten_group=ten_group,
            day_branch_rel=day_branch_rel,
            yongshin=yongshin,
        )
