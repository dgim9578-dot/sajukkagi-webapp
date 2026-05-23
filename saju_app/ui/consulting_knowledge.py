"""공통 상담 지식: 챗봇 주입 자료를 여러 STEP에서 함께 쓰는 상담 기준."""

from __future__ import annotations

from saju_app.ui.components import DAEWON_TEN_INTERP


# STEP11 AI 챗봇 · 상담 톤의 기준(페르소나)
SAJU_KKAGI_CHATBOT_PERSONA = """
당신은 20년 경력의 따뜻하고 현실적인 사주명리 상담사 "사주까기"입니다.

【최우선 참고】
- 사용자가 앱에 입력한 사주(년·월·일·시 + 성별)와 현재 대운·세운(시기) 정보를 가장 먼저 반영합니다.
- 질문 문장에 직접 답합니다. 일반론·반복 문장·질문과 무관한 사주 설명은 피합니다.

【해석 원칙】
- 자평진전·삼명통회·적천수 등 고전 원리를 바탕으로 하되, 현대 생활(직장·연애·돈·가족·이사)에 적용 가능하게 설명합니다.
- "반드시", "무조건", "100%" 대신 "가능성이 높다", "~경향이 있다", "이런 흐름에서는 ~하는 것이 유리하다"를 사용합니다.
- 긍정적 기회와 주의점을 균형 있게 제시합니다.
- 공포·저주·불안 조장은 금지합니다. 해결책과 구체적 행동 조언을 중심으로 말합니다.
- 건강·임신·수술·법률·투자는 단정·예언 금지, 참고용이며 해당 분야 전문가 상담이 우선임을 필요 시 짧게 안내합니다.
""".strip()


def chatbot_system_prompt(*, html_output: bool = True) -> str:
    """OpenAI 등 AI 챗봇 system 메시지 본문."""
    fmt = (
        "답변은 HTML만 사용(<b>, <br>, <i>, <ul>, <li> 정도). 마크다운(**)은 쓰지 마세요."
        if html_output
        else "답변은 한국어 존댓말(~해요/합니다)로 작성하세요."
    )
    return f"{SAJU_KKAGI_CHATBOT_PERSONA}\n\n【출력 형식】\n{fmt}"


def chatbot_persona_intro_html() -> str:
    """챗봇 화면·규칙 기반 답변 상단에 쓰는 짧은 페르소나 안내."""
    return (
        '<span style="color:#6d28d9;font-weight:700;">🌿 사주까기</span> '
        "<i>20년 경력 · 따뜻하고 현실적인 사주 상담 톤으로 안내합니다.</i>"
    )


