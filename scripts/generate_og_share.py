"""카카오·SNS용 og-share.png (1200×630) 생성 — ``python scripts/generate_og_share.py``"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static" / "og-share.png"

_FONT_CANDIDATES = (
    Path(r"C:\Windows\Fonts\malgunbd.ttf"),
    Path(r"C:\Windows\Fonts\malgun.ttf"),
    Path(r"C:\Windows\Fonts\batang.ttc"),
    Path("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"),
)


def _load_font(size: int):
    from PIL import ImageFont

    for fp in _FONT_CANDIDATES:
        if fp.is_file():
            try:
                return ImageFont.truetype(str(fp), size)
            except OSError:
                continue
    return ImageFont.load_default()


def _draw_paper_gradient(draw, w: int, h: int) -> None:
    for y in range(h):
        t = y / h
        r = int(248 * (1 - t) + 228 * t)
        g = int(242 * (1 - t) + 214 * t)
        b = int(232 * (1 - t) + 198 * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def _draw_corner_ornament(draw, x: int, y: int, *, flip_x: bool, flip_y: bool) -> None:
  length = 72
  thick = 3
  color = "#c9a227"
  dx = -1 if flip_x else 1
  dy = -1 if flip_y else 1
  draw.line([(x, y), (x + dx * length, y)], fill=color, width=thick)
  draw.line([(x, y), (x, y + dy * length)], fill=color, width=thick)
  draw.ellipse(
      (x - 5, y - 5, x + 5, y + 5),
      fill="#e8c547",
      outline="#8a6d1a",
      width=1,
  )


def _draw_dragon_silhouette(draw) -> None:
    """은은한 용·봉황 실루엣."""
  gold = (212, 175, 55, 90)
  draw.arc((40, 180, 380, 520), 200, 340, fill=gold, width=2)
  draw.arc((60, 200, 360, 480), 210, 330, fill=gold, width=1)
  draw.arc((820, 160, 1160, 500), 20, 160, fill=gold, width=2)
  draw.arc((860, 190, 1120, 470), 30, 150, fill=gold, width=1)


def main() -> int:
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("pip install Pillow 후 다시 실행하세요.")
        return 1

    w, h = 1200, 630
    img = Image.new("RGB", (w, h), "#f4eee4")
    draw = ImageDraw.Draw(img, "RGBA")
    _draw_paper_gradient(draw, w, h)
    _draw_dragon_silhouette(draw)

    # 상단 금빛 하이라이트
    for r in range(180, 0, -4):
        a = max(0, int(28 * (1 - r / 180)))
        draw.ellipse(
            (w // 2 - r * 3, -r, w // 2 + r * 3, r * 2),
            fill=(255, 248, 220, a),
        )

    cx, cy = 300, 315
    # 인장 후광
    for r in range(100, 60, -6):
        a = int(12 + (100 - r) * 0.35)
        draw.ellipse(
            (cx - r, cy - r, cx + r, cy + r),
            fill=(212, 175, 55, a),
        )
    draw.ellipse((cx - 82, cy - 82, cx + 82, cy + 82), outline="#d4af37", width=8)
    draw.ellipse((cx - 66, cy - 66, cx + 66, cy + 66), fill="#1a1510")
    font_seal = _load_font(54)
    draw.text((cx, cy), "命", fill="#e8d5a0", font=font_seal, anchor="mm")

    font_title = _load_font(92)
    font_sub = _load_font(34)
    font_tag = _load_font(36)
    draw.text((620, 278), "사주까기", fill="#1a1a2e", font=font_title, anchor="lm")
    draw.text((620, 352), "LUXURY SAJU INSIGHT", fill="#8a6d1a", font=font_sub, anchor="lm")
    draw.text((620, 412), "당신의 운명을 정밀하게 읽다", fill="#3d3528", font=font_tag, anchor="lm")
    draw.rectangle((620, 462, 1000, 468), fill="#d4af37")
    draw.rectangle((622, 464, 998, 466), fill="#f5e6a8")

    _draw_corner_ornament(draw, 48, 42, flip_x=False, flip_y=False)
    _draw_corner_ornament(draw, w - 48, 42, flip_x=True, flip_y=False)
    _draw_corner_ornament(draw, 48, h - 42, flip_x=False, flip_y=True)
    _draw_corner_ornament(draw, w - 48, h - 42, flip_x=True, flip_y=True)

    # 미세 금박 점
    dots = (
        (520, 120),
        (1080, 200),
        (140, 480),
        (1050, 520),
        (580, 540),
    )
    for dx, dy in dots:
        draw.ellipse((dx - 3, dy - 3, dx + 3, dy + 3), fill="#e8c547")

    img = img.convert("RGB")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"OK: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
