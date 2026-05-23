"""STEP3 인생 핵심 운세 ↔ 3D 브리핑 덱 텍스트 동기화(Streamlit·API 공용)."""

from __future__ import annotations

from typing import Any

_ORGAN_MAP_HEALTH: dict[str, str] = {
    "木": "간·담낭·눈·신경",
    "火": "심장·혈액·정신",
    "土": "비장·위·소화기",
    "金": "폐·대장·호흡기",
    "水": "신장·방광·생식기·뼈",
}

_LIFE_CARD_ORDER = ("wealth", "marriage", "career", "health")

_EL_KO: dict[str, str] = {
    "木": "목(木)",
    "火": "화(火)",
    "土": "토(土)",
    "金": "금(金)",
    "水": "수(水)",
}

_DAY_STEM_ROLE: dict[str, str] = {
    "甲": "큰 나무처럼 성장·추진이 앞서고, 방향을 잡는 리더형 기질입니다.",
    "乙": "풀·덩굴처럼 유연하게 맞추며, 관계와 협업에서 빛나는 기질입니다.",
    "丙": "태양 불꽃처럼 밝게 드러나고, 말·행동으로 분위기를 이끄는 기질입니다.",
    "丁": "촛불처럼 섬세한 감각과 집중력이 있으며, 디테일에 강한 기질입니다.",
    "戊": "넓은 땅처럼 받쳐 주고, 신뢰·안정을 쌓는 중재형 기질입니다.",
    "己": "밭 흙처럼 실속과 끈기가 있으며, 꾸준히 결과를 만드는 기질입니다.",
    "庚": "쇠처럼 결단이 빠르고, 원칙·정리에 강한 기질입니다.",
    "辛": "보석처럼 예민한 판단력과 미감이 있으며, 품질을 중시합니다.",
    "壬": "큰 물처럼 흐름을 읽고, 적응·확장에 강한 기질입니다.",
    "癸": "이슬·샘물처럼 내면이 깊고, 직관·공감이 뛰어난 기질입니다.",
}

_KEYWORD_MEANING: dict[str, str] = {
    "열정": "火 기운 — 표현·추진·인연에서 에너지가 앞으로 나옵니다.",
    "표현": "말·글·콘텐츠로 자신을 드러낼 때 운이 붙기 쉽습니다.",
    "성장": "배움·도전·확장의 방향으로 기운이 흐릅니다.",
    "리더십": "주도권·결정·책임을 맡을 때 강점이 드러납니다.",
    "창의": "새로운 방식·아이디어로 문제를 푸는 힘이 있습니다.",
    "안정": "반복·신뢰·실속을 쌓을 때 유리합니다.",
    "결단": "선택과 정리를 빠르게 할 때 유리합니다.",
    "지혜": "상황을 넓게 보고, 타이밍을 지키는 편이 유리합니다.",
    "자립": "비견 기운 — 스스로 기준을 세우고 독립적으로 나아가기 쉽습니다.",
    "책임": "정관 기운 — 역할·약속·조직 안에서 신뢰를 얻기 쉽습니다.",
    "기회": "재성 기운 — 실리·수익·기회 포착에 민감합니다.",
    "학습": "인성 기운 — 배움·멘토·내면 축적이 강합니다.",
}


def health_tip_from_engine(*, strength: str, max_el: str, min_el: str) -> str:
    mx = str(max_el or "").strip()
    mn = str(min_el or "").strip()
    organ_mx = _ORGAN_MAP_HEALTH.get(mx, "전신")
    organ_mn = _ORGAN_MAP_HEALTH.get(mn, "전신")
    s = str(strength or "")
    if "신강" in s:
        return f"{mx} 기운이 두드러져 {organ_mx} 쪽 과부하·열감에 유의하면 좋습니다."
    if "신약" in s:
        return f"{mn} 기운이 상대적으로 약해 {organ_mn} 보완 리듬을 가볍게 유지하는 편이 좋습니다."
    return (
        f"강약이 중화에 가까워 {organ_mx}·{organ_mn} 균형을 번갈아 챙기면 "
        "컨디션이 안정됩니다."
    )


def _clamp_score_10(raw: object) -> int:
    try:
        return max(1, min(10, int(float(str(raw or "5")))))
    except (TypeError, ValueError):
        return 5


def _birth_year_from_dict(birth: dict[str, Any] | None) -> int:
    if not isinstance(birth, dict):
        return 2000
    try:
        y = int(birth.get("year", 0))
        if 1900 <= y <= 2100:
            return y
    except (TypeError, ValueError):
        pass
    return 2000


