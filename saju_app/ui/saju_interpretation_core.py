"""STEP3 개인화 해석 코어 — 일주·십성·코퍼스·원국 메타·시주·대운·세운을 조합."""

from __future__ import annotations

from typing import Any

from saju.core.engine import STEM_ELEMENT
from saju.core.gapja_utils import has_hour_pillar, is_valid_pillar
from saju_app.ui.ilju_profiles import get_ilju_profile

_EL_KO = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}

_BRANCH_DAY_TONE: dict[str, str] = {
    "子": "내면·직관·밤 시간대에 집중력이 올라가는 편입니다.",
    "丑": "끈기와 축적, 묵묵히 결과를 쌓는 실행형에 가깝습니다.",
    "寅": "새 출발·도전·리더십 욕구가 강하게 드러납니다.",
    "卯": "관계·협업·섬세한 조율에서 강점이 나옵니다.",
    "辰": "변화·확장·큰 그림과 현실 사이를 오가는 타입입니다.",
    "巳": "표현·설득·아이디어를 빠르게 밖으로 끄집어내는 편입니다.",
    "午": "열정·속도·눈에 띄는 성과를 중시합니다.",
    "未": "배려·수용·장기 프로젝트에 잘 버티는 편입니다.",
    "申": "기민함·전략·문제 해결과 기회 포착에 강합니다.",
    "酉": "완성도·미감·원칙·정리 정돈에 예민합니다.",
    "戌": "책임·신뢰·조직·약속을 지키는 쪽으로 기운이 모입니다.",
    "亥": "상상·학습·깊은 공감과 흐름 읽기에 강합니다.",
}

_HOUR_BRANCH_LIFE: dict[str, str] = {
    "子": "저녁~자정 전후에 사고·감정이 또렷해지며, 말년에는 학습·정리·대화형 활동이 맞습니다.",
    "丑": "늦은 밤~새벽 리듬에 가깝고, 말년은 꾸준한 축적·자산·기술 정리에 강점이 드러납니다.",
    "寅": "새벽·이른 아침 에너지로, 말년에도 도전·이동·개척 욕구가 남을 수 있습니다.",
    "卯": "아침·출근 시간대 기운으로, 말년에는 인맥·협업·후배·자녀와의 소통이 핵심입니다.",
    "辰": "오전 중반의 변화·확장 기운으로, 말년 전환·이사·직업 재정비 이벤트가 올 수 있습니다.",
    "巳": "오전 후반~점심 전 표현력이 올라가며, 말년에는 강의·글·콘텐츠·후배 양성에 강합니다.",
    "午": "정오·오후 초반의 열정으로, 말년에도 무대·리더·대표 역할 욕구가 남을 수 있습니다.",
    "未": "오후 중반의 배려·돌봄 기운으로, 말년은 가족·생활·건강·서비스형 활동이 안정적입니다.",
    "申": "늦은 오후·전략·기회 포착에 강하며, 말년에는 재테크·네트워크·기술 활용이 유리합니다.",
    "酉": "저녁·정리·완성도 기운으로, 말년에는 품질·브랜드·약속 이행·유산이 중요해집니다.",
    "戌": "해 질 녘·책임·신뢰 기운으로, 말년에는 조직·가족·약속·후손 문제에 집중하기 쉽습니다.",
    "亥": "밤·직관·상상력 기운으로, 말년에는 연구·예술·상담·여행·영성 쪽 만족도가 높아집니다.",
}

_STRENGTH_LIFE_ANGLE: dict[str, str] = {
    "신강": "기운이 앞으로 나오는 편이라, 스스로 밀고 나갈 때 성과가 빨리 드러납니다. 다만 과속·과욕은 피하는 것이 좋습니다.",
    "신약": "주변·환경·사람의 도움을 빌릴 때 유리합니다. 혼자 모든 것을 떠안기보다 분업·협력이 체감 운을 살립니다.",
    "중화": "극단보다 균형이 무기입니다. 한 가지 기울기만 고집하기보다 시기에 맞게 강·약을 바꿔 쓰면 안정적입니다.",
}

_YONGSHIN_LIFE_TIP: dict[str, str] = {
    "木": "성장·학습·새 프로젝트·초록·동쪽 동선처럼 ‘확장’을 상징하는 선택이 잘 맞습니다.",
    "火": "표현·관계·활동·빛·따뜻한 색처럼 ‘드러냄’과 ‘연결’이 핵심입니다.",
    "土": "루틴·신뢰·중재·실속·중앙 역할처럼 ‘받쳐 주기’가 강점입니다.",
    "金": "정리·결단·품질·원칙·계약처럼 ‘기준’과 ‘마무리’에 강합니다.",
    "水": "휴식·직관·유연한 이동·정보 수집처럼 ‘흐름 읽기’가 중요합니다.",
}


