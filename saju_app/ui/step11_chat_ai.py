"""STEP11 AI 챗봇 답변 생성 — OpenAI(선택) + 상담 지식 + 사주 엔진."""

from __future__ import annotations

import html
import os
from pathlib import Path
from typing import Any

import streamlit as st

from saju_app.ui import consulting_corpus as CC
from saju_app.ui import consulting_knowledge as K

try:
    from openai import OpenAI

    _OPENAI_SDK_AVAILABLE = True
except ImportError:
    OpenAI = None  # type: ignore[misc, assignment]
    _OPENAI_SDK_AVAILABLE = False

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CONSULTING_DIR = _PROJECT_ROOT / "data" / "saju_consulting"

_CHAT_DISCLAIMER = (
    "<i>※ 건강·법률·투자 등은 참고용이며 전문가 상담이 우선입니다.</i>"
)
_CHAT_BLOAT_MARKERS = (
    "학습 자료 발췌",
    "상담 지침에서",
    "참고 지침",
    "적용 원칙",
    "참고 시기",
    "보다 정밀한",
    "20년 경력",
    "사주까기</span>",
    "📎",
    "📚",
    "🔑",
    "📊",
    "📍",
)


def _openai_api_key() -> str:
    try:
        key = st.secrets.get("OPENAI_API_KEY", "")
        if key:
            return str(key).strip()
    except Exception:
        pass
    return str(os.getenv("OPENAI_API_KEY", "") or "").strip()


def _openai_client() -> Any | None:
    if not _OPENAI_SDK_AVAILABLE or OpenAI is None:
        return None
    key = _openai_api_key()
    if not key:
        return None
    return OpenAI(api_key=key)


def load_external_consulting_corpus() -> str:
    """``data/saju_consulting/`` 아래 txt·md 학습 자료를 읽습니다."""
    return CC.load_external_consulting_corpus()


def _step11_training_rules() -> dict[str, dict[str, object]]:
    """STEP11에 넣어 둔 마스터 지침(학습 자료) — 코드에 포함된 본문."""
    try:
        from saju.ui import step_11 as s11

        rules = getattr(s11, "SAJU_PRO_MASTER_RULES", None)
        if isinstance(rules, dict) and rules:
            return rules
    except Exception:
        pass
    return K.SAJU_PRO_MASTER_RULES


def _master_rules_brief() -> str:
    lines: list[str] = []
    for data in _step11_training_rules().values():
        if not isinstance(data, dict):
            continue
        title = str(data.get("title", ""))
        rules = data.get("rules", ())
        if title:
            lines.append(f"## {title}")
        if isinstance(rules, (list, tuple)):
            for rule in rules[:4]:
                lines.append(f"- {rule}")
    return "\n".join(lines)


def _matched_rules_for_question(user_text: str, *, limit: int = 4) -> list[str]:
    text = str(user_text or "")
    matched: list[str] = []
    for data in _step11_training_rules().values():
        if not isinstance(data, dict):
            continue
        keywords = tuple(data.get("keywords", ())) if isinstance(data, dict) else ()
        if not any(str(k) and str(k) in text for k in keywords):
            continue
        rules = data.get("rules", ())
        if isinstance(rules, (list, tuple)):
            matched.extend(str(rule) for rule in rules[:2])
    return matched[:limit]


def _corpus_snippet_for_question(user_text: str, *, max_len: int = 900) -> str:
    """구조화된 Q&A 코퍼스에서 질문에 맞는 발췌."""
    return CC.corpus_snippet_for_question(user_text, apply="step11", max_len=max_len)


def _extra_guidance_html(
    user_text: str,
    *,
    gender: str,
    daewoon_ten: str,
    strength: str,
    yongshin: str,
) -> str:
    """step_11.py 에 있는 스토리텔링·마스터 지침 HTML."""
    try:
        from saju.ui import step_11 as s11

        parts: list[str] = []
        story = s11._storytelling_guidance_html(
            user_text,
            gender=gender,
            daewoon_ten=daewoon_ten,
            strength=strength,
            yongshin=yongshin,
        )
        master = s11._master_guidance_html(
            user_text,
            strength=strength,
            yongshin=yongshin,
        )
        if story:
            parts.append(story)
        if master:
            parts.append(master)
        return "".join(parts)
    except Exception:
        return ""


def _timing_dict(engine: dict) -> dict[str, Any]:
    try:
        gt = engine.get("get_timing_flow")
        timing = gt() if callable(gt) else {}
        if not isinstance(timing, dict):
            timing = {}
    except Exception:
        timing = {}
    return {
        "phase": str(timing.get("phase", "보통")),
        "score": int(timing.get("score", 50)),
        "daewoon_index": int(timing.get("daewoon_index", 0)),
        "age": int(timing.get("age", 0)),
    }


def _daewoon_ten(daewoon_index: int) -> str:
    return ["인성", "비견", "식상", "재성", "관성"][int(daewoon_index) % 5]


