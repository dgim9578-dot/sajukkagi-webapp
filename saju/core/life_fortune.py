"""STEP3 인생 핵심 운세 — 일주·십성·월지·대운 기반 맞춤 해설."""

from __future__ import annotations

import re
from typing import Any

_STEM_ELEMENT: dict[str, str] = {
    "甲": "木",
    "乙": "木",
    "丙": "火",
    "丁": "火",
    "戊": "土",
    "己": "土",
    "庚": "金",
    "辛": "金",
    "壬": "水",
    "癸": "水",
}

_ELEMENT_KO_TO_HANJA: dict[str, str] = {
    "목": "木",
    "화": "火",
    "토": "土",
    "금": "金",
    "수": "水",
}


def _normalize_element(el: str) -> str:
    s = str(el or "").strip()
    if not s:
        return ""
    return _ELEMENT_KO_TO_HANJA.get(s, s)

_EL_KO: dict[str, str] = {
    "木": "목",
    "火": "화",
    "土": "토",
    "金": "금",
    "水": "수",
}

_NOISE_PHRASES = (
    "원국 전체와 대운·세운이 겹칠 때",
    "같은 일주라도 출생 시간·성별·대운에",
    "60갑자 중",
    "개인의 선택·습관·시기와 함께",
    "합·충·형이 많으면",
    "약한 오행을 생활 습관으로",
    "십성(재·관·식·비겁·인) 분포에 따라",
    "용신 방향의 환경·사람·색·음식을",
)

# 재성 가중치 구간별 — 숫자가 다르면 문장이 달라짐
_JAE_TIER: list[tuple[float, str]] = [
    (
        0.0,
        "재성이 거의 드러나지 않아({jae:.1f}), 월급·저축·지출 룰을 직접 설계하는 타입입니다. "
        "한 번에 크게 벌기보다 **{ys_tip}** 쪽으로 천천히 축적하는 전략이 맞습니다.",
    ),
    (
        0.55,
        "재성 {jae:.1f} — 재물 신호는 약하지만, **{month_wealth}** 테마와 맞물리면 "
        "특정 시기·특정 분야에서 수입이 튀어 오릅니다.",
    ),
    (
        1.0,
        "재성 {jae:.1f} — 한두 축(본업·부업)에 집중하면 효율이 좋아지는 편입니다. "
        "**{day_wealth}**",
    ),
    (
        1.6,
        "재성 {jae:.1f} — 수입·자산 축이 분명합니다. **{day_wealth}** "
        "다만 {strength_tip}",
    ),
    (
        2.4,
        "재성 {jae:.1f} — 재물 기회가 여러 번 올 수 있는 구조입니다. "
        "**{day_wealth}** {strength_tip}",
    ),
    (
        3.2,
        "재성 {jae:.1f} — 원국에 재성이 강해, 사업·투자·거래·다중 수입원을 동시에 "
        "다루기 쉬운 타입입니다. **{day_wealth}**",
    ),
]

_SPOUSE_TIER: list[tuple[float, str]] = [
    (
        0.0,
        "{spouse_label} {star:.1f} — 인연·가정 테마가 약해, 형식보다 **감정·자유·대화**를 "
        "중시하는 관계가 잘 맞습니다. 서두르지 말고 신뢰부터 쌓으세요.",
    ),
    (
        0.55,
        "{spouse_label} {star:.1f} — 인연이 ‘없는’ 것은 아니나, **{ilju_rel}**",
    ),
    (
        1.2,
        "{spouse_label} {star:.1f} — 적당히 있어, **{ilju_rel}** "
        "약속·역할을 천천히 맞추면 안정감이 커집니다.",
    ),
    (
        2.0,
        "{spouse_label} {star:.1f} — 배우자·인연 축이 분명합니다. **{ilju_rel}** "
        "경계·돈·가족 룰을 문서로 정하면 오래 갑니다.",
    ),
    (
        2.8,
        "{spouse_label} {star:.1f} — 인연·가정·약속 테마가 강합니다. **{ilju_rel}** "
        "다만 {clash_tip}",
    ),
]