SAJU_PRO_MASTER_RULES: dict[str, dict[str, object]] = {
    "love_and_marriage": {
        "title": "연애 / 결혼 / 이별 / 궁합",
        "keywords": ("연애", "결혼", "궁합", "이별", "재회", "속마음", "인연", "배우자", "사랑"),
        "rules": (
            "여성은 관성운, 남성은 재성운에 인연·결혼운이 강하게 발동합니다.",
            "편관·편재 인연은 초반 끌림이 강하지만 피로와 구속감이 생기기 쉽습니다.",
            "정관·정재 인연은 처음은 심심해도 안정감과 책임감이 깊어지는 편입니다.",
            "일간 상생과 일지 합이 함께 살아나면 정서·생활 리듬이 맞는 궁합으로 봅니다.",
        ),
    },
    "wealth_and_business": {
        "title": "재물 / 사업 / 투자",
        "keywords": ("돈", "재물", "금전", "사업", "투자", "주식", "부동산", "창업", "손실"),
        "rules": (
            "편재는 큰 기회와 변동성, 정재는 급여·저축·고정 수입의 안정성을 봅니다.",
            "식상생재는 개인 기술·콘텐츠·전문성을 수익으로 연결하는 흐름입니다.",
            "비겁·겁재가 강한 시기에는 돈거래, 동업, 충동 지출을 줄여야 합니다.",
            "신약 사주는 큰 승부보다 현금 흐름과 방어 전략을 먼저 세우는 편이 안전합니다.",
        ),
    },
    "career_and_job": {
        "title": "직장 / 이직 / 진급",
        "keywords": ("직장", "회사", "취업", "진급", "승진", "이직", "퇴사", "커리어"),
        "rules": (
            "관성은 조직·평가·직함, 재성은 조건·연봉·성과, 식상은 기술과 표현력입니다.",
            "편관운의 진급은 발탁·파격, 정관운의 진급은 순서와 안정 승진에 가깝습니다.",
            "상관견관 흐름이 강하면 감정적 퇴사보다 조건 확인과 시기 조절이 중요합니다.",
            "지지충이 강한 해에는 부서 변화, 강제 이동, 생활 리듬 변화가 함께 올 수 있습니다.",
        ),
    },
    "health_and_move": {
        "title": "건강 / 임신 / 이사",
        "keywords": (
            "건강",
            "임신",
            "출산",
            "준비",
            "수술",
            "질병",
            "아픈",
            "아프",
            "병원",
            "부모",
            "어머니",
            "아버지",
            "간병",
            "요양",
            "모시",
            "입원",
            "이사",
            "이동",
            "거처",
        ),
        "rules": (
            "일지와 세운 지지가 충하면 이동수는 강해지지만 계약·일정·컨디션을 함께 봐야 합니다.",
            "식상·인성은 준비와 보강의 축으로 읽되, 임신·건강 결정은 의료진 상담이 우선입니다.",
            "용신이 살아나는 공간, 동선, 수면·식사 루틴을 잡으면 생활 안정감이 빨리 붙습니다.",
            "몸과 관련된 해석은 단정하지 않고 컨디션 관리 참고로만 안내해야 합니다.",
        ),
    },
    "education_and_exam": {
        "title": "공부 / 시험",
        "keywords": ("공부", "시험", "합격", "성적", "자격증", "면접"),
        "rules": (
            "인성은 공부운의 기본이지만 과하면 잡생각과 미루기가 늘 수 있습니다.",
            "식상이 강하면 표현과 실전 풀이가 좋지만 집중이 분산될 수 있습니다.",
            "관성이 살아나면 루틴, 시간표, 압박 관리가 합격 체감에 중요합니다.",
        ),
    },
}


SAJU_STORYTELLING_DATABASE: dict[str, dict[str, str]] = {
    "love_and_marriage": {
        "female_pyeongwan": "편관운은 불꽃같은 설렘을 주지만, 시간이 지나면 구속감이나 스트레스로 바뀔 수 있어요. 초반 감정에 휩쓸리기보다 상대의 책임감과 생활 태도를 같이 보셔야 합니다.",
        "female_jeonggwan": "정관운은 처음엔 답답하거나 심심해 보여도 함께 시간을 보낼수록 신뢰와 안정감이 쌓이는 인연입니다. 빠른 확신보다 진득하게 지켜보는 태도가 좋습니다.",
        "male_pyeonjae": "편재운은 눈이 번쩍 뜨일 만큼 매력적인 인연이나 큰 기회가 들어오는 흐름입니다. 다만 쟁취 욕구가 강해질수록 체력과 마음의 소모도 커지니 페이스 조절이 필요합니다.",
        "male_jeongjae": "정재운은 화려함보다 안정감이 있는 인연과 생활 기반을 뜻합니다. 짜릿함은 덜해도 오래 갈 사람, 현실을 함께 만들 사람을 보는 눈이 중요합니다.",
        "reunion": "재회운은 그리움만으로 판단하면 같은 문제가 반복되기 쉽습니다. 다시 만난다면 무엇을 바꿀지, 말투·거리·약속을 구체적으로 정해야 관계가 새로워집니다.",
        "compatibility": "궁합은 점수보다 생활에서 체감되는 보완이 중요합니다. 강한 사람은 밀어붙이기보다 속도를 낮추고, 약한 사람은 참기보다 필요한 것을 말해야 균형이 맞습니다.",
        "caution": "관계가 흔들리는 시기에는 밖의 설렘보다 관계 안의 균열을 먼저 봐야 합니다. 감정이 뜨거울수록 단정적인 말과 시험하듯 던지는 질문은 줄이는 편이 좋습니다.",
    },
    "wealth_and_career": {
        "siksang_wealth": "식상생재 흐름은 내 재능, 기술, 말, 콘텐츠가 돈이 되는 구조입니다. 가만히 기다리기보다 작은 결과물을 밖으로 보여줄수록 재물 흐름이 살아납니다.",
        "money_caution": "비겁·겁재가 강한 시기에는 내 돈을 노리는 사람이나 예상 밖 지출이 늘 수 있습니다. 지인 돈거래, 무리한 동업, 충동 투자는 한 번 더 멈추는 것이 좋습니다.",
        "job_caution": "상관견관 흐름이 느껴질 때는 윗사람이나 조직이 답답해 보이고 퇴사 충동이 올라올 수 있습니다. 감정으로 끊기보다 조건, 다음 자리, 생활비를 먼저 확인하세요.",
        "job_growth": "관성·재성·식상이 함께 움직이면 평가, 조건, 실력이 밖으로 드러납니다. 이직이나 승진은 말보다 증거 자료, 성과 기록, 포트폴리오가 힘을 냅니다.",
    },
    "move_and_health": {
        "move": "이사는 단순히 장소를 바꾸는 일이 아니라 생활 리듬을 새로 짜는 일입니다. 계약, 비용, 동선, 수면 환경이 안정되면 운의 체감도 훨씬 편안해집니다.",
        "pregnancy": "임신·출산·건강은 사주로 가능성을 단정하지 않습니다. 이 화면은 생활 리듬 참고이고, 실제 판단은 산부인과와 의료진 상담을 가장 우선으로 두세요.",
        "condition": "컨디션이 흔들리는 흐름에서는 큰 결정을 몰아서 하기보다 수면, 식사, 이동량부터 줄여야 합니다. 몸이 안정되면 판단도 훨씬 선명해집니다.",
    },
}


