"""``data/saju_consulting/`` Q&A 코퍼스 — 전 STEP 공통 매칭·표시."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import streamlit as st

from saju_app.ui import consulting_knowledge as K

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CORPUS_DIR = _PROJECT_ROOT / "data" / "saju_consulting"

_CATEGORY_TOPIC: dict[str, str] = {
    "love": "love",
    "job": "job",
    "wealth": "wealth",
    "wellbeing": "health",
    "timing": "general",
    "family": "health",
    "social": "general",
    "health": "health",
    "charm": "general",
    "move": "move",
}

_STEP_DEFAULT_QUERY: dict[str, str] = {
    "step3": "사주 원국 인생 방향 용신 기운",
    "step4": "궁합 연애 결혼 관계",
    "step5": "신살 역마 재살 인간관계 건강",
    "step6": "오늘 운세 하루 흐름",
    "step7": "주역 궁금한 일 방향",
    "step8": "타로 질문 운세",
    "step9": "대운 세운 흐름 올해",
    "step10": "올해 총평 대운 인생 방향",
    "step11": "상담 질문",
    "mbti": "직업 적성 커리어 매력",
}


@dataclass(frozen=True)
class ConsultingQA:
    category: str
    keywords: tuple[str, ...]
    applies: frozenset[str]
    question: str
    answer: str
    source: str


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end < 0:
        return {}, text
    block = text[3:end].strip()
    body = text[end + 3 :].lstrip()
    meta: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        meta[key.strip().lower()] = val.strip()
    return meta, body


def _split_applies(raw: str) -> frozenset[str]:
    parts = [p.strip().lower() for p in re.split(r"[,;\s]+", raw) if p.strip()]
    return frozenset(parts)


def _parse_qa_blocks(body: str) -> list[tuple[str, str]]:
    chunks = re.split(r"(?m)^##\s*Q\.\s*", body)
    out: list[tuple[str, str]] = []
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        lines = chunk.split("\n", 1)
        q_line = lines[0].strip()
        rest = lines[1] if len(lines) > 1 else ""
        ans = rest
        m = re.search(r"\*\*A\.\*\*\s*", rest, flags=re.IGNORECASE)
        if m:
            ans = rest[m.end() :].strip()
        ans = re.sub(r"^---+\s*", "", ans, flags=re.MULTILINE).strip()
        ans = re.sub(r"\n---+\s*$", "", ans).strip()
        if q_line and ans:
            out.append((q_line, ans))
    return out


@lru_cache(maxsize=1)
def load_consulting_qa() -> tuple[ConsultingQA, ...]:
    entries: list[ConsultingQA] = []
    if not _CORPUS_DIR.is_dir():
        return tuple()
    for path in sorted(_CORPUS_DIR.glob("*.md")):
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        meta, body = _parse_frontmatter(raw)
        category = str(meta.get("category") or "general").lower()
        kw_raw = str(meta.get("keywords") or "")
        keywords = tuple(k.strip() for k in kw_raw.split(",") if k.strip())
        applies = _split_applies(str(meta.get("applies") or ""))
        for question, answer in _parse_qa_blocks(body):
            entries.append(
                ConsultingQA(
                    category=category,
                    keywords=keywords,
                    applies=applies,
                    question=question,
                    answer=answer,
                    source=path.name,
                )
            )
    return tuple(entries)


def reload_consulting_corpus() -> int:
    """파일 추가 후 캐시 갱신(관리·개발용)."""
    load_consulting_qa.cache_clear()
    return len(load_consulting_qa())


def infer_category(query: str) -> str:
    text = str(query or "").strip()
    if not text:
        return "general"
    topic = K.normalize_topic(text)
    if topic in ("love", "job", "wealth", "health", "move", "study"):
        rev = {v: k for k, v in _CATEGORY_TOPIC.items()}
        return rev.get(topic, "general")
    for cat, qa in _category_keyword_hits(text):
        if cat:
            return cat
    return "general"


def _category_keyword_hits(text: str) -> list[tuple[str, int]]:
    scores: dict[str, int] = {}
    for entry in load_consulting_qa():
        score = 0
        for kw in entry.keywords:
            if kw and kw in text:
                score += 2
        if entry.category:
            scores[entry.category] = scores.get(entry.category, 0) + score
    return sorted(scores.items(), key=lambda x: -x[1])


def _score_entry(entry: ConsultingQA, query: str, *, apply: str | None) -> int:
    q = str(query or "").strip().lower()
    if not q:
        return 0
    score = 0
    if apply and entry.applies and apply.lower() not in entry.applies:
        score -= 4
    q_norm = re.sub(r"\s+", "", q)
    eq_norm = re.sub(r"\s+", "", entry.question.lower())
    if eq_norm and (eq_norm in q_norm or q_norm in eq_norm):
        score += 80
    for kw in entry.keywords:
        if len(kw) >= 2 and kw in q:
            score += 8
    for tok in re.findall(r"[가-힣]{2,}", q):
        if tok in entry.question:
            score += 5
        if tok in entry.answer:
            score += 1
    cat = infer_category(q)
    if cat == entry.category:
        score += 6
    return score


def match_consulting(
    query: str,
    *,
    apply: str | None = None,
    category: str | None = None,
    limit: int = 2,
) -> list[ConsultingQA]:
    """질문·키워드에 맞는 현장 Q&A (최대 limit건)."""
    q = str(query or "").strip()
    if not q and not category:
        q = _STEP_DEFAULT_QUERY.get(str(apply or "").lower(), "사주 상담")
    cat_filter = str(category or "").lower() if category else ""
    if not cat_filter and q:
        cat_filter = infer_category(q)

    scored: list[tuple[int, ConsultingQA]] = []
    for entry in load_consulting_qa():
        if cat_filter and entry.category != cat_filter and _score_entry(entry, q, apply=apply) < 15:
            continue
        sc = _score_entry(entry, q, apply=apply)
        if sc > 0:
            scored.append((sc, entry))
    scored.sort(key=lambda x: (-x[0], x[1].source, x[1].question))
    seen: set[str] = set()
    out: list[ConsultingQA] = []
    for _sc, entry in scored:
        key = f"{entry.question}|{entry.source}"
        if key in seen:
            continue
        seen.add(key)
        out.append(entry)
        if len(out) >= max(1, int(limit)):
            break
    if out:
        return out
    if cat_filter:
        for entry in load_consulting_qa():
            if entry.category == cat_filter:
                out.append(entry)
                if len(out) >= limit:
                    break
    return out


def format_answers_plain(entries: list[ConsultingQA], *, max_chars: int = 1200) -> str:
    parts: list[str] = []
    total = 0
    for e in entries:
        block = f"Q. {e.question}\n{e.answer}"
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\n\n".join(parts)


def format_answers_html(entries: list[ConsultingQA]) -> str:
    if not entries:
        return ""
    blocks: list[str] = []
    for e in entries:
        q = html.escape(e.question)
        a = html.escape(e.answer).replace("\n", "<br>")
        blocks.append(
            '<motion class="saju-corpus-qa" style="margin-bottom:0.85rem;">'
            f'<div style="font-weight:700;color:#6d28d9;margin-bottom:0.25rem;">Q. {q}</motion>'
            f'<div style="opacity:0.92;">{a}</motion>'
        )
    fixed = "".join(blocks).replace("<motion", "<div").replace("</motion>", "</div>")
    return (
        '<div style="font-size:0.92rem;line-height:1.65;color:#334155;">'
        f"{fixed}"
        '<p style="margin:0.35rem 0 0;font-size:0.8rem;opacity:0.75;">'
        "※ 사주까기 현장 상담 사례 기반 참고입니다."
        "</p></div>"
    )


def corpus_snippet_for_question(
    user_text: str,
    *,
    apply: str | None = "step11",
    limit: int = 2,
    max_len: int = 900,
) -> str:
    """AI·규칙 답변에 넣을 발췌 텍스트."""
    return format_answers_plain(
        match_consulting(user_text, apply=apply, limit=limit),
        max_chars=max_len,
    )


def direct_answer_html(
    user_text: str,
    *,
    apply: str | None = "step11",
) -> str | None:
    """가장 잘 맞는 Q&A 1건을 HTML 답변 블록으로."""
    hits = match_consulting(user_text, apply=apply, limit=1)
    if not hits:
        return None
    e = hits[0]
    a = html.escape(e.answer).replace("\n", "<br>")
    q = html.escape(e.question)
    return (
        f"💬 <b>질문:</b> {html.escape(str(user_text or '')[:120])}<br><br>"
        f"⭐ <b>현장 상담 답변</b> ({html.escape(e.category)})<br>"
        f"<i>Q. {q}</i><br><br>{a}"
    )


def render_consulting_panel(
    query: str,
    *,
    apply: str,
    title: str = "🌿 현장 상담 참고 (사주까기)",
    expanded: bool = False,
    limit: int = 2,
    container_key: str | None = None,
) -> bool:
    """Streamlit expander로 코퍼스 Q&A 표시. 표시했으면 True."""
    entries = match_consulting(query, apply=apply, limit=limit)
    if not entries:
        return False
    html_body = format_answers_html(entries)
    if container_key:
        with st.container(key=container_key):
            with st.expander(title, expanded=expanded):
                st.markdown(html_body, unsafe_allow_html=True)
    else:
        with st.expander(title, expanded=expanded):
            st.markdown(html_body, unsafe_allow_html=True)
    return True


def sinsal_consulting_query(unique_sins: list[str]) -> str:
    """STEP5 신살 → 코퍼스 검색어."""
    parts: list[str] = ["신살", "사주"]
    mapping = {
        "역마": "이사 이동 해외",
        "재살": "재물 돈 투자",
        "년살": "연애 인연 매력",
        "도화": "연애 인연",
        "화개": "마음 불안 고독",
        "육해": "건강 스트레스 인간관계",
        "망신": "인간관계 직장",
        "겁살": "돈 손실",
    }
    for sin in unique_sins:
        for key, words in mapping.items():
            if key in sin:
                parts.append(words)
    return " ".join(parts)


def mbti_consulting_query(mbti: str) -> str:
    m = str(mbti or "").strip().upper()
    if m in ("ENTJ", "ENTP", "ESTJ", "ESTP"):
        return f"{mbti} 직업 이직 리더십 사업"
    if m in ("INFJ", "INFP", "ENFJ", "ENFP"):
        return f"{mbti} 연애 상담 창의 커리어"
    if m in ("ISTJ", "ISFJ", "ESTJ", "ESFJ"):
        return f"{mbti} 직장 안정 취업"
    return f"{mbti} 적성 커리어 매력 자신감"


def load_external_consulting_corpus() -> str:
    """STEP11 AI용 전체 코퍼스(기존 API 호환)."""
    if not _CORPUS_DIR.is_dir():
        return ""
    chunks: list[str] = []
    total = 0
    for path in sorted(_CORPUS_DIR.glob("*.md")):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").strip()
        except OSError:
            continue
        if not text:
            continue
        piece = f"[{path.name}]\n{text[:8000]}"
        chunks.append(piece)
        total += len(piece)
        if total >= 24000:
            break
    return "\n\n".join(chunks)
