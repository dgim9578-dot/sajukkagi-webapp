"""인생 로드맵 — 30·40·50대 대운·세운 짧은 텍스트 요약."""

from __future__ import annotations

from collections import Counter
from typing import Any

import streamlit as st

from saju_app.core import calculations as C
from saju_app.ui import components as M


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
) -> str:
    lines: list[str] = [
        "아래는 **10년 대운**과 **입춘 기준 세운(연간 십성)**을 묶어, "
        "30·40·50대를 **짧은 문장**으로만 정리한 참고 요약입니다. "
        "계약·이직·투자 결정은 현실 조건과 전문가 상담을 우선하세요.\n",
    ]

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
            dae_bits.append(
                f"**{pill}({ten})** {int(r.get('year_start', 0))}~{int(r.get('year_end', 0))}년"
            )
        c: Counter[str] = Counter()
        for y in range(y0, y1 + 1):
            _, ten = _seyun_for_year(year=y, day_stem=day_stem, hour=hour)
            c[ten] += 1
        top = c.most_common(2)
        seyun_phrase = (
            " · ".join(f"{t}({n}년)" for t, n in top) if top else "뚜렷한 편중 없음"
        )
        dae_phrase = " / ".join(dae_bits[:2]) if dae_bits else "대운 구간 데이터 없음"
        lines.append(
            f"**{label}** ({y0}~{y1}년, 만 {a0}~{a1}세): "
            f"대운은 {dae_phrase}. "
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
    lines.append(
        f"\n**올해 {current_year}년** 세운은 **{ten}**({pillar}), "
        f"같은 시기 10년 대운은 **{dae_now}** 입니다."
    )
    return "\n".join(lines)


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
    st.caption(
        "복잡한 연도 도표 대신 **30·40·50대 한 줄 요약**만 제공합니다. "
        f"(세운은 입춘 연주 기준이며 month_method={month_method} 설정과 완전히 같지 않을 수 있습니다.)"
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

    st.markdown(
        _roadmap_text_summary(
            birth_year=int(birth_year),
            day_stem=day_stem,
            hour=h,
            dae_rows=rows,
            current_year=M.now_kst().year,
        )
    )
