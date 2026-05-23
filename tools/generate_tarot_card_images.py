from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from tarot_data import tarot_cards


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "tarot_images"
W, H = 600, 1000


def _font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/malgunbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


FONT_TITLE = _font(36)
FONT_SUB = _font(24)
FONT_ROMAN = _font(32)
FONT_SMALL = _font(18)


def _safe_filename(image_path: str) -> str:
    return Path(image_path).name


def _label_for(card_name: str) -> str:
    labels = {
        "The Fool": "바보",
        "The Magician": "마법사",
        "The High Priestess": "여사제",
        "The Empress": "여제",
        "The Emperor": "황제",
        "The Hierophant": "교황",
        "The Lovers": "연인",
        "The Chariot": "전차",
        "Strength": "힘",
        "The Hermit": "은둔자",
        "Wheel of Fortune": "운명의 수레바퀴",
        "Justice": "정의",
        "The Hanged Man": "매달린 사람",
        "Death": "죽음",
        "Temperance": "절제",
        "The Devil": "악마",
        "The Tower": "탑",
        "The Star": "별",
        "The Moon": "달",
        "The Sun": "태양",
        "Judgement": "심판",
        "The World": "세계",
    }
    if card_name in labels:
        return labels[card_name]
    return (
        card_name.replace("Wands", "완드")
        .replace("Cups", "컵")
        .replace("Swords", "소드")
        .replace("Pentacles", "펜타클")
        .replace("Ace", "에이스")
        .replace("Page", "페이지")
        .replace("Knight", "기사")
        .replace("Queen", "여왕")
        .replace("King", "왕")
        .replace(" of ", " ")
    )


def _center(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font, fill) -> None:
    x, y = xy
    box = draw.textbbox((0, 0), text, font=font)
    tw = box[2] - box[0]
    draw.text((x - tw / 2, y), text, font=font, fill=fill)


def _star(draw: ImageDraw.ImageDraw, x: int, y: int, r: int, fill) -> None:
    draw.line((x - r, y, x + r, y), fill=fill, width=1)
    draw.line((x, y - r, x, y + r), fill=fill, width=1)


def _draw_symbol(draw: ImageDraw.ImageDraw, card_name: str, seed: int) -> None:
    rng = random.Random(seed)
    gold = (215, 174, 96)
    pale = (238, 221, 176)
    violet = (114, 88, 164)
    cx, cy = W // 2, 420

    if "Cups" in card_name:
        draw.ellipse((cx - 80, cy - 50, cx + 80, cy + 90), outline=gold, width=5)
        draw.rectangle((cx - 35, cy + 70, cx + 35, cy + 145), fill=None, outline=gold, width=5)
        draw.arc((cx - 100, cy - 70, cx + 100, cy + 80), 0, 180, fill=pale, width=3)
    elif "Swords" in card_name:
        draw.line((cx, cy - 170, cx, cy + 170), fill=gold, width=8)
        draw.polygon([(cx, cy - 215), (cx - 28, cy - 160), (cx + 28, cy - 160)], fill=pale)
        draw.line((cx - 95, cy + 65, cx + 95, cy + 65), fill=gold, width=8)
    elif "Pentacles" in card_name:
        pts = []
        for i in range(5):
            a = -math.pi / 2 + i * 2 * math.pi / 5
            pts.append((cx + math.cos(a) * 120, cy + math.sin(a) * 120))
        order = [0, 2, 4, 1, 3, 0]
        draw.line([pts[i] for i in order], fill=gold, width=5)
        draw.ellipse((cx - 145, cy - 145, cx + 145, cy + 145), outline=pale, width=4)
    elif "Wands" in card_name:
        draw.line((cx - 60, cy + 170, cx + 65, cy - 180), fill=gold, width=12)
        for _ in range(8):
            x = rng.randint(cx - 90, cx + 100)
            y = rng.randint(cy - 150, cy + 120)
            draw.ellipse((x, y, x + 14, y + 14), fill=violet)
    elif card_name in {"The Moon", "The High Priestess"}:
        draw.pieslice((cx - 130, cy - 150, cx + 130, cy + 110), 70, 290, fill=pale)
        draw.pieslice((cx - 70, cy - 150, cx + 190, cy + 110), 70, 290, fill=(16, 23, 52))
    elif card_name in {"The Sun", "The Star"}:
        for i in range(16):
            a = i * math.pi / 8
            draw.line((cx, cy, cx + math.cos(a) * 170, cy + math.sin(a) * 170), fill=gold, width=3)
        draw.ellipse((cx - 78, cy - 78, cx + 78, cy + 78), fill=pale)
    elif card_name == "Death":
        draw.line((cx - 90, cy + 150, cx + 90, cy - 150), fill=pale, width=8)
        draw.line((cx - 80, cy - 135, cx + 120, cy - 40), fill=gold, width=5)
    else:
        draw.ellipse((cx - 120, cy - 120, cx + 120, cy + 120), outline=gold, width=5)
        draw.arc((cx - 170, cy - 170, cx + 170, cy + 170), 200, 340, fill=pale, width=5)
        draw.line((cx, cy - 150, cx, cy + 150), fill=violet, width=5)


def create_card(card: dict[str, str], index: int) -> None:
    rng = random.Random(index * 999)
    img = Image.new("RGB", (W, H), (9, 15, 38))
    draw = ImageDraw.Draw(img)

    for y in range(H):
        t = y / H
        r = int(8 + 20 * t)
        g = int(13 + 10 * t)
        b = int(35 + 45 * t)
        draw.line((0, y, W, y), fill=(r, g, b))

    for _ in range(130):
        x = rng.randint(20, W - 20)
        y = rng.randint(20, H - 20)
        alpha = rng.randint(80, 180)
        color = (alpha, alpha - 20, 120)
        _star(draw, x, y, rng.randint(1, 4), color)

    gold = (205, 158, 84)
    pale = (239, 219, 172)
    draw.rounded_rectangle((35, 30, W - 35, H - 30), radius=26, outline=gold, width=4)
    draw.rounded_rectangle((55, 55, W - 55, H - 55), radius=20, outline=(92, 70, 120), width=2)
    draw.rectangle((75, 735, W - 75, 900), fill=(13, 18, 45), outline=gold, width=2)

    roman = str(index) if index < 22 else ""
    if roman:
        _center(draw, (W // 2, 70), roman, FONT_ROMAN, pale)

    _draw_symbol(draw, card["name"], index)

    _center(draw, (W // 2, 760), card["name"].upper(), FONT_TITLE, pale)
    _center(draw, (W // 2, 815), _label_for(card["name"]), FONT_SUB, gold)
    _center(draw, (W // 2, 875), "Mystic Flow Tarot", FONT_SMALL, (178, 145, 94))

    out = OUT_DIR / _safe_filename(card["image"])
    img.save(out, "JPEG", quality=92)


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    for index, card in enumerate(tarot_cards):
        create_card(card, index)
    print(f"created {len(tarot_cards)} cards in {OUT_DIR}")


if __name__ == "__main__":
    main()
