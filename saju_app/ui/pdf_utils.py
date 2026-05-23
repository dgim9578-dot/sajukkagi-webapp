"""총평 등 한글 PDF — ReportLab(프리미엄 레이아웃) 우선, fpdf2 폴백."""

from __future__ import annotations

import html
import os
import re
from io import BytesIO
from typing import Callable, Optional


def find_korean_ui_font_ttf() -> Optional[str]:
    """맑은 고딕·나눔·Noto 등 흔한 경로. 없으면 None."""
    candidates: list[str] = []
    windir = os.environ.get("WINDIR", "")
    if windir:
        candidates.extend(
            [
                os.path.join(windir, "Fonts", "malgun.ttf"),
                os.path.join(windir, "Fonts", "malgunsl.ttf"),
                os.path.join(windir, "Fonts", "NanumGothic.ttf"),
            ]
        )
    candidates.extend(
        [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.ttf",
            "/Library/Fonts/NanumGothic.ttf",
            "/Library/Fonts/AppleGothic.ttf",
        ]
    )
    for p in candidates:
        if p and os.path.isfile(p) and p.lower().endswith(".ttf"):
            return p
    return None


def _markdownish_to_plain(text: str) -> str:
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    s = re.sub(r"^#+\s*", "", s, flags=re.MULTILINE)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    return s.strip()


def _escape_reportlab_paragraph(text: str) -> str:
    """ReportLab Paragraph XML 이스케이프 + 줄바꿈."""
    t = html.escape(text.replace("\r\n", "\n").replace("\r", "\n"), quote=False)
    return t.replace("\n", "<br/>")


def _build_total_review_pdf_reportlab(*, title: str, body: str) -> Optional[bytes]:
    """한지·금박 라인 느낌의 A4 PDF (ReportLab)."""
    font_path = find_korean_ui_font_ttf()
    if not font_path:
        return None
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except ImportError:
        return None

    plain = _markdownish_to_plain(body)
    if not plain:
        return None

    safe_title = _markdownish_to_plain(title)[:200]

    font_name = "SajuKO"
    try:
        pdfmetrics.registerFont(TTFont(font_name, font_path))
    except Exception:
        return None

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=22 * mm,
        bottomMargin=22 * mm,
        title=safe_title[:80],
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "SajuRptTitle",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=17,
        leading=24,
        textColor=colors.HexColor("#7a5e12"),
        spaceAfter=14,
        alignment=TA_LEFT,
    )
    body_style = ParagraphStyle(
        "SajuRptBody",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=11,
        leading=17,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=10,
        alignment=TA_JUSTIFY,
    )
    foot_style = ParagraphStyle(
        "SajuRptFoot",
        parent=styles["Normal"],
        fontName=font_name,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#64748b"),
        spaceBefore=16,
    )

    def _page_bg(canvas: object, _doc: object) -> None:
        c = canvas
        w, h = A4
        c.saveState()
        c.setFillColor(colors.HexColor("#fdf8f0"))
        c.rect(0, 0, w, h, fill=1, stroke=0)
        # 금박 상단 라인
        c.setStrokeColor(colors.HexColor("#d4af37"))
        c.setLineWidth(1.2)
        c.line(18 * mm, h - 16 * mm, w - 18 * mm, h - 16 * mm)
        # 먹 테두리(은은)
        c.setStrokeColor(colors.HexColor("#c9a227"))
        c.setLineWidth(0.45)
        inset = 12 * mm
        c.rect(inset, inset, w - 2 * inset, h - 2 * inset, fill=0, stroke=1)
        c.restoreState()

    story: list = []
    story.append(Paragraph(_escape_reportlab_paragraph(safe_title), title_style))
    story.append(Spacer(1, 4))
    for block in re.split(r"\n{2,}", plain):
        line = block.strip()
        if not line:
            continue
        story.append(Paragraph(_escape_reportlab_paragraph(line), body_style))
        story.append(Spacer(1, 3))
    story.append(
        Paragraph(
            _escape_reportlab_paragraph("사주프로 · 개인 참고용 리포트 (의학·법률 자문 아님)"),
            foot_style,
        )
    )

    try:
        doc.build(story, onFirstPage=_page_bg, onLaterPages=_page_bg)
    except Exception:
        return None
    raw = buf.getvalue()
    return raw if raw else None


