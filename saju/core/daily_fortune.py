"""STEP6 오늘의 운세 — 원국·오늘 일진·일지 관계·날짜별 맞춤 점수·해설."""

from __future__ import annotations

import datetime
import hashlib
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

_EL_KO: dict[str, str] = {
    "木": "목",
    "火": "화",
    "土": "토",
    "金": "금",
    "水": "수",
}

_CATEGORIES = ("재물", "연애", "직장", "건강", "공부")

# 오늘 일간→본인 십성 그룹 가중치
_TEN_GROUP_DELTA: dict[str, dict[str, int]] = {
    "재물": {"재성": 14, "식상": 8, "관성": 3, "인성": 4, "비겁": -8},
    "연애": {"재성": 12, "식상": 9, "관성": 6, "인성": 5, "비겁": -6},
    "직장": {"관성": 13, "식상": 8, "인성": 5, "재성": 3, "비겁": -5},
    "건강": {"인성": 11, "관성": 9, "식상": 5, "재성": 2, "비겁": -4},
    "공부": {"인성": 14, "관성": 8, "식상": 4, "재성": -3, "비겁": -4},
}

# 일지 관계별 카테고리 보정
_BRANCH_REL_DELTA: dict[str, dict[str, int]] = {
    "합(六合)": {"재물": 6, "연애": 10, "직장": 5, "건강": 4, "공부": 3},
    "충(沖)": {"재물": -8, "연애": -6, "직장": 4, "건강": -10, "공부": -4},
    "형(刑)": {"재물": -5, "연애": -7, "직장": -3, "건강": -8, "공부": -3},
    "해(害)": {"재물": -4, "연애": -8, "직장": -2, "건강": -5, "공부": -2},
    "없음": {"재물": 0, "연애": 0, "직장": 0, "건강": 0, "공부": 0},
}

