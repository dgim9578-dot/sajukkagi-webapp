"""Resolve Universal-style tarot PNG paths under static/tarot/universal."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent
UNIVERSAL_DIR = _PROJECT_ROOT / "static" / "tarot" / "universal"
LEGACY_DIR = _PROJECT_ROOT / "tarot_images"
CARD_BACK_FILENAME = "cardback.png"

_MAJOR_FILENAMES: tuple[str, ...] = (
    "0thefool.png",
    "1themagician.png",
    "2thehighpriestess.png",
    "3theempress.png",
    "4theemperor.png",
    "5thehierophant.png",
    "6thelovers.png",
    "7thechariot.png",
    "8strength.png",
    "9thehermit.png",
    "10wheeloffortune.png",
    "11justice.png",
    "12thehangedman.png",
    "13death.png",
    "14temperance.png",
    "15thedevil.png",
    "16thetower.png",
    "17thestar.png",
    "18themoon.png",
    "19thesun.png",
    "20judgement.png",
    "21theworld.png",
)

_MAJOR_NAMES: tuple[str, ...] = (
    "The Fool",
    "The Magician",
    "The High Priestess",
    "The Empress",
    "The Emperor",
    "The Hierophant",
    "The Lovers",
    "The Chariot",
    "Strength",
    "The Hermit",
    "Wheel of Fortune",
    "Justice",
    "The Hanged Man",
    "Death",
    "Temperance",
    "The Devil",
    "The Tower",
    "The Star",
    "The Moon",
    "The Sun",
    "Judgement",
    "The World",
)

_RANK_KEYS: dict[str, str] = {
    "Ace": "ace",
    "Two": "two",
    "Three": "three",
    "Four": "four",
    "Five": "five",
    "Six": "six",
    "Seven": "seven",
    "Eight": "eight",
    "Nine": "nine",
    "Ten": "ten",
    "Page": "page",
    "Knight": "knight",
    "Queen": "queen",
    "King": "king",
}

_SUIT_KEYS: dict[str, str] = {
    "Wands": "wands",
    "Cups": "cups",
    "Swords": "swords",
    "Pentacles": "pentacles",
}


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _fuzzy_universal_match(expected: str, index: dict[str, Path]) -> Path | None:
    if not expected:
        return None
    if expected in index:
        return index[expected]
    for key, path in index.items():
        if key == "cardback":
            continue
        if expected in key or key in expected:
            return path
    return None


@lru_cache(maxsize=1)
def _universal_index() -> dict[str, Path]:
    if not UNIVERSAL_DIR.is_dir():
        return {}
    return {_normalize(path.stem): path for path in UNIVERSAL_DIR.glob("*.png")}


def rw_filename_for_card(card_name: str) -> str | None:
    """Rider-Waite style names used in the uploaded deck (e.g. 0_The_Fool.png)."""
    name = card_name.strip()
    if name in _MAJOR_NAMES:
        idx = _MAJOR_NAMES.index(name)
        title = name.replace(" ", "_")
        return f"{idx}_{title}.png"
    if " of " not in name:
        return None
    rank, suit = name.split(" of ", 1)
    return f"{rank}_of_{suit}.png"


def universal_filename_for_card(card_name: str) -> str | None:
    name = card_name.strip()
    if name in _MAJOR_NAMES:
        return _MAJOR_FILENAMES[_MAJOR_NAMES.index(name)]
    if " of " not in name:
        return None
    rank, suit = name.split(" of ", 1)
    rank_key = _RANK_KEYS.get(rank)
    suit_key = _SUIT_KEYS.get(suit)
    if not rank_key or not suit_key:
        return None
    return f"{rank_key}of{suit_key}.png"


def resolve_card_image_path(
    card_name: str,
    *,
    legacy_image: str | None = None,
) -> str | None:
    """Return an absolute path to a card image, preferring static/tarot/universal."""
    index = _universal_index()
    for filename in (
        rw_filename_for_card(card_name),
        universal_filename_for_card(card_name),
    ):
        if not filename:
            continue
        universal_path = UNIVERSAL_DIR / filename
        if universal_path.is_file():
            return str(universal_path.resolve())
        expected = _normalize(Path(filename).stem)
        if index and expected in index:
            return str(index[expected].resolve())
        if index:
            fuzzy = _fuzzy_universal_match(expected, index)
            if fuzzy is not None:
                return str(fuzzy.resolve())

    if index:
        normalized_name = _normalize(card_name)
        if normalized_name in index:
            return str(index[normalized_name].resolve())
        fuzzy = _fuzzy_universal_match(normalized_name, index)
        if fuzzy is not None:
            return str(fuzzy.resolve())

    if legacy_image:
        legacy_path = Path(legacy_image)
        if not legacy_path.is_absolute():
            legacy_path = _PROJECT_ROOT / legacy_path
        if legacy_path.is_file():
            return str(legacy_path.resolve())
    return None


def resolve_card_back_path() -> str | None:
    path = UNIVERSAL_DIR / CARD_BACK_FILENAME
    if path.is_file():
        return str(path.resolve())
    index = _universal_index()
    return str(index[_normalize("cardback")].resolve()) if "cardback" in index else None


def universal_asset_status() -> dict[str, int | bool | str]:
    index = _universal_index()
    expected = 78
    matched = sum(
        1
        for name in _MAJOR_NAMES
        if resolve_card_image_path(name) is not None
    )
    for suit in _SUIT_KEYS:
        for rank in _RANK_KEYS:
            card_name = f"{rank} of {suit}"
            if resolve_card_image_path(card_name) is not None:
                matched += 1
    return {
        "dir_exists": UNIVERSAL_DIR.is_dir(),
        "dir": str(UNIVERSAL_DIR),
        "png_on_disk": len(index),
        "cards_resolved": matched,
        "expected_cards": expected,
        "ready": matched >= expected,
        "card_back": resolve_card_back_path() is not None,
    }
