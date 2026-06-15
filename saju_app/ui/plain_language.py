"""사주 해석 — 젊은 세대도 읽기 쉬운 쉬운 말 변환 레이어.

전문 용어는 가능한 한 '쉬운 설명(원래 용어)' 형태로 바꿉니다.
엔진·계산 로직은 건드리지 않고, 사용자에게 보이는 문장만 후처리합니다.
"""

from __future__ import annotations

import re
from dataclasses import replace

from saju_app.ui.interpretation_types import StructuredInterpretation

_EL_KO = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}

# 긴 구문부터 치환 (짧은 키워드 치환 전에)
_PHRASES: tuple[tuple[str, str], ...] = (
    ("천간 십성", "나의 역할 유형(십성)"),
    ("지지 충(衝)", "관계·환경이 크게 바뀌는 신호(충)"),
    ("지지 합(合)", "사람·환경이 잘 맞아붙는 신호(합)"),
    ("대운·세운", "10년·1년 운세 흐름(대운·세운)"),
    ("대운·세운 연결", "10년·1년 운세 연결"),
    ("십성 패턴", "성격·일하는 방식 패턴(십성)"),
    ("원국 지지", "타고난 기본 성향(원국)"),
    ("원국 체질", "타고난 체질(원국)"),
    ("원국 건강", "타고난 건강 포인트(원국)"),
    ("일간의 힘", "나 자신의 기본 에너지"),
    ("일간 대비", "나(일간) 기준으로"),
    ("입춘 기준 세운", "올해 기준 1년 운(세운)"),
    ("10년 대운", "10년짜리 큰 흐름(대운)"),
    ("현재 대운", "지금 10년 흐름(대운)"),
    ("컨디션 관리 주의도", "몸·마음 관리 필요도"),
    ("체감 운", "실제로 느끼는 운"),
    ("조후 보완", "계절·환경 맞춤 보완(조후)"),
    ("월지·조후", "태어난 달·계절 기운(조후)"),
    ("지장간", "숨은 성향(지장간)"),
    ("비겁·인성", "나를 돕는 기운(비겁·인성)"),
    ("재성·관성", "돈·일·책임 기운(재성·관성)"),
    ("식상(食傷)", "표현·창의 기운(식상)"),
    ("인성(印星)", "학습·지원 기운(인성)"),
    ("비겁(比劫)", "나와 비슷한·경쟁 기운(비겁)"),
    ("관성(官)", "책임·조직·규칙 기운(관성)"),
    ("재성(財)", "돈·현실·기회 기운(재성)"),
    ("설기·제어", "에너지를 빼고 조절"),
    ("설기·활용", "에너지를 밖으로 쓰기"),
    ("설기·분산", "에너지를 나눠 쓰기"),
    ("보강·회복", "에너지를 채우고 회복"),
    ("균형축", "균형의 기준"),
    ("균형형 구조", "극단 없이 중간형"),
    ("판단 필요", "아직 더 봐야 함"),
    ("합·충", "잘 맞음·부딪힘"),
    ("합 六合", "잘 맞는 합(六合)"),
    ("충 沖", "변화·충돌(沖)"),
)

# 단어 단위 — 괄호 안에 원래 용어 유지
_TERMS: tuple[tuple[str, str], ...] = (
    ("신강약", "내 에너지 강약(신강약)"),
    ("신강", "에너지가 강한 편(신강)"),
    ("신약", "에너지가 약한 편(신약)"),
    ("중화", "중간·균형형(중화)"),
    ("용신", "내게 도움 되는 핵심 기운(용신)"),
    ("희신", "도움 되는 보조 기운(희신)"),
    ("기신", "조심할 기운(기신)"),
    ("구신", "부담 되는 기운(구신)"),
    ("십성", "10가지 역할 유형(십성)"),
    ("비견", "나와 같은 편(비견)"),
    ("겁재", "경쟁·협력 편(겁재)"),
    ("식신", "편안한 표현(식신)"),
    ("상관", "날카로운 표현·아이디어(상관)"),
    ("정재", "안정적인 돈·수입(정재)"),
    ("편재", "유동적인 돈·사업(편재)"),
    ("정관", "규칙·책임·승진(정관)"),
    ("편관", "압박·도전·경쟁(편관)"),
    ("정인", "공부·자격·보호(정인)"),
    ("편인", "직관·독학·예술(편인)"),
    ("대운", "10년 큰 흐름(대운)"),
    ("세운", "1년 흐름(세운)"),
    ("일주", "나의 핵심 성격(일주)"),
    ("년주", "어릴 때·가족 배경(년주)"),
    ("월주", "사회생활·직장 기질(월주)"),
    ("시주", "말년·저녁·숨은 성향(시주)"),
    ("일간", "나 자신(일간)"),
    ("천간", "겉으로 드러나는 기운(천간)"),
    ("지지", "속·환경·밑바닥(지지)"),
    ("오행", "다섯 기운(목·화·토·금·수)"),
    ("조후", "태어난 계절·환경(조후)"),
    ("역마", "이동·변화(역마)"),
    ("도화", "매력·연애(도화)"),
    ("화개", "예술·고독(화개)"),
    ("원국", "타고난 팔자(원국)"),
    ("일진", "오늘의 기운(일진)"),
)

