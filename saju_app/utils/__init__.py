"""작은 유틸 함수 모음."""

from __future__ import annotations

import datetime
import html
from zoneinfo import ZoneInfo


def hx(s: object) -> str:
    """신뢰 불가 텍스트를 HTML 이스케이프."""
    return html.escape(str(s), quote=True)


def html_br(s: object) -> str:
    """본문: 태그 불가, 줄바꿈만 <br/>."""
    return html.escape(str(s), quote=True).replace("\n", "<br/>")


def md_bold_to_html_safe(md: str) -> str:
    """`**내용**`만 <b>로 변환(내용·바깥 문자열 모두 escape)."""
    text = str(md)
    parts: list[str] = []
    last = 0
    import re

    for m in re.finditer(r"\*\*(.+?)\*\*", text):
        parts.append(html.escape(text[last : m.start()], quote=True))
        parts.append("<b>" + html.escape(m.group(1), quote=True) + "</b>")
        last = m.end()
    parts.append(html.escape(text[last:], quote=True))
    return "".join(parts)


def match_body_html(body: str) -> str:
    """궁합 해설: `<b>`·`**`·줄바꿈을 안전한 HTML로 변환."""
    import re

    text = str(body or "")
    text = re.sub(r"<b>(.*?)</b>", r"**\1**", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    return md_bold_to_html_safe(text).replace("\n", "<br/>")


def now_kst() -> datetime.datetime:
    """서버 환경과 무관하게 한국시간(KST) 기준 '현재' 반환."""
    return datetime.datetime.now(tz=ZoneInfo("Asia/Seoul"))
