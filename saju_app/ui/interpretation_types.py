"""구조화 해석 데이터 — UI·components 의존 없음(순환 import 방지)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StructuredInterpretation:
    one_liner: str
    tags: list[str]
    detail_paragraphs: list[str]
    advice: list[tuple[str, str]]
    harmony_pct: int
    harmony_caption: str