_CAREER_DOM: dict[str, str] = {
    "guan": "관성 {v:.1f} — 조직·규범·책임·승진·공무·대기업 경로에서 성과를 쌓기 유리합니다.",
    "sik": "식상 {v:.1f} — 창의·기술·표현·프리랜서·콘텐츠·자영업형 경로에 강점이 있습니다.",
    "in_cnt": "인성 {v:.1f} — 전문·연구·자격·교육·학술·멘토링 쪽으로 깊이를 더하면 유리합니다.",
    "bigyeop": "비겁 {v:.1f} — 동업·팀·자기 브랜드·독립·경쟁 구도에서 두각을 내기 쉽습니다.",
    "jae": "재성 {v:.1f} — 영업·거래·유통·재테크·사업 수익 등 ‘돈의 흐름’과 맞닿은 직무가 맞습니다.",
}


def _clip_ilju(text: str, *, max_len: int = 100) -> str:
    s = str(text or "").strip()
    if not s:
        return ""
    for noise in _NOISE_PHRASES:
        s = s.replace(noise, "")
    s = re.sub(r"\s+", " ", s).strip()
    parts = re.split(r"(?<=[.!?。])\s+", s)
    out = ""
    for p in parts:
        p = p.strip()
        if len(p) < 12:
            continue
        if out:
            out += " "
        out += p
        if len(out) >= max_len:
            break
    out = out.strip() or s[:max_len].strip()
    if len(out) > max_len:
        out = out[: max_len - 1].rstrip() + "…"
    return out


def _tier_pick(tiers: list[tuple[float, str]], value: float) -> str:
    picked = tiers[0][1]
    for threshold, template in tiers:
        if value >= threshold:
            picked = template
    return picked


def _is_female(gender: str) -> bool:
    g = str(gender or "")
    return any(tok in g for tok in ("여", "女", "F", "f"))


def _marriage_window(timing: dict[str, Any], now_year: int) -> str:
    age = int(timing.get("age") or 0)
    if age <= 0:
        return ""
    birth_year = int(now_year) - age
    d_start = int(timing.get("daewoon_first_start_age") or 0)
    di = int(timing.get("daewoon_index") or 0)
    return f"{birth_year + d_start + di * 10}~{birth_year + d_start + di * 10 + 9}년"


def _clamp_score(n: float) -> int:
    return max(2, min(10, int(round(n))))


def _load_branch_maps() -> tuple[dict, dict, dict]:
    try:
        from saju_app.ui.ilju_data import BRANCH_C, BRANCH_R, BRANCH_P
    except Exception:
        return {}, {}, {}
    return BRANCH_P, BRANCH_R, BRANCH_C


def _load_day_el_maps() -> tuple[dict, dict]:
    try:
        from saju_app.ui.ilju_data import STEM_C, STEM_R
    except Exception:
        return {}, {}
    # 재물용 — 일간별 수입 스타일 (기존 engine 매핑과 동일)
    wealth = {
        "木": "성장·교육·프로젝트형 수입",
        "火": "표현·마케팅·관계 기반 수입",
        "土": "실속·저축·부동산·장기 누적형",
        "金": "전문·계약·브랜드·정리형 수입",
        "水": "정보·유통·이동·네트워크형 수입",
    }
    return wealth, STEM_C


