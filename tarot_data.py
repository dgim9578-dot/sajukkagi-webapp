"""Universal-style 78 tarot card data and draw helpers for STEP 8."""

from __future__ import annotations

import random
from typing import TypedDict

from tarot_assets import resolve_card_image_path


class TarotCard(TypedDict):
    name: str
    image: str
    keyword: str
    message: str
    advice: str
    love: str
    reunion: str
    feeling: str
    career: str
    money: str
    study: str
    health: str
    meaning_up: str
    meaning_rev: str


SPREADS: dict[str, dict[str, object]] = {
    "1카드": {
        "count": 1,
        "positions": ("오늘의 핵심",),
    },
    "3카드": {
        "count": 3,
        "positions": ("현재", "흐름", "조언"),
    },
    "5카드": {
        "count": 5,
        "positions": ("현재", "막힌 부분", "숨은 도움", "가까운 흐름", "실천 조언"),
    },
}


_MAJOR_ARCANA: list[tuple[str, str, str, str, str]] = [
    ("The Fool", "Fool.jpg", "새로운 시작과 자유로운 도전의 에너지", "충동적인 선택과 불안정한 흐름", "두려움보다 설렘을 따라가 보세요."),
    ("The Magician", "Magician.jpg", "강한 추진력과 현실화 능력", "자신감 부족과 방향 혼란", "당신 안의 가능성을 믿어야 할 때예요."),
    ("The High Priestess", "Priestess.jpg", "직감과 숨겨진 진실", "감정 혼란과 오해", "답은 이미 당신 안에 있어요."),
    ("The Empress", "Empress.jpg", "풍요와 사랑, 감성의 확장", "감정 소모와 관계 피로", "스스로를 충분히 아껴주세요."),
    ("The Emperor", "Emperor.jpg", "질서와 책임, 안정적인 리더십", "고집과 통제, 경직된 태도", "기준을 세우되 마음의 여지도 남겨두세요."),
    ("The Hierophant", "Hierophant.jpg", "전통과 조언, 배움의 흐름", "틀에 갇힌 판단과 답답함", "믿을 만한 조언을 참고해 보세요."),
    ("The Lovers", "Lovers.jpg", "선택과 끌림, 관계의 조화", "망설임과 관계의 엇갈림", "마음이 원하는 방향을 솔직히 바라보세요."),
    ("The Chariot", "Chariot.jpg", "전진과 의지, 목표를 향한 추진력", "방향 상실과 과한 욕심", "흔들려도 방향을 하나로 정하세요."),
    ("Strength", "Strength.jpg", "부드러운 힘과 인내", "감정 기복과 자신감 약화", "강하게 밀기보다 차분히 다루세요."),
    ("The Hermit", "Hermit.jpg", "성찰과 거리두기, 내면의 지혜", "고립감과 지나친 고민", "잠시 물러나 마음을 정리해 보세요."),
    ("Wheel of Fortune", "Wheel_of_Fortune.jpg", "전환점과 흐름의 변화", "예측 어려움과 타이밍 지연", "흐름이 바뀔 때를 놓치지 마세요."),
    ("Justice", "Justice.jpg", "균형과 판단, 공정한 결과", "불균형과 미뤄진 결정", "감정보다 사실을 기준으로 보세요."),
    ("The Hanged Man", "Hanged_Man.jpg", "멈춤과 관점 전환", "답답한 정체와 희생감", "서두르지 말고 시야를 바꿔보세요."),
    ("Death", "Death.jpg", "끝과 새로운 시작", "과거에 대한 집착", "놓아야 새로운 흐름이 들어옵니다."),
    ("Temperance", "Temperance.jpg", "조화와 회복, 균형 잡힌 흐름", "조급함과 흐름의 불균형", "천천히 맞춰가면 좋아집니다."),
    ("The Devil", "Devil.jpg", "집착과 욕망, 강한 끌림", "벗어나기 어려운 패턴", "끌림과 의존을 구분해 보세요."),
    ("The Tower", "Tower.jpg", "갑작스러운 변화와 깨달음", "불안한 변화 회피", "무너진 자리에서 새 기준을 세우세요."),
    ("The Star", "Star.jpg", "희망과 회복, 맑은 가능성", "기대 약화와 마음의 지침", "작은 희망을 계속 살려두세요."),
    ("The Moon", "Moon.jpg", "불확실성과 감정의 깊이", "오해와 불안의 확대", "확신이 없을수록 천천히 확인하세요."),
    ("The Sun", "Sun.jpg", "기쁨과 성공, 밝은 에너지", "과한 낙관과 지연된 성취", "좋은 흐름을 숨기지 말고 표현하세요."),
    ("Judgement", "Judgement.jpg", "각성과 재평가, 다시 열리는 기회", "미련과 결정 지연", "마음의 결론을 피하지 마세요."),
    ("The World", "World.jpg", "완성과 성취, 큰 흐름의 마무리", "미완성과 마지막 점검", "이제 다음 단계로 넘어갈 준비를 하세요."),
]