def normalize_topic(topic: str) -> str:
    text = str(topic or "")
    if any(k in text for k in ("이사", "이동", "부동산", "거처")):
        return "move"
    if any(k in text for k in ("이직", "직장", "퇴사", "승진", "취업", "커리어")):
        return "job"
    if any(
        k in text
        for k in (
            "재물",
            "돈",
            "금전",
            "투자",
            "사업",
            "거래",
            "성사",
            "계약",
            "협상",
            "영업",
            "매출",
            "판매",
            "주식",
            "코인",
            "매매",
        )
    ):
        return "wealth"
    if any(k in text for k in ("결혼", "연애", "재회", "속마음", "인연", "궁합", "사랑")):
        return "love"
    if any(
        k in text
        for k in (
            "임신",
            "출산",
            "준비",
            "건강",
            "수술",
            "질병",
            "아픈",
            "아프",
            "병원",
            "부모",
            "간병",
            "요양",
            "모시",
            "입원",
        )
    ):
        return "health"
    if any(k in text for k in ("공부", "시험", "합격", "성적")):
        return "study"
    return "general"


def _is_female_gender(gender: str) -> bool:
    return any(token in str(gender or "") for token in ("여", "女", "F", "f"))


def _matched_master_rules(topic: str) -> list[str]:
    text = str(topic or "")
    matched: list[str] = []
    for key, data in SAJU_PRO_MASTER_RULES.items():
        keywords = tuple(data.get("keywords", ())) if isinstance(data, dict) else ()
        if any(str(k) and str(k) in text for k in keywords):
            rules = tuple(data.get("rules", ()))
            matched.extend(str(rule) for rule in rules[:2])
    return matched[:4]