_TEN_GROUP: dict[str, str] = {
    "비겁": "나·동료 쪽",
    "식상": "표현·창의 쪽",
    "재성": "돈·현실 쪽",
    "관성": "일·책임 쪽",
    "인성": "공부·지원 쪽",
}

_SECTION_HEADERS: tuple[tuple[str, str], ...] = (
    ("【신강약 ", "【내 에너지 강약("),
    ("【용신 ", "【핵심 보조 기운("),
    ("【천간 십성】", "【역할 유형(십성)】"),
    ("【십성 패턴】", "【성격·일 패턴(십성)】"),
    ("【시주 ", "【말년·저녁 성향(시주 "),
    ("【대운·세운 연결】", "【10년·1년 운 연결】"),
    ("【지지 충", "【변화 신호(충"),
    ("【지지 합", "【협력 신호(합"),
    (" 일주 · ", " 일주(나) · "),
)


def _el_readable(el: str) -> str:
    e = str(el or "").strip()
    if e in _EL_KO:
        return f"{_EL_KO[e]}({e})"
    return e


def to_plain_text(text: str, *, level: str = "youth") -> str:
    """전문 용어를 쉬운 말로 풀어 씁니다."""
    if level != "youth" or not str(text or "").strip():
        return str(text or "")

    out = str(text)

    for src, dst in _SECTION_HEADERS:
        out = out.replace(src, dst)

    for src, dst in _PHRASES:
        out = out.replace(src, dst)

    for src, dst in _TERMS:
        if src in out:
            out = out.replace(src, dst)

    for han, ko in _EL_KO.items():
        # 단독 한자 오행 → 목(木)
        out = re.sub(
            rf"(?<![가-힣\(]){re.escape(han)}(?![\)가-힣])",
            f"{ko}({han})",
            out,
        )

    for grp, plain in _TEN_GROUP.items():
        out = out.replace(f"({grp})", f"({plain})")
        out = out.replace(f"· {grp}", f"· {plain}")

    # 남은 어려운 표현 완화
    out = out.replace("드러납니다", "드러납니다")
    out = out.replace("읽혀", "보여")
    out = out.replace("읽히는", "보이는")
    out = out.replace("읽는", "보는")
    out = re.sub(r"\s{2,}", " ", out)
    return out.strip()


def to_plain_tag(tag: str) -> str:
    t = to_plain_text(str(tag or ""))
    t = t.replace("우세 ", "강한 기운 ")
    t = t.replace("보완 ", "채우면 좋은 ")
    return t


def to_plain_structured(data: StructuredInterpretation) -> StructuredInterpretation:
    return replace(
        data,
        one_liner=to_plain_text(data.one_liner),
        tags=[to_plain_tag(t) for t in data.tags],
        detail_paragraphs=[to_plain_text(p) for p in data.detail_paragraphs],
        advice=[(icon, to_plain_text(body)) for icon, body in data.advice],
        harmony_caption=to_plain_text(data.harmony_caption),
    )


def plain_caption_line() -> str:
    return "💬 **쉬운 말 해석** — 괄호 안은 원래 사주 용어예요."


def simplify_jukchunsu_advice(strength: str, yongshin: str) -> str:
    ys = _el_readable(yongshin) if yongshin in _EL_KO else yongshin
    if str(strength) == "신강":
        return (
            f"에너지가 강한 편(신강)이라, 돈·일·책임(재성·관성)을 잘 쓰고 "
            f"핵심 보조 기운 {ys}으로 과한 힘을 조절하면 좋아요."
        )
    if str(strength) == "신약":
        return (
            f"에너지가 약한 편(신약)이라, 나를 돕는 기운(비겁·인성)과 "
            f"핵심 보조 기운 {ys}으로 컨디션을 먼저 채우는 게 중요해요."
        )
    return (
        f"극단 없이 중간형(중화)이라, 핵심 보조 기운 {ys}을 기준으로 "
        f"무리하지 않게 리듬을 맞추면 안정적이에요."
    )
