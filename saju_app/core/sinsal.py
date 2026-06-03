"""12신살(연지·일지 삼합 패군 기준) — 순수 계산, Streamlit 비의존."""

from __future__ import annotations

# 지지 순환(子부터)
ZHI_CYCLE = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 각 지지가 속한 삼합(화·목·수·금)
JI_TO_SAMHAP: dict[str, str] = {
    "寅": "화",
    "午": "화",
    "戌": "화",
    "亥": "목",
    "卯": "목",
    "未": "목",
    "申": "수",
    "子": "수",
    "辰": "수",
    "巳": "금",
    "酉": "금",
    "丑": "금",
}

# 삼합별 패군(12신살 순환 시작 지지)
SAMHAP_START: dict[str, str] = {
    "화": "寅",
    "목": "亥",
    "수": "申",
    "금": "巳",
}

# 패군부터 순행하는 12신살 이름(STEP5 해석문과 맞춤: 역마·재살·화개 등)
SINSAL_ORDER: list[str] = [
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


def normalize_branch(br: str | None) -> str:
    if not br:
        return ""
    s = str(br).strip()
    if not s:
        return ""
    ch = s[-1]
    return ch if ch in JI_TO_SAMHAP or ch in ZHI_CYCLE else ch


def _sinsal_mapping_from_anchor(anchor_branch: str | None) -> dict[str, str] | None:
    """삼합 그룹의 패군(시작지)부터 12신살을 지지에 대응."""
    if not anchor_branch:
        return None
    ab = normalize_branch(anchor_branch)
    if not ab or ab not in JI_TO_SAMHAP:
        return None
    samhap_group = JI_TO_SAMHAP[ab]
    start_ji = SAMHAP_START.get(samhap_group)
    if not start_ji or start_ji not in ZHI_CYCLE:
        return None
    start_idx = ZHI_CYCLE.index(start_ji)
    out: dict[str, str] = {}
    for i in range(12):
        current_ji = ZHI_CYCLE[(start_idx + i) % 12]
        out[current_ji] = SINSAL_ORDER[i]
    return out


def calculate_sinsal(u_gapja: list[str] | tuple[str, ...] | None) -> dict[str, dict[str, str]]:
    """12신살: 연지 기준 + 일지(日支) 기준을 함께 표기."""
    empty = {
        "년지": {"연기준": "없음", "일기준": "없음"},
        "월지": {"연기준": "없음", "일기준": "없음"},
        "일지": {"연기준": "없음", "일기준": "없음"},
        "시지": {"연기준": "없음", "일기준": "없음"},
    }
    try:
        if not u_gapja or len(u_gapja) < 1:
            return empty

        def get_branch(p: object) -> str | None:
            if isinstance(p, str):
                if len(p) >= 2:
                    return normalize_branch(p[1])
                return normalize_branch(p[-1] if p else None)
            if isinstance(p, (list, tuple)) and len(p) >= 2:
                return normalize_branch(str(p[1]))
            return None

        year_branch = get_branch(u_gapja[0])
        day_branch = get_branch(u_gapja[2]) if len(u_gapja) > 2 else None

        map_y = _sinsal_mapping_from_anchor(year_branch)
        map_d = _sinsal_mapping_from_anchor(day_branch)

        def label(m: dict[str, str] | None, br: str | None) -> str:
            if not m or not br:
                return "없음"
            nb = normalize_branch(br)
            return m.get(nb, "없음")

        keys = ["년지", "월지", "일지", "시지"]
        pillars = [
            u_gapja[0],
            u_gapja[1] if len(u_gapja) > 1 else None,
            u_gapja[2] if len(u_gapja) > 2 else None,
            u_gapja[3] if len(u_gapja) > 3 else None,
        ]
        out: dict[str, dict[str, str]] = {}
        for k, p in zip(keys, pillars):
            br = get_branch(p) if p else None
            out[k] = {
                "연기준": label(map_y, br),
                "일기준": label(map_d, br),
            }
        return out
    except Exception:
        return empty
