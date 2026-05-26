"""인생 로드맵 — 30·40·50대 대운·세운 짧은 텍스트 요약."""

from __future__ import annotations

from collections import Counter
from typing import Any

import streamlit as st

from saju_app.core import calculations as C
from saju_app.ui import components as M

_ROADMAP_INTRO = "계약·이직·의료 결정은 전문가와 상의하고, 여기 출력은 참고용입니다."


def _seyun_for_year(
    *,
    year: int,
    day_stem: str,
    hour: int | None,
) -> tuple[str, str]:
    pillar = C.get_bazi_year_pillar_lichun(year, 6, 15, hour)
    if not pillar or len(pillar) < 1:
        return "—", "비견"
    gst = pillar[0]
    ten = M.get_detailed_ten_stem(day_stem, gst)
    return pillar, ten


def _roadmap_text_summary(
    *,
    birth_year: int,
    day_stem: str,
    hour: int | None,
    dae_rows: list[dict[str, Any]],
    current_year: int,
) -> tuple[str, str]:
    decade_lines: list[str] = []

    for label, a0, a1 in (("30대", 30, 39), ("40대", 40, 49), ("50대", 50, 59)):
        y0, y1 = int(birth_year) + a0, int(birth_year) + a1
        dae_bits: list[str] = []
        for r in dae_rows:
            if int(r.get("year_end", 0)) < y0 or int(r.get("year_start", 0)) > y1:
                continue
            pill = str(r.get("pillar", "") or "").strip()
            if len(pill) < 2:
                continue
            ten = M.get_detailed_ten_stem(day_stem, pill[0])
            dae_bits.append(f"**{pill}({ten})**")
        c: Counter[str] = Counter()
        for y in range(y0, y1 + 1):
            _, ten = _seyun_for_year(year=y, day_stem=day_stem, hour=hour)
            c[ten] += 1
        top = c.most_common(1)
        seyun_phrase = (
            f"{top[0][0]}({top[0][1]}년)" if top else "뚜렷한 편중 없음"
        )
        dae_phrase = " / ".join(dae_bits[:2]) if dae_bits else "대운 구간 데이터 없음"
        decade_lines.append(
            f"**{label}**: 대운은 {dae_phrase}. "
            f"이때 세운 십성은 주로 {seyun_phrase} 쪽으로 많이 겹칩니다."
        )

    pillar, ten = _seyun_for_year(year=current_year, day_stem=day_stem, hour=hour)
    dr = None
    for r in dae_rows:
        ys = int(r.get("year_start", 0))
        ye = int(r.get("year_end", ys + 9))
        if ys <= current_year <= ye:
            dr = r
            break
    dae_now = "—"
    if dr:
        pill = str(dr.get("pillar", "") or "").strip()
        if len(pill) >= 2:
            dae_now = f"{pill}({M.get_detailed_ten_stem(day_stem, pill[0])})"
    current_line = (
        f"**올해 {current_year}년** 세운은 **{ten}**({pillar}), "
        f"같은 시기 10년 대운은 **{dae_now}** 입니다."
    )
    return "\n\n".join(decade_lines), current_line


def render_life_roadmap_block(
    *,
    u_gapja: list[str],
    u_data: tuple | list,
    u_gender: str,
    birth_year: int,
    zi_boundary: str,
    month_method: str,
) -> None:
    st.subheader("🗺️ 내 인생 전체 로드맵 — 대운 + 세운")
    st.markdown(_ROADMAP_INTRO)
    st.caption(
        f"세운은 입춘 연주 기준이며 month_method={month_method} 설정과 완전히 같지 않을 수 있습니다."
    )

    day_stem = u_gapja[2][0] if len(u_gapja) > 2 else "甲"
    try:
        t_str = u_data[3] if isinstance(u_data, (list, tuple)) and len(u_data) > 3 else "모름"
        h = C.convert_time_str_to_hour(str(t_str), zi_boundary=str(zi_boundary))
    except Exception:
        h = None

    dae = M.compute_daewoon_schedule(
        list(u_gapja),
        u_data,
        str(u_gender),
        int(birth_year),
        zi_boundary=str(zi_boundary),
        n_terms=12,
    )
    rows = list(dae.get("rows") or [])
    if not rows:
        st.info("대운 데이터가 없어 로드맵 요약을 만들지 못했습니다.")
        return

    decades_md, current_md = _roadmap_text_summary(
        birth_year=int(birth_year),
        day_stem=day_stem,
        hour=h,
        dae_rows=rows,
        current_year=M.now_kst().year,
    )

    with st.container(key="step9_roadmap_decades"):
        st.markdown(decades_md)

    with st.container(key="step9_roadmap_current"):
        st.markdown(current_md)