def _ten_god_summary(u_gapja: list[str]) -> str:
    if len(u_gapja) < 3:
        return ""
    try:
        from saju_app.ui import components as M

        day_stem = u_gapja[2][0]
        parts: list[str] = []
        for i, label in enumerate(("년", "월", "시")):
            idx = (0, 1, 3)[i]
            if idx >= len(u_gapja) or not is_valid_pillar(u_gapja[idx]):
                if idx == 3:
                    parts.append("시주 미입력")
                continue
            ten = M.get_detailed_ten_stem(day_stem, u_gapja[idx][0])
            parts.append(f"{label}간 {ten}")
        return " · ".join(parts)
    except Exception:
        return ""


def _ilju_from_db(ilju: str) -> dict[str, str]:
    key = str(ilju or "").strip()
    if len(key) < 2:
        return {"personality": "", "career": "", "relationship": ""}
    return get_ilju_profile(key)


def _hour_pillar_detail(u_gapja: list[str]) -> str:
    if not has_hour_pillar(u_gapja):
        return ""
    hp = str(u_gapja[3]).strip()
    if len(hp) < 2:
        return ""
    try:
        from saju_app.ui import components as M

        day_stem = u_gapja[2][0]
        hour_stem, hour_branch = hp[0], hp[1]
        ten = M.get_detailed_ten_stem(day_stem, hour_stem)
        ten_note = M.DAEWON_TEN_INTERP.get(ten, "")
        branch_life = _HOUR_BRANCH_LIFE.get(hour_branch, "")
        el = _EL_KO.get(STEM_ELEMENT.get(hour_stem, ""), "")
        return (
            f"【시주 {hp}】 시간 천간 십성 {ten}({el}) — {ten_note}. "
            f"{branch_life} "
            "출생 시간이 반영되어 저녁 컨디션·말년·자녀·후배·말·행동 습관 해석 정밀도가 올라갔습니다."
        ).strip()
    except Exception:
        return f"【시주 {hp}】 말년·저녁 리듬·세부 성격 해석에 반영됩니다."


def _corpus_snippets(*, ilju: str, strength: str, yongshin: str, max_el: str) -> list[str]:
    try:
        from saju_app.ui import consulting_corpus as CC

        queries = [
            CC.query_for_step(
                "step3",
                topic="default",
                ilju=ilju,
                yongshin=yongshin,
                strength=strength,
            ),
            f"용신 {yongshin} {strength} 원국",
            f"{_EL_KO.get(max_el, max_el)} 기운",
        ]
        seen: set[str] = set()
        out: list[str] = []
        for q in queries:
            for hit in CC.match_consulting(q, apply="step3", limit=1):
                ans = str(hit.answer or "").strip()
                if len(ans) < 30 or ans in seen:
                    continue
                seen.add(ans)
                out.append(ans[:420])
                if len(out) >= 2:
                    return out
        return out
    except Exception:
        return []


