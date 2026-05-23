"""Smoke-check Universal tarot assets for STEP 8."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tarot_assets import UNIVERSAL_DIR, universal_asset_status
from tarot_data import TAROT_CARDS


def main() -> int:
    status = universal_asset_status()
    print("Universal dir:", status["dir"])
    print("Dir exists:", status["dir_exists"])
    print("PNG files on disk:", status["png_on_disk"])
    print("Cards resolved:", status["cards_resolved"], "/", status["expected_cards"])
    print("Card back:", status["card_back"])
    print("Ready:", status["ready"])

    missing = [card["name"] for card in TAROT_CARDS if not Path(card["image"]).is_file()]
    if missing:
        print("\nMissing images (first 10):")
        for name in missing[:10]:
            print(" -", name)
        if len(missing) > 10:
            print(f" ... and {len(missing) - 10} more")
        return 1

    sample = TAROT_CARDS[0]
    print("\nSample card:", sample["name"])
    print("Sample path:", sample["image"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
