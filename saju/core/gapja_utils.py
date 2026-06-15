"""간지(四柱) 유효성 — 시주 '모름' 등 잘못된 기둥을 엔진에서 제외."""

from __future__ import annotations

# engine.py와 순환 import 방지 — 천간·지지만 로컬 집합으로 검증
_VALID_STEMS: frozenset[str] = frozenset("甲乙丙丁戊己庚辛壬癸")
_VALID_BRANCHES: frozenset[str] = frozenset("子丑寅卯辰巳午未申酉戌亥")

_INVALID_PILLAR_EXACT: frozenset[str] = frozenset(
    {"", "??", "?", "모름", "unknown", "none", "null"}
)

def is_valid_pillar(pillar: object) -> bool:
    """년·월·일·시 기둥이 '갑자' 형태의 유효 간지인지."""
    s = str(pillar or "").strip()
    if len(s) < 2:
        return False
    if s.lower() in _INVALID_PILLAR_EXACT:
        return False
    if s.replace("?", "").strip() == "":
        return False
    stem, branch = s[0], s[1]
    return stem in _VALID_STEMS and branch in _VALID_BRANCHES


def effective_pillars(u_gapja: list[str] | tuple[str, ...] | None) -> list[str]:
    """엔진 계산에 쓸 유효 기둥만 (순서 유지)."""
    out: list[str] = []
    if not u_gapja:
        return out
    for p in u_gapja:
        if is_valid_pillar(p):
            out.append(str(p).strip())
    return out


def has_hour_pillar(u_gapja: list[str] | tuple[str, ...] | None) -> bool:
    """4번째(시주)가 유효한지."""
    if not u_gapja or len(u_gapja) < 4:
        return False
    return is_valid_pillar(u_gapja[3])


def pillar_slot_label(index: int) -> str:
    return ("년주", "월주", "일주", "시주")[index] if 0 <= index < 4 else "기둥"


def day_pillar_from_gapja(
    gapja: list[str] | tuple[str, ...] | None,
    *,
    index: int = 2,
) -> str | None:
    """사주 리스트에서 일주(기본 index=2) 간지를 반환. 유효하지 않으면 None."""
    if not gapja or index >= len(gapja):
        return None
    pillar = str(gapja[index] or "").strip()
    return pillar if is_valid_pillar(pillar) else None


def ilju_parts_from_gapja(
    gapja: list[str] | tuple[str, ...] | None,
    *,
    index: int = 2,
    fallback_ilju: str = "甲子",
) -> tuple[str, str, str | None]:
    """일주·일간·일지 — 유효 일주가 없으면 fallback_ilju에서 stem만 씁니다."""
    pillar = day_pillar_from_gapja(gapja, index=index)
    if pillar:
        stem = pillar[0]
        branch = pillar[1] if len(pillar) >= 2 else None
        return pillar, stem, branch
    fb = str(fallback_ilju or "甲子").strip() or "甲子"
    stem = fb[0] if fb else "甲"
    branch = fb[1] if len(fb) >= 2 else None
    return fb, stem, branch


def format_day_branch_rel_label(
    rel: str,
    u_day_branch: str | None,
    p_day_branch: str | None,
) -> str:
    """UI용 — '없음'을 '일지 없음'으로 오해하지 않게 구분합니다."""
    if not str(u_day_branch or "").strip() or not str(p_day_branch or "").strip():
        return "일지 미확인"
    r = str(rel or "").strip() or "없음"
    if r == "없음":
        return "무관(합·충·형·해 없음)"
    return r