def build_step3_core(
    u_gapja: list[str],
    engine: dict[str, Any],
    *,
    gender: str = "",
    birth_record: tuple | list | None = None,
    birth_year: int | None = None,
    zi_boundary: str = "23:30",
) -> dict[str, Any]:
    """STEP3용 개인화 코어 — interpretation_layout에서 소비."""
    ilju = u_gapja[2] if len(u_gapja) > 2 else ""
    strength = str(engine.get("strength") or "중화")
    yongshin = str(engine.get("yongshin") or "판단 필요")
    max_el = str(engine.get("max_el") or "木")
    min_el = str(engine.get("min_el") or "水")
    day_stem = str(engine.get("day_stem") or (ilju[0] if ilju else ""))
    day_el = str(engine.get("day_el") or STEM_ELEMENT.get(day_stem, ""))

    jae = int(engine.get("ten_jae") or 0)
    guan = int(engine.get("ten_guan") or 0)
    sik = int(engine.get("ten_sik") or 0)
    bigyeop = int(engine.get("ten_bigyeop") or 0)
    in_cnt = int(engine.get("ten_in") or 0)
    clash = int(engine.get("clash") or 0)
    combine = int(engine.get("combine") or 0)

    ilju_prof = _ilju_from_db(ilju)
    personality = ilju_prof.get("personality") or ""
    career = ilju_prof.get("career") or ""
    relationship = ilju_prof.get("relationship") or ""
    ten_line = _ten_god_summary(list(u_gapja))
    strength_line = _STRENGTH_LIFE_ANGLE.get(strength, "")
    yong_tip = _YONGSHIN_LIFE_TIP.get(yongshin, f"{yongshin} 기운을 생활 습관에 녹이면 균형이 좋아집니다.")
    hour_detail = _hour_pillar_detail(list(u_gapja))

    timing_summary = ""
    if birth_year is not None:
        try:
            from saju_app.ui.step3_timing_summary import build_step3_timing_summary

            timing_summary = build_step3_timing_summary(
                u_gapja=list(u_gapja),
                u_data=birth_record,
                gender=str(gender or ""),
                birth_year=int(birth_year),
                yongshin=yongshin,
                engine=engine,
                zi_boundary=str(zi_boundary or "23:30"),
            )
        except Exception:
            timing_summary = ""

    corpus = _corpus_snippets(ilju=ilju, strength=strength, yongshin=yongshin, max_el=max_el)

    blocks: list[str] = []
    if strength_line:
        blocks.append(f"【내 에너지 {strength}】 {strength_line}")
    if yongshin != "판단 필요" and yong_tip:
        blocks.append(f"【핵심 보조 기운 {yongshin}】 {yong_tip}")
    if ten_line:
        blocks.append(f"【역할 유형(십성)】 {ten_line}")
    if hour_detail:
        blocks.append(hour_detail)
    elif not has_hour_pillar(u_gapja):
        blocks.append(
            "【시주 참고】 출생 시간 미입력 — 말년·자녀·저녁 컨디션·세부 성격 해석은 "
            "3주(년·월·일) 기준입니다. STEP2에서 시간을 입력하면 시주까지 반영되어 정밀도가 올라갑니다."
        )
    if timing_summary:
        blocks.append(f"【10년·1년 운】 {timing_summary}")

    ten_pattern: list[str] = []
    if jae >= 2:
        ten_pattern.append("돈·기회(재성) 기운이 두드러져 수입·현실 감각에 민감합니다.")
    elif jae == 0:
        ten_pattern.append("돈·기회(재성) 기운이 약해 현금·자산은 스스로 설계하는 편이 유리합니다.")
    if guan >= 2:
        ten_pattern.append("일·책임(관성) 기운이 있어 약속·조직·평판이 자주 등장합니다.")
    if sik >= 2:
        ten_pattern.append("표현·창의(식상) 기운이 강해 말·기술·콘텐츠 쪽 재능이 잘 드러납니다.")
    if bigyeop >= 2:
        ten_pattern.append("나·동료(비겁) 기운이 많아 독립·경쟁·협업 구도가 반복될 수 있습니다.")
    if in_cnt >= 2:
        ten_pattern.append("공부·지원(인성) 기운이 있어 학습·멘토·자격에 강합니다.")
    if ten_pattern:
        blocks.append("【성격·일 패턴】 " + " ".join(ten_pattern[:3]))

    if clash >= 2:
        blocks.append(
            f"【환경 변화 신호 {clash}】 이사·전환·관계 재정비 신호가 강합니다. "
            "급한 결정보다 일정·계약을 먼저 정리하는 편이 안전합니다."
        )
    if combine >= 2:
        blocks.append(
            f"【협력 신호 {combine}】 사람·환경이 잘 맞아 도움을 받기 쉬운 구조입니다."
        )

    g = str(gender or "")
    if any(x in g for x in ("여", "女", "F", "f")):
        if guan >= 1:
            blocks.append(
                "【여성 원국】 일·책임(관성) 흐름은 인연·배우자·사회적 역할과 연결되기 쉬워, "
                "관계에서 약속·경계를 분명히 할수록 안정됩니다."
            )
    elif g:
        if jae >= 1:
            blocks.append(
                "【남성 원국】 돈·연애(재성) 흐름은 배우자·재물 기회와 연결되기 쉬워, "
                "감정과 계약을 함께 보는 편이 유리합니다."
            )

    blocks.extend(corpus)

    from saju_app.ui.plain_language import to_plain_text

    interpretation_200 = to_plain_text("\n\n".join(blocks).strip())

    return {
        "ok": True,
        "ilju": ilju,
        "day_stem": day_stem,
        "day_el": day_el,
        "interpretation_200": interpretation_200,
        "personality": personality,
        "career": career,
        "relationship": relationship,
        "timing_summary": timing_summary,
        "hour_detail": hour_detail,
        "ten_god_line": ten_line,
        "corpus_hits": len(corpus),
        "pillar_count": len([p for p in u_gapja if is_valid_pillar(p)]),
        "has_hour": has_hour_pillar(u_gapja),
        "min_el": min_el,
    }