def _corpus_direct_answer_html(user_text: str) -> str:
    """학습 Q&A 코퍼스에서 질문에 맞는 핵심 답(있을 때만)."""
    ut = str(user_text or "").strip()
    if not ut:
        return ""
    hits = CC.match_consulting(ut, apply="step11", limit=1)
    if not hits:
        return ""
    ans = str(hits[0].answer or "").strip()
    if len(ans) < 40:
        return ""
    return html.escape(ans).replace("\n", "<br>")[:720]


def _assemble_compact_chat_html(*, direct: str, tip: str) -> str:
    """챗봇: 핵심 답변 + 추가 해석 + 면책만."""
    tip_html = html.escape(tip).replace("\n", "<br>")
    return (
        f"⭐ <b>핵심 답변</b><br>{direct}<br><br>"
        f"📖 <b>추가 해석</b><br>{tip_html}<br><br>"
        f"{_CHAT_DISCLAIMER}"
    )


def _chat_reply_has_bloat(text: str) -> bool:
    low = str(text or "")
    return any(m in low for m in _CHAT_BLOAT_MARKERS)


def _sanitize_openai_chat_html(body: str) -> str:
    """OpenAI 출력에서 금지 섹션·인트로를 제거하고 핵심/추가 블록만 남깁니다."""
    raw = str(body or "").strip()
    if not raw or _chat_reply_has_bloat(raw):
        return ""
    if "핵심 답변" not in raw or "추가 해석" not in raw:
        return ""

    text = raw
    for marker in (
        "학습 자료",
        "상담 지침",
        "참고 지침",
        "적용 원칙",
        "참고 시기",
        "보다 정밀한",
    ):
        idx = text.find(marker)
        if idx > 0:
            text = text[:idx]

    if "※" not in text:
        text = f"{text.rstrip()}<br><br>{_CHAT_DISCLAIMER}"
    return text.strip()


def _direct_answer_paragraph(
    user_text: str,
    *,
    topic: str,
    yongshin: str,
    strength: str,
    phase: str,
    score: int,
) -> str:
    """질문에 바로 답하는 첫 문단(템플릿 반복 최소화)."""
    ut = str(user_text or "")
    ys = str(yongshin or "균형")

    corpus_direct = _corpus_direct_answer_html(ut)
    if corpus_direct:
        return corpus_direct

    if topic == "health":
        if any(k in ut for k in ("부모", "어머니", "아버지", "모시", "요양", "병원", "어디")):
            return (
                "부모님 건강과 **어디로 모실지**는 사주만으로 병명·병원을 정하지 않습니다. "
                "우선 주치의·응급 여부를 확인하고, **전문 진료 접근성·간병 동선·수면·식사 환경**을 "
                "기준으로 자택 간병·요양·병원 인근 거주를 비교하세요. "
                f"운의 흐름상 지금은 {phase.replace('🌱 ', '').replace('🚀 ', '').replace('🔥 ', '').replace('⚖️ ', '').replace('🧘 ', '')} "
                f"(체감 {score}점)이라 큰 환경 변화는 서류·비용·가족 돌봄 여력을 먼저 맞추는 편이 안전합니다. "
                f"생활 환경은 용신 <b>{html.escape(ys)}</b> 기운이 편한 쪽(조용함·온도·동선)을 우선하세요."
            )
        return (
            "건강·치료·수술 관련 질문은 **의료진 판단이 최우선**입니다. "
            "사주는 컨디션·생활 리듬 참고용으로만 보시고, 증상이 있으면 검진·상담을 먼저 받으세요. "
            f"지금 시기는 {html.escape(phase)} 흐름으로, 무리한 결정보다 회복·루틴 정리가 먼저입니다."
        )

    if topic == "love":
        return (
            "연애·결혼·인연 질문은 관성·재성 흐름과 함께 **상대의 생활 태도·약속·스트레스 반응**을 "
            "같이 보는 것이 핵심입니다. 감정만으로 단정하기보다 2~3주 관찰 후 말과 행동의 일치를 확인하세요."
        )
    if topic == "wealth":
        return (
            "재물·사업 질문은 단기 수익보다 **현금 흐름·계약·지인 돈거래**를 먼저 점검하는 것이 중요합니다. "
            "기회가 보여도 검증 없는 투자·동업은 피하는 편이 낫습니다."
        )
    if topic == "job":
        return (
            "직장·이직 질문은 감정적 퇴사보다 **다음 조건·생활비·역할**을 먼저 적어 보는 것이 좋습니다. "
            "이직 타이밍은 면접·제안·평가가 동시에 움직일 때 체감이 큽니다."
        )
    if topic == "move":
        return (
            "이사·거처는 **계약·비용·병원·직장 접근성·수면 환경**을 함께 보세요. "
            "운에서 이동수가 강해도 서류와 일정을 먼저 고정하는 편이 후회가 적습니다."
        )
    if topic == "study":
        return (
            "공부·시험은 범위 확장보다 **오답·핵심 개념 반복**과 시간표 고정이 체감에 더 잘 붙는 시기입니다."
        )

    return (
        "질문하신 내용은 십성·용신·시기를 함께 봐야 깊이가 생깁니다. "
        f"지금은 용신 <b>{html.escape(ys)}</b>이 살아나는 환경·사람·시간대를 고르는지가 기준입니다."
    )


