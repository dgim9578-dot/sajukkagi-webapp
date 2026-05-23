"""오행 바·십성 아이콘·용신 강조 등 시각 요소."""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

from saju.core.engine import STEM_ELEMENT

from saju_app.ui import components as M

# 십성(세분) → 아이콘 (비견=검, 정재=동전 등)
TEN_STEM_ICONS: dict[str, str] = {
    "비견": "⚔️",
    "겁재": "🗡️",
    "식신": "🥢",
    "상관": "✨",
    "편재": "💵",
    "정재": "🪙",
    "편관": "🏛️",
    "정관": "⚖️",
    "편인": "📿",
    "정인": "📖",
}

_EL_ORDER: tuple[tuple[str, str, str], ...] = (
    ("木", "목", "wood"),
    ("火", "화", "fire"),
    ("土", "토", "earth"),
    ("金", "금", "metal"),
    ("水", "수", "water"),
)


def ten_stem_icon(ten: str) -> str:
    return TEN_STEM_ICONS.get(str(ten).strip(), "✨")


def _pct(elements: dict[str, Any], el: str) -> int:
    try:
        v = float(elements.get(el, 0) or 0)
    except (TypeError, ValueError):
        v = 0.0
    return max(0, min(100, int(round(v))))


def yongshin_hero_html(yongshin: str) -> str:
    ys = str(yongshin or "").strip()
    if not ys or ys == "판단 필요":
        inner = (
            f'<span class="saju-yongshin-core is-muted">{html.escape(ys or "판단 필요")}</span>'
            '<span class="saju-yongshin-sub">일간·월령을 기준으로 용신을 산출합니다</span>'
        )
    else:
        ko = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}.get(ys, ys)
        inner = (
            f'<span class="saju-yongshin-label">용신</span>'
            f'<span class="saju-yongshin-core">{html.escape(ys)}</span>'
            f'<span class="saju-yongshin-ko">{html.escape(ko)} 기운</span>'
            '<span class="saju-yongshin-sub">선택·방향·타이밍의 북극성</span>'
        )
    return f'<div class="saju-yongshin-hero" role="group" aria-label="용신">{inner}</div>'


def element_energy_bars_html(
    elements: dict[str, Any],
    *,
    yongshin_el: str | None,
) -> str:
    """오행별 수평 바(그라데이션). 용신 오행은 하이라이트."""
    rows: list[str] = ['<div class="saju-oheng-bars" role="img" aria-label="오행 에너지">']
    for han, ko, data_el in _EL_ORDER:
        pct = _pct(elements, han)
        is_ys = bool(yongshin_el and yongshin_el == han)
        cls = "saju-elbar-fill"
        if is_ys:
            cls += " is-yongshin"
        rows.append('<div class="saju-elbar">')
        rows.append(
            f'<div class="saju-elbar-label"><span class="ko">{html.escape(ko)}</span>'
            f'<span class="han">{html.escape(han)}</span></div>'
        )
        rows.append('<div class="saju-elbar-track">')
        rows.append(
            f'<div class="{cls}" data-el="{html.escape(data_el)}" '
            f'style="width:{pct}%;" title="{html.escape(ko)} {pct}%"></div>'
        )
        rows.append("</div>")
        rows.append(f'<div class="saju-elbar-pct">{pct}%</div>')
        rows.append("</div>")
    rows.append("</div>")
    return "".join(rows)


def ten_stem_strip_html(u_gapja: list[str]) -> str:
    """일간 기준 네 천간의 십성 + 아이콘."""
    if not u_gapja or len(u_gapja) < 4:
        return ""
    day_stem = u_gapja[2][0] if len(u_gapja[2]) >= 1 else "甲"
    labels = ("년간", "월간", "일간", "시간")
    chips: list[str] = ['<div class="saju-tenstrip">']
    for i in range(4):
        g = u_gapja[i]
        if not g or len(str(g)) < 1:
            continue
        stem = str(g)[0]
        if stem not in STEM_ELEMENT:
            continue
        ten = M.get_detailed_ten_stem(day_stem, stem)
        ic = ten_stem_icon(ten)
        chips.append('<div class="saju-tenchip">')
        chips.append(f'<span class="saju-ten-ic" aria-hidden="true">{ic}</span>')
        chips.append(f'<span class="saju-ten-name">{html.escape(ten)}</span>')
        chips.append(f'<span class="saju-ten-pill">{html.escape(labels[i])}</span>')
        chips.append("</div>")
    chips.append("</div>")
    return "".join(chips)


def render_oheng_visual_panel(
    *,
    engine: dict[str, Any],
    u_gapja: list[str],
    container_key: str = "saju_oheng_viz",
    show_yongshin_hero: bool = True,
    show_bars: bool = True,
    show_ten_strip: bool = True,
) -> None:
    """오행 바 + (선택) 용신 히어로 + 천간 십성 스트립."""
    ys = str(engine.get("yongshin") or "판단 필요")
    yong_el = ys if ys and ys != "판단 필요" and ys in ("木", "火", "土", "金", "水") else None
    elements = engine.get("elements") or {}

    with st.container(key=container_key):
        if show_yongshin_hero:
            st.markdown(yongshin_hero_html(ys), unsafe_allow_html=True)
        if show_bars:
            st.markdown(
                element_energy_bars_html(elements, yongshin_el=yong_el),
                unsafe_allow_html=True,
            )
        if show_ten_strip and u_gapja and len(u_gapja) >= 4:
            st.caption("일간 기준 · 네 천간의 십성")
            st.markdown(ten_stem_strip_html(u_gapja), unsafe_allow_html=True)
