"""3D 브리핑 · 슬라이드 덱 API (``saju_storage`` 확장)."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

log = logging.getLogger(__name__)

_FORTUNE_KEYWORDS_BY_ELEMENT: dict[str, list[str]] = {
    "木": ["성장", "창의", "도전", "유연"],
    "火": ["열정", "표현", "인연", "활력"],
    "土": ["안정", "신뢰", "중재", "실속"],
    "金": ["결단", "원칙", "정리", "성과"],
    "水": ["지혜", "직관", "적응", "내면"],
}


def _storage():
    import saju_storage as s

    return s


def _generate_visual_themes(day_stem: str) -> dict[str, str]:
    s = _storage()
    themes: dict[str, dict[str, str]] = {
        "木": {"primary": "#22C55E", "accent": "#86EFAC", "bg": "#052E16"},
        "火": {"primary": "#EF4444", "accent": "#FCA5A5", "bg": "#450A0A"},
        "土": {"primary": "#D4AF37", "accent": "#FDE68A", "bg": "#1C1917"},
        "金": {"primary": "#E5E7EB", "accent": "#F8FAFC", "bg": "#0F172A"},
        "水": {"primary": "#3B82F6", "accent": "#93C5FD", "bg": "#0C1929"},
    }
    el = s.STEM_ELEMENT.get(str(day_stem or ""), "土")
    return dict(themes.get(el, themes["土"]))


def build_gapja_briefing_meta(
    gapja: list[str],
    birth: dict[str, Any] | None = None,
) -> dict[str, Any]:
    s = _storage()
    _ = birth
    base = s.build_gapja_design_meta(gapja)
    day_stem = str(base.get("day_stem") or "")
    day_el = s.STEM_ELEMENT.get(day_stem, "土")
    counts = base.get("element_counts") if isinstance(base.get("element_counts"), dict) else {}
    if not counts:
        counts = {el: 0 for el in ("木", "火", "土", "金", "水")}

    strong: list[str] = []
    weak: list[str] = []
    if counts:
        max_el = max(counts.items(), key=lambda x: int(x[1] or 0))[0]
        min_el = min(counts.items(), key=lambda x: int(x[1] or 0))[0]
        strong = [str(max_el)]
        weak = [str(min_el)]

    generate_pairs: list[dict[str, str]] = []
    control_pairs: list[dict[str, str]] = []
    for el in ("木", "火", "土", "金", "水"):
        gen_to = s._element_generates(el)
        if gen_to:
            generate_pairs.append({"from": el, "to": gen_to})
        ctrl_to = s._element_controls(el)
        if ctrl_to:
            control_pairs.append({"from": el, "to": ctrl_to})

    keywords = list(_FORTUNE_KEYWORDS_BY_ELEMENT.get(day_el, ["균형", "성장", "인연"]))
    ten_counts = base.get("ten_god_counts") if isinstance(base.get("ten_god_counts"), dict) else {}
    if ten_counts:
        top_ten = max(ten_counts.items(), key=lambda x: int(x[1] or 0))[0]
        ten_kw = {
            "비견": "자립",
            "겁재": "경쟁",
            "식신": "표현",
            "상관": "창의",
            "편재": "기회",
            "정재": "안정 수익",
            "편관": "도전",
            "정관": "책임",
            "편인": "직관",
            "정인": "학습",
        }
        if top_ten in ten_kw:
            keywords.insert(0, ten_kw[top_ten])

    return {
        **base,
        "day_master_element": day_el,
        "visual_themes": _generate_visual_themes(day_stem),
        "energy_flow": {
            "strong": strong,
            "weak": weak,
            "generate": generate_pairs,
            "control": control_pairs,
        },
        "fortune_keywords": keywords[:6],
        "ten_god_strength": sorted(
            ten_counts.items(),
            key=lambda x: int(x[1] or 0),
            reverse=True,
        )[:3],
    }


def _generate_fortune_cards(
    meta: dict[str, Any],
    consultation_type: str = "general",
) -> list[dict[str, Any]]:
    counts = meta.get("element_counts") if isinstance(meta.get("element_counts"), dict) else {}
    max_el = ""
    if counts:
        max_el = max(counts.items(), key=lambda x: int(x[1] or 0))[0]

    def _score(base: int) -> int:
        bonus = int(counts.get(max_el, 0) or 0) * 3
        return max(42, min(96, base + bonus))

    cards = [
        {
            "id": "love",
            "title": "혼인운",
            "emoji": "❤️",
            "score": _score(72),
            "summary": "감정 표현과 타이밍을 맞추면 인연이 붙기 쉬운 흐름입니다.",
            "color": "#F472B6",
            "particle": "heart",
        },
        {
            "id": "career",
            "title": "커리어운",
            "emoji": "💼",
            "score": _score(68),
            "summary": "역할이 분명해질수록 성과가 드러나는 시기입니다.",
            "color": "#60A5FA",
            "particle": "star",
        },
        {
            "id": "wealth",
            "title": "재물운",
            "emoji": "💰",
            "score": _score(70),
            "summary": "수익 기회는 보이지만 조건·리스크 확인이 관건입니다.",
            "color": "#FBBF24",
            "particle": "coin",
        },
    ]
    pref = str(consultation_type or "general").strip().lower()
    if pref in ("love", "match", "연애"):
        cards = [cards[0], cards[1], cards[2]]
    elif pref in ("career", "직장"):
        cards = [cards[1], cards[0], cards[2]]
    elif pref in ("wealth", "재물"):
        cards = [cards[2], cards[1], cards[0]]
    return cards


def _generate_recommendations(meta: dict[str, Any]) -> list[dict[str, str]]:
    s = _storage()
    yong_hint = str(meta.get("day_stem") or "")
    day_el = str(meta.get("day_master_element") or s.STEM_ELEMENT.get(yong_hint, "土"))
    weak = (meta.get("energy_flow") or {}).get("weak") if isinstance(meta.get("energy_flow"), dict) else []
    weak_txt = ", ".join(str(x) for x in (weak or [])) or "약한 기운"
    return [
        {
            "title": "오늘의 한 줄",
            "desc": f"{day_el} 기운을 살리는 작은 습관 하나를 정해 반복해 보세요.",
        },
        {
            "title": "관계·일",
            "desc": "말보다 약속과 루틴을 지키는 편이 체감 운을 올립니다.",
        },
        {
            "title": "피해야 할 것",
            "desc": f"약한 기운({weak_txt})을 더 소모하는 무리한 확장·갈등은 줄이세요.",
        },
    ]


def generate_saju_briefing(
    display_name: str,
    birth: dict[str, Any],
    gapja: list[str],
    consultation_type: str = "general",
) -> dict[str, Any]:
    s = _storage()
    fp = s.user_profile_fingerprint(display_name=display_name, birth=birth)
    meta = build_gapja_briefing_meta(gapja, birth)
    counts = meta.get("element_counts") if isinstance(meta.get("element_counts"), dict) else {}
    keywords = meta.get("fortune_keywords") if isinstance(meta.get("fortune_keywords"), list) else []
    balance_score = round(sum(int(v or 0) for v in counts.values()) / 5.0, 2)

    if gapja:
        s.upsert_user_profile(display_name=display_name, birth=birth, gapja=list(gapja))
    s.touch_user_profile(fp)

    payload = {
        "fingerprint": fp,
        "display_name": display_name,
        "generated_at": s._now_kst_iso(),
        "consultation_type": consultation_type,
        "overview": {
            "day_master": meta.get("day_stem"),
            "day_master_element": meta.get("day_master_element"),
            "balance_score": balance_score,
            "main_keywords": keywords[:4],
        },
        "pillars_3d": meta.get("pillars"),
        "energy_flow": meta.get("energy_flow"),
        "ten_god": {
            "counts": meta.get("ten_god_counts"),
            "strength": meta.get("ten_god_strength"),
        },
        "fortune_cards": _generate_fortune_cards(meta, consultation_type),
        "visual_themes": meta.get("visual_themes"),
        "recommendations": _generate_recommendations(meta),
        "shareable": {
            "title": f"{display_name}님의 사주 브리핑",
            "thumbnail_keywords": keywords[:3],
        },
        "gapja_meta": meta,
    }
    try:
        from saju_app.ui.briefing_life_sync import enrich_briefing_with_gapja_engine

        payload = enrich_briefing_with_gapja_engine(
            payload,
            [str(x) for x in gapja],
            birth if isinstance(birth, dict) else None,
        )
    except Exception:
        log.exception("generate_saju_briefing: life_insights enrich failed")
        try:
            from saju_app.ui.briefing_life_sync import attach_core_interpretation_to_briefing

            payload = attach_core_interpretation_to_briefing(
                payload,
                [str(x) for x in gapja],
                birth if isinstance(birth, dict) else None,
            )
        except Exception:
            log.exception("generate_saju_briefing: core_interpretation attach failed")
    return payload


def get_user_briefing(
    display_name: str,
    birth: dict[str, Any],
    gapja: list[str],
    *,
    consultation_type: str = "general",
) -> dict[str, Any]:
    try:
        return generate_saju_briefing(
            display_name,
            birth,
            gapja,
            consultation_type=consultation_type,
        )
    except Exception:
        log.exception("get_user_briefing failed")
        s = _storage()
        pillars: list[dict[str, Any]] = []
        try:
            pillars = list(s.build_gapja_design_meta(list(gapja or [])).get("pillars") or [])
        except Exception:
            log.exception("get_user_briefing fallback meta failed")
        return {
            "error": "브리핑 생성 중 오류가 발생했습니다.",
            "display_name": display_name,
            "pillars": pillars,
            "pillars_3d": pillars,
        }


def get_sample_briefing() -> dict[str, Any]:
    sample_gapja = ["甲子", "乙丑", "丙寅", "丁卯"]
    display_name = "김사주"
    birth: dict[str, Any] = {
        "year": 1990,
        "month": 3,
        "day": 15,
        "lunar": False,
        "leap_month": False,
        "time_str": "10:30",
    }
    meta = build_gapja_briefing_meta(sample_gapja, birth)
    counts = meta.get("element_counts") if isinstance(meta.get("element_counts"), dict) else {}
    keywords = meta.get("fortune_keywords") if isinstance(meta.get("fortune_keywords"), list) else []
    if not keywords:
        keywords = ["열정", "성장", "리더십", "표현"]
    balance_score = round(sum(int(v or 0) for v in counts.values()) / 5.0, 2)
    s = _storage()
    sample_payload = {
        "fingerprint": "test_sample_123",
        "display_name": display_name,
        "generated_at": s._now_kst_iso(),
        "consultation_type": "general",
        "sample": True,
        "overview": {
            "day_master": meta.get("day_stem") or "丙",
            "day_master_element": meta.get("day_master_element") or "火",
            "balance_score": balance_score if balance_score > 0 else 78.0,
            "main_keywords": keywords[:4],
        },
        "pillars_3d": meta.get("pillars"),
        "energy_flow": meta.get("energy_flow"),
        "ten_god": {
            "counts": meta.get("ten_god_counts"),
            "strength": meta.get("ten_god_strength"),
        },
        "fortune_cards": _generate_fortune_cards(meta, "general"),
        "visual_themes": meta.get("visual_themes"),
        "recommendations": _generate_recommendations(meta),
        "shareable": {
            "title": f"{display_name}님의 사주 브리핑",
            "thumbnail_keywords": keywords[:3],
        },
        "gapja_meta": meta,
    }
    try:
        from saju_app.ui.briefing_life_sync import enrich_briefing_with_gapja_engine

        sample_payload = enrich_briefing_with_gapja_engine(
            sample_payload,
            sample_gapja,
            birth,
        )
    except Exception:
        log.exception("get_sample_briefing: life_insights enrich failed")
    return sample_payload


def match_briefing_fingerprint(user_fp: str, partner_fp: str) -> str:
    u = str(user_fp or "").strip()
    p = str(partner_fp or "").strip()
    if not u or not p:
        return ""
    pair = "|".join(sorted([u, p]))
    return hashlib.sha256(f"match:{pair}".encode("utf-8")).hexdigest()


def _generate_match_fortune_cards(
    *,
    match_score: int,
    day_branch_rel: str,
) -> list[dict[str, Any]]:
    ms = max(0, min(100, int(match_score)))
    rel = str(day_branch_rel or "보통")
    love = min(96, ms + (6 if "합" in rel else -4 if "충" in rel else 0))
    life = min(94, ms)
    wealth = min(92, ms - 2)
    caution = max(38, 100 - ms + 10)
    return [
        {
            "id": "match_love",
            "title": "감정·인연",
            "emoji": "💕",
            "score": love,
            "summary": f"일지 관계 {rel} — 정서적 결속과 타이밍을 함께 맞추면 유리합니다.",
            "color": "#FB7185",
            "particle": "heart",
        },
        {
            "id": "match_life",
            "title": "생활·역할",
            "emoji": "🏠",
            "score": life,
            "summary": "생활 리듬과 역할 분담을 정하면 궁합 체감이 빠르게 올라갑니다.",
            "color": "#60A5FA",
            "particle": "star",
        },
        {
            "id": "match_wealth",
            "title": "재물·약속",
            "emoji": "💰",
            "score": wealth,
            "summary": "지출·저축 기준을 합의하면 갈등을 줄일 수 있습니다.",
            "color": "#FBBF24",
            "particle": "coin",
        },
        {
            "id": "match_caution",
            "title": "주의 포인트",
            "emoji": "⚠️",
            "score": caution,
            "summary": "충·강약 차이가 크면 규칙과 휴식을 먼저 정리하는 편이 안전합니다.",
            "color": "#F59E0B",
            "particle": "star",
        },
    ]


def generate_match_briefing(
    *,
    user_name: str,
    user_birth: dict[str, Any],
    user_gapja: list[str],
    partner_name: str,
    partner_birth: dict[str, Any],
    partner_gapja: list[str],
    match_score: int = 70,
    day_branch_rel: str = "",
) -> dict[str, Any]:
    s = _storage()
    u_fp = s.user_profile_fingerprint(display_name=user_name, birth=user_birth)
    p_fp = s.user_profile_fingerprint(display_name=partner_name, birth=partner_birth)
    m_fp = match_briefing_fingerprint(u_fp, p_fp)
    if not m_fp:
        raise ValueError("match briefing fingerprint failed")

    base = generate_saju_briefing(
        user_name,
        user_birth,
        list(user_gapja),
        consultation_type="match",
    )
    meta = base.get("gapja_meta") if isinstance(base.get("gapja_meta"), dict) else {}
    themes = meta.get("visual_themes") if isinstance(meta.get("visual_themes"), dict) else {}
    if not themes:
        themes = _generate_visual_themes(str(meta.get("day_stem") or ""))

    cards = _generate_match_fortune_cards(
        match_score=match_score,
        day_branch_rel=day_branch_rel,
    )
    display = f"{str(user_name).strip()} · {str(partner_name).strip()}"
    out = {
        **base,
        "fingerprint": m_fp,
        "display_name": display,
        "consultation_type": "match",
        "overview": {
            **(base.get("overview") if isinstance(base.get("overview"), dict) else {}),
            "balance_score": float(max(0, min(100, int(match_score)))),
            "main_keywords": ["궁합", "인연", day_branch_rel or "조화", "역할"],
        },
        "fortune_cards": cards,
        "visual_themes": themes,
        "shareable": {
            "title": f"{display} 궁합 브리핑",
            "thumbnail_keywords": ["궁합", str(match_score), day_branch_rel or "인연"],
        },
        "match": {
            "score": int(match_score),
            "day_branch_rel": str(day_branch_rel),
            "user_fingerprint": u_fp,
            "partner_fingerprint": p_fp,
            "user_name": str(user_name).strip(),
            "partner_name": str(partner_name).strip(),
            "user_gapja": [str(x) for x in user_gapja[:4]],
            "partner_gapja": [str(x) for x in partner_gapja[:4]],
        },
        "recommendations": [
            {
                "title": "궁합 한 줄",
                "desc": f"종합 {match_score}점 · 일지 {day_branch_rel} — 서로의 빈틈을 메우는 루틴이 핵심입니다.",
            },
            {
                "title": "대화·약속",
                "desc": "감정이 앞서기보다 일정·역할·재정 룰을 먼저 맞추면 안정감이 커집니다.",
            },
            {
                "title": "피할 패턴",
                "desc": "승패 싸움·충동적 결정은 피하고, 휴식 시간을 서로 보장하세요.",
            },
        ],
    }
    try:
        s.kv_set_json(f"briefing:{m_fp}", out)
        s.kv_set_json(f"briefing:match:{m_fp}", out)
    except Exception:
        log.exception("generate_match_briefing cache failed")
    return out


def load_cached_briefing(fingerprint: str) -> dict[str, Any] | None:
    s = _storage()
    fp = str(fingerprint or "").strip()
    if not fp:
        return None
    obj = s.kv_get_json(f"briefing:{fp}")
    if isinstance(obj, dict):
        return obj
    mobj = s.kv_get_json(f"briefing:match:{fp}")
    return mobj if isinstance(mobj, dict) else None


def get_briefing_by_fingerprint(fingerprint: str) -> dict[str, Any] | None:
    s = _storage()
    fp = str(fingerprint or "").strip()
    if not fp:
        return None
    profile = s.get_user_profile(fp)
    birth = profile.get("birth") if isinstance(profile, dict) and isinstance(profile.get("birth"), dict) else {}
    gapja = (
        [str(x) for x in profile.get("gapja")]
        if isinstance(profile, dict) and isinstance(profile.get("gapja"), list)
        else []
    )
    cached = load_cached_briefing(fp)
    if cached and isinstance(cached, dict):
        if gapja and len(gapja) >= 3:
            try:
                from saju_app.ui.briefing_life_sync import (
                    attach_core_interpretation_to_briefing,
                    enrich_briefing_with_gapja_engine,
                )

                if not cached.get("life_insights"):
                    cached = enrich_briefing_with_gapja_engine(cached, gapja, birth)
                ov = cached.get("overview")
                core = (
                    ov.get("core_interpretation")
                    if isinstance(ov, dict) and isinstance(ov.get("core_interpretation"), dict)
                    else {}
                )
                if not str(core.get("summary") or "").strip():
                    cached = attach_core_interpretation_to_briefing(cached, gapja, birth)
                s.kv_set_json(f"briefing:{fp}", cached)
            except Exception:
                log.exception("get_briefing_by_fingerprint: cache enrich failed")
        return cached
    if not profile or len(gapja) < 3:
        return None
    briefing = generate_saju_briefing(
        display_name=str(profile.get("display_name") or ""),
        birth=birth,
        gapja=gapja,
    )
    try:
        s.kv_set_json(f"briefing:{fp}", briefing)
    except Exception:
        pass
    return briefing


def upsert_user_profile_with_briefing(
    *,
    display_name: str,
    birth: dict[str, Any],
    gapja: list[str],
    consultation_type: str = "general",
    cache_briefing: bool = True,
) -> str | None:
    s = _storage()
    fp = s.upsert_user_profile(
        display_name=display_name,
        birth=birth,
        gapja=list(gapja),
    )
    if fp and cache_briefing:
        try:
            briefing = generate_saju_briefing(
                display_name,
                birth,
                list(gapja),
                consultation_type=consultation_type,
            )
            s.kv_set_json(f"briefing:{fp}", briefing)
        except Exception:
            log.exception("upsert_user_profile_with_briefing: briefing cache failed")
    return fp
