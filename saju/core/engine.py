"""Streamlit 세션과 분리된 사주 분석 엔진(오행·신강약·용신 등)."""

from __future__ import annotations

import datetime
from collections.abc import Callable
from typing import Any

from zoneinfo import ZoneInfo

# ==================== 오행 매핑 ====================
STEM_ELEMENT: dict[str, str] = {
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


def normalize_element_symbol(el: str) -> str:
    """오행 표기(한글·한자 혼용)를 한자 木火土金水로 통일합니다."""
    s = str(el or "").strip()
    if not s:
        return ""
    return _ELEMENT_KO_TO_HANJA.get(s, s)


BRANCH_ELEMENT: dict[str, str] = {
    "子": "水",
    "丑": "土",
    "寅": "木",
    "卯": "木",
    "辰": "土",
    "巳": "火",
    "午": "火",
    "未": "土",
    "申": "金",
    "酉": "金",
    "戌": "土",
    "亥": "水",
}


def get_relation(day_el: str, other_el: str) -> str:
    if day_el == other_el:
        return "비겁"

    if (
        (day_el == "木" and other_el == "火")
        or (day_el == "火" and other_el == "土")
        or (day_el == "土" and other_el == "金")
        or (day_el == "金" and other_el == "水")
        or (day_el == "水" and other_el == "木")
    ):
        return "식상"

    if (
        (day_el == "木" and other_el == "土")
        or (day_el == "火" and other_el == "金")
        or (day_el == "土" and other_el == "水")
        or (day_el == "金" and other_el == "木")
        or (day_el == "水" and other_el == "火")
    ):
        return "재성"

    if (
        (day_el == "木" and other_el == "金")
        or (day_el == "火" and other_el == "水")
        or (day_el == "土" and other_el == "木")
        or (day_el == "金" and other_el == "火")
        or (day_el == "水" and other_el == "土")
    ):
        return "관성"

    if (
        (day_el == "木" and other_el == "水")
        or (day_el == "火" and other_el == "木")
        or (day_el == "土" and other_el == "火")
        or (day_el == "金" and other_el == "土")
        or (day_el == "水" and other_el == "金")
    ):
        return "인성"

    return "기타"


# ==================== 지지 충 / 합 ====================
BRANCH_CLASH: list[tuple[str, str]] = [
    ("子", "午"),
    ("丑", "未"),
    ("寅", "申"),
    ("卯", "酉"),
    ("辰", "戌"),
    ("巳", "亥"),
]

BRANCH_COMBINE: list[tuple[str, str]] = [
    ("子", "丑"),
    ("寅", "亥"),
    ("卯", "戌"),
    ("辰", "酉"),
    ("巳", "申"),
    ("午", "未"),
]


def check_branch_relation(branches: list[str]) -> tuple[int, int, float]:
    clash_count = 0
    combine_count = 0

    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            pair = (branches[i], branches[j])
            reverse_pair = (branches[j], branches[i])

            if pair in BRANCH_CLASH or reverse_pair in BRANCH_CLASH:
                clash_count += 1

            if pair in BRANCH_COMBINE or reverse_pair in BRANCH_COMBINE:
                combine_count += 1

    clash_score = clash_count * -1.5
    combine_score = combine_count * 1.0

    return clash_count, combine_count, clash_score + combine_score


def evaluate_month_power(day_el: str, month_branch: str) -> dict[str, Any]:
    month_el = BRANCH_ELEMENT.get(month_branch)

    if not month_el:
        return {"relation": "알수없음", "score": 0}

    relation = get_relation(day_el, month_el)

    score_map = {
        "비겁": +2.0,
        "인성": +2.5,
        "식상": -1.5,
        "재성": -2.0,
        "관성": -2.5,
    }

    return {"relation": relation, "score": score_map.get(relation, 0)}


def calculate_strength(
    u_gapja: list[str],
    *,
    birth_solar: tuple[int, int, int] | None = None,
) -> dict[str, Any]:
    """신강약: `saju_engine` 모듈(藏干·만세력 보조) 위임."""
    from saju.core import saju_engine as _saju_engine

    return _saju_engine.calculate_strength(u_gapja, birth_solar=birth_solar)


def calculate_yongshin(result: dict[str, Any]) -> dict[str, Any]:
    day_el = result["day_el"]
    strength = result["strength"]

    GENERATE = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}

    CONTROL = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

    def get_resource(el: str) -> str | None:
        for k, v in GENERATE.items():
            if v == el:
                return k
        return None

    def get_controller(el: str) -> str | None:
        for k, v in CONTROL.items():
            if v == el:
                return k
        return None

    def get_output(el: str) -> str | None:
        return GENERATE.get(el)

    def get_wealth(el: str) -> str | None:
        return CONTROL.get(el)

    if strength == "신강":
        yongshin = get_output(day_el)
        second = get_wealth(day_el)

    elif strength == "신약":
        yongshin = get_resource(day_el)
        second = day_el

    else:
        yongshin = get_controller(day_el)
        second = get_output(day_el)

    return {"yongshin": yongshin, "secondary": second}