def _storytelling_tip(topic: str, *, gender: str, daewoon_ten: str) -> str:
    text = str(topic or "")
    is_female = _is_female_gender(gender)
    love = SAJU_STORYTELLING_DATABASE["love_and_marriage"]
    wealth = SAJU_STORYTELLING_DATABASE["wealth_and_career"]
    move = SAJU_STORYTELLING_DATABASE["move_and_health"]

    if any(k in text for k in ("재회", "이별", "헤어", "속마음")):
        return love["reunion"]
    if any(k in text for k in ("궁합", "감정", "인연", "연애", "결혼")):
        if "정관" in str(daewoon_ten) and is_female:
            return love["female_jeonggwan"]
        if "정재" in str(daewoon_ten) and not is_female:
            return love["male_jeongjae"]
        if "주의" in text:
            return love["caution"]
        if "생활" in text or "궁합" in text:
            return love["compatibility"]
        return love["female_pyeongwan"] if is_female else love["male_pyeonjae"]
    if any(k in text for k in ("이직", "직장", "퇴사", "커리어", "승진")):
        if any(k in text for k in ("퇴사", "주의", "상사")):
            return wealth["job_caution"]
        return wealth["job_growth"]
    if any(
        k in text
        for k in (
            "재물",
            "돈",
            "금전",
            "사업",
            "투자",
            "거래",
            "성사",
            "계약",
            "협상",
            "영업",
            "매출",
            "판매",
            "주식",
            "코인",
            "매매",
        )
    ):
        if any(k in text for k in ("손실", "주의", "동업", "비겁", "겁재")):
            return wealth["money_caution"]
        return wealth["siksang_wealth"]
    if any(k in text for k in ("이사", "이동", "거처")):
        return move["move"]
    if any(
        k in text
        for k in ("임신", "출산", "건강", "수술", "질병", "아픈", "아프", "병원", "부모", "모시", "요양")
    ):
        if "임신" in text or "출산" in text:
            return move["pregnancy"]
        if any(k in text for k in ("부모", "모시", "요양", "병원", "어디")):
            return (
                "부모님·가족 건강과 거처는 사주로 병명·병원을 단정하지 않습니다. "
                "다만 이동·환경 기운이 강할 때는 **진료 접근성(응급·전문의)·간병 동선·수면·식사 환경**을 "
                "먼저 보는 것이 좋습니다. 무리한 이사보다 의료진 상담 후, 병원·요양·자택 간병 중 "
                "컨디션과 비용·가족 돌봄 여력에 맞는 선택을 비교하세요."
            )
        return move["condition"]
    return ""


def _strength_posture(strength: str) -> str:
    stg = str(strength or "중화")
    if "신강" in stg and "신약" not in stg:
        return "신강한 구조라면 기회가 왔을 때 직접 선택하고 밀고 나가는 힘이 살아납니다. 다만 과속하면 충돌이 커지므로 기준을 먼저 세우세요."
    if "신약" in stg and "신강" not in stg:
        return "신약한 구조라면 혼자 힘으로 밀어붙이기보다 사람·환경·타이밍을 빌리는 전략이 운을 편하게 엽니다."
    return "강약이 섞이거나 중화에 가까운 구조라면 한쪽으로 몰아붙이기보다 관계·돈·일정의 균형표를 먼저 잡는 것이 좋습니다."


def _daewoon_line(*, daewoon_pillar: str, daewoon_ten: str) -> str:
    dp = str(daewoon_pillar or "").strip()
    dt = str(daewoon_ten or "").strip()
    if len(dp) < 2 or not dt:
        return ""
    hint = str(DAEWON_TEN_INTERP.get(dt, "") or "").strip()
    tail = f" — {hint}" if hint else ""
    return f"같은 시기 **10년 대운 {dp}**(천간 십성 **{dt}**){tail}."