def build_engine_dict_for_gapja(
    gapja: list[str],
    birth: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """세션 없이 간지·출생연도만으로 STEP3와 동일한 엔진 dict 생성."""
    if not gapja or len(gapja) < 3:
        return None
    try:
        from saju.core.engine import SajuEngine

        eng = SajuEngine(birth_year=_birth_year_from_dict(birth)).build(
            [str(x) for x in gapja]
        )
        return eng if isinstance(eng, dict) and eng.get("day_stem") else None
    except Exception:
        return None


def merge_engine_life_insights_into_briefing(
    briefing: dict[str, Any],
    engine: dict[str, Any],
    *,
    strength: str = "",
    max_el: str = "",
    min_el: str = "",
) -> dict[str, Any]:
    """STEP3 「인생 핵심 운세」 해석을 3D 덱 fortune_cards·life_insights에 반영."""
    if not isinstance(briefing, dict) or not isinstance(engine, dict):
        return briefing

    st = str(strength or engine.get("strength") or "")
    mx = str(max_el or engine.get("max_el") or "")
    mn = str(min_el or engine.get("min_el") or "")

    health_tip = health_tip_from_engine(strength=st, max_el=mx, min_el=mn)
    life: dict[str, Any] = {
        "wealth": {
            "id": "wealth",
            "title": "재물운",
            "emoji": "💰",
            "score": _clamp_score_10(engine.get("wealth_strength")),
            "summary": str(engine.get("wealth_comment") or "").strip(),
            "color": "#D4AF37",
        },
        "marriage": {
            "id": "love",
            "title": "혼인운",
            "emoji": "❤️",
            "score": _clamp_score_10(engine.get("marriage_strength")),
            "summary": str(engine.get("marriage_comment") or "").strip(),
            "color": "#F472B6",
        },
        "career": {
            "id": "career",
            "title": "커리어운",
            "emoji": "💼",
            "score": _clamp_score_10(engine.get("career_strength")),
            "summary": str(engine.get("career_comment") or "").strip(),
            "color": "#60A5FA",
        },
        "health": {
            "id": "health",
            "title": "원국 체질 힌트",
            "emoji": "🩺",
            "score": None,
            "summary": health_tip,
            "color": "#F472B6",
        },
    }
    briefing["life_insights"] = life

    cards: list[dict[str, Any]] = []
    for key in ("wealth", "marriage", "career"):
        item = life.get(key)
        if not isinstance(item, dict):
            continue
        summ = str(item.get("summary") or "").strip()
        if not summ:
            continue
        sc = item.get("score")
        cards.append(
            {
                "id": str(item.get("id") or key),
                "title": str(item.get("title") or key),
                "emoji": str(item.get("emoji") or "✨"),
                "score": max(42, min(96, int(sc) * 10)) if sc is not None else 72,
                "summary": summ,
                "color": str(item.get("color") or "#d4af37"),
                "particle": (
                    "coin"
                    if key == "wealth"
                    else "heart"
                    if key == "marriage"
                    else "star"
                ),
            }
        )
    health_item = life.get("health")
    if isinstance(health_item, dict) and str(health_item.get("summary") or "").strip():
        cards.append(
            {
                "id": "health",
                "title": "원국 체질 힌트",
                "emoji": "🩺",
                "score": 0,
                "summary": str(health_item.get("summary") or ""),
                "color": "#F472B6",
                "particle": "star",
            }
        )
    if cards:
        briefing["fortune_cards"] = cards

    elements = engine.get("elements") if isinstance(engine.get("elements"), dict) else {}
    if elements:
        pairs = [
            (el, int(elements.get(el, 0) or 0))
            for el in ("木", "火", "土", "金", "水")
            if el in elements
        ]
        pairs.sort(key=lambda x: -x[1])
        if pairs:
            ef = briefing.get("energy_flow")
            if not isinstance(ef, dict):
                ef = {}
            ef["strong"] = [p[0] for p in pairs[:2]]
            ef["weak"] = [p[0] for p in pairs[-2:]]
            briefing["energy_flow"] = ef

    ov = briefing.get("overview")
    if isinstance(ov, dict) and st:
        ov["strength_hint"] = st
        if mx:
            ov["max_element"] = mx
        if mn:
            ov["min_element"] = mn

    recs = list(briefing.get("recommendations") or [])
    career_block = life.get("career")
    cc = (
        str(career_block.get("summary") or "").strip()
        if isinstance(career_block, dict)
        else ""
    )
    if cc and recs:
        recs = list(recs)
        if recs and isinstance(recs[0], dict):
            recs[0] = {**recs[0], "desc": cc[:280]}
    wc = str(engine.get("wealth_comment") or "").strip()
    mc = str(engine.get("marriage_comment") or "").strip()
    if wc or mc or cc:
        synced_recs: list[dict[str, str]] = []
        if mc:
            synced_recs.append(
                {
                    "title": "인연·표현",
                    "desc": mc[:280],
                }
            )
        if wc:
            synced_recs.append(
                {
                    "title": "재물·루틴",
                    "desc": wc[:280],
                }
            )
        if cc:
            synced_recs.append(
                {
                    "title": "커리어·역할",
                    "desc": cc[:280],
                }
            )
        if st:
            synced_recs.append(
                {
                    "title": "체질·에너지",
                    "desc": (
                        f"신강약 {st} — {health_tip[:200]}"
                        if health_tip
                        else f"신강약 {st} 기준으로 무리한 확장은 피하세요."
                    ),
                }
            )
        briefing["recommendations"] = synced_recs[:4] or recs
    elif recs:
        briefing["recommendations"] = recs

    return briefing


def _balance_comment(*, counts: dict[str, Any], score: object) -> str:
    try:
        sc = round(float(score), 1)
    except (TypeError, ValueError):
        sc = 0.0
    vals = [int(counts.get(el, 0) or 0) for el in ("木", "火", "土", "金", "水")]
    spread = (max(vals) - min(vals)) if vals else 0
    if spread <= 18:
        return (
            f"균형 지수 {sc} — 오행 분포가 비교적 고릅니다. "
            "한쪽으로 치우치지 않고, 상황에 맞게 기운을 바꿔 쓰기 좋은 편입니다."
        )
    if spread >= 32:
        mx = max(counts.items(), key=lambda x: int(x[1] or 0))[0] if counts else "土"
        mn = min(counts.items(), key=lambda x: int(x[1] or 0))[0] if counts else "水"
        return (
            f"균형 지수 {sc} — {_EL_KO.get(mx, mx)} 기운이 두드러지고 "
            f"{_EL_KO.get(mn, mn)}은 상대적으로 약합니다. "
            "강점을 살리되, 약한 기운은 생활 습관으로 보완하는 전략이 유리합니다."
        )
    return (
        f"균형 지수 {sc} — 강·약 기운이 함께 있습니다. "
        "잘 쓰는 기운에 집중하고, 부족한 기운은 무리하게 키우지 않는 편이 좋습니다."
    )


def build_core_slide_interpretation(
    *,
    gapja: list[str],
    meta: dict[str, Any],
    engine: dict[str, Any] | None = None,
    display_name: str = "",
    balance_score: object = 0,
) -> dict[str, Any]:
    """3D 덱 「핵심」 슬라이드용 사주 해석 본문."""
    from saju.core.engine import STEM_ELEMENT

    day_stem = str(meta.get("day_stem") or "")
    if not day_stem and len(gapja) > 2 and len(str(gapja[2])) >= 1:
        day_stem = str(gapja[2])[0]
    day_el = str(meta.get("day_master_element") or STEM_ELEMENT.get(day_stem, "土"))
    ilju = str(gapja[2]) if len(gapja) > 2 else ""
    counts = meta.get("element_counts") if isinstance(meta.get("element_counts"), dict) else {}
    keywords = meta.get("fortune_keywords") if isinstance(meta.get("fortune_keywords"), list) else []
    main_kw = [str(k) for k in keywords[:4] if str(k).strip()]

    strength = str((engine or {}).get("strength") or "중화")
    yongshin = str((engine or {}).get("yongshin") or "판단 필요")
    max_el = str((engine or {}).get("max_el") or "")
    min_el = str((engine or {}).get("min_el") or "")
    if not max_el and counts:
        max_el = max(counts.items(), key=lambda x: int(x[1] or 0))[0]
    if not min_el and counts:
        min_el = min(counts.items(), key=lambda x: int(x[1] or 0))[0]

    name = str(display_name or "").strip() or "고객"
    stem_role = _DAY_STEM_ROLE.get(day_stem, f"{_EL_KO.get(day_el, day_el)} 일간의 기본 성향이 중심에 있습니다.")

    summary = (
        f"이 장은 {name}님 사주에서 **‘나’를 가리키는 기준인 일간(日干)** 을 설명합니다. "
        f"년·월·시는 환경과 시기, **일간 {day_stem}({day_el})** 은 성격·선택·컨디션의 중심축입니다. "
        f"{stem_role}"
    )

    keyword_notes: list[dict[str, str]] = []
    for kw in main_kw:
        meaning = _KEYWORD_MEANING.get(
            kw,
            f"팔자 전체 흐름에서 자주 드러나는 {day_el}·십성 기반 키워드입니다.",
        )
        keyword_notes.append({"keyword": kw, "meaning": meaning})

    bullets: list[str] = [
        f"일주(日柱): {ilju or '—'} — 하루의 기본 리듬과 컨디션의 기준입니다.",
        f"신강·신약: {strength} — 기운을 쓰는 속도와 부담 감수량의 체감을 가늠합니다.",
    ]
    if yongshin and yongshin != "판단 필요":
        bullets.append(
            f"용신(用神): {yongshin} — 지금 구조에서 보완·활용하면 좋은 핵심 오행입니다."
        )
    if max_el:
        pct = int(counts.get(max_el, 0) or 0) if counts else 0
        bullets.append(
            f"가장 강한 오행: {_EL_KO.get(max_el, max_el)}"
            + (f" ({pct}%)" if pct else "")
            + " — 재능·에너지가 모이는 방향입니다."
        )
    if min_el and min_el != max_el:
        bullets.append(
            f"보완 포인트: {_EL_KO.get(min_el, min_el)} — 무리하지 않고 챙기면 컨디션이 안정됩니다."
        )

    return {
        "headline": "핵심 — 당신 사주의 중심축(일간)",
        "slide_purpose": (
            "사주 네 기둥(년·월·일·시) 중 **일간**만 따로 본 화면입니다. "
            "뒤에 나오는 재물·혼인·커리어 카드는 이 기준 위에 쌓인 영역별 해석입니다."
        ),
        "summary": summary,
        "day_pillar": ilju,
        "day_stem_role": stem_role,
        "keyword_notes": keyword_notes,
        "balance_label": "오행 균형 지수",
        "balance_comment": _balance_comment(counts=counts, score=balance_score),
        "insight_bullets": bullets[:5],
    }


def attach_core_interpretation_to_briefing(
    briefing: dict[str, Any],
    gapja: list[str],
    birth: dict[str, Any] | None = None,
    *,
    engine: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """overview.core_interpretation — 「핵심」 슬라이드 해석 본문."""
    if not isinstance(briefing, dict) or not gapja or len(gapja) < 3:
        return briefing
    meta = briefing.get("gapja_meta")
    if not isinstance(meta, dict) or not meta:
        try:
            from saju_storage import build_gapja_briefing_meta

            meta = build_gapja_briefing_meta([str(x) for x in gapja], birth)
            briefing["gapja_meta"] = meta
        except Exception:
            meta = {}
    eng = engine if isinstance(engine, dict) and engine.get("day_stem") else build_engine_dict_for_gapja(gapja, birth)
    ov = briefing.get("overview")
    if not isinstance(ov, dict):
        ov = {}
        briefing["overview"] = ov
    ov["core_interpretation"] = build_core_slide_interpretation(
        gapja=[str(x) for x in gapja],
        meta=meta if isinstance(meta, dict) else {},
        engine=eng,
        display_name=str(briefing.get("display_name") or ""),
        balance_score=ov.get("balance_score"),
    )
    return briefing


def enrich_briefing_with_gapja_engine(
    briefing: dict[str, Any],
    gapja: list[str],
    birth: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """브리핑 JSON에 엔진 기반 항목별 해석을 병합(STEP3·3D 덱 동일 문장)."""
    if not isinstance(briefing, dict):
        return briefing
    eng = build_engine_dict_for_gapja(gapja, birth)
    if eng:
        briefing = merge_engine_life_insights_into_briefing(
            briefing,
            eng,
            strength=str(eng.get("strength") or ""),
            max_el=str(eng.get("max_el") or ""),
            min_el=str(eng.get("min_el") or ""),
        )
    return attach_core_interpretation_to_briefing(briefing, gapja, birth, engine=eng)


def life_insights_to_fortune_cards(
    life_insights: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """life_insights → fortune_cards 슬라이드 배열(프론트·API 공용 형식)."""
    if not isinstance(life_insights, dict):
        return []
    out: list[dict[str, Any]] = []
    for key in _LIFE_CARD_ORDER:
        item = life_insights.get(key)
        if not isinstance(item, dict):
            continue
        summ = str(item.get("summary") or "").strip()
        if not summ:
            continue
        sc = item.get("score")
        particle = "star"
        if key == "wealth":
            particle = "coin"
        elif key == "marriage":
            particle = "heart"
        out.append(
            {
                "id": str(item.get("id") or key),
                "title": str(item.get("title") or key),
                "emoji": str(item.get("emoji") or "✨"),
                "score": (
                    max(42, min(96, int(sc) * 10))
                    if sc is not None and key != "health"
                    else 0
                ),
                "summary": summ,
                "color": str(item.get("color") or "#d4af37"),
                "particle": particle,
            }
        )
    return out
