"""STEP4 궁합 — 두 사람 사주(간지·오행·십성·일지)를 비교한 맞춤 해설."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from saju.core.engine import BRANCH_ELEMENT, STEM_ELEMENT, get_relation
from saju_app.ui.components import (
    branch_pair_relation,
    day_branch_match_label,
    is_yin_stem,
    stem_he_relation,
)

_EL_KO: dict[str, str] = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}

_TEN_NARR: dict[str, str] = {
    "비견": "동료·친구처럼 대등하게 맞서며, 서로의 고집이 비슷할 때 경쟁이 붙습니다.",
    "겁재": "친밀하지만 자원·주도권 다툼이 생기기 쉬워, 경계선을 분명히 할수록 오래 갑니다.",
    "식신": "편안한 호감·배려로 풀리며, 일상과 식사·대화에서 친밀감이 커집니다.",
    "상관": "말과 표현이 활발해 설렘이 크지만, 말실수·자극으로 다툼도 빠를 수 있습니다.",
    "정재": "현실·생활·돈·약속으로 관계가 굳어지며, 안정적인 배우자 인연에 가깝습니다.",
    "편재": "끌림·기회·변동이 함께 오며, 연애 초반 스파크가 강한 편입니다.",
    "정관": "책임·신뢰·규칙으로 묶이며, 결혼·장기 동거 논의로 이어지기 쉽습니다.",
    "편관": "강한 끌림과 압박이 공존하며, 열정 뒤 피로·통제 갈등을 조심해야 합니다.",
    "정인": "보호·조언·정서적 안식으로 이어지며, 상대를 돌보는 쪽이 관계를 지탱합니다.",
    "편인": "직관·영감·비밀스러운 끌림이 있으나, 거리감·오해가 생기기도 합니다.",
}

_REL_NARR: dict[str, str] = {
    "비겁": "기질·속도가 비슷해 편하지만, 고집 충돌 시 양보가 어렵습니다.",
    "식상": "한쪽이 표현·아이디어를 내고 다른 쪽이 받아들이는 흐름으로, 대화가 활발합니다.",
    "재성": "현실·돈·성과·책임으로 연결되며, 생활·재정 이슈가 관계의 핵심 축이 됩니다.",
    "관성": "규칙·평가·책임·약속이 관계를 움직이며, 안정·결혼 논의로 이어지기 쉽습니다.",
    "인성": "보호·조언·정서적 지지가 강하며, 한쪽이 다른 쪽을 키워 주는 구도입니다.",
}


def _el_ko(el: str) -> str:
    s = str(el or "").strip()
    return _EL_KO.get(s, s)


def _section_label(base: str, ctx: Step4MatchContext, *, partner: bool = False) -> str:
    """카드 제목에 상대 이름·일주를 넣어 조합마다 구분."""
    if partner:
        return f"{base} · {ctx.p_name} {ctx.p_ilju}"
    return f"{base} · {ctx.u_ilju}"


def _pair_lead(ctx: Step4MatchContext) -> str:
    return (
        f"<b>{ctx.u_name}</b>({ctx.u_ilju}) × <b>{ctx.p_name}</b>({ctx.p_ilju}) · "
        f"일지 <b>{ctx.day_branch_rel}</b><br>"
    )


@dataclass(frozen=True)
class Step4MatchFactors:
    """궁합 점수 산출에 쓰인 핵심 지표."""

    day_branch_rel: str
    day_branch_same: bool
    day_stem_he: str
    mutual_sheng: bool
    element_balance: int
    spouse_star_fit: int
    yongshin_fit: int
    dae_overlap: int
    pillar_harmony: int
    pillar_conflict: int
    yin_yang_day: str
    match_score: int


@dataclass(frozen=True)
class Step4MatchContext:
    u_name: str
    p_name: str
    u_gapja: tuple[str, ...]
    p_gapja: tuple[str, ...]
    u_ilju: str
    p_ilju: str
    u_day_stem: str
    p_day_stem: str
    u_day_branch: str | None
    p_day_branch: str | None
    u_day_el: str
    p_day_el: str
    u_strength: str
    p_strength: str
    u_max_el: str
    u_min_el: str
    p_max_el: str
    p_min_el: str
    u_yong: str
    p_yong: str
    u_gender: str
    p_gender: str
    day_branch_rel: str
    day_branch_same: bool
    day_stem_he: str
    mutual_sheng: bool
    pillar_harmony: int
    pillar_conflict: int
    yin_yang_day: str
    u_spouse_el: str
    p_spouse_el: str
    u_next_3: tuple[str, ...]
    p_next_3: tuple[str, ...]
    match_score: int
    el_supplement: str


def _pillar_branch(gapja: tuple[str, ...], idx: int) -> str | None:
    if idx >= len(gapja):
        return None
    p = str(gapja[idx] or "")
    return p[1] if len(p) >= 2 else None


def _pillar_stem(gapja: tuple[str, ...], idx: int) -> str | None:
    if idx >= len(gapja):
        return None
    p = str(gapja[idx] or "")
    return p[0] if p else None


def _count_pillar_branch_stats(
    u_gapja: tuple[str, ...], p_gapja: tuple[str, ...]
) -> tuple[int, int]:
    """년·월·일 지지의 합(六合) 개수와 충·형·해 개수."""
    harmony = 0
    conflict = 0
    for idx in (0, 1, 2):
        rel = branch_pair_relation(_pillar_branch(u_gapja, idx), _pillar_branch(p_gapja, idx))
        if rel.startswith("합"):
            harmony += 1
        elif rel.startswith("충") or rel.startswith("형") or rel.startswith("해"):
            conflict += 1
    return harmony, conflict


def _count_stem_he(u_gapja: tuple[str, ...], p_gapja: tuple[str, ...]) -> int:
    n = 0
    for idx in (0, 1, 2):
        rel = stem_he_relation(_pillar_stem(u_gapja, idx), _pillar_stem(p_gapja, idx))
        if rel.startswith("天干合"):
            n += 1
    return n


def _mutual_element_flow(u_el: str, p_el: str) -> bool:
    """일간 오행이 서로 생(生)·돕(인성)하는 순환에 가까운지."""
    u2p = get_relation(u_el, p_el)
    p2u = get_relation(p_el, u_el)
    return (u2p == "식상" and p2u == "인성") or (p2u == "식상" and u2p == "인성")


def compute_step4_match_factors(
    *,
    u_gapja: list[str] | tuple[str, ...],
    p_gapja: list[str] | tuple[str, ...],
    u_day_branch: str | None,
    p_day_branch: str | None,
    u_day_stem: str,
    p_day_stem: str,
    u_day_el: str,
    p_day_el: str,
    u_max_el: str,
    u_min_el: str,
    p_max_el: str,
    p_min_el: str,
    u_yong: str,
    p_yong: str,
    u_gender: str,
    p_gender: str,
    u_spouse_el: str,
    p_spouse_el: str,
    u_next_3: list[str] | tuple[str, ...],
    p_next_3: list[str] | tuple[str, ...],
    get_ten_fn,
) -> Step4MatchFactors:
    """일지·천간합·오행·용신·년월 합·충·음양·대운을 종합해 점수 산출."""
    from saju_app.ui import components as C

    ug = tuple(str(x) for x in (u_gapja or ()))
    pg = tuple(str(x) for x in (p_gapja or ()))
    day_branch_same = bool(
        u_day_branch and p_day_branch and str(u_day_branch) == str(p_day_branch)
    )
    day_branch_rel = day_branch_match_label(u_day_branch, p_day_branch)
    day_stem_he = stem_he_relation(u_day_stem, p_day_stem)
    mutual_sheng = _mutual_element_flow(u_day_el, p_day_el)

    element_balance = 0
    if u_max_el == p_min_el or p_max_el == u_min_el:
        element_balance += 8
    if u_max_el == p_max_el:
        element_balance -= 6
    if u_min_el == p_min_el:
        element_balance -= 2
    if mutual_sheng:
        element_balance += 4

    spouse_star_fit = 0
    if p_max_el == u_spouse_el:
        spouse_star_fit += 7
    if u_max_el == p_spouse_el:
        spouse_star_fit += 7
    if p_min_el == u_spouse_el:
        spouse_star_fit -= 3
    if u_min_el == p_spouse_el:
        spouse_star_fit -= 3

    yongshin_fit = 0
    if u_yong and p_yong and u_yong == p_yong:
        yongshin_fit += 6
    if u_yong and p_yong and (u_yong == p_max_el or p_yong == u_max_el):
        yongshin_fit += 3
    if u_yong and p_min_el == u_yong:
        yongshin_fit += 2
    if p_yong and u_min_el == p_yong:
        yongshin_fit += 2

    u_to_p = [get_ten_fn(u_day_stem, g[0]) for g in (u_next_3 or ()) if g]
    p_to_u = [get_ten_fn(p_day_stem, g[0]) for g in (p_next_3 or ()) if g]
    dae_overlap = 0
    if any("관" in x for x in u_to_p) and any("관" in x for x in p_to_u):
        dae_overlap -= 2
    if any("인" in x for x in u_to_p) or any("인" in x for x in p_to_u):
        dae_overlap += 2
    shared = [g for g in u_next_3 if g in p_next_3]
    if shared:
        dae_overlap += 2

    pillar_harmony, pillar_conflict = _count_pillar_branch_stats(ug, pg)
    stem_he_count = _count_stem_he(ug, pg)
    yin_yang_balanced = is_yin_stem(u_day_stem) != is_yin_stem(p_day_stem)
    if yin_yang_balanced:
        yin_yang_day = "음양 조화"
    else:
        yin_yang_day = "음양 동극(같은 극성)"

    match_score = C.calc_simple_match_score(
        day_branch_rel=day_branch_rel,
        element_balance=element_balance,
        spouse_star_fit=spouse_star_fit,
        yongshin_fit=yongshin_fit,
        dae_overlap=dae_overlap,
        day_branch_same=day_branch_same,
        day_stem_he=day_stem_he.startswith("天干合"),
        mutual_sheng=mutual_sheng,
        pillar_harmony=pillar_harmony,
        pillar_conflict=pillar_conflict,
        yin_yang_balanced=yin_yang_balanced,
    )
    if stem_he_count >= 2:
        match_score = min(99, match_score + 2)

    return Step4MatchFactors(
        day_branch_rel=day_branch_rel,
        day_branch_same=day_branch_same,
        day_stem_he=day_stem_he,
        mutual_sheng=mutual_sheng,
        element_balance=element_balance,
        spouse_star_fit=spouse_star_fit,
        yongshin_fit=yongshin_fit,
        dae_overlap=dae_overlap,
        pillar_harmony=pillar_harmony,
        pillar_conflict=pillar_conflict,
        yin_yang_day=yin_yang_day,
        match_score=int(match_score),
    )


def build_step4_match_context(
    *,
    u_name: str,
    p_name: str,
    u_gapja: list[str],
    p_gapja: list[str],
    u_engine: dict[str, Any],
    p_engine: dict[str, Any],
    u_max_el: str,
    u_min_el: str,
    p_max_el: str,
    p_min_el: str,
    u_yong: str,
    p_yong: str,
    u_gender: str,
    p_gender: str,
    day_branch_rel: str,
    day_branch_same: bool = False,
    day_stem_he: str = "없음",
    mutual_sheng: bool = False,
    pillar_harmony: int = 0,
    pillar_conflict: int = 0,
    yin_yang_day: str = "",
    u_spouse_el: str,
    p_spouse_el: str,
    u_next_3: list[str],
    p_next_3: list[str],
    match_score: int,
) -> Step4MatchContext:
    u_ilju = u_gapja[2] if len(u_gapja) > 2 else "甲子"
    p_ilju = p_gapja[2] if len(p_gapja) > 2 else "甲子"
    u_ds = u_ilju[0] if u_ilju else "甲"
    p_ds = p_ilju[0] if p_ilju else "甲"
    u_db = u_ilju[1] if len(u_ilju) >= 2 else None
    p_db = p_ilju[1] if len(p_ilju) >= 2 else None
    u_de = str(u_engine.get("day_el") or STEM_ELEMENT.get(u_ds, "木"))
    p_de = str(p_engine.get("day_el") or STEM_ELEMENT.get(p_ds, "木"))
    el_sup = f"{u_max_el} ↔ {p_min_el}"
    return Step4MatchContext(
        u_name=str(u_name or "본인").strip(),
        p_name=str(p_name or "상대").strip(),
        u_gapja=tuple(str(x) for x in (u_gapja or ())),
        p_gapja=tuple(str(x) for x in (p_gapja or ())),
        u_ilju=str(u_ilju),
        p_ilju=str(p_ilju),
        u_day_stem=u_ds,
        p_day_stem=p_ds,
        u_day_branch=u_db,
        p_day_branch=p_db,
        u_day_el=u_de,
        p_day_el=p_de,
        u_strength=str(u_engine.get("strength") or "중화"),
        p_strength=str(p_engine.get("strength") or "중화"),
        u_max_el=u_max_el,
        u_min_el=u_min_el,
        p_max_el=p_max_el,
        p_min_el=p_min_el,
        u_yong=u_yong,
        p_yong=p_yong,
        u_gender=u_gender,
        p_gender=p_gender,
        day_branch_rel=str(day_branch_rel or "없음"),
        day_branch_same=bool(day_branch_same),
        day_stem_he=str(day_stem_he or "없음"),
        mutual_sheng=bool(mutual_sheng),
        pillar_harmony=int(pillar_harmony),
        pillar_conflict=int(pillar_conflict),
        yin_yang_day=str(yin_yang_day or ""),
        u_spouse_el=u_spouse_el,
        p_spouse_el=p_spouse_el,
        u_next_3=tuple(u_next_3 or ()),
        p_next_3=tuple(p_next_3 or ()),
        match_score=int(match_score),
        el_supplement=el_sup,
    )


def _ten_cross(get_ten_fn, u_stem: str, p_stem: str) -> tuple[str, str]:
    u2p = get_ten_fn(u_stem, p_stem)
    p2u = get_ten_fn(p_stem, u_stem)
    return u2p, p2u


def _branch_key(a: str | None, b: str | None) -> tuple[str, str]:
    aa = str(a or "?").strip()
    bb = str(b or "?").strip()
    return (aa, bb) if aa <= bb else (bb, aa)


def _branch_el_exchange(a: str, b: str) -> str:
    """지지 오행 상생·상극 한 줄."""
    ea = BRANCH_ELEMENT.get(a, "")
    eb = BRANCH_ELEMENT.get(b, "")
    if not ea or not eb:
        return ""
    rel_ab = get_relation(ea, eb)
    rel_ba = get_relation(eb, ea)
    if rel_ab == "식상":
        return f"지지 오행 <b>{_el_ko(ea)}→{_el_ko(eb)}</b> 생(生) 흐름"
    if rel_ab == "재성":
        return f"지지 <b>{_el_ko(ea)}</b>이 <b>{_el_ko(eb)}</b>을 극(克)하는 긴장"
    if rel_ab == "관성":
        return f"지지 <b>{_el_ko(ea)}</b>·<b>{_el_ko(eb)}</b> 극(克) — 역할·규칙 충돌 주의"
    if rel_ab == "인성":
        return f"지지 <b>{_el_ko(ea)}</b>이 <b>{_el_ko(eb)}</b>을 돕는 흐름"
    if rel_ab == "비겁":
        return f"지지 오행이 둘 다 <b>{_el_ko(ea)}</b> — 비슷한 리듬"
    if rel_ba == "식상":
        return f"지지 <b>{_el_ko(eb)}→{_el_ko(ea)}</b> 생(生) 흐름"
    return f"지지 <b>{_el_ko(ea)}↔{_el_ko(eb)}</b> 교차"


# 일지 조합별 맞춤 (합·충·형·해·없음 공통 — 상대가 바뀌면 문장이 달라짐)
_BRANCH_PAIR_NARR: dict[tuple[str, str], str] = {
    ("巳", "辰"): (
        "일지 <b>巳(사화)</b>·<b>辰(진토)</b>는 합·충은 없으나 <b>火生土</b>로 "
        "한쪽이 추진하면 다른 쪽이 받아 안정·집안이 굳어지기 쉽습니다. "
        "토 쪽이 답답해지기 전에 **역할·말할 때점**을 맞추세요."
    ),
    ("寅", "巳"): (
        "일지 <b>寅巳</b>는 <b>형(刑)·해(害)</b>에 가깝습니다. "
        "겉으로는 다투기보다 **고집·속도·말실수**가 겹칠 때 피로가 큽니다. "
        "결론을 내리기 전에 하루 쉬는 규칙이 필요합니다."
    ),
    ("寅", "辰"): (
        "일지 <b>寅(인목)</b>·<b>辰(진토)</b>는 <b>卯辰해</b>와 달리 직접 해·충은 없으나 "
        "<b>木↔土</b>로 한쪽이 밀면 다른 쪽이 버티기 쉽습니다. "
        "집안·돈·육아 같은 **현실 룰**을 문서로 맞추면 편합니다."
    ),
}


def _chong_deep_narrative(ctx: Step4MatchContext) -> str:
    """충(沖) — 강한 끌림과 다툼·이별 리스크의 오르내림."""
    ua, pb = ctx.u_day_branch or "?", ctx.p_day_branch or "?"
    return (
        f"<br><b>충(沖) 심층</b> — <b>{ua}↔{pb}</b>는 첫 만남·재회 때 "
        f"<b>자극·설렘</b>이 크게 올라갑니다. 다만 생활 리듬·말투·가치관이 "
        f"부딪히면 감정이 <b>급상승→급하강</b>하는 파도처럼 반복되기 쉽습니다. "
        f"<b>{ctx.u_name}</b>·<b>{ctx.p_name}</b>({ctx.u_ilju}×{ctx.p_ilju})는 "
        "싸움의 승패보다 <b>쿨다운·휴식·금전·역할 규칙</b>을 문서로 정할 때 "
        "이별·단절 리스크가 내려갑니다. 대운·세운에서 충이 다시 강해지는 해에는 "
        "이사·직장·가족 이슈와 함께 관계도 흔들릴 수 있으니, "
        "그 시기엔 큰 결정을 미루는 편이 안전합니다."
    )


def _stem_he_note(ctx: Step4MatchContext) -> str:
    rel = ctx.day_stem_he
    if not rel.startswith("天干合"):
        stem_he_n = _count_stem_he(ctx.u_gapja, ctx.p_gapja)
        if stem_he_n:
            return (
                f"<br>일간 천간합은 없으나 <b>년·월·일 천간합 {stem_he_n}건</b>이 있어 "
                "마음이 통하는 구간이 있습니다."
            )
        return "<br>일간 <b>천간합(天干合)</b>은 없습니다. 말로 마음을 맞추는 습관이 더 중요합니다."
    return (
        f"<br>일간 <b>{ctx.u_day_stem}↔{ctx.p_day_stem}</b> <b>{rel}</b> — "
        "겉말보다 <b>마음이 먼저 통하는</b> 느낌이 붙기 쉽습니다. "
        "다만 천간합만으로 생활 리듬까지 맞는다고 보지는 마세요."
    )


def _pillar_harmony_audit(ctx: Step4MatchContext) -> str:
    ph, pc = ctx.pillar_harmony, ctx.pillar_conflict
    lines = [
        f"년·월·일 지지 기준 — <b>합(六合) {ph}건</b> · "
        f"<b>충·형·해 {pc}건</b>"
    ]
    if ph >= 2 and pc == 0:
        lines.append(
            "일지·월지에 합이 많고 과도한 충·형·해가 없어 "
            "<b>집안·생활 환경</b>이 맞물리기 쉬운 편입니다."
        )
    elif pc >= 2:
        lines.append(
            "년·월·일에 충·형·해가 겹치면 가족·직장·이사 이슈와 "
            "감정이 <b>동시에</b> 흔들리기 쉽습니다. 규칙·합의를 먼저."
        )
    elif ph >= 1:
        lines.append("합 흐름이 일부 있어, 환경만 맞추면 체감 궁합이 올라갑니다.")
    else:
        lines.append(
            "뚜렷한 합은 적으나, 일지·오행·천간합으로 보완할 여지가 있습니다."
        )
    return "<br>".join(lines)


def _element_spouse_note(ctx: Step4MatchContext, *, u2p: str, p2u: str) -> str:
    lines: list[str] = []
    lines.extend(_element_exchange(ctx))
    if ctx.mutual_sheng:
        lines.append(
            "<b>상호 생(生)·돕(印)</b> 흐름 — 한쪽이 밀면 다른 쪽이 받아 "
            "기운이 <b>순환</b>하기 쉬운 구조입니다."
        )
    is_m_u = "남" in ctx.u_gender
    is_m_p = "남" in ctx.p_gender
    if is_m_u:
        lines.append(
            f"<b>{ctx.u_name}</b>(남): <b>재성(財星)</b> 축 <b>{ctx.u_spouse_el}({_el_ko(ctx.u_spouse_el)})</b> — "
            f"아내·연인 기운. 상대 강한 <b>{ctx.p_max_el}</b>이 이 축과 맞으면 인연이 선명합니다."
        )
    if is_m_p:
        lines.append(
            f"<b>{ctx.p_name}</b>(남): <b>재성(財星)</b> 축 <b>{ctx.p_spouse_el}({_el_ko(ctx.p_spouse_el)})</b>."
        )
    if (not is_m_u) and any(x in ctx.u_gender for x in ("여", "女", "F", "f")):
        lines.append(
            f"<b>{ctx.u_name}</b>(여): <b>관성(官星)</b> 축 <b>{ctx.u_spouse_el}({_el_ko(ctx.u_spouse_el)})</b> — "
            f"남편·배우자 기운."
        )
    if (not is_m_p) and any(x in ctx.p_gender for x in ("여", "女", "F", "f")):
        lines.append(
            f"<b>{ctx.p_name}</b>(여): <b>관성(官星)</b> 축 <b>{ctx.p_spouse_el}({_el_ko(ctx.p_spouse_el)})</b>."
        )
    lines.append(
        f"일간 십성 교차: <b>{u2p}</b>/<b>{p2u}</b> — "
        f"{_TEN_NARR.get(u2p, '')}"
    )
    return "<br>".join(lines)


def _yongshin_mutual_note(ctx: Step4MatchContext) -> str:
    base = _yongshin_note(ctx)
    extra: list[str] = []
    if ctx.u_yong and ctx.p_max_el == ctx.u_yong:
        extra.append(
            f"<b>{ctx.p_name}</b>의 강한 <b>{ctx.p_max_el}</b>이 "
            f"<b>{ctx.u_name}</b> 용신 <b>{ctx.u_yong}</b>을 살려 줍니다."
        )
    if ctx.p_yong and ctx.u_max_el == ctx.p_yong:
        extra.append(
            f"<b>{ctx.u_name}</b>의 강한 <b>{ctx.u_max_el}</b>이 "
            f"<b>{ctx.p_name}</b> 용신 <b>{ctx.p_yong}</b>을 보완합니다."
        )
    if ctx.u_yong and ctx.p_yong and ctx.u_yong != ctx.p_yong:
        extra.append(
            "용신이 다르면 각자 회복 루틴(수면·식사·공간)을 강요하지 말고 "
            "<b>공통 시간</b>만 설계하세요."
        )
    if not extra:
        return base
    return base + "<br>" + "<br>".join(extra)


def _branch_pair_narrative(ctx: Step4MatchContext, *, brief: bool = False) -> str:
    """일지 관계 + 지지 쌍 — 정선주(巳辰) vs 김지현(巳寅) 등 조합마다 다른 문장."""
    rel = ctx.day_branch_rel
    ua, pb = ctx.u_day_branch or "?", ctx.p_day_branch or "?"
    pair = _branch_key(ua, pb)
    if ctx.day_branch_same:
        text = (
            f"일지 <b>{ua}</b>가 <b>동일</b>합니다. 생활 리듬·수면·식사·취향이 비슷해 "
            f"<b>속궁합</b>이 가장 높은 편입니다. "
            f"<b>{ctx.u_ilju}×{ctx.p_ilju}</b>는 편하지만, "
            "같은 고집·같은 약점도 겹치므로 **서로의 빈 오행**을 챙기는 습관이 필요합니다."
        )
    elif rel.startswith("합"):
        text = (
            f"일지 <b>{ua}↔{pb}</b>가 <b>합(六合)</b>이라 정서적 끌림·집안 안정감이 붙기 쉽습니다. "
            f"<b>{ctx.u_ilju}×{ctx.p_ilju}</b> 조합은 편해질수록 불만을 쌓지 말고 감사·요청을 자주 하세요."
        )
    elif rel.startswith("충"):
        text = (
            f"일지 <b>{ua}↔{pb}</b>가 <b>충(沖)</b>입니다. "
            f"끌림·자극은 강하지만 다툼·이별 리스크도 함께 오르내립니다. "
            f"<b>{ctx.u_name}</b>·<b>{ctx.p_name}</b>는 싸움의 승패보다 "
            "**휴식·역할·금전 룰**을 먼저 정리하세요."
        )
        if not brief:
            text += _chong_deep_narrative(ctx)
    elif rel.startswith("형"):
        text = (
            f"일지 <b>{ua}↔{pb}</b> <b>형(刑)</b> — 표면 평화 속 **고집·말실수·피로**가 겹치기 쉽습니다. "
            f"<b>{ctx.p_name}</b>({ctx.p_ilju})와는 결론을 서두르지 말고 쿨다운 후 대화하세요."
        )
    elif rel.startswith("해"):
        text = (
            f"일지 <b>{ua}↔{pb}</b> <b>해(害)</b> — 친밀한데 **오해·질투·타이밍**이 어긋나기 쉽습니다. "
            f"의도를 확인하는 질문 한 번이 <b>{ctx.u_ilju}×{ctx.p_ilju}</b> 체감 궁합을 바꿉니다."
        )
    elif pair in _BRANCH_PAIR_NARR:
        text = _BRANCH_PAIR_NARR[pair]
    else:
        ex = _branch_el_exchange(ua, pb)
        text = (
            f"일지 <b>{ua}↔{pb}</b>는 합·충·형·해가 뚜렷하지 않습니다. "
            f"{ex + ' — ' if ex else ''}"
            f"<b>{ctx.p_name}</b>({ctx.p_ilju})와는 표면 갈등보다 **오해·타이밍·피로** 누적을 조심하세요. "
            "말할 때점만 맞춰도 체감 궁합이 달라집니다."
        )
    if brief:
        return text.split("。")[0].split(".")[0] + "." if "." in text else text[:120] + "…"
    return text


def _day_el_pair_note(ctx: Step4MatchContext) -> str:
    """일간 오행 교차 — 상대마다 다른 문장."""
    u, p = ctx.u_day_el, ctx.p_day_el
    rel_u = get_relation(u, p)
    rel_p = get_relation(p, u)
    if u == p:
        return (
            f"일간 둘 다 <b>{_el_ko(u)}</b>(<b>{ctx.u_ilju}</b>·<b>{ctx.p_ilju}</b>)라 "
            "속도·고집이 비슷한 편입니다. 편하지만 **양보 습관**이 없으면 피로가 쌓입니다."
        )
    return (
        f"<b>{ctx.u_name}</b> <b>{_el_ko(u)}</b>→<b>{ctx.p_name}</b> <b>{_el_ko(p)}</b> <b>{rel_u}</b> — "
        f"{_REL_NARR.get(rel_u, '기질 에너지가 교차합니다.')}"
        f"<br><b>{ctx.p_name}</b> <b>{_el_ko(p)}</b>→<b>{ctx.u_name}</b> <b>{rel_p}</b> — "
        f"{_REL_NARR.get(rel_p, '')}"
    )


def _year_month_pillar_note(ctx: Step4MatchContext, *, get_ten_fn) -> str:
    uy = ctx.u_gapja[0] if ctx.u_gapja else "?"
    py = ctx.p_gapja[0] if ctx.p_gapja else "?"
    um = ctx.u_gapja[1] if len(ctx.u_gapja) > 1 else "?"
    pm = ctx.p_gapja[1] if len(ctx.p_gapja) > 1 else "?"
    yb_u, yb_p = (uy[1] if len(uy) >= 2 else "?"), (py[1] if len(py) >= 2 else "?")
    mb_u, mb_p = (um[1] if len(um) >= 2 else "?"), (pm[1] if len(pm) >= 2 else "?")
    y_rel = branch_pair_relation(yb_u, yb_p)
    m_rel = branch_pair_relation(mb_u, mb_p)
    u_y2p = get_ten_fn(uy[0] if uy else "?", py[0] if py else "?")
    lines = [
        f"년주 <b>{uy}</b>↔<b>{py}</b> · 일지 <b>{y_rel}</b> · "
        f"{ctx.u_name}→{ctx.p_name} <b>{u_y2p}</b>",
        f"월주 <b>{um}</b>↔<b>{pm}</b> · 일지 <b>{m_rel}</b>",
    ]
    if y_rel.startswith("충") or m_rel.startswith("충"):
        lines.append("년·월 축에 **충**이 있어 가족·직장·이사 이슈가 동시에 올 수 있습니다.")
    elif y_rel.startswith("합") or m_rel.startswith("합"):
        lines.append("년·월 **합** 흐름이 있어 집안·직장 환경이 맞물리기 쉽습니다.")
    else:
        lines.append(
            f"년·월은 <b>{y_rel}</b>/<b>{m_rel}</b> — 환경·부모·직장 배경이 "
            f"<b>{ctx.p_ilju}</b> 일주와 함께 생활 리듬을 만듭니다."
        )
    return "<br>".join(lines)


def _spouse_structure_note(
    ctx: Step4MatchContext, *, u2p: str, p2u: str, is_f_u: bool, is_f_p: bool
) -> str:
    if not (is_f_u or is_f_p):
        return ""
    if is_f_p:
        ten_to_male = p2u
        female, ilju = ctx.p_name, ctx.p_ilju
    else:
        ten_to_male = u2p
        female, ilju = ctx.u_name, ctx.u_ilju
    if "관" in ten_to_male or "재" in ten_to_male:
        return (
            f"<br><b>{female}</b>(<b>{ilju}</b>) 일주는 상대에게 <b>{ten_to_male}</b>으로 읽혀 "
            "약속·배우자·재물 주제가 선명합니다."
        )
    return (
        f"<br><b>{female}</b>(<b>{ilju}</b>) — 연애·결혼은 <b>{u2p}/{p2u}</b> 교차로 "
        f"<b>{ctx.u_ilju}×{ctx.p_ilju}</b>만의 패턴을 봅니다."
    )


def _coordination_tail(ctx: Step4MatchContext) -> str:
    if ctx.day_branch_rel.startswith("형") or ctx.day_branch_rel.startswith("해"):
        return (
            "친밀·성적 리듬은 단일 점수로 단정하지 않으며, "
            f"<b>{ctx.day_branch_rel}</b> 조합은 **스트레스·말실수 주기**와 존중이 우선입니다."
        )
    if ctx.u_strength != ctx.p_strength:
        return (
            "친밀·성적 리듬은 강약 차이만큼 **속도 조율**이 중요하며, "
            "한쪽이 지칠 때 다른 쪽이 기다리는 습관이 필요합니다."
        )
    return (
        "친밀·성적 리듬은 단일 점수로 단정하지 않으며, "
        f"<b>{ctx.p_ilju}</b> 조합의 스트레스 주기와 존중이 우선입니다."
    )


def _element_exchange(ctx: Step4MatchContext) -> list[str]:
    lines: list[str] = []
    if ctx.u_max_el == ctx.p_min_el:
        lines.append(
            f"<b>{ctx.u_name}</b>의 강한 <b>{ctx.u_max_el}({_el_ko(ctx.u_max_el)})</b>이 "
            f"<b>{ctx.p_name}</b>의 약한 <b>{ctx.p_min_el}({_el_ko(ctx.p_min_el)})</b>을 보완합니다."
        )
    if ctx.p_max_el == ctx.u_min_el:
        lines.append(
            f"<b>{ctx.p_name}</b>의 강한 <b>{ctx.p_max_el}({_el_ko(ctx.p_max_el)})</b>이 "
            f"<b>{ctx.u_name}</b>의 약한 <b>{ctx.u_min_el}({_el_ko(ctx.u_min_el)})</b>을 보완합니다."
        )
    if ctx.u_max_el == ctx.p_max_el:
        lines.append(
            f"둘 다 <b>{ctx.u_max_el}({_el_ko(ctx.u_max_el)})</b>이 강해 **비슷한 고집·속도**로 편하지만, "
            "같은 축이 과하면 피로·경쟁도 커질 수 있습니다."
        )
    if ctx.u_min_el == ctx.p_min_el:
        lines.append(
            f"둘 다 <b>{ctx.u_min_el}({_el_ko(ctx.u_min_el)})</b>이 약해, "
            "그 영역(건강·집중·재정 중 해당 축)은 **서로 챙기는 습관**이 필요합니다."
        )
    if not lines:
        lines.append(
            f"오행 보완 축은 <b>{ctx.el_supplement}</b>로 읽히며, "
            "서로 다른 강·약 분포가 맞물려야 생활 밸런스가 잡힙니다."
        )
    return lines


def _strength_pair_note(ctx: Step4MatchContext) -> str:
    u, p = ctx.u_strength, ctx.p_strength
    head = f"<b>{ctx.p_name}</b>({ctx.p_ilju}) 강약 <b>{p}</b> · <b>{ctx.u_name}</b>({ctx.u_ilju}) <b>{u}</b> — "
    if u == p:
        if u == "신강":
            return (
                head
                + "둘 다 신강이라 추진력이 강합니다. "
                "서로 밀어붙이기보다 **역할 분담**을 정하면 시너지가 큽니다."
            )
        if u == "신약":
            return (
                head
                + "둘 다 신약이라 섬세하지만 결정이 늦어질 수 있습니다. "
                "작은 것부터 **합의한 실행**이 관계를 살립니다."
            )
        return head + f"둘 다 <b>{u}</b> 구조라 **조율·타이밍**이 관건입니다."
    if u == "신강" and p == "신약":
        return (
            head
            + f"<b>{ctx.u_name}</b>이 밀고 <b>{ctx.p_name}</b>이 받아 주는 구도입니다. "
            "강한 쪽이 말을 줄이고 약한 쪽의 표현을 끌어내면 균형이 맞습니다."
        )
    if u == "신약" and p == "신강":
        return (
            head
            + f"<b>{ctx.p_name}</b>이 밀고 <b>{ctx.u_name}</b>이 받아 주는 구도입니다. "
            "주도권을 나누고, 약한 쪽이 필요를 분명히 말할수록 오해가 줄어듭니다."
        )
    return (
        head
        + "강약이 엇갈립니다. 한쪽이 힘들 때 다른 쪽이 속도를 맞추는 것이 핵심입니다."
    )


def _yongshin_note(ctx: Step4MatchContext) -> str:
    uy, py = ctx.u_yong, ctx.p_yong
    if uy and py and uy == py:
        return (
            f"<b>{ctx.u_name}</b>·<b>{ctx.p_name}</b> 용신이 둘 다 <b>{uy}({_el_ko(uy)})</b>입니다. "
            f"같은 기운이지만 <b>{ctx.p_ilju}</b> 일주와 <b>{ctx.p_strength}</b> 강약에 따라 "
            "생활 속도는 달라질 수 있으니, 휴식·식사 리듬은 각자 확인하세요."
        )
    if uy and py:
        return (
            f"용신: <b>{ctx.u_name}</b> <b>{uy}({_el_ko(uy)})</b> · "
            f"<b>{ctx.p_name}</b> <b>{py}({_el_ko(py)})</b> — "
            f"<b>{ctx.p_ilju}</b> 조합은 환경 취향이 다를 수 있어 공통 시간만 설계하는 편이 좋습니다."
        )
    return (
        f"<b>{ctx.p_name}</b>({ctx.p_ilju}) 용신 정보가 불명확하면, "
        "먼저 각자 피로가 덜한 생활 루틴부터 맞춰 보세요."
    )


def _daewoon_overlap_note(ctx: Step4MatchContext) -> str:
    u3, p3 = ctx.u_next_3, ctx.p_next_3
    if not u3 or not p3:
        return "대운 흐름은 STEP9에서 더 자세히 보실 수 있습니다."
    shared = [g for g in u3 if g in p3]
    if shared:
        return (
            f"가까운 대운에 <b>{', '.join(shared)}</b> 흐름이 겹쳐, "
            "같은 시기에 이사·직장·관계 이슈가 동시에 올 수 있습니다. "
            "중요한 결정은 **함께 일정을 맞춰** 진행하세요."
        )
    return (
        f"<b>{ctx.u_name}</b> {', '.join(u3)} · <b>{ctx.p_name}</b> {', '.join(p3)}로 "
        "시기가 엇갈려, 한쪽이 바쁠 때 다른 쪽이 기다려 주는 구조가 필요합니다."
    )


def pair_analysis_banner(ctx: Step4MatchContext) -> str:
    """STEP4 상단 조합 배너(어두운 배경·밝은 글씨)."""
    u4 = " · ".join(ctx.u_gapja[:4]) if len(ctx.u_gapja) >= 4 else ctx.u_ilju
    p4 = " · ".join(ctx.p_gapja[:4]) if len(ctx.p_gapja) >= 4 else ctx.p_ilju
    stem_bit = (
        f" · 천간 <b>{ctx.day_stem_he}</b>"
        if ctx.day_stem_he.startswith("天干合")
        else ""
    )
    yy = f" · <b>{ctx.yin_yang_day}</b>" if ctx.yin_yang_day else ""
    return (
        f'<div class="step4-pair-banner">'
        f"<b>{ctx.u_name}</b> <span class='step4-pair-pillars'>{u4}</span>"
        f" × <b>{ctx.p_name}</b> <span class='step4-pair-pillars'>{p4}</span>"
        f" · 일지 <b>{ctx.day_branch_rel}</b>{stem_bit}{yy}"
        f" · 합{ctx.pillar_harmony}/충형해{ctx.pillar_conflict}"
        f" · 종합 <b>{ctx.match_score}</b>점"
        f"</div>"
    )


def _pillar_labels() -> tuple[str, ...]:
    return ("년주", "월주", "일주", "시주")


def pillar_compare_note(ctx: Step4MatchContext, *, get_ten_fn) -> str:
    """네 기둥·십성 교차 — 상대가 바뀌면 문장이 달라집니다."""
    labels = _pillar_labels()
    lines: list[str] = []
    ug = list(ctx.u_gapja[:4])
    pg = list(ctx.p_gapja[:4])
    for i, lab in enumerate(labels):
        u_p = ug[i] if i < len(ug) else "?"
        p_p = pg[i] if i < len(pg) else "?"
        u_st = u_p[0] if u_p and len(u_p) >= 1 else "?"
        p_st = p_p[0] if p_p and len(p_p) >= 1 else "?"
        u2p = get_ten_fn(u_st, p_st)
        p2u = get_ten_fn(p_st, u_st)
        lines.append(
            f"<b>{lab}</b> {u_p}↔{p_p} · "
            f"{ctx.u_name}→{ctx.p_name} <b>{u2p}</b> / "
            f"{ctx.p_name}→{ctx.u_name} <b>{p2u}</b>"
        )
    return "<br>".join(lines)


def tab_love_sections(
    ctx: Step4MatchContext, *, get_ten_fn
) -> list[tuple[str, str, str]]:
    u2p, p2u = _ten_cross(get_ten_fn, ctx.u_day_stem, ctx.p_day_stem)
    rel_u = get_relation(ctx.u_day_el, ctx.p_day_el)
    rel_p = get_relation(ctx.p_day_el, ctx.u_day_el)
    is_f_u = any(x in ctx.u_gender for x in ("여", "女", "F", "f"))
    is_f_p = any(x in ctx.p_gender for x in ("여", "女", "F", "f"))
    spouse_note = _spouse_structure_note(
        ctx, u2p=u2p, p2u=p2u, is_f_u=is_f_u, is_f_p=is_f_p
    )
    body1 = (
        _pair_lead(ctx)
        + "<b>① 일지 궁합(최우선)</b><br>"
        + f"일지 <b>{ctx.u_day_branch or '?'}</b> ↔ <b>{ctx.p_day_branch or '?'}</b> · "
        f"<b>{ctx.day_branch_rel}</b><br>"
        + _branch_pair_narrative(ctx)
        + spouse_note
        + "<br><b>② 천간합·음양</b>"
        + _stem_he_note(ctx)
        + f"<br>일간 음양: <b>{ctx.yin_yang_day}</b> — "
        + (
            "한쪽이 양·한쪽이 음이면 역할 분담이 자연스럽습니다."
            if ctx.yin_yang_day.startswith("음양 조화")
            else "같은 극성(양·양/음·음)은 속도·고집이 비슷해 편하지만 충돌도 커질 수 있습니다."
        )
    )
    body2 = (
        _pair_lead(ctx)
        + "<b>③ 오행 보완·배우자 십성</b><br>"
        + _element_spouse_note(ctx, u2p=u2p, p2u=p2u)
        + "<br>일간 오행: <b>"
        + rel_u
        + "</b> / <b>"
        + rel_p
        + "</b> — "
        + _REL_NARR.get(rel_u, "")
    )
    body3 = (
        _pair_lead(ctx)
        + "<b>④ 용신·년월·대운</b><br>"
        + _yongshin_mutual_note(ctx)
        + "<br>"
        + _pillar_harmony_audit(ctx)
        + "<br>"
        + f"<b>{ctx.p_name}</b> 대운: {', '.join(ctx.p_next_3)}<br>"
        + _daewoon_overlap_note(ctx)
    )
    body4 = _pair_lead(ctx) + pillar_compare_note(ctx, get_ten_fn=get_ten_fn)
    return [
        (_section_label("감정·일지 관계", ctx, partner=True), body1, "rose"),
        (_section_label("십성·끌림 방향", ctx, partner=True), body2, "purple"),
        (_section_label("용신·대운 타이밍", ctx, partner=True), body3, "green"),
        (_section_label("네 기둥 십성 교차", ctx, partner=True), body4, "purple"),
    ]


def tab_life_sections(ctx: Step4MatchContext, *, get_ten_fn) -> list[tuple[str, str, str]]:
    u2p, p2u = _ten_cross(get_ten_fn, ctx.u_day_stem, ctx.p_day_stem)
    body1 = (
        _pair_lead(ctx)
        + "<b>오행·생활 리듬</b><br>"
        + "<br>".join(_element_exchange(ctx))
        + "<br>"
        + _strength_pair_note(ctx)
        + "<br>"
        + (
            "<b>상호 생(生) 순환</b> 구조입니다.<br>"
            if ctx.mutual_sheng
            else ""
        )
        + f"생활 리듬: <b>{ctx.u_name}</b> <b>{ctx.u_max_el}</b> · <b>{ctx.p_name}</b> <b>{ctx.p_max_el}</b> 주도."
    )
    body2 = (
        _pair_lead(ctx)
        + _year_month_pillar_note(ctx, get_ten_fn=get_ten_fn)
        + "<br>"
        + _day_el_pair_note(ctx)
        + "<br>"
        f"역할 십성 <b>{u2p}</b>/<b>{p2u}</b> — <b>{ctx.p_name}</b>과의 생활·직장 패턴.<br>"
        + _daewoon_overlap_note(ctx)
    )
    return [
        (_section_label("생활·오행 리듬", ctx, partner=True), body1, "blue"),
        (_section_label("역할·커리어 타이밍", ctx, partner=True), body2, "blue"),
    ]


def tab_wealth_sections(ctx: Step4MatchContext) -> list[tuple[str, str, str]]:
    u_sp = _el_ko(ctx.u_spouse_el)
    p_sp = _el_ko(ctx.p_spouse_el)
    u_line = (
        f"<b>{ctx.u_name}</b>({ctx.u_gender}): 배우자·재물 축 <b>{ctx.u_spouse_el}({u_sp})</b>, "
        f"강 <b>{ctx.u_max_el}</b> / 약 <b>{ctx.u_min_el}</b>"
    )
    p_line = (
        f"<b>{ctx.p_name}</b>({ctx.p_gender}): 배우자·재물 축 <b>{ctx.p_spouse_el}({p_sp})</b>, "
        f"강 <b>{ctx.p_max_el}</b> / 약 <b>{ctx.p_min_el}</b>"
    )
    clash = ""
    if ctx.u_max_el == ctx.p_max_el:
        clash = (
            f"<br>둘 다 <b>{ctx.u_max_el}</b> 재성·성과 축이 강해, "
            "돈·지출·투자 기준이 비슷하면 편하지만 **과소비·투자 성향**도 닮을 수 있습니다."
        )
    elif ctx.u_max_el == ctx.p_min_el or ctx.p_max_el == ctx.u_min_el:
        clash = (
            "<br>한쪽이 돈·실무를 끌고 다른 쪽이 소비·감정 소비를 키우기 쉬우니, "
            "**한도·저축·카드 규칙**을 문서로 정리하세요."
        )
    if ctx.u_spouse_el == ctx.p_spouse_el:
        tail = (
            f"재물·배우자 축이 둘 다 <b>{ctx.u_spouse_el}({_el_ko(ctx.u_spouse_el)})</b>로 같아, "
            "돈·약속 기준을 맞추기 쉽습니다."
        )
    else:
        tail = (
            f"<b>{ctx.u_name}</b> 축 <b>{ctx.u_spouse_el}</b> · <b>{ctx.p_name}</b> 축 <b>{ctx.p_spouse_el}</b> — "
            "큰 지출·저축은 합의, 생활비·용돈은 각자 자율로 나누는 편이 맞습니다."
        )
    body = _pair_lead(ctx) + u_line + "<br>" + p_line + clash + "<br>" + _yongshin_note(ctx) + "<br>" + tail
    return [(_section_label("재물·배우자 축 비교", ctx, partner=True), body, "gold")]


def tab_caution_sections(ctx: Step4MatchContext) -> list[tuple[str, str, str]]:
    risk: list[str] = []
    ua, pb = ctx.u_day_branch or "?", ctx.p_day_branch or "?"
    if ctx.pillar_conflict >= 2:
        risk.append(
            f"년·월·일 충·형·해 <b>{ctx.pillar_conflict}건</b>: "
            "가족·직장·이사와 감정이 동시에 흔들릴 수 있습니다."
        )
    if ctx.day_branch_same:
        risk.append(
            f"일지 <b>{ua}</b> 동일: 편하지만 <b>같은 약점·고집</b>이 겹칠 수 있어 "
            "약한 오행·휴식 리듬을 서로 챙기세요."
        )
    elif ctx.day_branch_rel.startswith("충"):
        risk.append(
            f"일지 <b>{ua}↔{pb}</b> 충: 끌림 뒤 다툼·이별 리스크 — **쿨다운·휴식** 규칙을 정하세요."
        )
    elif ctx.day_branch_rel.startswith("형"):
        risk.append(
            f"일지 <b>{ua}↔{pb}</b> 형: 고집·말실수가 겹치면 피로가 큽니다. 결론은 하루 뒤에."
        )
    elif ctx.day_branch_rel.startswith("해"):
        risk.append(
            f"일지 <b>{ua}↔{pb}</b> 해: 오해·질투·타이밍 어긋남 — 의도 확인 질문을 습관화하세요."
        )
    elif ctx.day_branch_rel.startswith("합"):
        risk.append(
            f"일지 <b>{ua}↔{pb}</b> 합: 편해질수록 불만을 쌓지 말고 감사·요청을 자주 하세요."
        )
    else:
        pair = _branch_key(ua, pb)
        if pair == ("巳", "辰"):
            risk.append(
                "巳辰(火生土): 한쪽이 밀면 다른 쪽이 답답해지기 전에 **역할·말할 때점**을 맞추세요."
            )
        elif pair == ("寅", "巳"):
            risk.append(
                "寅巳 형·해: 속도·고집 충돌 — 결론을 서두르지 말고 쿨다운 후 대화하세요."
            )
        else:
            risk.append(
                f"일지 <b>{ua}↔{pb}</b>: 합·충은 약하나 **오해·피로** 누적을 조심하세요."
            )
    if ctx.u_strength != ctx.p_strength:
        risk.append(
            f"강약 차이(<b>{ctx.u_strength}</b>·<b>{ctx.p_strength}</b>): "
            "한쪽이 지칠 때 다른 쪽이 **속도를 낮추는** 연습이 필요합니다."
        )
    if ctx.u_yong and ctx.p_yong and ctx.u_yong != ctx.p_yong:
        risk.append(
            f"용신 불일치(<b>{ctx.u_yong}</b>·<b>{ctx.p_yong}</b>): "
            "각자 회복법(수면·식사·공간)이 달라 **강요하지 말 것**."
        )
    if ctx.u_max_el == ctx.p_max_el:
        risk.append(
            f"같은 오행 과다(<b>{ctx.u_max_el}</b>): 고집·경쟁·피로가 동시에 올 수 있습니다."
        )
    if not risk:
        risk.append(
            f"<b>{ctx.u_ilju}×{ctx.p_ilju}</b>: 특이한 충·극은 적으나 피로·오해 누적은 조심하세요."
        )
    body1 = (
        _pair_lead(ctx)
        + f"종합 <b>{ctx.match_score}</b>점<br>"
        + "<br>".join(f"· {x}" for x in risk)
    )
    body2 = (
        _pair_lead(ctx)
        + _strength_pair_note(ctx)
        + "<br>"
        + _branch_pair_narrative(ctx)
        + "<br>"
        + _coordination_tail(ctx)
    )
    return [
        (_section_label("주의 포인트", ctx, partner=True), body1, "amber"),
        (_section_label("조율·갈등 예방", ctx, partner=True), body2, "amber"),
    ]


def conclusion_sections(
    ctx: Step4MatchContext, *, get_ten_fn
) -> list[tuple[str, str, str]]:
    """title, body, tone — 상대 일주·십성·일지마다 문장이 달라집니다."""
    u2p, p2u = _ten_cross(get_ten_fn, ctx.u_day_stem, ctx.p_day_stem)
    strength_bits: list[str] = [
        f"<b>{ctx.u_ilju}</b> × <b>{ctx.p_ilju}</b> · 일지 <b>{ctx.day_branch_rel}</b> · "
        f"십성 <b>{u2p}/{p2u}</b>"
    ]
    if ctx.day_branch_same:
        strength_bits.append(
            "일지 동일 — 생활·생체 리듬이 비슷해 <b>속궁합</b>이 가장 높은 편입니다."
        )
    if ctx.day_stem_he.startswith("天干合"):
        strength_bits.append(f"일간 <b>{ctx.day_stem_he}</b> — 마음이 통하는 느낌이 붙기 쉽습니다.")
    if ctx.mutual_sheng:
        strength_bits.append("일간 오행이 <b>상호 생·돕</b>는 순환 구조입니다.")
    if ctx.u_max_el == ctx.p_min_el:
        strength_bits.append(
            f"<b>{ctx.u_name}</b>의 <b>{ctx.u_max_el}</b>이 "
            f"<b>{ctx.p_name}</b>의 약한 <b>{ctx.p_min_el}</b>을 메웁니다."
        )
    if ctx.p_max_el == ctx.u_min_el:
        strength_bits.append(
            f"<b>{ctx.p_name}</b>의 <b>{ctx.p_max_el}</b>이 "
            f"<b>{ctx.u_name}</b>의 약한 <b>{ctx.u_min_el}</b>을 메웁니다."
        )
    if ctx.u_yong and ctx.p_yong and ctx.u_yong == ctx.p_yong:
        strength_bits.append(
            f"용신 <b>{ctx.u_yong}({_el_ko(ctx.u_yong)})</b>이 같아 생활·휴식 리듬을 맞추기 쉽습니다."
        )
    if len(strength_bits) == 1:
        strength_bits.append(
            f"강한 축 <b>{ctx.u_max_el}</b>·<b>{ctx.p_max_el}</b>이 달라 "
            "역할만 나누면 시너지가 납니다."
        )
    strength = "<br>".join(strength_bits)

    caution_bits: list[str] = [
        f"종합 <b>{ctx.match_score}</b>점 · "
        f"<b>{ctx.u_strength}</b>·<b>{ctx.p_strength}</b>"
    ]
    if ctx.day_branch_rel.startswith("충"):
        caution_bits.append(
            f"일지 <b>{ctx.day_branch_rel}</b>: 감정 폭발 전 쿨다운·생활 규칙을 먼저 정하세요."
        )
    elif ctx.day_branch_rel.startswith("합"):
        caution_bits.append(
            f"일지 <b>{ctx.day_branch_rel}</b>: 편해질수록 불만을 쌓지 말고 감사·요청을 자주 하세요."
        )
    elif ctx.day_branch_rel.startswith("형"):
        caution_bits.append(
            f"일지 <b>{ctx.day_branch_rel}</b>: 고집·말실수·피로 겹침 — 쿨다운 후 대화하세요."
        )
    elif ctx.day_branch_rel.startswith("해"):
        caution_bits.append(
            f"일지 <b>{ctx.day_branch_rel}</b>: 오해·질투·타이밍 어긋남을 조심하세요."
        )
    else:
        pair = _branch_key(ctx.u_day_branch, ctx.p_day_branch)
        if pair == ("巳", "辰"):
            caution_bits.append(
                "巳辰(火生土): 역할·말할 때점을 맞추지 않으면 답답함이 쌓입니다."
            )
        elif pair == ("寅", "巳"):
            caution_bits.append(
                "寅巳 형·해: 속도·고집 충돌 — 결론을 서두르지 마세요."
            )
        else:
            caution_bits.append(
                f"일지 <b>{ctx.u_day_branch}↔{ctx.p_day_branch}</b>: "
                "오해·타이밍·피로 누적을 조심하세요."
            )
    if ctx.u_strength != ctx.p_strength:
        caution_bits.append(
            "강약 차이: 한쪽이 지칠 때 다른 쪽이 속도를 낮추는 연습이 필요합니다."
        )
    if ctx.u_yong and ctx.p_yong and ctx.u_yong != ctx.p_yong:
        caution_bits.append(
            f"용신 <b>{ctx.u_yong}</b>·<b>{ctx.p_yong}</b>이 달라 회복법을 강요하지 마세요."
        )
    caution = "<br>".join(caution_bits)

    action = (
        _yongshin_mutual_note(ctx)
        + "<br>"
        + _pillar_harmony_audit(ctx)
        + "<br>"
        + _daewoon_overlap_note(ctx)
        + "<br>"
        + f"일간 십성: <b>{ctx.u_name}</b>→<b>{ctx.p_name}</b> <b>{u2p}</b>, "
        f"<b>{ctx.p_name}</b>→<b>{ctx.u_name}</b> <b>{p2u}</b> — "
        f"이 조합({ctx.u_ilju}×{ctx.p_ilju})만의 실행 포인트입니다."
    )
    return [
        ("핵심 강점", strength, "green"),
        ("주의 포인트", caution, "amber"),
        ("실행 포인트", action, "gold"),
    ]
