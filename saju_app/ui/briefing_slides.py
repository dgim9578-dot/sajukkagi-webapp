"""Streamlit용 브리핑 슬라이드(카드·타임라인·랜딩) HTML."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from saju.core.engine import STEM_ELEMENT

_ELEMENT_DOT: dict[str, str] = {
    "木": "#22C55E",
    "火": "#EF4444",
    "土": "#D4AF37",
    "金": "#E5E7EB",
    "水": "#3B82F6",
}


def _hx(s: object) -> str:
    return html.escape(str(s or ""), quote=True)


def render_fortune_cards_row(
    cards: list[dict[str, Any]] | None,
    *,
    key_prefix: str = "fortune",
) -> None:
    """`fortune_cards` 3장 카드 덱 (STEP6)."""
    if not cards:
        return
    n = min(len(cards), 3)
    cols = st.columns(n)
    for i, card in enumerate(cards[:n]):
        if not isinstance(card, dict):
            continue
        title = str(card.get("title") or "운세")
        emoji = str(card.get("emoji") or "✨")
        score = int(card.get("score") or 0)
        summary = str(card.get("summary") or "")
        color = str(card.get("color") or "#d4af37")
        with cols[i]:
            st.markdown(
                f"""
<div class="saju-briefing-fortune-card" style="--fc:{_hx(color)};">
  <div class="saju-briefing-fortune-emoji">{_hx(emoji)}</div>
  <div class="saju-briefing-fortune-title">{_hx(title)}</div>
  <div class="saju-briefing-fortune-score">{score}<span>%</span></div>
  <p class="saju-briefing-fortune-sum">{_hx(summary[:120])}{"…" if len(summary) > 120 else ""}</p>
</div>
""",
                unsafe_allow_html=True,
            )


def render_recommendations_row(
    recs: list[dict[str, Any]] | None,
    *,
    key_prefix: str = "rec",
) -> None:
    """`recommendations` 슬라이드 (STEP10)."""
    if not recs:
        return
    for i, rec in enumerate(recs[:4]):
        if not isinstance(rec, dict):
            continue
        st.markdown(
            f"""
<div class="saju-briefing-rec-card">
  <div class="saju-briefing-rec-title">{_hx(rec.get("title") or "조언")}</div>
  <p class="saju-briefing-rec-desc">{_hx(str(rec.get("desc") or ""))}</p>
</div>
""",
            unsafe_allow_html=True,
        )


def render_match_briefing_slides(
    *,
    match_pct: int,
    day_branch_rel: str,
    yong_harmony: str,
    el_supplement: str,
    one_liners: dict[str, str] | None = None,
) -> None:
    """궁합 4슬라이드 요약 (STEP4)."""
    lines = one_liners or {}
    slides = [
        ("💕 감정", lines.get("love", f"일지 {day_branch_rel} — 정서 결속·타이밍을 먼저 맞추세요."), "#fb7185"),
        ("💼 생활", lines.get("life", "오행 리듬과 역할 분담이 궁합의 생활 축입니다."), "#60a5fa"),
        ("💰 재물", lines.get("wealth", "지출·저축 기준을 합의하면 갈등이 줄어듭니다."), "#fbbf24"),
        ("⚠️ 주의", lines.get("caution", "충·강약 차이는 규칙과 휴식으로 조율하세요."), "#f59e0b"),
    ]
    st.markdown(
        f"""
<div class="saju-match-hero-score">
  <span class="saju-match-hero-label">종합 궁합</span>
  <span class="saju-match-hero-num">{int(match_pct)}</span><span class="saju-match-hero-unit">점</span>
</div>
""",
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    for i, (label, body, tone) in enumerate(slides):
        with cols[i]:
            st.markdown(
                f"""
<div class="saju-match-slide" style="--ms-tone:{_hx(tone)};">
  <div class="saju-match-slide-label">{_hx(label)}</div>
  <p class="saju-match-slide-body">{_hx(body)}</p>