_SUITS = {
    "Wands": {
        "ko": "완드",
        "theme": "열정과 행동",
        "love": "관계에 활기가 생기지만 서두르면 엇갈릴 수 있어요.",
        "career": "일과 목표에서 움직임이 커지고 실행력이 중요해요.",
        "money": "수입보다 기회와 확장 가능성을 먼저 살펴야 해요.",
        "study": "집중력은 움직일 때 살아납니다. 계획을 행동으로 옮겨보세요.",
        "health": "에너지가 올라오지만 과로와 무리한 리듬은 조심하세요.",
    },
    "Cups": {
        "ko": "컵",
        "theme": "감정과 관계",
        "love": "감정 교류가 핵심입니다. 마음을 부드럽게 표현해 보세요.",
        "career": "사람과 분위기가 성과에 영향을 주는 흐름입니다.",
        "money": "감정적 소비를 줄이고 필요한 지출만 남기는 것이 좋아요.",
        "study": "마음이 안정될수록 이해력과 기억력이 좋아집니다.",
        "health": "감정 피로를 풀고 충분한 휴식을 챙겨야 합니다.",
    },
    "Swords": {
        "ko": "소드",
        "theme": "생각과 판단",
        "love": "말과 오해가 중요합니다. 감정보다 대화의 방향을 정리하세요.",
        "career": "판단력과 문서, 소통이 성패를 가를 수 있어요.",
        "money": "계산을 냉정하게 해야 손실을 줄일 수 있습니다.",
        "study": "분석과 정리가 잘 맞는 흐름입니다. 핵심을 요약해 보세요.",
        "health": "생각이 많아 피로가 쌓일 수 있으니 수면을 챙기세요.",
    },
    "Pentacles": {
        "ko": "펜타클",
        "theme": "현실과 재물",
        "love": "느리지만 안정적인 관계 흐름을 만들 수 있어요.",
        "career": "성과는 꾸준함과 현실적인 준비에서 나옵니다.",
        "money": "재물 흐름을 차분히 다지기 좋은 시기입니다.",
        "study": "반복과 루틴이 가장 큰 힘이 됩니다.",
        "health": "생활 패턴, 식사, 몸의 기본 리듬을 회복하는 것이 중요해요.",
    },
}

_RANKS: list[tuple[str, str, str, str]] = [
    ("Ace", "시작", "새로운 씨앗과 가능성", "기회가 있는데도 망설이는 흐름"),
    ("Two", "선택", "균형을 잡아야 하는 선택", "갈등과 우유부단함"),
    ("Three", "확장", "협력과 성장의 조짐", "기대만큼 속도가 나지 않는 흐름"),
    ("Four", "안정", "기초를 다지는 안정감", "닫힌 태도와 정체감"),
    ("Five", "갈등", "변화 속의 충돌과 조정", "소모적인 갈등이 길어질 수 있음"),
    ("Six", "회복", "균형 회복과 작은 성취", "인정받지 못하는 답답함"),
    ("Seven", "도전", "버티고 지켜내는 힘", "불안과 방어적인 태도"),
    ("Eight", "속도", "흐름이 빨라지고 변화가 생김", "흐름이 막히거나 조급해짐"),
    ("Nine", "축적", "경험과 결과가 쌓이는 시기", "지친 마음과 부담감"),
    ("Ten", "완성", "한 주기의 마무리와 책임", "과부하와 내려놓지 못함"),
    ("Page", "소식", "새로운 배움과 소식", "미숙함과 준비 부족"),
    ("Knight", "움직임", "빠른 진행과 적극성", "성급함과 방향 흔들림"),
    ("Queen", "성숙", "감정과 현실을 품는 성숙함", "예민함과 자기 소모"),
    ("King", "주도", "상황을 이끄는 책임감", "권위적 태도와 부담"),
]


_TOPIC_FIELD: dict[str, str] = {
    "연애": "love",
    "재회": "reunion",
    "상대의 속마음": "feeling",
    "직장": "career",
    "금전": "money",
    "공부": "study",
    "건강": "health",
}


def _major_topic_text(
    card_name: str,
    meaning_up: str,
    meaning_rev: str,
    message: str,
    topic: str,
) -> str:
    return (
        f"【{topic}】 {card_name} — 핵심: {meaning_up}. "
        f"실천 조언: {message} "
        f"흐름이 무거우면: {meaning_rev}"
    )