# 십성 세부(정재/편관 등) 한 줄 — ten_group보다 촘촘
_TEN_DETAIL_MSG: dict[str, dict[str, str]] = {
    "재물": {
        "정재": "오늘은 계획된 수입·정산·저축에 유리합니다. 큰 투자보다 확실한 한 건에 집중하세요.",
        "편재": "뜻밖의 기회·거래·부수입 신호가 있습니다. 조건 확인 후 '작게' 실행하세요.",
        "식신": "아이디어·콘텐츠·판매 테스트가 돈으로 연결되기 쉽습니다.",
        "상관": "과감한 제안·협상이 통할 수 있으나, 말실수·과소비를 조심하세요.",
        "정관": "고정지출·세금·약속 이행이 재물 흐름을 좌우합니다. 충동 지출은 보류하세요.",
        "편관": "압박·마감·의무 비용이 늘 수 있습니다. 우선순위를 정해 지출하세요.",
        "정인": "정보·문서·계약 검토가 손실을 막습니다. 서류·약관을 꼼꼼히 보세요.",
        "편인": "내부 정리·환불·정산·숨은 비용을 찾기 좋은 날입니다.",
        "비견": "동업·나눔·경쟁 지출이 생기기 쉽습니다. 지갑·대출선을 지키세요.",
        "겁재": "빌려줌·과소비·충동 구매에 특히 취약합니다. '오늘은 안 쓴다'를 먼저 정하세요.",
    },
    "연애": {
        "정재": "호감·약속·관계 진전에 유리합니다. 구체적인 만남·일정을 잡아 보세요.",
        "편재": "설렘·썸·새 인연이 살아납니다. 가벼운 접촉부터 시작하세요.",
        "식신": "말·메시지·유머가 관계를 움직입니다. 칭찬은 구체적으로 하세요.",
        "상관": "자극·밀당·솔직한 표현이 통할 수 있으나, 말실수도 조심하세요.",
        "정관": "신뢰·예의·약속 이행이 득점입니다. 진지한 태도가 잘 맞습니다.",
        "편관": "긴장·시험·거리감이 생길 수 있습니다. 압박 대신 존중을 보여 주세요.",
        "정인": "편안한 대화·공감·회복에 유리합니다. 감정 정리 대화를 권합니다.",
        "편인": "혼자만의 시간·거리 조절이 필요할 수 있습니다. 상대 공간을 존중하세요.",
        "비견": "고집·자존심 다툼이 생기기 쉽습니다. '맞다/틀리다'보다 기분을 먼저 확인하세요.",
        "겁재": "질투·비교·삼각 관계 이슈에 취약합니다. 불필요한 오해를 줄이세요.",
    },
    "직장": {
        "정재": "성과·매출·KPI가 눈에 띄는 날입니다. 숫자로 결과를 남기세요.",
        "편재": "기회·거래·외부 미팅이 잡히기 쉽습니다. 빠르게 팔로업하세요.",
        "식신": "기획·발표·설득·초안 공유에 유리합니다. 60% 완성도로 먼저 보여 주세요.",
        "상관": "아이디어·개선안·불만 제기가 통할 수 있으나, 상사와의 말투는 부드럽게.",
        "정관": "규칙·평가·마감·책임이 강조됩니다. 정확도와 시간 약속이 성과를 좌우합니다.",
        "편관": "압박·변동·감독·검열 이슈가 올 수 있습니다. 서류·근거를 준비하세요.",
        "정인": "지원·정보·멘토·레퍼런스가 도움이 됩니다. 혼자 해결하지 마세요.",
        "편인": "내부 정리·문서·학습·재정비에 좋습니다. 큰 도약보다 기반 다지기.",
        "비견": "동료·팀 이슈·경쟁이 부각됩니다. 이기기보다 합의·역할 분담을 먼저.",
        "겁재": "이해관계·크레딧·주도권 다툼이 생기기 쉽습니다. 기록을 남기세요.",
    },
    "건강": {
        "정재": "바쁜 일정·이동으로 피로가 쌓일 수 있습니다. 중간 휴식 10분을 넣으세요.",
        "편재": "활동량이 늘기 쉽습니다. 수분·스트레칭을 자주 하세요.",
        "식신": "활력은 오르나 과로하면 탈이 납니다. 강도보다 지속을 선택하세요.",
        "상관": "스트레스·말·카페인 과다에 취약합니다. 수면 시간을 지키세요.",
        "정관": "루틴·규칙적 식사·운동 시간이 효과적입니다. 몸의 리듬을 맞추세요.",
        "편관": "긴장·어깨·두통·수면 질 저하에 주의하세요. 쿨다운 시간이 필요합니다.",
        "정인": "회복·보양·수면·수분에 유리합니다. 무리한 승부는 피하세요.",
        "편인": "면역·소화·컨디션 기복이 있을 수 있습니다. 자극적인 음식은 줄이세요.",
        "비겁": "승부욕·과운동·남과 비교는 금물입니다. 내 페이스를 지키세요.",
        "겁재": "감정 기복·불면·소화 불편이 올 수 있습니다. 일찍 쉬는 선택을.",
    },
    "공부": {
        "정재": "공부 외 유혹·SNS·쇼핑이 늘 수 있습니다. 환경부터 정리하세요.",
        "편재": "짧은 집중보다 주의가 분산되기 쉽습니다. 타이머·25분 뽀모도로를 쓰세요.",
        "식신": "요약·발표·글쓰기·설명에 유리합니다. 배운 내용을 말로 정리하세요.",
        "상관": "창의·토론·남의 답과 다른 접근이 통합니다. 토론·발표 준비에 좋습니다.",
        "정관": "계획·시간표·루틴이 잘 먹힙니다. 오늘은 '예정대로' 밀어붙이세요.",
        "편관": "시험·면접·압박 학습에 강하지만, 스트레스 관리가 필요합니다.",
        "정인": "흡수·암기·개념 정리·노트 필기에 최적입니다. 어려운 과목을 오늘.",
        "편인": "독학·연구·깊이 있는 독서에 유리합니다. 혼자 몰입하기 좋습니다.",
        "비겁": "경쟁·비교로 지치기 쉽습니다. 나의 페이스·오답노트에 집중하세요.",
        "겁재": "친구·그룹 스터디에서 산만해질 수 있습니다. 혼자 공부 시간을 확보하세요.",
    },
}


def _clamp(n: float, lo: int = 28, hi: int = 97) -> int:
    return max(lo, min(hi, int(round(n))))