def get_element_scores(u_gapja: list[str] | None) -> dict[str, int]:
    """
    사주 데이터를 바탕으로 오행 점수를 계산하여 차트와 총평의 데이터를 일치시킵니다.
    월지(계절)에 가중치를 부여하여 실제 사주 명리학적 비중을 산출합니다.
    """
    if not u_gapja:
        return {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}

    scores = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}

    for i, g in enumerate(u_gapja or []):
        if not g or len(g) < 2:
            continue
        s, b = g[0], g[1]

        s_w, b_w = (15, 30) if i == 1 else (10, 15)

        if s in STEM_ELEMENT:
            scores[STEM_ELEMENT[s]] += s_w
        if b in BRANCH_ELEMENT:
            scores[BRANCH_ELEMENT[b]] += b_w

    total = sum(scores.values())
    if total == 0:
        return {k: 0 for k in scores}

    return {k: round((v / total) * 100) for k, v in scores.items()}


def _detailed_ten_stem(user_stem: str, target_stem: str) -> str:
    """일간 천간 기준 십성(천간). `saju_app.ui.components.get_detailed_ten_stem`과 동일 규칙."""
    u_el = STEM_ELEMENT.get(user_stem, "木")
    t_el = STEM_ELEMENT.get(target_stem, "木")
    u_yin = user_stem in ("乙", "丁", "己", "辛", "癸")
    t_yin = target_stem in ("乙", "丁", "己", "辛", "癸")
    if u_el == t_el:
        return "비견" if u_yin == t_yin else "겁재"
    if (u_el, t_el) in [("木", "火"), ("火", "土"), ("土", "金"), ("金", "水"), ("水", "木")]:
        return "식신" if u_yin == t_yin else "상관"
    if (u_el, t_el) in [("木", "土"), ("火", "金"), ("土", "水"), ("金", "木"), ("水", "火")]:
        return "정재" if u_yin != t_yin else "편재"
    if (u_el, t_el) in [("木", "金"), ("火", "水"), ("土", "木"), ("金", "火"), ("水", "土")]:
        return "정관" if u_yin != t_yin else "편관"
    return "정인" if u_yin != t_yin else "편인"


def _pillar_ten_stem_counts(u_gapja: list[str]) -> tuple[int, int, int, int, int]:
    """일간 기준 천간 십성 요약(년·월·일·시)."""
    if len(u_gapja) < 3 or not u_gapja[2]:
        return 0, 0, 0, 0, 0
    day_stem = u_gapja[2][0]
    jae = guan = sik = bigyeop = in_cnt = 0
    for i in range(4):
        g = u_gapja[i] if i < len(u_gapja) else ""
        if not g or len(g) < 1:
            continue
        t = _detailed_ten_stem(day_stem, g[0])
        if t in ("정재", "편재"):
            jae += 1
        elif t in ("정관", "편관"):
            guan += 1
        elif t in ("식신", "상관"):
            sik += 1
        elif t in ("비견", "겁재"):
            bigyeop += 1
        elif "인" in t:
            in_cnt += 1
    return jae, guan, sik, bigyeop, in_cnt


def _clamp_life_score(n: float) -> int:
    return max(2, min(10, int(round(n))))