</div>
""",
                unsafe_allow_html=True,
            )
    st.caption(
        f"용신 조화 {yong_harmony} · 오행 보완 {el_supplement} — 탭에서 상세 해설"
    )


def render_daewoon_timeline(
    *,
    rows: list[dict[str, Any]],
    current_age: int,
    user_stem: str,
    birth_year: int,
) -> int | None:
    """대운 가로 타임라인 + 선택 구간 상세. 선택된 row index 반환."""
    if not rows:
        st.caption("대운 데이터가 없습니다.")
        return None

    labels: list[str] = []
    active_idx = 0
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            continue
        age_start = int(row.get("age_start", 0))
        age_end = int(row.get("age_end", age_start + 9))
        start_year = int(row.get("year_start", birth_year + age_start))
        end_year = int(row.get("year_end", start_year + 9))
        pillar = str(row.get("pillar") or "—")
        labels.append(f"{start_year}~{end_year} · {pillar}")
        if age_start <= current_age <= age_end:
            active_idx = len(labels) - 1

    st.caption("구간을 선택하면 아래에 십성·한 줄 해설이 표시됩니다.")
    pick = st.radio(
        "대운 구간",
        options=list(range(len(labels))),
        format_func=lambda j: labels[j],
        index=min(active_idx, len(labels) - 1),
        horizontal=True,
        key="step9_daewoon_timeline_pick",
        label_visibility="collapsed",
    )

    # 가로 타임라인 HTML
    chips: list[str] = []
    for i, row in enumerate(rows[: len(labels)]):
        if not isinstance(row, dict):
            continue
        pillar = str(row.get("pillar") or "—")
        age_start = int(row.get("age_start", 0))
        age_end = int(row.get("age_end", age_start + 9))
        cur = age_start <= current_age <= age_end
        sel = i == pick
        cls = "saju-dw-chip"
        if cur:
            cls += " saju-dw-chip--now"
        if sel:
            cls += " saju-dw-chip--sel"
        chips.append(
            f'<span class="{cls}">{_hx(pillar)}<small>{age_start}~{age_end}세</small></span>'
        )
    st.markdown(
        f'<div class="saju-dw-timeline" role="list">{"".join(chips)}</div>',
        unsafe_allow_html=True,
    )

    row = rows[pick] if 0 <= pick < len(rows) else None
    if not isinstance(row, dict):
        return pick
    dae_ganji = str(row.get("pillar") or "")
    dae_stem = dae_ganji[0] if len(dae_ganji) >= 1 else ""
    ten = ""
    try:
        from saju_app.ui import components as M

        ten = M.get_detailed_ten_stem(user_stem, dae_stem)
    except Exception:
        ten = "—"
    result = ""
    try:
        from saju_app.ui import components as M

        result = M.DAEWON_TEN_INTERP.get(ten, "기본 운 흐름")
    except Exception:
        result = "기본 운 흐름"

    c1, c2 = st.columns([1, 3])
    with c1:
        st.metric("십성", ten)
        st.caption(dae_ganji)
    with c2:
        st.info(result)
    return pick


def landing_solar_mini_html(
    *,
    name_ko: str,
    summary: str,
    prep_hint: str,
) -> str:
    """STEP1 미니 슬라이드 1장 — 절기 요약."""
    return f"""
<div class="saju-landing-mini-slide">
  <p class="saju-landing-mini-kicker">오늘의 24절기</p>
  <h3 class="saju-landing-mini-title">{_hx(name_ko)}</h3>
  <p class="saju-landing-mini-body">{_hx(summary)}</p>
  <p class="saju-landing-mini-prep">{_hx(prep_hint)}</p>
</div>
""".strip()


def step2_oheng_preview_html(*, gapja: list[str] | None) -> str:
    """생년 간지 기준 오행 점 프리뷰."""
    if not gapja or len(gapja) < 1 or len(str(gapja[0])) < 1:
        return ""
    stem = str(gapja[0])[0]
    el = STEM_ELEMENT.get(stem, "土")
    col = _ELEMENT_DOT.get(el, "#D4AF37")
    ko = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}.get(el, el)
    return f"""
<div class="saju-step2-oheng-preview">
  <span class="saju-step2-oheng-dot" style="background:{_hx(col)};"></span>
  <span>년간 <b>{_hx(stem)}</b> · {ko}({el}) 기운</span>
</div>
""".strip()


def render_sinsal_card_deck(
    sins: list[str],
    meanings: dict[str, str],
    *,
    display_fn: Any,
) -> None:
    """STEP5 신살 카드 — 선택 시 의미 표시."""
    if not sins:
        st.caption("표시할 신살이 없습니다.")
        return
    pick = st.radio(
        "신살 카드",
        options=sins,
        format_func=display_fn,
        horizontal=True,
        key="step5_sin_pick_radio",
        label_visibility="collapsed",
    )
    meaning = meanings.get(pick, "")
    st.markdown(
        f"""
<div class="saju-sinsal-flip-card">
  <div class="saju-sinsal-flip-front">{_hx(display_fn(pick))}</div>
  <p class="saju-sinsal-flip-back">{_hx(meaning)}</p>
