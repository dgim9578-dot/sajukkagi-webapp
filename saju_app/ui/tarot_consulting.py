"""타로 상담 로직 — 질문·주제·위치·카드·방향에 따라 해석을 분기합니다."""

from __future__ import annotations

import hashlib
import re
from typing import Any

# step_08 과 동일한 주제 키 (한글 라벨)
_TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "금전": (
        "돈",
        "금전",
        "재물",
        "수입",
        "지출",
        "투자",
        "사업",
        "빚",
        "월급",
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
        "체결",
        "납품",
        "수주",
        "견적",
    ),
    "직장": ("직장", "이직", "회사", "상사", "퇴사", "승진", "면접", "일", "커리어", "취업"),
    "공부": ("공부", "시험", "합격", "학교", "성적", "자격증"),
    "건강": ("건강", "몸", "피로", "스트레스", "수면", "아프", "병", "컨디션"),
    "연애": ("연애", "썸", "좋아", "사랑", "남친", "여친", "애인", "소개팅", "고백", "데이트", "결혼"),
    "재회": ("재회", "헤어", "전남", "전여", "복합", "다시 만", "연락 없", "차단", "이별"),
    "속마음": ("속마음", "진심", "어떻게 느끼", "나를 어떻게", "좋아하", "마음이"),
}

_TOPIC_MATCH_ORDER: tuple[str, ...] = (
    "금전",
    "직장",
    "공부",
    "건강",
    "연애",
    "재회",
    "속마음",
)

_TOPIC_CARD_FIELD: dict[str, str] = {
    "연애": "love",
    "재회": "reunion",
    "속마음": "feeling",
    "직장": "career",
    "금전": "money",
    "공부": "study",
    "건강": "health",
    "일반": "advice",
}

_POSITION_HOOKS: dict[str, dict[str, str]] = {
    "1카드": {
        "오늘의 핵심": "오늘 이 질문의 핵심 에너지는",
    },
    "3카드": {
        "현재": "지금 이 질문이 놓인 자리(현재)는",
        "흐름": "앞으로 펼쳐질 흐름은",
        "조언": "지금 선택·행동에 대한 조언은",
    },
    "5카드": {
        "현재": "지금 상황의 중심은",
        "막힌 부분": "막히거나 불안한 지점은",
        "숨은 도움": "눈에 덜 보이지만 도움이 되는 힘은",
        "가까운 흐름": "가까운 시일의 흐름은",
        "실천 조언": "실제로 움직이기 좋은 방향은",
    },
}

_TOPIC_CLOSERS: dict[str, tuple[str, ...]] = {
    "연애": (
        "감정을 확인한 뒤, 말의 속도를 상대 리듬에 맞추면 관계가 덜 흔들립니다.",
        "확답을 재촉하기보다 신뢰가 쌓이는 행동(약속·시간·말투)을 먼저 맞춰 보세요.",
        "끌림만으로 결론 내리지 말고, 생활 리듬이 맞는지 한 번 더 보세요.",
    ),
    "재회": (
        "연락 타이밍보다, 다시 만날 때 바뀔 약속·거리·말투를 먼저 정하는 편이 낫습니다.",
        "그리움이 크면 같은 패턴이 반복되기 쉬우니, 연락 전에 내가 바꿀 한 가지를 정하세요.",
        "상대 반응을 시험하듯 몰아붙이기보다, 짧고 부담 없는 접점부터 여세요.",
    ),
    "속마음": (
        "상대의 말 한마디보다, 연락 빈도·약속 지키는 방식·거리 조절을 함께 보세요.",
        "확인이 필요하면 직접 묻되, 단정·비내 대신 관찰한 사실을 말로 옮기세요.",
        "마음을 추측만 하지 말고, 작은 질문 하나로 방향을 확인해 보세요.",
    ),
    "직장": (
        "감정적 퇴사·이직보다 제안 조건·역할·성과 기록을 먼저 정리하세요.",
        "말로만 밀기보다 문서·수치·포트폴리오로 근거를 남기면 흐름이 열립니다.",
        "상사·조직과의 마찰은 '누가 틀렸다'보다 업무 기준을 맞추는 쪽이 유리합니다.",
    ),
    "금전": (
        "큰 승부보다 현금 흐름·고정 지출·비상금을 먼저 점검하세요.",
        "충동 지출·지인 돈거래는 한 번 더 멈추고, 수입 구조를 단순화하세요.",
        "기회가 보여도 계약·기한·손실 한도를 숫자로 적어 두고 움직이세요.",
    ),
    "공부": (
        "계획만 늘리기보다 문제 풀이·요약·복습 비중을 오늘부터 조정하세요.",
        "집중이 흐트러지면 환경(시간·장소·폰)을 먼저 바꾸는 편이 낫습니다.",
        "시험·면접은 말보다 연습 기록·모의·피드백 루프가 점수를 만듭니다.",
    ),
    "건강": (
        "큰 결정보다 수면·식사·이동량부터 회복 루틴을 잡으세요.",
        "몸 신호를 무시한 채 밀어붙이면 판단도 흐려지니, 휴식을 일정에 넣으세요.",
        "증상·치료는 반드시 의료진 상담을 우선하고, 사주는 생활 리듬 참고로만 보세요.",
    ),
    "일반": (
        "지금은 한 가지 선택에 모든 것을 걸기보다, 작은 실험으로 방향을 확인하세요.",
        "감정이 뜨거울수록 결론을 미루고, 사실·일정·비용을 먼저 적어 보세요.",
        "주변 의견보다 내가 유지할 수 있는 루틴이 무엇인지부터 정리하세요.",
    ),
}