def consulting_tip_for_action_year(
    topic: str,
    *,
    year: int,
    year_pillar: str = "",
    seyun_ten: str = "",
    branch_rel: str = "",
    daewoon_pillar: str = "",
    daewoon_ten: str = "",
    strength: str = "",
    yongshin: str = "",
    gender: str = "",
    yong_aligns: bool = False,
) -> str:
    """STEP9 행동 타이밍 — 선택 연도·세운·대운·일지 관계가 반영된 연도별 상담."""
    y = int(year)
    pill = str(year_pillar or "—").strip()
    ten = str(seyun_ten or "—").strip()
    rel = str(branch_rel or "없음").strip()
    ys = str(yongshin or "균형").strip()
    is_female = _is_female_gender(gender)
    love = SAJU_STORYTELLING_DATABASE["love_and_marriage"]
    wealth = SAJU_STORYTELLING_DATABASE["wealth_and_career"]
    move_db = SAJU_STORYTELLING_DATABASE["move_and_health"]

    head = (
        f"**{y}년** 입춘 기준 세운 **{pill}**, 일간 대비 천간 십성 **{ten}**, "
        f"일지↔세운 지지 **{rel}**입니다."
    )
    dae = _daewoon_line(daewoon_pillar=daewoon_pillar, daewoon_ten=daewoon_ten)
    lines: list[str] = [head]
    if dae:
        lines.append(dae)

    t = normalize_topic(topic)
    if t == "move":
        if "충" in rel:
            lines.append(
                f"{y}년에는 일지·세운 **충(沖)**이 겹쳐 이사·환경 전환 에너지는 살아나지만, "
                "계약·이사 일정·몸 컨디션이 함께 흔들리기 쉽습니다. 서류·비용·동선을 먼저 고정하세요."
            )
        elif "합" in rel:
            lines.append(
                f"{y}년 **합(六合)** 기운은 거처·생활 리듬을 새로 맞추기에 동조가 나오기 쉬운 편으로 읽힙니다. "
                "다만 합만 보고 서두르기보다 실거주·통근·수면 환경을 직접 확인하세요."
            )
        else:
            lines.append(
                f"{y}년은 지지 합·충이 두드러지지 않아, **예산·계약·이사 업체 일정**만 안정되면 "
                "이사를 현실적으로 조율하기 좋은 해로 보는 경우가 많습니다."
            )
        if yong_aligns:
            lines.append(
                f"{y}년 세운 천간이 용신 **{ys}**과 맞닿아, 이전 후 안정감이 붙기 쉬운 흐름으로도 읽힙니다."
            )
        if ten in ("비견", "겁재"):
            lines.append(
                f"세운 **{ten}**이면 주변과 역할·비용 분담을 먼저 정리한 뒤 이사를 검토하는 편이 낫습니다."
            )
        lines.append(move_db["move"])
    elif t == "job":
        if any(x in ten for x in ("정관", "편관", "정재", "편재", "식신", "상관")):
            lines.append(
                f"{y}년 세운 **{ten}**은 제안·평가·성과가 겉으로 드러나기 쉬운 흐름으로 읽히는 경우가 많습니다. "
                f"{wealth['job_growth']}"
            )
        elif "인" in ten:
            lines.append(
                f"{y}년 세운 **{ten}**(인성)은 배움·자격·내부 정비에 유리하고, 겉으로는 움직임이 천천히 보일 수 있습니다."
            )
        else:
            lines.append(
                f"{y}년 세운 **{ten}**은 이직보다 실력·포트폴리오·협업 관계를 쌓는 타이밍으로 읽는 경우가 많습니다."
            )
        if "상관" in ten:
            lines.append(
                f"{y}년 세운 **{ten}** — {wealth['job_caution']}"
            )
        if ten in ("비견", "겁재"):
            lines.append(
                f"{y}년 세운 **{ten}** — {wealth['money_caution']}"
            )
        if daewoon_ten and "관" in str(daewoon_ten):
            lines.append(
                f"10년 대운 **{daewoon_ten}**과 {y}년 세운 **{ten}**이 겹치면 조직·직함·책임 이슈가 동시에 올라올 수 있어, "
                "감정적 퇴사보다 다음 역할·연봉·생활비를 먼저 적어 두세요."
            )
    elif t == "love":
        if "충" in rel:
            lines.append(
                f"{y}년 일지·세운 **충**이면 약속·일정이 어긋나기 쉬워, 결혼·동거는 **대화·합의**를 먼저 두는 편이 좋습니다."
            )
        if is_female and any(x in ten for x in ("정관", "편관")):
            lines.append(
                f"{y}년 세운 **{ten}**이면 여성에게 관성운이 작동해 관계를 구체화·안정화하기 좋은 흐름으로 읽는 경우가 많습니다."
            )
            if "편관" in ten:
                lines.append(love["female_pyeongwan"])
            elif "정관" in ten:
                lines.append(love["female_jeonggwan"])
        elif not is_female and any(x in ten for x in ("정재", "편재")):
            lines.append(
                f"{y}년 세운 **{ten}**이면 남성에게 재성운이 작동해 가정·생활 기반을 잡기 좋은 흐름으로 읽는 경우가 많습니다."
            )
            if "편재" in ten:
                lines.append(love["male_pyeonjae"])
            elif "정재" in ten:
                lines.append(love["male_jeongjae"])
        elif "합" in rel:
            lines.append(
                f"{y}년 지지 **합**은 정서적 끌림·동조가 살아나기 쉬우나, 생활 리듬·돈·가족 이슈까지 맞는지 확인하세요."
            )
        else:
            lines.append(
                f"{y}년 세운 **{ten}**만으로는 인연 공식화 체감이 약할 수 있어, "
                "월운·일진·상대 사주까지 겹칠 때 결혼·동거를 검토하는 편이 낫습니다."
            )
    elif t == "health" and any(k in str(topic) for k in ("임신", "출산", "준비")):
        if "충" in rel:
            lines.append(
                f"{y}년 지지 **충**이면 몸·일정이 바쁘게 느껴질 수 있어, 임신·준비 일정을 무리하게 압축하지 마세요."
            )
        if any(x in ten for x in ("식신", "상관", "정인", "편인")):
            lines.append(
                f"{y}년 세운 **{ten}**은 전통적으로 준비·보강 축으로 읽히는 경우가 있어, "
                "수면·영양·회복 루틴을 챙기기 좋은 해로 보는 해석이 많습니다."
            )
        else:
            lines.append(
                f"{y}년 세운 **{ten}**은 임신 가능성을 단정하지 않습니다. "
                "산부인과 상담·검사가 항상 우선입니다."
            )
        lines.append(move_db["pregnancy"])
        lines.append(f"생활 루틴 참고로는 용신 **{ys}**을 살리는 수면·식사·회복 습관을 안정판으로 삼으세요.")
    elif t == "health":
        if "충" in rel:
            lines.append(
                f"{y}년 일지·세운 **충**이면 피로·수면·일정 리듬이 흔들리기 쉬워 "
                "정기 검진·휴식·무리한 일정 압축을 피하는 편이 좋습니다."
            )
        elif any(x in ten for x in ("정관", "편관")):
            lines.append(
                f"{y}년 세운 **{ten}**은 책임·스트레스·업무 부담이 몸에 쌓이기 쉬운 흐름으로 읽히는 경우가 많습니다. "
                "혈압·소화·수면 루틴을 먼저 점검하세요."
            )
        elif any(x in ten for x in ("식신", "상관", "정인", "편인")):
            lines.append(
                f"{y}년 세운 **{ten}**은 **회복·영양·생활 습관**을 정비하기 좋은 해로 읽는 해석이 많습니다."
            )
        else:
            lines.append(
                f"{y}년 세운 **{ten}**은 **정기 검진·가벼운 운동·수면** 같은 기본 루틴을 지키는 해로 보는 편입니다."
            )
        lines.append(
            "건강·질병·수술은 사주로 단정하지 않습니다. 증상·치료·검진은 의료진 상담이 우선입니다."
        )
        lines.append(f"생활 루틴 참고로는 용신 **{ys}**을 살리는 수면·식사·회복 습관을 안정판으로 삼으세요.")
    elif t == "wealth":
        if any(x in ten for x in ("정재", "편재")):
            lines.append(
                f"{y}년 세운 **{ten}**은 **저축·연금·임대·고정 수입** 등 재정을 정리·확장하기 좋은 흐름으로 읽히는 경우가 많습니다."
            )
        elif any(x in ten for x in ("식신", "상관")):
            lines.append(
                f"{y}년 세운 **{ten}**은 **기술·전문성·콘텐츠**를 수익으로 연결하기 좋은 해로 읽히는 경우가 있습니다. "
                f"{wealth['siksang_wealth']}"
            )
        elif ten in ("비견", "겁재"):
            lines.append(f"{y}년 세운 **{ten}** — {wealth['money_caution']}")
        else:
            lines.append(
                f"{y}년 세운 **{ten}**은 **무리한 확장**보다 **현금 흐름·부채·연금**을 점검하는 해로 보는 편입니다."
            )
        if "충" in rel:
            lines.append(
                f"{y}년 일지·세운 **충**이면 **큰 거래·투자 일정**이 바뀌기 쉬워 서류·자금 계획을 먼저 고정하세요."
            )
        if yong_aligns:
            lines.append(
                f"{y}년 세운 천간이 용신 **{ys}**과 맞닿아 재정 판단·계약이 덜 흔들리기 쉽습니다."
            )
    else:
        lines.append(
            f"{y}년 세운 **{ten}**과 일지 관계 **{rel}**을 함께 보고, "
            f"용신 **{ys}**이 살아나는 환경·사람·시간대를 고르는지가 기준입니다."
        )

    lines.append(_strength_posture(strength))
    return " ".join(x for x in lines if str(x).strip())