def _date_jitter(when: datetime.date, category: str, u_ilju: str) -> int:
    """같은 십성이라도 날짜·일주마다 점수가 달라지도록 결정적 지터."""
    key = f"{when.isoformat()}|{category}|{u_ilju}".encode("utf-8")
    h = int(hashlib.md5(key).hexdigest()[:4], 16)
    return (h % 9) - 4  # -4 ~ +4


def _ten_group(ten_detail: str) -> str:
    if ten_detail in ("비견", "겁재"):
        return "비겁"
    if ten_detail in ("식신", "상관"):
        return "식상"
    if ten_detail in ("정재", "편재"):
        return "재성"
    if ten_detail in ("정관", "편관"):
        return "관성"
    return "인성"


def _natal_boost(category: str, tc: dict[str, float], *, is_female: bool) -> float:
    jae = float(tc.get("jae", 0))
    guan = float(tc.get("guan", 0))
    sik = float(tc.get("sik", 0))
    bigyeop = float(tc.get("bigyeop", 0))
    in_cnt = float(tc.get("in_cnt", 0))
    spouse = guan if is_female else jae
    if category == "재물":
        return min(20.0, jae * 6.5)
    if category == "연애":
        return min(18.0, spouse * 5.5)
    if category == "직장":
        return min(18.0, guan * 4.5 + sik * 3.0)
    if category == "건강":
        return min(16.0, in_cnt * 4.0 + max(0.0, 3.0 - bigyeop * 0.8))
    if category == "공부":
        return min(20.0, in_cnt * 5.5 + guan * 2.0)
    return 0.0


def _branch_rel_key(rel: str) -> str:
    r = str(rel or "").strip()
    if r.startswith("합"):
        return "합(六合)"
    if r.startswith("충"):
        return "충(沖)"
    if r.startswith("형"):
        return "형(刑)"
    if r.startswith("해"):
        return "해(害)"
    return "없음"


def _clip(text: str, max_len: int = 95) -> str:
    s = str(text or "").strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1].rstrip() + "…"