</div>
""",
        unsafe_allow_html=True,
    )


_EL_KO_SLIDE: dict[str, str] = {
    "木": "목",
    "火": "화",
    "土": "토",
    "金": "금",
    "水": "수",
}


def _fortune_cards_from_briefing(briefing: dict[str, Any]) -> list[dict[str, Any]]:
    life = briefing.get("life_insights")
    if isinstance(life, dict) and life:
        try:
            from saju_app.ui.briefing_life_sync import life_insights_to_fortune_cards

            cards = life_insights_to_fortune_cards(life)
            if cards:
                return cards
        except Exception:
            pass
    raw = briefing.get("fortune_cards")
    return raw if isinstance(raw, list) else []


def render_unified_analysis_deck(
    briefing: dict[str, Any] | None,
    *,
    step: int = 3,
) -> bool:
    """3D 덱 슬라이드와 동일 항목·문장을 사주분석(STEP3) 한 화면에 표시."""
    if not isinstance(briefing, dict) or not briefing:
        return False

    ov = briefing.get("overview") if isinstance(briefing.get("overview"), dict) else {}
    core = ov.get("core_interpretation") if isinstance(ov.get("core_interpretation"), dict) else {}
    dm = str(ov.get("day_master") or "—")
    el = str(ov.get("day_master_element") or "")
    el_ko = _EL_KO_SLIDE.get(el, el)

    with st.container(key=f"step{step}_deck_core"):
        st.markdown(
            f"""
<div class="saju-unified-deck-section">
  <p class="saju-unified-deck-kicker">1 · 핵심</p>
  <h3 class="saju-unified-deck-title">{_hx(core.get("headline") or "핵심 — 당신 사주의 중심축(일간)")}</h3>
  <p class="saju-unified-deck-purpose">{_hx(core.get("slide_purpose") or "일간은 성향·선택의 기준입니다. 아래 운세는 이 기준 위의 영역별 해석입니다.")}</p>
  <div class="saju-unified-dm-block">
    <p class="saju-unified-dm-label">일간 (Day Master)</p>
    <p class="saju-unified-dm-char">{_hx(dm)}</p>
    <p class="saju-unified-dm-el">{_hx(el_ko)} 오행</p>
  </div>
  <p class="saju-unified-deck-body">{_hx(core.get("summary") or f"일간 {dm}({el_ko})이 이 사주의 중심입니다.")}</p>
</div>
""",
            unsafe_allow_html=True,
        )
        notes = core.get("keyword_notes")
        if isinstance(notes, list) and notes:
            kw_html = "".join(
                f'<li class="saju-unified-kw-item"><b>{_hx(n.get("keyword"))}</b>'
                f'<span>{_hx(n.get("meaning"))}</span></li>'
                for n in notes[:4]
                if isinstance(n, dict)
            )
            st.markdown(
                f'<ul class="saju-unified-kw-list">{kw_html}</ul>',
                unsafe_allow_html=True,
            )
        elif ov.get("main_keywords"):
            kws = ov.get("main_keywords")
            if isinstance(kws, list):
                chips = "".join(
                    f'<span class="saju-unified-kw-chip">{_hx(k)}</span>'
                    for k in kws[:4]
                )
                st.markdown(f'<div class="saju-unified-kw-chips">{chips}</div>', unsafe_allow_html=True)
        bal = _hx(core.get("balance_comment") or f"균형 지수 {ov.get('balance_score', '—')}")
        st.markdown(
            f'<div class="saju-unified-balance-box"><b>오행 균형</b><p>{bal}</p></div>',
            unsafe_allow_html=True,
        )

    ef = briefing.get("energy_flow") if isinstance(briefing.get("energy_flow"), dict) else {}
    strong = ef.get("strong") if isinstance(ef.get("strong"), list) else []
    weak = ef.get("weak") if isinstance(ef.get("weak"), list) else []
    with st.container(key=f"step{step}_deck_energy"):
        s_txt = " · ".join(_EL_KO_SLIDE.get(str(x), str(x)) for x in strong) or "—"
        w_txt = " · ".join(_EL_KO_SLIDE.get(str(x), str(x)) for x in weak) or "—"
        st.markdown(
            f"""
<div class="saju-unified-deck-section">
  <p class="saju-unified-deck-kicker">2 · 에너지</p>
  <h3 class="saju-unified-deck-title">오행 에너지 흐름</h3>
  <p class="saju-unified-deck-body">강한 기운은 활용 포인트, 약한 기운은 보완 포인트입니다. 상생·상극 관계는 아래 원국 차트와 해석에서 함께 봅니다.</p>
  <p class="saju-unified-deck-body"><b>강</b> { _hx(s_txt) } &nbsp;|&nbsp; <b>약</b> { _hx(w_txt) }</p>
