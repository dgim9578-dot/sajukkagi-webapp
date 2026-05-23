"""STEP 8 - AI 타로 점 (질문 중심 · 클릭으로 카드 공개)."""

from __future__ import annotations

from datetime import datetime
import html
import hashlib
import math
import os
import random
import re
import time

from PIL import Image, ImageDraw, ImageFont
import streamlit as st

try:
    from openai import OpenAI

    _OPENAI_SDK_AVAILABLE = True
except ImportError:
    OpenAI = None  # type: ignore[misc, assignment]
    _OPENAI_SDK_AVAILABLE = False

from saju_app.ui import consulting_knowledge as K
from saju_app.ui import components as M
from saju_app.ui import tarot_consulting as T
from saju_app.ui.execution import rerun_full_app
from tarot_assets import resolve_card_back_path, resolve_card_image_path
from tarot_data import SPREADS, TAROT_CARDS, draw_cards, reading_signature


def _openai_api_key() -> str:
    try:
        key = st.secrets.get("OPENAI_API_KEY", "")
        if key:
            return str(key)
    except Exception:
        pass
    return os.getenv("OPENAI_API_KEY", "")


def _openai_client() -> OpenAI | None:
    if not _OPENAI_SDK_AVAILABLE or OpenAI is None:
        return None
    key = _openai_api_key()
    if not key:
        return None
    return OpenAI(api_key=key)