def build_daily_fortune(
    *,
    u_gapja: list[str],
    today_gapja: list[str],
    when: datetime.date,
    engine: dict[str, Any],
    ten_counts: dict[str, float],
    ten_detail: str,
    ten_group: str,
    u_name: str = "사용자",
    gender: str = "",
    branch_pair_relation_fn,
) -> dict[str, Any]:
    """STEP6용 — 카테고리별 점수·해설·메타."""
    u_ilju = str(u_gapja[2]) if len(u_gapja) > 2 else ""
    t_ilju = str(today_gapja[2]) if len(today_gapja) > 2 else ""
    u_db = u_ilju[1] if len(u_ilju) >= 2 else ""
    t_db = t_ilju[1] if len(t_ilju) >= 2 else ""
    u_stem = u_ilju[0] if u_ilju else "甲"
    t_stem = t_ilju[0] if t_ilju else "甲"
    t_el = _STEM_ELEMENT.get(t_stem, "木")
    day_el = str(engine.get("day_el") or _STEM_ELEMENT.get(u_stem, "木"))
    yongshin = str(engine.get("yongshin") or "판단 필요")
    strength = str(engine.get("strength") or "중화")
    max_el = str(engine.get("max_el") or day_el)
    min_el = str(engine.get("min_el") or day_el)

    is_f = any(x in str(gender) for x in ("여", "女", "F", "f"))
    day_branch_rel = branch_pair_relation_fn(u_db, t_db)
    br_key = _branch_rel_key(day_branch_rel)

    prof: dict[str, str] = {"career": "", "relationship": ""}
    if u_ilju:
        try:
            from saju_app.ui.ilju_profiles import get_ilju_profile

            prof = get_ilju_profile(u_ilju)
        except Exception:
            pass

    yong_bonus = 0
    if yongshin and yongshin != "판단 필요":
        if t_el == yongshin:
            yong_bonus = 8
        elif strength == "신약" and t_el == min_el:
            yong_bonus = -6
        elif strength == "신강" and t_el == max_el:
            yong_bonus = 4

    scores: dict[str, int] = {}
    comments: dict[str, str] = {}

    branch_narr = {
        "합(六合)": f"본인 일지 {u_db}와 오늘 일지 {t_db}가 **합(六合)** — {t_ilju} 일진과 기운이 맞물리기 쉬운 날입니다.",
        "충(沖)": f"일지 {u_db}↔{t_db} **충(沖)** — 일정·감정·지출이 바뀌기 쉬워 무리한 결정은 피하세요.",
        "형(刑)": f"일지 {u_db}↔{t_db} **형(刑)** — 피로·말실수·긴장이 겹치기 쉽습니다.",
        "해(害)": f"일지 {u_db}↔{t_db} **해(害)** — 오해·타이밍 어긋남을 조심하세요.",
        "없음": f"오늘 일진 {t_ilju}({_EL_KO.get(t_el, t_el)}) · 본인 일주 {u_ilju} — 일지 특별 합·충은 없습니다.",
    }.get(br_key, "")

    for cat in _CATEGORIES:
        base = 38.0
        natal = _natal_boost(cat, ten_counts, is_female=is_f)
        ten_d = float(_TEN_GROUP_DELTA.get(cat, {}).get(ten_group, 0))
        br_d = float(_BRANCH_REL_DELTA.get(br_key, {}).get(cat, 0))
        jitter = float(_date_jitter(when, cat, u_ilju))
        raw = base + natal + ten_d + br_d + float(yong_bonus) + jitter
        if strength == "신약" and cat in ("건강", "공부"):
            raw += 2.0
        if strength == "신강" and cat in ("직장", "재물") and ten_group == "비겁":
            raw -= 3.0
        scores[cat] = _clamp(raw)

        ten_msg = _TEN_DETAIL_MSG.get(cat, {}).get(
            ten_detail, "오늘 흐름에 맞춰 유연하게 조절하세요."
        )
        ilju_bit = ""
        if cat in ("재물", "직장") and prof.get("career"):
            ilju_bit = _clip(prof["career"], 88)
        elif cat == "연애" and prof.get("relationship"):
            ilju_bit = _clip(prof["relationship"], 88)

        natal_line = {
            "재물": f"{u_name}님 원국 재성 {ten_counts.get('jae', 0):.1f} · {strength} · 강 {_EL_KO.get(max_el, max_el)}",
            "연애": f"{u_name}님 {'관성' if is_f else '재성'}(인연) { (ten_counts.get('guan', 0) if is_f else ten_counts.get('jae', 0)):.1f} · {u_ilju}",
            "직장": f"{u_name}님 관성 {ten_counts.get('guan', 0):.1f} · 식상 {ten_counts.get('sik', 0):.1f} · {strength}",
            "건강": f"{u_name}님 {strength} · 약한 {_EL_KO.get(min_el, min_el)} 보완 · 인성 {ten_counts.get('in_cnt', 0):.1f}",
            "공부": f"{u_name}님 인성 {ten_counts.get('in_cnt', 0):.1f} · 관성 {ten_counts.get('guan', 0):.1f} · {strength}",
        }.get(cat, "")

        parts = [
            f"【{when.month}/{when.day}】오늘 {t_ilju} × 본인 {u_ilju}",
            branch_narr,
            ten_msg,
        ]
        if ilju_bit:
            parts.append(f"일주 테마: {ilju_bit}")
        if natal_line:
            parts.append(natal_line)
        if yongshin and yongshin != "판단 필요":
            parts.append(
                f"용신 {_EL_KO.get(yongshin, yongshin)}({yongshin}) — "
                f"오늘 {_EL_KO.get(t_el, t_el)}({t_el}) 기운과 "
                f"{'조화' if t_el == yongshin else '균형 맞추기'}가 체감 포인트입니다."
            )
        comments[cat] = " ".join(p for p in parts if p).strip()

    avg = int(sum(scores[c] for c in _CATEGORIES) / len(_CATEGORIES))
    core = (
        f"오늘 {t_ilju} · 십성 {ten_detail}({ten_group}) · "
        f"일지 {day_branch_rel} · 종합 {avg}%"
    )

    return {
        "scores": scores,
        "comments": comments,
        "avg_score": avg,
        "core_summary": core,
        "today_ilju": t_ilju,
        "user_ilju": u_ilju,
        "day_branch_rel": day_branch_rel,
        "today_el": t_el,
    }