def _engine_life_foci(
    u_gapja: list[str],
    *,
    strength: str,
    combine: int,
    clash: int,
    timing: dict[str, Any],
    now_year: int,
) -> dict[str, str]:
    """STEP3 등 UI용 재물·혼인·커리어 점수/코멘트(원국·대운 휴리스틱, 참고용)."""
    jae, guan, sik, bigyeop, _in_cnt = _pillar_ten_stem_counts(u_gapja)
    st = str(strength or "중화")
    try:
        cmb = int(combine)
    except (TypeError, ValueError):
        cmb = 0
    try:
        clh = int(clash)
    except (TypeError, ValueError):
        clh = 0

    w_raw = 5.0 + min(4.0, jae * 1.8)
    if st == "신강" and bigyeop >= 2:
        w_raw -= 1.5
    if st == "신약" and jae >= 3:
        w_raw -= 1.0
    if cmb >= 2:
        w_raw += 1.0
    if clh >= 3:
        w_raw -= 0.5

    m_raw = 5.0 + min(3.0, guan * 1.2) + min(2.0, jae * 0.8)
    if clh >= 3:
        m_raw -= 1.5
    if cmb >= 2:
        m_raw += 1.0
    if guan == 0 and jae >= 2:
        m_raw -= 0.5

    c_raw = 5.0 + min(3.5, guan * 1.1 + sik * 0.9)
    if sik >= 2:
        c_raw += 0.8
    if guan >= 2:
        c_raw += 0.5

    ws = _clamp_life_score(w_raw)
    ms = _clamp_life_score(m_raw)
    cs = _clamp_life_score(c_raw)

    if jae >= 2:
        wc = (
            "재성이 드러나 수입·자산 축이 분명한 편입니다. 흐름을 타면 누적이 잘 붙습니다."
        )
    elif jae == 0:
        wc = "재가 약하게 보여 현금·저축 리듬을 스스로 설계하는 것이 유리합니다."
    else:
        wc = "재가 한두 축에 모여, 시기를 가려 쓰면 효율이 좋아지는 타입입니다."

    age = int(timing.get("age") or 0)
    phase = str(timing.get("phase") or "")
    if age >= 34:
        wc += " 30대 중반 이후 재물운이 급상승하는 구간으로도 읽힙니다."
    elif "확장" in phase:
        wc += " 지금 대운은 재물 축이 확장되기 쉬운 흐름입니다."

    if guan >= 2:
        mc = "관이 정돈되어 약속·책임이 인연의 핵심 테마로 읽히기 쉽습니다."
    elif guan == 0:
        mc = "관이 약해 형식보다 감정·자유로운 흐름을 선호할 수 있습니다. 맞춤이 필요합니다."
    else:
        mc = "관이 한두 곳에 있어, 관계에서 역할과 경계를 정하면 안정감이 커집니다."

    if cmb >= 1 or guan >= 1:
        if now_year <= 2029:
            mc += " 2027~2029년 전후에 좋은 인연 가능성이 열리기 쉽습니다."
        else:
            mc += " 대운이 바뀌는 시기 전후에 인연 신호를 주목하면 좋습니다."
    else:
        mc += " 합·충이 맞물리는 해에 인연 운이 살아나기 쉽습니다."

    if "성장" in phase or "확장" in phase:
        cc = "현재 대운이 승진·이직에 비교적 유리한 흐름입니다. "
    elif "시작" in phase:
        cc = "새 출발·전환이 읽히는 대운으로, 직무 방향을 가볍게 넓히기 좋습니다. "
    elif "조정" in phase or "정리" in phase:
        cc = "정리·조정의 대운이라 이직보다는 내실 다지기에 유리합니다. "
    else:
        cc = ""

    if guan + sik >= 3:
        cc += "관·식상이 살아 직무·전문성에서 두각을 내기 좋은 조합입니다."
    elif sik >= 2:
        cc += "식상이 강해 창의·표현·기술로 밥그릇을 키우기 좋습니다."
    elif guan >= 1:
        cc += "관이 받쳐줘 조직·규범 안에서 성과를 쌓기 유리한 편입니다."
    else:
        cc += "다양한 축이 섞여, 한 가지 강점을 ‘주무기’로 고르는 전략이 이득입니다."

    return {
        "wealth_strength": str(ws),
        "wealth_comment": wc.strip(),
        "marriage_strength": str(ms),
        "marriage_comment": mc.strip(),
        "career_strength": str(cs),
        "career_comment": cc.strip(),
    }


def _default_now_kst() -> datetime.datetime:
    return datetime.datetime.now(tz=ZoneInfo("Asia/Seoul"))