</div>
""",
            unsafe_allow_html=True,
        )

    pillars = briefing.get("pillars_3d")
    if isinstance(pillars, list) and pillars:
        with st.container(key=f"step{step}_deck_pillars"):
            pills = " · ".join(
                _hx(str(p.get("pillar") or "")) for p in pillars[:4] if isinstance(p, dict)
            )
            st.markdown(
                f"""
<div class="saju-unified-deck-section">
  <p class="saju-unified-deck-kicker">3 · 사주팔자</p>
  <h3 class="saju-unified-deck-title">당신의 사주 팔자</h3>
  <p class="saju-unified-deck-body">년·월·일·시 네 기둥: <b>{pills}</b></p>
</div>
""",
                unsafe_allow_html=True,
            )

    cards = _fortune_cards_from_briefing(briefing)
    if cards:
        with st.container(key=f"step{step}_deck_fortune"):
            st.markdown(
                '<p class="saju-unified-deck-kicker">4~7 · 영역별 운세</p>'
                '<h3 class="saju-unified-deck-title">재물 · 혼인 · 커리어 · 체질</h3>'
                '<p class="saju-unified-deck-body">STEP4 「인생 핵심 운세」와 <b>동일한 점수·해석</b>입니다.</p>',
                unsafe_allow_html=True,
            )
            n = min(len(cards), 4)
            cols = st.columns(2 if n >= 2 else 1, gap="small")
            for i, card in enumerate(cards[:4]):
                if not isinstance(card, dict):
                    continue
                title = str(card.get("title") or "운세")
                emoji = str(card.get("emoji") or "✨")
                score = int(card.get("score") or 0)
                summary = str(card.get("summary") or "")
                color = str(card.get("color") or "#d4af37")
                score_html = (
                    f'<div class="saju-briefing-fortune-score">{score}<span>%</span></div>'
                    if score > 0
                    else '<p class="saju-briefing-fortune-note">원국·대운 기준 참고 해석</p>'
                )
                with cols[i % len(cols)]:
                    st.markdown(
                        f"""
<div class="saju-briefing-fortune-card" style="--fc:{_hx(color)};">
  <div class="saju-briefing-fortune-emoji">{_hx(emoji)}</div>
  <div class="saju-briefing-fortune-title">{_hx(title)}</div>
  {score_html}
  <p class="saju-briefing-fortune-sum">{_hx(summary)}</p>
</div>
""",
                        unsafe_allow_html=True,
                    )

    tg = briefing.get("ten_god") if isinstance(briefing.get("ten_god"), dict) else {}
    counts = tg.get("counts") if isinstance(tg.get("counts"), dict) else {}
    if counts:
        with st.container(key=f"step{step}_deck_tengod"):
            max_c = max(int(v or 0) for v in counts.values()) or 1
            bars = []
            for name, cnt in sorted(counts.items(), key=lambda x: -int(x[1] or 0)):
                w = max(8, int(100 * int(cnt or 0) / max_c))
                bars.append(
                    f'<div class="saju-unified-tg-row">'
                    f'<span class="saju-unified-tg-name">{_hx(name)}</span>'
                    f'<span class="saju-unified-tg-bar" style="width:{w}%;"></span>'
                    f'<span class="saju-unified-tg-val">{int(cnt or 0)}</span></div>'
                )
            st.markdown(
                f"""
<div class="saju-unified-deck-section">
  <p class="saju-unified-deck-kicker">8 · 십성</p>
  <h3 class="saju-unified-deck-title">십성 분포</h3>
  <div class="saju-unified-tg-chart">{"".join(bars)}</div>
</div>
""",
                unsafe_allow_html=True,
            )

    recs = briefing.get("recommendations")
    if isinstance(recs, list) and recs:
        with st.container(key=f"step{step}_deck_rec"):
            st.markdown(
                '<p class="saju-unified-deck-kicker">9 · 조언</p>'
                '<h3 class="saju-unified-deck-title">올해의 핵심 조언</h3>',
                unsafe_allow_html=True,
            )
            render_recommendations_row(recs, key_prefix=f"step{step}_rec")

    return True


def render_step11_keyword_rail(keywords: list[str] | None) -> None:
    """STEP11 키워드 미니카드."""
    if not keywords:
        return
    chips = "".join(
        f'<span class="saju-s11-kw-chip">{_hx(k)}</span>' for k in keywords[:3]
    )
    st.markdown(
        f'<div class="saju-s11-kw-rail">{chips}</div>',
        unsafe_allow_html=True,
    )
