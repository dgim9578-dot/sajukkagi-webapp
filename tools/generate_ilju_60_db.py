"""60일주 장문 DB (ilju_60.json) 생성 — personality·career·relationship 각 200자 이상."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from saju_app.ui.ilju_data import ILJU_JSON_PATH, write_ilju_json


def main() -> None:
    out = write_ilju_json()
    print(f"wrote 60 ilju profiles -> {out}")


if __name__ == "__main__":
    main()