def infer_tarot_topic(question: str) -> str:
    """질문에서 타로 상담 주제(연애·재회·직장 등)를 추론합니다."""
    text = str(question or "").strip().lower()
    if not text:
        return "일반"
    best_topic = "일반"
    best_score = 0
    for topic in _TOPIC_MATCH_ORDER:
        words = _TOPIC_KEYWORDS.get(topic, ())
        score = sum(1 for word in words if word in text)
        if score > best_score:
            best_score = score
            best_topic = topic
    return best_topic


def _question_intent(question: str) -> str:
    q = str(question or "").strip()
    if not q:
        return "explore"
    if any(w in q for w in ("될까", "할까", "해도", "가능", "괜찮", "맞을까", "되나")):
        return "decision"
    if any(w in q for w in ("언제", "시기", "타이밍", "때")):
        return "timing"
    if any(w in q for w in ("왜", "이유", "원인")):
        return "why"
    if any(w in q for w in ("어떻게", "방법", "해야")):
        return "how"
    return "explore"


def _pick_variant(options: tuple[str, ...], seed: str) -> str:
    if not options:
        return ""
    idx = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16) % len(options)
    return options[idx]


def _topic_line(card: dict[str, Any], topic: str, *, reversed: bool) -> str:
    """질문 주제 1개에 맞는 해석만 (전 카테고리 묶음 message 필드는 사용하지 않음)."""
    field = _TOPIC_CARD_FIELD.get(topic, "advice")
    line = str(card.get(field) or "").strip()
    if not line:
        line = card_energy_text(card, reversed=reversed)
    elif reversed:
        rev = str(card.get("meaning_rev") or "").strip()
        if rev and rev not in line:
            line = f"{line} (역방향에서는 {rev}의 기운이 강조됩니다.)"
    return line


def card_energy_text(card: dict[str, Any], *, reversed: bool) -> str:
    if reversed:
        return (
            str(card.get("meaning_rev") or "").strip()
            or str(card.get("meaning_up") or "").strip()
            or str(card.get("keyword") or "").strip()
            or "역방향 에너지를 참고해 주세요."
        )
    return (
        str(card.get("meaning_up") or "").strip()
        or str(card.get("keyword") or "").strip()
        or "카드의 기본 흐름을 참고해 주세요."
    )


def interpret_card_for_question(
    *,
    card: dict[str, Any],
    card_direction: str,
    position: str,
    spread: str,
    question: str,
    topic: str | None = None,
) -> str:
    """한 장의 카드를 질문·주제·위치에 맞게 해석한 본문(마크다운)."""
    topic_key = topic or infer_tarot_topic(question)
    reversed = str(card_direction or "").strip() == "역방향"
    hooks = _POSITION_HOOKS.get(spread, _POSITION_HOOKS["3카드"])
    hook = hooks.get(position, f"{position} 자리에서는")
    topic_line = _topic_line(card, topic_key, reversed=reversed)
    intent = _question_intent(question)
    q_short = str(question or "").strip()
    if len(q_short) > 72:
        q_short = q_short[:69] + "…"

    intent_line = ""
    if intent == "decision" and q_short:
        intent_line = f"**선택·가능성** 관점에서 보면, "
    elif intent == "timing" and q_short:
        intent_line = f"**시기·속도** 관점에서 보면, "
    elif intent == "why" and q_short:
        intent_line = f"**원인·마음** 관점에서 보면, "
    elif intent == "how" and q_short:
        intent_line = f"**방법·실천** 관점에서 보면, "
    elif q_short:
        intent_line = f"질문「{q_short}」에 대해 "

    parts = [
        f"**{position}** · {card.get('name', '카드')} ({card_direction})",
        f"{hook}, {intent_line}{topic_line}",
    ]
    advice = str(card.get("advice") or "").strip()
    if advice:
        parts.append(f"**한 줄 조언**: {advice}")
    return "\n\n".join(p for p in parts if p)


