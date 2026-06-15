"""STEP3 요약용 대운·세운 1~2문장 (STEP9/10 로직 공유)."""

from __future__ import annotations

from typing import Any

from saju.core.engine import STEM_ELEMENT


def _parse_birth_hour(
    u_data: tuple | list | None,
    *,
    zi_boundary: str = "23:30",
) -> int | None:
    if not isinstance(u_data, (list, tuple)) or len(u_data) < 4:
        return None
    t_str = str(u_data[3] or "").strip()
    if not t_str or t_str in ("모름", "??", "?"):
        return None
    try:
        from saju_app.core import calculations as C

        return C.convert_time_str_to_hour(t_str, zi_boundary=str(zi_boundary))
    except Exception:
        return None


def build_step3_timing_summary(
    *,
    u_gapja: list[str],
    u_data: tuple | list | None,
    gender: str,
    birth_year: int,
    yongshin: str,
    engine: dict[str, Any],
    zi_boundary: str = "23:30",
) -> str:
    """현재 대운 + 올해 세운을 STEP3 상세에 연결할 1~2문장."""
    if len(u_gapja) < 3:
        return ""
    try:
        from saju_app.ui import components as M
        from saju_app.ui.action_timing import _dae_row_for_year, _year_saeun_ctx
    except Exception:
        return ""

    day_stem = u_gapja[2][0]
    cur_year = M.now_kst().year
    cur_age = max(0, cur_year - int(birth_year or 2000))

    try:
        dae = M.compute_daewoon_schedule(
            list(u_gapja),
            u_data,
            str(gender or "남자"),
            int(birth_year or 2000),
            zi_boundary=str(zi_boundary or "23:30"),
            n_terms=12,
        )
    except Exception:
        dae = {"rows": []}

    rows = list(dae.get("rows") or [])
    dae_row = _dae_row_for_year(rows, cur_year)
    hour = _parse_birth_hour(u_data, zi_boundary=zi_boundary)
    ctx = _year_saeun_ctx(year=cur_year, u_gapja=list(u_gapja), hour=hour)

    parts: list[str] = []

    if dae_row:
        dp = str(dae_row.get("pillar") or "").strip()
        if len(dp) >= 2:
            ten = M.get_detailed_ten_stem(day_stem, dp[0])
            interp = M.DAEWON_TEN_INTERP.get(ten, "기본 운 흐름")
            a0 = int(dae_row.get("age_start", 0))
            a1 = int(dae_row.get("age_end", a0 + 9))
            parts.append(
                f"현재 대운 {dp}({ten}, {STEM_ELEMENT.get(dp[0], '')}) — "
                f"만 {a0}~{a1}세 구간. {interp}"
            )

    tf = engine.get("get_timing_flow")
    phase = ""
    if callable(tf):
        try:
            tfd = tf()
            if isinstance(tfd, dict):
                phase = str(tfd.get("phase") or "").strip()
        except Exception:
            pass
    if phase and len(parts) < 2:
        parts.append(f"엔진 시기 흐름: {phase.replace('🌱 ', '').replace('🚀 ', '').replace('🔥 ', '').replace('⚖️ ', '').replace('🧘 ', '')} (만 {cur_age}세).")

    pill = str(ctx.get("연주") or "—")
    ten_s = str(ctx.get("세운십성") or "—")
    rel = str(ctx.get("지지관계") or "없음")
    ys = str(yongshin or "").strip()
    ys_note = ""
    if ys in ("木", "火", "土", "金", "水") and str(ctx.get("세천간") or "") in STEM_ELEMENT:
        if STEM_ELEMENT.get(str(ctx.get("세천간") or ""), "") == ys:
            ys_note = f" 올해 세운 천간이 용신 {ys}과 맞닿아 선택·계약·관계에서 안정감이 붙기 쉽습니다."
    parts.append(
        f"{cur_year}년 세운 {pill}({ten_s}), 일지와 {rel}.{ys_note}"
    )

    return " ".join(parts[:2]).strip()
