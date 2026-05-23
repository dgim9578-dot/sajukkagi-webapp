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

    # 상단 뱃지: 무료 사주풀이
    font_badge = _load_font(36)
    badge_text = "무료 사주풀이"
    bbox = draw.textbbox((0, 0), badge_text, font=font_badge)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 36, 18
    bx1, by1 = 72, 52
    bx2, by2 = bx1 + tw + pad_x * 2, by1 + th + pad_y * 2
    draw.rounded_rectangle((bx1, by1, bx2, by2), radius=32, fill="#d4af37", outline="#8a6d1a", width=2)
    draw.text((bx1 + pad_x, by1 + pad_y - 2), badge_text, fill="#1a1208", font=font_badge)

    cx, cy = 300, 340
    draw.ellipse((cx - 80, cy - 80, cx + 80, cy + 80), outline="#d4af37", width=7)
    draw.ellipse((cx - 64, cy - 64, cx + 64, cy + 64), fill="#1a1510")
    font_seal = _load_font(52)
    draw.text((cx, cy), "命", fill="#e8d5a0", font=font_seal, anchor="mm")

    font_title = _load_font(88)
    font_sub = _load_font(32)
    font_tag = _load_font(34)
    draw.text((620, 285), "사주까기", fill="#1a1a2e", font=font_title, anchor="lm")
    draw.text((620, 355), "LUXURY SAJU INSIGHT", fill="#8a6d1a", font=font_sub, anchor="lm")
    draw.text((620, 415), "당신의 운명을 정밀하게 읽다", fill="#3d3528", font=font_tag, anchor="lm")
    draw.rectangle((620, 465, 980, 469), fill="#d4af37")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    print(f"OK: {OUT}")
    print("카카오 미리보기용 — GitHub push 후 24시간 이내 반영될 수 있습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