class SajuEngine:
    """사주 간지(u_gapja)로 엔진 결과 dict를 생성. UI/세션 상태에 의존하지 않습니다."""

    __slots__ = (
        "_birth_year",
        "_now",
        "_birth_solar",
        "_daewoon_first_start_age",
        "_daewoon_forward",
    )

    def __init__(
        self,
        birth_year: int | None = None,
        *,
        now: Callable[[], datetime.datetime] | None = None,
        birth_solar: tuple[int, int, int] | None = None,
        daewoon_first_start_age: int = 0,
        daewoon_forward: bool = True,
    ) -> None:
        self._birth_year = 2000 if birth_year is None else int(birth_year)
        self._now = now or _default_now_kst
        self._birth_solar = birth_solar
        self._daewoon_first_start_age = max(0, int(daewoon_first_start_age))
        self._daewoon_forward = bool(daewoon_forward)

    @classmethod
    def from_birth_record(cls, u_data: Any) -> SajuEngine:
        """u_data == (year, month, day, ...) 형태일 때 출생연도만 사용."""
        if isinstance(u_data, (list, tuple)) and u_data:
            try:
                return cls(birth_year=int(u_data[0]))
            except (TypeError, ValueError):
                return cls()
        return cls()

    def build(self, u_gapja: list[str]) -> dict[str, Any]:
        """
        UI와 분리된 '단일 엔진 결과'를 제공합니다.
        - 오행 분포: get_element_scores 단일 사용
        - 신강/신약/용신: calculate_strength + calculate_yongshin 단일 사용
        - 재물·혼인·커리어: wealth_* / marriage_* / career_* (점수 문자열·한 줄 코멘트, 참고용)
        """
        if not u_gapja or len(u_gapja) < 3:
            return {
                "day_stem": "甲",
                "day_el": "木",
                "elements": {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0},
                "max_el": "木",
                "min_el": "水",
                "strength": "중화",
                "yongshin": "판단 필요",
                "yongshin_secondary": None,
                "strength_score": 0,
                "wealth_strength": "5",
                "wealth_comment": "사주 정보를 입력하면 재물운 맞춤 분석을 드립니다.",
                "marriage_strength": "5",
                "marriage_comment": "사주 정보를 입력하면 혼인운 맞춤 분석을 드립니다.",
                "career_strength": "5",
                "career_comment": "사주 정보를 입력하면 커리어운 맞춤 분석을 드립니다.",
            }

        day_stem = u_gapja[2][0]
        day_el = STEM_ELEMENT.get(day_stem, "木")

        elements = get_element_scores(u_gapja)
        max_el = max(elements, key=elements.get) if elements else "木"
        min_el = min(elements, key=elements.get) if elements else "水"

        strength_result = calculate_strength(
            u_gapja, birth_solar=self._birth_solar
        )
        yong = calculate_yongshin(strength_result)

        birth_year = self._birth_year
        d_start = self._daewoon_first_start_age

        def get_ten(target_el: str) -> str:
            return get_relation(day_el, target_el)

        def get_timing_flow() -> dict[str, Any]:
            now_year = self._now().year
            age = max(0, now_year - birth_year)
            if age < d_start:
                daewoon_index = 0
            else:
                daewoon_index = max(0, (age - d_start) // 10)
            cycle = daewoon_index % 5

            if cycle == 0:
                phase, score = "🌱 시작기", 40
            elif cycle == 1:
                phase, score = "🚀 성장기", 70
            elif cycle == 2:
                phase, score = "🔥 확장기", 90
            elif cycle == 3:
                phase, score = "⚖️ 조정기", 60
            else:
                phase, score = "🧘 정리기", 30

            return {
                "age": age,
                "phase": phase,
                "score": score,
                "daewoon_index": daewoon_index,
                "daewoon_first_start_age": d_start,
                "daewoon_forward": self._daewoon_forward,
            }

        timing_flow = get_timing_flow()
        life_foci = _engine_life_foci(
            u_gapja,
            strength=str(strength_result.get("strength", "중화")),
            combine=int(strength_result.get("combine") or 0),
            clash=int(strength_result.get("clash") or 0),
            timing=timing_flow,
            now_year=self._now().year,
        )

        return {
            "day_stem": day_stem,
            "day_el": day_el,
            "elements": elements,
            "max_el": max_el,
            "min_el": min_el,
            "strength": strength_result.get("strength", "중화"),
            "yongshin": normalize_element_symbol(
                str(yong.get("yongshin") or "판단 필요")
            )
            or "판단 필요",
            "yongshin_secondary": yong.get("secondary"),
            "strength_score": strength_result.get("score", 0),
            "clash": strength_result.get("clash", 0),
            "combine": strength_result.get("combine", 0),
            "daewoon_first_start_age": d_start,
            "daewoon_forward": self._daewoon_forward,
            "get_ten": get_ten,
            "get_timing_flow": get_timing_flow,
            **life_foci,
        }