def spread_synthesis(
    *,
    question: str,
    spread: str,
    positions: list[str],
    cards: list[dict[str, Any]],
    directions: list[str],
    topic: str | None = None,
) -> str:
    """스프레드 전체를 질문에 맞게 엮은 종합 해석(비-AI)."""
    topic_key = topic or infer_tarot_topic(question)
    q = str(question or "").strip()
    blocks: list[str] = []

    if q:
        blocks.append(f"**질문**: {q}")
    blocks.append(f"**상담 주제**: {topic_key} · **스프레드**: {spread}")

    card_summaries: list[str] = []
    for idx, card in enumerate(cards):
        if not isinstance(card, dict):
            continue
        pos = positions[idx] if idx < len(positions) else f"{idx + 1}번째"
        direction = directions[idx] if idx < len(directions) else "정방향"
        rev = direction == "역방향"
        tline = _topic_line(card, topic_key, reversed=rev)
        card_summaries.append(f"- **{pos}** ({card.get('name')}, {direction}): {tline}")

    if card_summaries:
        blocks.append("**카드 흐름 요약**\n" + "\n".join(card_summaries))

    seed = "|".join(
        [
            q,
            topic_key,
            spread,
            *(str(c.get("name", "")) for c in cards if isinstance(c, dict)),
            *(str(d) for d in directions),
        ]
    )
    closer = _pick_variant(_TOPIC_CLOSERS.get(topic_key, _TOPIC_CLOSERS["일반"]), seed)
    blocks.append(f"**종합 정리**: {closer}")

    if len(cards) >= 2:
        first = cards[0] if isinstance(cards[0], dict) else {}
        last = cards[-1] if isinstance(cards[-1], dict) else {}
        blocks.append(
            f"**시작→마무리**: {first.get('name', '?')}에서 {last.get('name', '?')}로 이어지며, "
            f"처음에 드러난 이슈를 마지막 카드의 조언으로 정리하는 흐름입니다."
        )

    return "\n\n".join(blocks)


def practical_advice_for_reading(
    *,
    question: str,
    cards: list[dict[str, Any]],
    directions: list[str],
    topic: str | None = None,
) -> str:
    """질문·카드 조합 기반 실천 조언(랜덤이 아닌 시드 분기)."""
    topic_key = topic or infer_tarot_topic(question)
    last = cards[-1] if cards and isinstance(cards[-1], dict) else {}
    direction = directions[-1] if directions else "정방향"
    rev = direction == "역방향"
    card_advice = str(last.get("advice") or "").strip()
    topic_line = _topic_line(last, topic_key, reversed=rev)
    seed = f"{question}|{topic_key}|{last.get('name', '')}|{direction}"
    closer = _pick_variant(_TOPIC_CLOSERS.get(topic_key, _TOPIC_CLOSERS["일반"]), seed + "|closer")

    parts = []
    if card_advice:
        parts.append(f"**마지막 카드 조언**: {card_advice}")
    if topic_line:
        parts.append(f"**{topic_key} 관점**: {topic_line}")
    parts.append(f"**실천 포인트**: {closer}")
    return "\n\n".join(parts)


def tarot_saju_bridge_tip(
    *,
    question: str,
    consulting_tip: str,
    topic: str | None = None,
) -> str:
    """사주 참고 문단을 타로 질문에 맞게 짧게 연결."""
    topic_key = topic or infer_tarot_topic(question)
    tip = str(consulting_tip or "").strip()
    if not tip:
        return "사주 정보가 연결되면, 타로 해석과 함께 생활·시기 참고를 덧붙일 수 있습니다."
    # 동일 사주 문단이 반복되지 않도록 질문 시드로 앞부분만 가변 길이
    seed = hashlib.sha256(f"{question}|{topic_key}".encode("utf-8")).hexdigest()
    max_len = 280 + (int(seed[:2], 16) % 120)
    if len(tip) > max_len:
        cut = tip[:max_len].rsplit(" ", 1)[0]
        tip = (cut or tip[:max_len]).rstrip() + "…"
    return (
        f"**{topic_key} 질문 + 사주 참고**: {tip}\n\n"
        f"(타로는 카드·위치 중심, 위 내용은 사주 흐름 보조입니다.)"
    )


def reading_cache_key(question: str, spread: str, signature: str) -> str:
    raw = f"{question.strip()}|{spread}|{signature}"
    return re.sub(r"[^a-zA-Z0-9]", "", hashlib.sha256(raw.encode("utf-8")).hexdigest())[:24]