def try_openai_chat_reply(
    *,
    user_text: str,
    engine: dict,
    day_stem: str,
    day_el: str,
    yongshin: str,
    strength: str,
    gender: str,
) -> str | None:
    """OpenAI API가 있으면 질문 맞춤 HTML 답변. 없으면 None."""
    client = _openai_client()
    if client is None:
        return None

    timing = _timing_dict(engine)
    daewoon_ten = _daewoon_ten(timing["daewoon_index"])
    gapja = st.session_state.get("u_gapja")
    gapja_txt = ""
    if isinstance(gapja, (list, tuple)):
        gapja_txt = " / ".join(str(x) for x in gapja[:4])

    corpus = load_external_consulting_corpus()
    rules = _master_rules_brief()
    tip = K.consulting_tip(
        user_text,
        strength=strength,
        yongshin=yongshin,
        daewoon_ten=daewoon_ten,
        gender=gender,
    )

    system = K.chatbot_system_prompt(html_output=True)
    user_prompt = f"""
고객 질문:
{user_text.strip()}

【최우선】 고객 사주·시기 (아래를 먼저 반영한 뒤 질문에 답하세요):
- 성별: {gender}
- 사주 간지(년·월·일·시): {gapja_txt or "미입력 — 일간·용신 위주로 참고"}
- 일간: {day_stem}({day_el})
- 신강약: {strength}
- 용신: {yongshin}
- 현재 대운·시기 흐름: {timing["phase"]} (체감 {timing["score"]}점, 나이 참고 {timing.get("age", 0)}세)
- 대운 십성 축: {daewoon_ten}

내부 상담 메모(질문 주제에 맞게 반영):
{tip}

마스터 지침(고전 원리 요약):
{rules}

추가 학습 자료(전체):
{corpus or "(data/saju_consulting 폴더에 학습 txt·md 없음)"}

질문 매칭 현장 Q&A 발췌(우선 반영):
{corpus_snip or "(매칭 Q&A 없음)"}

작성 형식:
1) 질문을 한 줄로 짚기
2) 위 사주·대운·시기를 근거로 한 핵심 2~3문장 (가능성·경향 표현, 질문 주제에만 집중)
3) 지금 시기({timing["phase"]})에서의 행동 조언 2가지
4) 주의할 점 1가지 (공포 조장 없이)
5) 마지막 한 줄 면책(참고용)
분량 220~380자, 한국어, 따뜻하고 현실적인 사주까기 톤.
불릿은 최대 3개, 문단은 짧게.
""".strip()

    try:
        response = client.chat.completions.create(
            model=os.getenv("SAJU_CHAT_MODEL", "gpt-4.1-mini"),
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.72,
        )
        body = str(response.choices[0].message.content or "").strip()
        if not body:
            return None
        if "<" not in body:
            body = html.escape(body).replace("\n", "<br>")
        cleaned = _sanitize_openai_chat_html(body)
        return cleaned or None
    except Exception:
        return None


def generate_rule_based_chat_html(
    *,
    user_text: str,
    engine: dict,
    day_stem: str,
    day_el: str,
    yongshin: str,
    strength: str,
    gender: str,
) -> str:
    """OpenAI 없을 때: STEP11 학습 지침 + 질문 주제별 맞춤."""
    ut = str(user_text or "").strip()
    timing = _timing_dict(engine)
    phase = timing["phase"]
    score = timing["score"]
    daewoon_ten = _daewoon_ten(timing["daewoon_index"])
    topic = K.normalize_topic(ut)

    direct = _direct_answer_paragraph(
        ut,
        topic=topic,
        yongshin=yongshin,
        strength=strength,
        phase=phase,
        score=score,
    )

    tip = K.consulting_tip(
        ut,
        strength=strength,
        yongshin=yongshin,
        daewoon_ten=daewoon_ten,
        gender=gender,
        for_chat=True,
    )

    return _assemble_compact_chat_html(direct=direct, tip=tip)


def generate_chat_reply_html(
    *,
    user_text: str,
    engine: dict,
    day_stem: str,
    day_el: str,
    yongshin: str,
    strength: str,
    gender: str,
) -> str:
    """OpenAI 우선(간결 형식), 실패 시 STEP11 학습 지침 + 상담 지식."""
    compact = generate_rule_based_chat_html(
        user_text=user_text,
        engine=engine,
        day_stem=day_stem,
        day_el=day_el,
        yongshin=yongshin,
        strength=strength,
        gender=gender,
    )
    ai = try_openai_chat_reply(
        user_text=user_text,
        engine=engine,
        day_stem=day_stem,
        day_el=day_el,
        yongshin=yongshin,
        strength=strength,
        gender=gender,
    )
    if ai and not _chat_reply_has_bloat(ai):
        return ai
    return compact