def _minor_topic_text(
    card_name: str,
    rank_ko: str,
    up_flow: str,
    rev_flow: str,
    suit_data: dict[str, str],
    topic: str,
) -> str:
    field = _TOPIC_FIELD.get(topic, "love")
    domain = str(suit_data.get(field, suit_data.get("theme", ""))).strip()
    if topic == "재회":
        domain = (
            f"{domain} "
            "재회·연락은 상대의 속도와 경계를 먼저 읽는 것이 중요합니다."
        ).strip()
    elif topic == "상대의 속마음":
        domain = (
            f"{domain} "
            "표현보다 행동·연락 패턴에서 마음의 온도를 확인해 보세요."
        ).strip()
    return (
        f"【{topic}】 {card_name}({rank_ko}) — {up_flow}. "
        f"{domain} "
        f"지연·역흐름 신호: {rev_flow}"
    )


def _build_card(
    name: str,
    image: str,
    meaning_up: str,
    meaning_rev: str,
    message: str,
    *,
    love: str | None = None,
    career: str | None = None,
    money: str | None = None,
    study: str | None = None,
    health: str | None = None,
) -> TarotCard:
    legacy_image = f"tarot_images/{image}"
    resolved_image = resolve_card_image_path(name, legacy_image=legacy_image) or legacy_image
    love_text = love or _major_topic_text(name, meaning_up, meaning_rev, message, "연애")
    reunion_text = _major_topic_text(name, meaning_up, meaning_rev, message, "재회")
    feeling_text = _major_topic_text(name, meaning_up, meaning_rev, message, "상대의 속마음")
    career_text = career or _major_topic_text(name, meaning_up, meaning_rev, message, "직장")
    money_text = money or _major_topic_text(name, meaning_up, meaning_rev, message, "금전")
    study_text = study or _major_topic_text(name, meaning_up, meaning_rev, message, "공부")
    health_text = health or _major_topic_text(name, meaning_up, meaning_rev, message, "건강")
    return {
        "name": name,
        "image": resolved_image,
        "keyword": meaning_up,
        "message": (
            f"정방향: {meaning_up}\n\n"
            f"역방향: {meaning_rev}\n\n"
            f"조언: {message}"
        ),
        "advice": message,
        "love": love_text,
        "reunion": reunion_text,
        "feeling": feeling_text,
        "career": career_text,
        "money": money_text,
        "study": study_text,
        "health": health_text,
        "meaning_up": meaning_up,
        "meaning_rev": meaning_rev,
    }


def _build_major_cards() -> list[TarotCard]:
    return [
        _build_card(name, image, meaning_up, meaning_rev, message)
        for name, image, meaning_up, meaning_rev, message in _MAJOR_ARCANA
    ]


def _build_minor_cards() -> list[TarotCard]:
    cards: list[TarotCard] = []
    for suit, suit_data in _SUITS.items():
        ko = suit_data["ko"]
        theme = suit_data["theme"]
        for rank, rank_ko, up_flow, rev_flow in _RANKS:
            name = f"{rank} of {suit}"
            image = f"{suit}_{rank}.jpg"
            meaning_up = f"{ko} {rank_ko}: {theme}에서 {up_flow}"
            meaning_rev = f"{ko} {rank_ko}: {rev_flow}"
            message = f"{theme}의 흐름을 현실에 맞게 조절해 보세요."
            cards.append(
                _build_card(
                    name,
                    image,
                    meaning_up,
                    meaning_rev,
                    message,
                    love=_minor_topic_text(
                        name, rank_ko, up_flow, rev_flow, suit_data, "연애"
                    ),
                    career=_minor_topic_text(
                        name, rank_ko, up_flow, rev_flow, suit_data, "직장"
                    ),
                    money=_minor_topic_text(
                        name, rank_ko, up_flow, rev_flow, suit_data, "금전"
                    ),
                    study=_minor_topic_text(
                        name, rank_ko, up_flow, rev_flow, suit_data, "공부"
                    ),
                    health=_minor_topic_text(
                        name, rank_ko, up_flow, rev_flow, suit_data, "건강"
                    ),
                )
            )
    return cards


tarot_cards: list[TarotCard] = _build_major_cards() + _build_minor_cards()
TAROT_CARDS: list[TarotCard] = tarot_cards


def draw_cards(count: int, *, seed: str) -> list[TarotCard]:
    rng = random.Random(seed)
    count = max(1, min(int(count), len(TAROT_CARDS)))
    return rng.sample(TAROT_CARDS, count)


def reading_signature(question: str, spread_name: str, cards: list[TarotCard]) -> str:
    names = ",".join(card["name"] for card in cards)
    return f"{spread_name}|{question.strip()}|{names}"
