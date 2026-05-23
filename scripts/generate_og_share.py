"""카카오·SNS용 og-share.png (1200×630) 생성 — ``python scripts/generate_og_share.py``"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static" / "og-share.png"

_FONT_CANDIDATES = (
    Path(r"C:\Windows\Fonts\malgunbd.ttf"),
    Path(r"C:\Windows\Fonts\batang.ttc"),
    Path("/usr/share/fonts/truetype/nanum/NanumMyeongjoBold.ttf"),
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


def main() -> int:
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("pip install Pillow 후 다시 실행하세요.")
        return 1

    w, h = 1200, 630
    img = Image.new("RGB", (w, h), "#ebe2d4")
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(244 * (1 - t) + 223 * t)
        g = int(238 * (1 - t) + 210 * t)
        b = int(228 * (1 - t) + 194 * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    cx, cy = 360, 315
    draw.ellipse((cx - 80, cy - 80, cx + 80, cy + 80), outline="#d4af37", width=7)
    draw.ellipse((cx - 64, cy - 64, cx + 64, cy + 64), fill="#1a1510")
    font_seal = _load_font(52)
    draw.text((cx, cy), "命", fill="#e8d5a0", font=font_seal, anchor="mm")

    font_title = _load_font(88)
    font_sub = _load_font(34)
    font_tag = _load_font(36)
    draw.text((640, 270), "사주까기", fill="#1a1a2e", font=font_title, anchor="lm")
    draw.text((640, 340), "LUXURY SAJU INSIGHT", fill="#8a6d1a", font=font_sub, anchor="lm")
    draw.text((640, 400), "당신의 운명을 정밀하게 읽다", fill="#3d3528", font=font_tag, anchor="lm")
    draw.rectangle((640, 450, 960, 454), fill="#d4af37")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"OK: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