def _build_total_review_pdf_fpdf(*, title: str, body: str) -> Optional[bytes]:
    """fpdf2 폴백."""
    font_path = find_korean_ui_font_ttf()
    if not font_path:
        return None
    try:
        from fpdf import FPDF
    except ImportError:
        return None

    plain = _markdownish_to_plain(body)
    if not plain:
        return None

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    try:
        pdf.add_font("KO", "", font_path)
    except Exception:
        return None
    pdf.set_font("KO", size=11)
    pdf.add_page()
    pdf.set_margins(18, 18, 18)
    safe_title = _markdownish_to_plain(title)[:120]
    pdf.set_font("KO", size=15)
    pdf.multi_cell(0, 9, safe_title)
    pdf.ln(4)
    pdf.set_font("KO", size=11)
    for block in re.split(r"\n{2,}", plain):
        line = block.replace("\r", "").strip()
        if not line:
            continue
        try:
            pdf.multi_cell(0, 6, line)
        except Exception:
            ascii_fallback = line.encode("ascii", "replace").decode("ascii")
            pdf.multi_cell(0, 6, ascii_fallback)
        pdf.ln(2)

    try:
        raw = pdf.output(dest="S")
    except Exception:
        return None
    if isinstance(raw, (bytes, bytearray)):
        return bytes(raw) if raw else None
    if isinstance(raw, str):
        return raw.encode("latin-1", errors="replace") or None
    return None


def build_total_review_pdf_bytes(*, title: str, body: str) -> Optional[bytes]:
    """한글 본문 PDF. ReportLab → fpdf2 순. 폰트·라이브러리 없으면 None."""
    builders: tuple[Callable[..., Optional[bytes]], ...] = (
        _build_total_review_pdf_reportlab,
        _build_total_review_pdf_fpdf,
    )
    for fn in builders:
        try:
            b = fn(title=title, body=body)
        except Exception:
            b = None
        if b:
            return b
    return None


def _build_pdf_weasyprint_simple(*, title: str, body: str) -> Optional[bytes]:
    """HTML→PDF (WeasyPrint). Windows 등에서 ReportLab용 .ttf가 없을 때 보조."""
    try:
        from weasyprint import HTML
    except ImportError:
        return None
    plain = _markdownish_to_plain(body)
    if not plain:
        return None
    safe_title = html.escape(_markdownish_to_plain(title)[:200])
    safe_body = html.escape(plain)
    doc = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<style>
@page {{ size: A4; margin: 18mm; }}
body {{ font-family: "Malgun Gothic", "Apple SD Gothic Neo", "Noto Sans KR", sans-serif;
  font-size: 11pt; color: #1a1a2e; line-height: 1.55; }}
h1 {{ font-size: 17pt; color: #7a5e12; margin: 0 0 14pt 0; font-weight: 700; }}
pre {{ white-space: pre-wrap; font-family: inherit; margin: 0; }}
.foot {{ font-size: 8.5pt; color: #64748b; margin-top: 18pt; }}
</style></head><body>
<h1>{safe_title}</h1>
<pre>{safe_body}</pre>
<p class="foot">사주프로 · 개인 참고용 리포트 (의학·법률 자문 아님)</p>
</body></html>"""
    buf = BytesIO()
    try:
        HTML(string=doc, base_url=os.getcwd()).write_pdf(buf)
    except Exception:
        return None
    raw = buf.getvalue()
    return raw if raw else None


def build_report_pdf_bytes(*, title: str, body: str) -> Optional[bytes]:
    """리포트 PDF: ReportLab → fpdf2 → (선택) WeasyPrint."""
    b = build_total_review_pdf_bytes(title=title, body=body)
    if b:
        return b
    try:
        return _build_pdf_weasyprint_simple(title=title, body=body)
    except Exception:
        return None


def render_pdf_download_button(
    *,
    pdf_bytes: bytes,
    file_name: str,
    label: str = "PDF 리포트 다운로드",
    key: str = "pdf_dl",
    use_container_width: bool = True,
) -> None:
    """PDF 다운로드 버튼(지연 생성·미리보기 iframe 방지).

    ``data`` 를 callable 로 넘기면 클릭 전까지 미디어 매니저에 등록되지 않아,
    모바일 WebView에서 빈 컴포넌트 iframe(파이썬 로고)이 끼는 현상을 줄입니다.
    """
    import streamlit as st

    payload = bytes(pdf_bytes)
    safe_name = str(file_name or "report.pdf").strip() or "report.pdf"

    st.download_button(
        label=str(label or "PDF 다운로드"),
        data=lambda p=payload: p,
        file_name=safe_name,
        mime="application/pdf",
        key=str(key),
        use_container_width=bool(use_container_width),
        on_click="ignore",
    )