def _tarot_font(size: int) -> ImageFont.ImageFont:
    for path in (
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/malgunbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _draw_center_text(
    draw: ImageDraw.ImageDraw,
    y: int,
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    *,
    width: int = 600,
) -> None:
    box = draw.textbbox((0, 0), text, font=font)
    draw.text(((width - (box[2] - box[0])) / 2, y), text, font=font, fill=fill)


def _generated_tarot_image(card: dict[str, str], card_direction: str = "정방향") -> Image.Image:
    """실제 카드 이미지 파일이 없을 때 쓰는 Blue Night 스타일 대체 카드."""
    width, height = 600, 1000
    img = Image.new("RGB", (width, height), (8, 12, 32))
    draw = ImageDraw.Draw(img)
    name = str(card.get("name") or "Tarot")
    seed = int(hashlib.sha256(name.encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed)

    for y in range(height):
        t = y / height
        draw.line((0, y, width, y), fill=(8 + int(16 * t), 12 + int(10 * t), 32 + int(42 * t)))

    gold = (214, 169, 92)
    pale = (240, 222, 178)
    violet = (99, 78, 145)

    for _ in range(90):
        x = rng.randint(35, width - 35)
        y = rng.randint(35, height - 35)
        r = rng.randint(1, 4)
        draw.line((x - r, y, x + r, y), fill=(210, 180, 120), width=1)
        draw.line((x, y - r, x, y + r), fill=(210, 180, 120), width=1)

    draw.rounded_rectangle((34, 28, width - 34, height - 28), radius=28, outline=gold, width=4)
    draw.rounded_rectangle((58, 58, width - 58, height - 58), radius=22, outline=(90, 72, 122), width=2)

    cx, cy = width // 2, 420
    if "Cups" in name:
        draw.ellipse((cx - 90, cy - 70, cx + 90, cy + 95), outline=gold, width=6)
        draw.rectangle((cx - 38, cy + 72, cx + 38, cy + 160), outline=gold, width=6)
    elif "Swords" in name:
        draw.line((cx, cy - 190, cx, cy + 170), fill=pale, width=9)
        draw.polygon([(cx, cy - 230), (cx - 30, cy - 172), (cx + 30, cy - 172)], fill=gold)
        draw.line((cx - 105, cy + 70, cx + 105, cy + 70), fill=gold, width=8)
    elif "Pentacles" in name:
        pts = []
        for i in range(5):
            a = -1.5708 + i * 6.28318 / 5
            pts.append((cx + math.cos(a) * 125, cy + math.sin(a) * 125))
        draw.line([pts[i] for i in [0, 2, 4, 1, 3, 0]], fill=gold, width=5)
        draw.ellipse((cx - 150, cy - 150, cx + 150, cy + 150), outline=pale, width=4)
    elif "Wands" in name:
        draw.line((cx - 70, cy + 180, cx + 70, cy - 185), fill=gold, width=13)
        for _ in range(9):
            x = rng.randint(cx - 95, cx + 95)
            y = rng.randint(cy - 160, cy + 130)
            draw.ellipse((x, y, x + 14, y + 14), fill=violet)
    elif name in {"The Moon", "The High Priestess"}:
        draw.pieslice((cx - 130, cy - 150, cx + 130, cy + 110), 70, 290, fill=pale)
        draw.pieslice((cx - 70, cy - 150, cx + 190, cy + 110), 70, 290, fill=(10, 16, 42))
    elif name in {"The Sun", "The Star"}:
        for i in range(16):
            a = i * 3.14159 / 8
            draw.line((cx, cy, cx + math.cos(a) * 170, cy + math.sin(a) * 170), fill=gold, width=3)
        draw.ellipse((cx - 78, cy - 78, cx + 78, cy + 78), fill=pale)
    else:
        draw.ellipse((cx - 125, cy - 125, cx + 125, cy + 125), outline=gold, width=5)
        draw.arc((cx - 175, cy - 175, cx + 175, cy + 175), 205, 340, fill=pale, width=5)
        draw.line((cx, cy - 150, cx, cy + 150), fill=violet, width=5)

    title_font = _tarot_font(34)
    sub_font = _tarot_font(22)
    small_font = _tarot_font(18)
    draw.rectangle((72, 735, width - 72, 905), fill=(12, 18, 46), outline=gold, width=2)
    _draw_center_text(draw, 762, name.upper(), title_font, pale, width=width)
    _draw_center_text(draw, 825, "Mystic Flow Tarot", sub_font, gold, width=width)
    _draw_center_text(draw, 875, str(card.get("keyword") or "Blue Night"), small_font, (178, 145, 94), width=width)

    if card_direction == "역방향":
        return img.rotate(180)
    return img


_QUESTION_KEY = "step8_tarot_question"
_SPREAD_KEY = "step8_tarot_spread"
_READING_KEY = "step8_tarot_reading"
_SIGNATURE_KEY = "step8_tarot_signature"

loading_messages = [
    "✨ 당신의 감정을 읽는 중...",
    "🌙 숨겨진 흐름을 확인하는 중...",
    "🔮 카드의 에너지가 연결되고 있어요...",
]

daily_messages = [
    "🌙 오늘은 감정보다 직감을 믿어보세요.",
    "✨ 새로운 흐름이 가까워지고 있어요.",
    "🃏 예상하지 못한 만남이 들어올 수 있어요.",
]

def _spread_count(spread_name: str) -> int:
    spread = SPREADS.get(spread_name, SPREADS["3카드"])
    try:
        return max(1, min(5, int(spread.get("count", 3))))
    except Exception:
        return 3


def _spread_positions(spread_name: str) -> list[str]:
    spread = SPREADS.get(spread_name, SPREADS["3카드"])
    positions = spread.get("positions")
    if isinstance(positions, (list, tuple)):
        return [str(p) for p in positions]
    return ["현재", "흐름", "조언"]


def _render_card_image(selected_card: dict[str, str], card_direction: str = "정방향") -> None:
    card_name = str(selected_card.get("name") or "").strip()
    image_path = str(selected_card.get("image") or "").strip()
    if card_name:
        resolved = resolve_card_image_path(card_name, legacy_image=image_path or None)
        if resolved:
            image_path = resolved
    if not image_path:
        return
    try:
        card_image = Image.open(image_path)
        if card_direction == "역방향":
            card_image = card_image.rotate(180)
        st.image(card_image, width=280)
    except Exception:
        st.image(_generated_tarot_image(selected_card, card_direction), width=280)


def _render_card_back_image() -> None:
    back_path = resolve_card_back_path()
    if back_path:
        try:
            st.image(Image.open(back_path), width=200)
            return
        except Exception:
            pass
    placeholder = {"name": "Card Back", "keyword": "뒷면"}
    st.image(_generated_tarot_image(placeholder, "정방향"), width=200)


def _saju_context_text() -> str:
    gapja = st.session_state.get("u_gapja")
    if not gapja or not isinstance(gapja, (list, tuple)):
        return "사주 정보가 아직 연결되지 않았습니다."
    name = M.session_user_display_name()
    pillars = " / ".join(str(x) for x in gapja[:4])
    return f"{name}님의 사주 흐름({pillars})을 참고해 타로 조언을 정리합니다."


def _tarot_consulting_tip_from_question(question: str) -> str:
    gapja = st.session_state.get("u_gapja")
    u_data = st.session_state.get("u_data", ())
    engine: dict = {}
    if isinstance(gapja, (list, tuple)):
        try:
            engine, _core = M.ensure_engine_and_core(list(gapja), birth_record=u_data)
        except Exception:
            engine = {}
    topic = T.infer_tarot_topic(question)
    daewoon_ten = ""
    if isinstance(engine, dict):
        gtf = engine.get("get_timing_flow")
        if callable(gtf):
            try:
                tf = gtf()
                if isinstance(tf, dict):
                    idx = int(tf.get("daewoon_index", 0) or 0)
                    daewoon_ten = ["인성", "비견", "식상", "재성", "관성"][idx % 5]
            except Exception:
                daewoon_ten = ""
    q = str(question or "").strip()
    if not q:
        return ""
    return K.consulting_tip(
        q,
        strength=str(engine.get("strength", "") or ""),
        yongshin=str(engine.get("yongshin", "") or ""),
        gender=str(st.session_state.get("u_gender", "") or ""),
        daewoon_ten=daewoon_ten,
    )


def _render_tarot_frame(*, title: str, body: str, tone: str = "#D4AF37") -> None:
    safe_title = M._hx(str(title or ""))
    safe_tone = M._hx(str(tone or "#D4AF37"))
    safe_body = M._hx(str(body or "")).replace("\n", "<br>")
    st.markdown(
        f"""
<div class="tarot-interpret-frame" style="--tarot-tone:{safe_tone};">
    <div class="tarot-interpret-title">{safe_title}</div>
    <div class="tarot-interpret-body">{safe_body}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def _prepare_reading(question: str, spread_name: str) -> None:
    count = _spread_count(spread_name)
    seed = "|".join(
        [
            question.strip(),
            spread_name,
            M.session_user_display_name(),
            str(st.session_state.get("u_gapja") or ""),
            M.now_kst().isoformat(),
        ]
    )
    cards = draw_cards(count, seed=seed)
    rng = random.Random(f"{seed}|direction")
    directions = [rng.choice(["정방향", "역방향"]) for _ in cards]
    positions = _spread_positions(spread_name)
    st.session_state[_READING_KEY] = {
        "question": question.strip(),
        "spread": spread_name,
        "count": count,
        "positions": positions,
        "cards": cards,
        "directions": directions,
        "revealed": [False] * count,
    }
    st.session_state[_SIGNATURE_KEY] = (
        reading_signature(question, spread_name, cards) + "|" + ",".join(directions)
    )


def _clear_reading() -> None:
    for key in (_READING_KEY, _SIGNATURE_KEY):
        st.session_state.pop(key, None)


def _reading_signature_key() -> str:
    return re.sub(r"[^a-zA-Z0-9]", "", str(st.session_state.get(_SIGNATURE_KEY) or "new"))[:24]


def _reveal_card(reading: dict, index: int) -> None:
    revealed = list(reading.get("revealed") or [])
    if index < 0 or index >= len(revealed):
        return
    if revealed[index]:
        return
    revealed[index] = True
    reading["revealed"] = revealed
    st.session_state[_READING_KEY] = reading


def _revealed_count(reading: dict) -> int:
    return sum(1 for flag in reading.get("revealed") or [] if flag)


def _all_revealed(reading: dict) -> bool:
    revealed = reading.get("revealed") or []
    count = int(reading.get("count") or len(revealed))
    return len(revealed) >= count and all(revealed[:count])


def _build_ai_tarot_prompt(reading: dict, consulting_tip: str) -> str:
    question = str(reading.get("question") or "")
    spread = str(reading.get("spread") or "3카드")
    positions = list(reading.get("positions") or [])
    cards = list(reading.get("cards") or [])
    directions = list(reading.get("directions") or [])
    card_blocks: list[str] = []
    for idx, card in enumerate(cards):
        if not isinstance(card, dict):
            continue
        pos = positions[idx] if idx < len(positions) else f"카드 {idx + 1}"
        direction = str(directions[idx]) if idx < len(directions) else "정방향"
        energy = (
            str(card.get("meaning_rev") or "")
            if direction == "역방향"
            else str(card.get("meaning_up") or "")
        )
        card_blocks.append(
            "\n".join(
                [
                    f"{idx + 1}) {pos} — {card.get('name')} ({direction})",
                    f"   카드 에너지: {energy}",
                    f"   실천 메시지: {card.get('advice') or card.get('message') or ''}",
                ]
            )
        )
    return f"""
사용자 질문:
{question or "(미입력)"}

스프레드: {spread} ({len(cards)}장)

뽑힌 카드 (위치·방향·의미를 반드시 구분):
{chr(10).join(card_blocks)}

사주 참고(보조):
{consulting_tip}

해석 지침:
- 사용자 질문 문장에 직접 답할 것 (일반론·반복 문장 금지)
- 카드·위치·정/역방향을 구분해 서로 다른 내용으로 쓸 것
- 2~3주 안의 행동 조언 2가지, 피해야 할 행동 1가지
- 공포·단정·의학·법률 조언 금지
- 한국어, 500~700자
""".strip()


def _render_ai_summary(reading: dict, consulting_tip: str) -> None:
    if not _OPENAI_SDK_AVAILABLE:
        st.info(
            "카드 기본 해석은 볼 수 있습니다. AI 심층 해석을 쓰려면 서버 PC에서 "
            "pip install openai 를 실행한 뒤 앱을 다시 켜 주세요."
        )
        return
    ai_client = _openai_client()
    if ai_client is None:
        st.caption("모든 카드를 확인하셨습니다. AI 심층 해석은 OpenAI API 키 설정 후 사용할 수 있습니다.")
        return
    try:
        prompt = _build_ai_tarot_prompt(reading, consulting_tip)
        with st.spinner("🔮 질문 전체 흐름을 정리하는 중..."):
            response = ai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "당신은 타로와 사주를 함께 보는 상담사입니다. "
                            "질문에 맞춰 카드별로 구분해 해석하고 같은 문장을 반복하지 마세요."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.65,
            )
        ai_result = response.choices[0].message.content
        st.markdown("---")
        _render_tarot_frame(
            title="AI 종합 타로 해석",
            body=str(ai_result or ""),
            tone="#60A5FA",
        )
    except Exception:
        st.caption("AI 타로 상담은 API 키 설정 후 사용할 수 있습니다.")


def _render_reading() -> None:
    reading = st.session_state.get(_READING_KEY)
    if not isinstance(reading, dict):
        return

    question = str(reading.get("question") or "").strip()
    spread = str(reading.get("spread") or "3카드")
    count = int(reading.get("count") or _spread_count(spread))
    positions = list(reading.get("positions") or _spread_positions(spread))
    cards = reading.get("cards") or []
    directions = reading.get("directions") or []
    revealed = list(reading.get("revealed") or [False] * count)
    sig = _reading_signature_key()

    if not isinstance(cards, list):
        return

    st.divider()
    st.markdown("### 타로 상담")
    if question:
        st.info(f"질문: {question}")
    st.caption(f"카드 {count}장 · {spread} · {_saju_context_text()}")

    remaining = count - _revealed_count(reading)
    if remaining > 0:
        st.markdown(
            f"**뒷면 카드를 골라 주세요.** 남은 선택 **{remaining}장** "
            f"(총 {count}장 중 {_revealed_count(reading)}장 공개됨)"
        )
    else:
        st.success("모든 카드를 확인했습니다.")

    topic = T.infer_tarot_topic(question)
    consulting_tip = _tarot_consulting_tip_from_question(question)

    # 선택 가능한 뒷면 카드 (가로 배치)
    unrevealed_indices = [i for i in range(count) if i < len(revealed) and not revealed[i]]
    if unrevealed_indices:
        cols = st.columns(min(len(unrevealed_indices), 5))
        for col_idx, card_idx in enumerate(unrevealed_indices):
            position = positions[card_idx] if card_idx < len(positions) else f"{card_idx + 1}번째"
            with cols[col_idx % len(cols)]:
                st.caption(position)
                _render_card_back_image()
                if st.button(
                    "카드 선택",
                    key=f"step8_pick_{sig}_{card_idx}",
                    use_container_width=True,
                    type="primary",
                ):
                    _reveal_card(reading, card_idx)
                    rerun_full_app()

    # 공개된 카드 + 해석
    for idx in range(count):
        if idx >= len(revealed) or not revealed[idx]:
            continue
        if idx >= len(cards) or not isinstance(cards[idx], dict):
            continue

        selected_card = cards[idx]
        card_direction = (
            str(directions[idx]) if idx < len(directions) else "정방향"
        )
        position = positions[idx] if idx < len(positions) else f"{idx + 1}번째"

        st.markdown("---")
        st.subheader(f"{position} · {selected_card['name']}")
        st.caption(f"방향: {card_direction}")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            _render_card_image(selected_card, card_direction)

        with st.expander(f"{position} · 상세 해설", expanded=False):
            _render_tarot_frame(
                title="카드 에너지",
                body=T.card_energy_text(
                    selected_card, reversed=card_direction == "역방향"
                ),
                tone="#D4AF37",
            )
            _render_tarot_frame(
                title="질문에 대한 해석",
                body=T.interpret_card_for_question(
                    card=selected_card,
                    card_direction=card_direction,
                    position=position,
                    spread=spread,
                    question=question,
                    topic=topic,
                ),
                tone="#8B5CF6",
            )

    if _all_revealed(reading):
        card_dicts = [c for c in cards if isinstance(c, dict)]
        dir_list = [
            str(directions[i]) if i < len(directions) else "정방향"
            for i in range(count)
        ]
        synth = T.spread_synthesis(
            question=question,
            spread=spread,
            positions=positions,
            cards=card_dicts,
            directions=dir_list,
            topic=topic,
        )
        st.markdown(
            f'<p class="step8-synth-lead">{html.escape(str(synth)[:220])}{"…" if len(str(synth)) > 220 else ""}</p>',
            unsafe_allow_html=True,
        )
        with st.expander("전체 타로 해설 · 조언 (펼쳐보기)", expanded=False):
            _render_tarot_frame(
                title="종합 타로 해석",
                body=synth,
                tone="#A78BFA",
            )
            if consulting_tip.strip():
                _render_tarot_frame(
                    title="사주 기반 상담 포인트",
                    body=T.tarot_saju_bridge_tip(
                        question=question,
                        consulting_tip=consulting_tip,
                        topic=topic,
                    ),
                    tone="#22C55E",
                )
            _render_ai_summary(reading, consulting_tip)
            _render_tarot_frame(
                title="질문 맞춤 실천 조언",
                body=T.practical_advice_for_reading(
                    question=question,
                    cards=card_dicts,
                    directions=dir_list,
                    topic=topic,
                ),
                tone="#F59E0B",
            )
        st.caption("타로 해석은 참고용입니다. 중요한 결정은 현실 상황과 상담을 함께 보세요.")


def render() -> None:
    M._require_u_gapja_or_halt()

    with M.premium_analysis_shell(8):
        st.markdown(
            """
<style>
img {
    border-radius: 20px;
    box-shadow: 0 0 30px rgba(160, 100, 255, 0.4);
    margin-top: 10px;
}
</style>
""",
            unsafe_allow_html=True,
        )

        M.render_mood_image("step08_hero", variant="hero", alt="AI 타로")
        st.markdown(
            """
<h1>🌙 Mystic Flow Tarot 🔮</h1>
<div style='text-align:center;font-size:18px;margin-bottom:30px;'>
당신의 감정과 운명의 흐름을 카드에 담아보세요.
</div>
""",
            unsafe_allow_html=True,
        )

        today = datetime.now().strftime("%Y.%m.%d")
        st.markdown(f"## 🌙 오늘의 흐름 · {today}")
        st.info(random.choice(daily_messages))
        st.warning(
            "타로와 AI 해석은 오락·참고용입니다. 건강, 임신, 질병, 법률, 투자 등 중요한 결정은 "
            "전문가 상담과 현실 정보를 우선해 주세요."
        )

        has_reading = isinstance(st.session_state.get(_READING_KEY), dict)

        if not has_reading:
            st.caption("질문 입력후 카드 숫자를 선택 하세요")

            st.markdown("---")
            M.render_mood_image("step08_mid_spread", variant="mid", alt="타로 스프레드")
            question = st.text_area(
                "궁금 사항을 입력 하세요",
                key=_QUESTION_KEY,
                placeholder=(
                    "예: 3개월째 썸인데 상대 연락이 줄었어요. 제가 먼저 연락해도 될까요?\n"
                    "예: 올해 안에 이직을 준비 중인데 지금 움직여도 될까요?"
                ),
                height=120,
            )
            spread_name = st.radio(
                "몇 장의 카드를 볼까요?",
                options=["1카드", "3카드", "5카드"],
                key=_SPREAD_KEY,
                index=1,
                horizontal=True,
                help="1장: 핵심만 · 3장: 현재·흐름·조언(권장) · 5장: 현재·막힘·도움·가까운 흐름·실천",
            )

            if st.button("🔮 카드 섞기", type="primary", use_container_width=True):
                if not str(question or "").strip():
                    st.warning("질문을 먼저 입력해 주세요.")
                else:
                    with st.spinner(random.choice(loading_messages)):
                        time.sleep(0.9)
                    _prepare_reading(str(question), str(spread_name))
                    rerun_full_app()
        else:
            if st.button("↩ 새 질문으로 다시하기", use_container_width=True):
                _clear_reading()
                rerun_full_app()

        _render_reading()
