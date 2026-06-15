"""만세력·전통 명리 보조가 반영된 신강약·용신 계산(간략 엔진의 상위 레이어).

`korean_lunar_calendar`는 생일 양력이 주어질 때 음력·절기 월과의 정합을 보조 가중으로만 사용합니다.
"""

from __future__ import annotations

from typing import Any

from saju.core.engine import (
    BRANCH_ELEMENT,
    STEM_ELEMENT,
    check_branch_relation,
    evaluate_month_power,
    get_relation,
)
from saju.core.gapja_utils import is_valid_pillar

# 지지藏干(本·中·余 비중 근사) — 일간 득지(通根)·월령 보조에 사용
BRANCH_HIDDEN_GAN: dict[str, list[tuple[str, float]]] = {
    "子": [("癸", 1.0)],
    "丑": [("己", 0.55), ("癸", 0.3), ("辛", 0.15)],
    "寅": [("甲", 0.55), ("丙", 0.25), ("戊", 0.2)],
    "卯": [("乙", 1.0)],
    "辰": [("戊", 0.55), ("乙", 0.25), ("癸", 0.2)],
    "巳": [("丙", 0.55), ("庚", 0.25), ("戊", 0.2)],
    "午": [("丁", 0.55), ("己", 0.45)],
    "未": [("己", 0.55), ("丁", 0.25), ("乙", 0.2)],
    "申": [("庚", 0.55), ("壬", 0.25), ("戊", 0.2)],
    "酉": [("辛", 1.0)],
    "戌": [("戊", 0.55), ("辛", 0.25), ("丁", 0.2)],
    "亥": [("壬", 0.55), ("甲", 0.45)],
}


def _hidden_root_score(day_el: str, branch: str, pillar_index: int) -> float:
    """일간 오행과 지지藏干의 관계(通根·印·比劫 등)를 소수로 가산."""
    bonus = 0.0
    for gan, w in BRANCH_HIDDEN_GAN.get(branch, []):
        gel = STEM_ELEMENT.get(gan)
        if not gel:
            continue
        rel = get_relation(day_el, gel)
        pos_w = w * (1.35 if pillar_index == 2 else 1.0) * (1.15 if pillar_index == 1 else 1.0)
        table = {
            "비겁": 0.55,
            "인성": 0.45,
            "식상": -0.25,
            "재성": -0.35,
            "관성": -0.45,
        }
        bonus += table.get(rel, 0.0) * pos_w
    return bonus


def _lunar_calendar_bonus(
    birth_solar: tuple[int, int, int] | None, month_branch: str
) -> float:
    """KARI 만세력: 양력 생일의 음력 월과 월지(절기월)의 기운이 어긋날 때 미세 보정."""
    if not birth_solar:
        return 0.0
    try:
        from korean_lunar_calendar import KoreanLunarCalendar
    except Exception:
        return 0.0
    y, m, d = birth_solar
    klc = KoreanLunarCalendar()
    if not klc.setSolarDate(int(y), int(m), int(d)):
        return 0.0
    lunar_m = int(klc.lunarMonth)
    # 음력 11·12·1월은 수기 편중이 많아, 월지가 화·목 위주일 때 소폭 완화
    mb_el = BRANCH_ELEMENT.get(month_branch)
    if lunar_m in (11, 12, 1) and mb_el in ("火", "木"):
        return 0.12
    if lunar_m in (4, 5, 6) and mb_el in ("水", "金"):
        return 0.1
    return 0.0


def calculate_strength(
    u_gapja: list[str],
    *,
    birth_solar: tuple[int, int, int] | None = None,
) -> dict[str, Any]:
    """
    신강약: 월령·천간·지지表 + 지지藏干 + (선택) 만세력 양력→음력 보조.
    """
    if not u_gapja or len(u_gapja) < 3 or not is_valid_pillar(u_gapja[2]):
        return {
            "day_el": "木",
            "score": 0.0,
            "strength": "중화",
            "clash": 0,
            "combine": 0,
        }

    day_stem = u_gapja[2][0]
    day_el = STEM_ELEMENT.get(day_stem)

    total_score = 0.0

    month_branch = u_gapja[1][1] if is_valid_pillar(u_gapja[1]) else ""
    if month_branch:
        month_result = evaluate_month_power(day_el, month_branch)
        total_score += month_result["score"] * 2.5
        total_score += _hidden_root_score(day_el, month_branch, 1)

    branch_indices = [i for i in (0, 2, 3) if i < len(u_gapja) and is_valid_pillar(u_gapja[i])]
    for i in branch_indices:
        branch = u_gapja[i][1]
        el = BRANCH_ELEMENT.get(branch)
        relation = get_relation(day_el, el)
        score_map = {
            "비겁": +1.5,
            "인성": +2.0,
            "식상": -1.0,
            "재성": -1.5,
            "관성": -2.0,
        }
        total_score += score_map.get(relation, 0)
        total_score += _hidden_root_score(day_el, branch, i)

    for i in range(min(4, len(u_gapja))):
        if not is_valid_pillar(u_gapja[i]):
            continue
        stem = u_gapja[i][0]
        el = STEM_ELEMENT.get(stem)
        relation = get_relation(day_el, el)
        score_map = {
            "비겁": +1.0,
            "인성": +1.2,
            "식상": -0.8,
            "재성": -1.0,
            "관성": -1.2,
        }
        total_score += score_map.get(relation, 0)

    branches = [
        u_gapja[i][1]
        for i in range(min(4, len(u_gapja)))
        if is_valid_pillar(u_gapja[i])
    ]
    clash_cnt, combine_cnt, branch_score = check_branch_relation(branches)
    total_score += branch_score
    total_score += _lunar_calendar_bonus(birth_solar, month_branch) if month_branch else 0.0

    if total_score >= 3:
        strength = "신강"
    elif total_score <= -3:
        strength = "신약"
    else:
        strength = "중화"

    return {
        "day_el": day_el,
        "score": round(total_score, 2),
        "strength": strength,
        "clash": clash_cnt,
        "combine": combine_cnt,
    }