def build_life_foci(
    u_gapja: list[str],
    *,
    strength: str,
    combine: int,
    clash: int,
    timing: dict[str, Any],
    now_year: int,
    gender: str = "",
    day_stem: str = "",
    day_el: str = "",
    yongshin: str = "",
    max_el: str = "",
    min_el: str = "",
    elements: dict[str, Any] | None = None,
    ten_counts: dict[str, float] | None = None,
) -> dict[str, str]:
    """재물·혼인·커리어 점수/코멘트 — 일주 DB·십성·월지·대운 반영."""
    tc = ten_counts or {}
    jae = float(tc.get("jae", 0.0))
    guan = float(tc.get("guan", 0.0))
    sik = float(tc.get("sik", 0.0))
    bigyeop = float(tc.get("bigyeop", 0.0))
    in_cnt = float(tc.get("in_cnt", 0.0))

    st = str(strength or "중화")
    de = str(day_el or _STEM_ELEMENT.get(str(day_stem or ""), "木"))
    de_ko = _EL_KO.get(de, de)
    ilju = str(u_gapja[2]).strip() if len(u_gapja) > 2 else ""
    ds = ilju[0] if ilju else str(day_stem or "")
    db = ilju[1] if len(ilju) >= 2 else ""
    mb = ""
    if len(u_gapja) > 1 and len(str(u_gapja[1])) >= 2:
        mb = str(u_gapja[1])[1]

    ys = _normalize_element(str(yongshin or ""))
    mx = str(max_el or de)
    mn = str(min_el or de)
    is_f = _is_female(gender)
    spouse_star = guan if is_f else jae
    spouse_label = "관성(배우자·책임)" if is_f else "재성(배우자·인연)"

    try:
        cmb = int(combine)
    except (TypeError, ValueError):
        cmb = 0
    try:
        clh = int(clash)
    except (TypeError, ValueError):
        clh = 0

    el_pct = elements if isinstance(elements, dict) else {}
    try:
        jae_el_pct = float(el_pct.get("金", 0) or 0) + float(el_pct.get("土", 0) or 0) * 0.35
    except (TypeError, ValueError):
        jae_el_pct = 0.0

    branch_p, branch_r, branch_c = _load_branch_maps()
    day_wealth_map, stem_c = _load_day_el_maps()
    day_wealth = day_wealth_map.get(de, "본인 강점 축에 맞는 수입 구조")

    prof: dict[str, str] = {"personality": "", "career": "", "relationship": ""}
    if ilju:
        try:
            from saju_app.ui.ilju_profiles import get_ilju_profile

            prof = get_ilju_profile(ilju)
        except Exception:
            pass

    ilju_career = _clip_ilju(prof.get("career", ""), max_len=95)
    ilju_rel = _clip_ilju(prof.get("relationship", ""), max_len=95)
    month_wealth = _clip_ilju(branch_p.get(mb, ""), max_len=60) or f"월지 {mb} 축"
    month_career = _clip_ilju(branch_c.get(mb, ""), max_len=70)
    month_rel = _clip_ilju(branch_r.get(mb, ""), max_len=70)

    if st == "신강" and bigyeop >= 1.5:
        strength_tip = "신강·비겁이 함께 있어 경쟁·동업·충동 지출만 조절하면 누적이 잘 붙습니다."
    elif st == "신약":
        strength_tip = (
            f"신약이라 {mn}({_EL_KO.get(mn, mn)})·용신 {ys or '—'} 보완이 재물 안정의 핵심입니다."
        )
    elif st == "신강":
        strength_tip = "신강이라 한 번 방향을 잡으면 수입 규모를 키우기 쉬우나, 과욕·확장 속도만 조절하세요."
    else:
        strength_tip = "중화라 환경·파트너·시기에 따라 재물 체감 차이가 큽니다."

    ys_tip = f"용신 {ys}" if ys and ys != "판단 필요" else f"약한 {mn}({_EL_KO.get(mn, mn)})"

    # ── 점수 (분산 확대) ──
    w_raw = 2.8 + jae * 2.15 + min(2.2, jae_el_pct / 22.0)
    if st == "신강" and bigyeop >= 1.8:
        w_raw -= 1.0
    if st == "신약" and jae >= 2.0:
        w_raw += 0.85
    if st == "신약" and jae < 0.55:
        w_raw -= 0.55
    if cmb >= 2:
        w_raw += 0.75
    if clh >= 3:
        w_raw -= 0.65
    if ys and ys == mx:
        w_raw += 0.45

    m_raw = 2.6 + min(4.2, spouse_star * 1.55)
    if clh >= 3:
        m_raw -= 1.15
    if cmb >= 2:
        m_raw += 0.85
    if spouse_star < 0.55:
        m_raw -= 0.75
    elif spouse_star >= 2.6:
        m_raw += 0.95
    if ilju_rel:
        m_raw += 0.25

    dom_key = max(
        ("guan", guan),
        ("sik", sik),
        ("in_cnt", in_cnt),
        ("bigyeop", bigyeop),
        ("jae", jae),
        key=lambda x: x[1],
    )[0]
    dom_val = {"guan": guan, "sik": sik, "in_cnt": in_cnt, "bigyeop": bigyeop, "jae": jae}[dom_key]

    c_raw = 2.7 + dom_val * 1.35 + sik * 0.45 + guan * 0.35
    if sik >= 1.8:
        c_raw += 0.75
    if guan >= 1.8:
        c_raw += 0.55
    if in_cnt >= 2.0 and sik < 1.0:
        c_raw += 0.35
    if bigyeop >= 2.5 and guan < 1.0:
        c_raw -= 0.45
    if ilju_career:
        c_raw += 0.2

    ws = _clamp_score(w_raw)
    ms = _clamp_score(m_raw)
    cs = _clamp_score(c_raw)

    # ── 재물 코멘트 ──
    wc_parts: list[str] = []
    if ilju:
        wc_parts.append(f"【{ilju}】{de_ko}({de}) 일간 · 재성 {jae:.1f} · {st}")
    jae_body = _tier_pick(_JAE_TIER, jae).format(
        jae=jae,
        ys_tip=ys_tip,
        month_wealth=month_wealth,
        day_wealth=day_wealth,
        strength_tip=strength_tip,
    )
    wc_parts.append(jae_body)
    if ilju_career:
        wc_parts.append(f"일주 재물·직업 테마: {ilju_career}")
    if month_wealth and mb:
        wc_parts.append(f"월지 {mb}: {month_wealth}")
    wc_parts.append(strength_tip)
    age = int(timing.get("age") or 0)
    phase = str(timing.get("phase") or "")
    if "확장" in phase or "성장" in phase:
        wc_parts.append(f"현재 {phase}({age}세) 대운 — 재물 축 확장·수입원 다변화에 유리합니다.")
    elif "조정" in phase or "정리" in phase:
        wc_parts.append(f"현재 {phase}({age}세) 대운 — 지출·부채·저축 구조를 정리하면 체감이 좋아집니다.")

    # ── 혼인 코멘트 ──
    clash_tip = (
        "원국 충(沖)이 있어 다툼·이별 주제도 함께 보고 말·약속 관리가 중요합니다."
        if clh >= 2
        else "갈등 시 쿨다운·역할 분담 규칙을 미리 정하면 관계가 안정됩니다."
    )
    mc_parts: list[str] = []
    if ilju:
        mc_parts.append(
            f"【{ilju}】{'여명' if is_f else '남명'} · {spouse_label} {spouse_star:.1f} · {st}"
        )
    mc_parts.append(
        _tier_pick(_SPOUSE_TIER, spouse_star).format(
            spouse_label=spouse_label,
            star=spouse_star,
            ilju_rel=ilju_rel or "감정·속도·생활 리듬을 맞추는 관계가 잘 맞습니다.",
            clash_tip=clash_tip,
        )
    )
    if month_rel and mb:
        mc_parts.append(f"월지 {mb} 인연: {month_rel}")
    win = _marriage_window(timing, int(now_year))
    if win:
        mc_parts.append(f"현재 대운({win}) — 관계·약속을 정리·확장하기 좋은 구간이 올 수 있습니다.")
    elif cmb >= 1:
        mc_parts.append("원국 合(합) 기운 — 소개·모임·재회 인연이 자연스럽게 붙는 시기에 신호가 강합니다.")

    # ── 커리어 코멘트 ──
    cc_parts: list[str] = []
    if ilju:
        cc_parts.append(f"【{ilju}】{de_ko} 일간 · {st}")
    dom_line = _CAREER_DOM.get(dom_key, "").format(v=dom_val)
    if dom_line:
        cc_parts.append(dom_line)
    if ilju_career:
        cc_parts.append(f"일주 커리어: {ilju_career}")
    elif ds and stem_c.get(ds):
        cc_parts.append(_clip_ilju(stem_c[ds], max_len=90))
    if month_career and mb:
        cc_parts.append(f"월지 {mb}: {month_career}")
    if "성장" in phase or "확장" in phase:
        cc_parts.append(f"{phase}({age}세) — 승진·이직·역할 확대에 비교적 유리합니다.")
    elif "시작" in phase:
        cc_parts.append(f"{phase}({age}세) — 새 출발·전환·스펙 쌓기에 좋은 흐름입니다.")
    elif "조정" in phase or "정리" in phase:
        cc_parts.append(f"{phase}({age}세) — 무리한 이직보다 내실·자격·포트폴리오 정리가 유리합니다.")
    if ys and ys != "판단 필요":
        cc_parts.append(f"용신 {ys} 기운이 드는 환경·업종·협업 방식을 고르면 커리어 체감이 올라갑니다.")

    return {
        "wealth_strength": str(ws),
        "wealth_comment": " ".join(x.strip() for x in wc_parts if str(x).strip()),
        "marriage_strength": str(ms),
        "marriage_comment": " ".join(x.strip() for x in mc_parts if str(x).strip()),
        "career_strength": str(cs),
        "career_comment": " ".join(x.strip() for x in cc_parts if str(x).strip()),
    }