def consulting_tip(
    topic: str,
    *,
    strength: str = "",
    yongshin: str = "",
    daewoon_ten: str = "",
    gender: str = "",
    for_chat: bool = False,
) -> str:
    """사주까기 상담 톤으로 각 기능이 공유하는 2~4문장 조언."""
    t = normalize_topic(topic)
    stg = str(strength or "중화")
    ys = str(yongshin or "균형")
    ten = str(daewoon_ten or "")
    is_female = any(x in str(gender or "") for x in ("여", "女", "F", "f"))

    posture = _strength_posture(stg)

    if t == "move":
        body = (
            "이사와 이동은 일지와 세운 지지가 충을 이루는지, 대운이 바뀌는 시기인지 함께 보는 것이 핵심입니다. "
            "충이 강하면 움직임은 생기지만 계약·일정·몸 컨디션이 함께 흔들릴 수 있어 서류와 비용을 먼저 고정해야 합니다. "
            f"용신 {ys}이 살아나는 방향의 공간, 생활 동선, 주변 환경을 고르면 이전 후 안정감이 더 빨리 붙습니다."
        )
    elif t == "job":
        body = (
            "이직은 관성·재성·식상이 어떻게 움직이는지에 따라 성격이 달라집니다. "
            "관성은 조직·평가·직함, 재성은 조건·연봉·성과, 식상은 내 기술과 포트폴리오를 밖으로 드러내는 흐름입니다. "
            f"현재 십성 흐름이 {ten or '뚜렷하지 않음'} 쪽이면 감정적 퇴사보다 제안 조건과 다음 역할을 먼저 확인하세요."
        )
    elif t == "love":
        body = (
            "연애와 결혼은 여성에게 관성, 남성에게 재성이 강하게 작동할 때 관계가 공식화되기 쉽습니다. "
            "편관·편재는 초반 끌림이 강하지만 피로가 빨리 올 수 있고, 정관·정재는 느리지만 안정감이 깊어지는 편입니다. "
            f"{'여성 관점에서는 관성운의 책임감과 약속 여부를 특히 보세요.' if is_female else '남성 관점에서는 재성운의 책임감과 생활 안정성을 특히 보세요.'}"
        )
    elif t == "health":
        body = (
            "임신·건강·수술 관련 흐름은 단정하지 않고 생활 리듬 참고로만 보아야 합니다. "
            "식상·인성은 준비와 보강의 축으로 읽을 수 있으나, 실제 임신·출산·치료 결정은 반드시 의료진 상담이 우선입니다. "
            f"사주에서는 용신 {ys}을 살리는 수면·식사·회복 루틴을 안정판으로 삼는 정도가 적절합니다."
        )
    elif t == "wealth":
        if for_chat:
            body = (
                "결정이 필요한 질문은 십성, 일지 관계, 용신을 함께 보아야 깊이가 생깁니다. "
                f"지금은 용신 {ys}이 살아나는 환경과 사람, 시간대를 고르는지가 상담의 기준입니다. "
                "상담 기준으로는 편재는 큰 기회와 변동성, 정재는 급여·저축·고정 수입의 안정성을 봅니다. "
                "식상생재는 개인 기술·콘텐츠·전문성을 수익으로 연결하는 흐름입니다."
            )
        else:
            body = (
                "재물은 편재와 정재의 성격을 나눠 보아야 합니다. 편재는 큰 기회와 변동성, 정재는 급여·저축·고정 수입의 안정성을 뜻합니다. "
                "비겁이 강한 시기에는 돈거래·동업·충동 지출을 줄이고, 식상생재가 살아나면 기술·콘텐츠·판매처럼 내 능력을 돈으로 연결하는 쪽이 좋습니다."
            )
    elif t == "study":
        body = (
            "공부와 시험은 인성운이 기본이지만, 식상이 강하면 표현과 실전 풀이가 좋아지고 관성이 살아나면 루틴과 압박 관리가 중요해집니다. "
            "인성이 과하면 생각만 많아질 수 있으니 정리 노트보다 실제 문제 풀이 비중을 늘리는 것이 좋습니다."
        )
    else:
        body = (
            "결정이 필요한 질문은 십성, 일지 관계, 용신을 함께 보아야 깊이가 생깁니다. "
            f"지금은 용신 {ys}이 살아나는 환경과 사람, 시간대를 고르는지가 상담의 기준입니다."
        )

    story = _storytelling_tip(topic, gender=gender, daewoon_ten=daewoon_ten)
    rules = _matched_master_rules(topic)
    rule_line = ""
    if rules and not (for_chat and t == "wealth"):
        rule_line = " 상담 기준으로는 " + " ".join(rules[:2])
    story_line = "" if for_chat else (f" {story}" if story else "")
    return f"{body}{story_line}{rule_line} {posture}".strip()


