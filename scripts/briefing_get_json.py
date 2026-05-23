"""브리핑 JSON을 stdout으로 출력 (Next.js / 로컬 로더용).

Usage:
    python scripts/briefing_get_json.py <fingerprint>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from saju_storage import get_briefing_by_fingerprint, load_cached_briefing  # noqa: E402


def main() -> None:
    fp = str(sys.argv[1] if len(sys.argv) > 1 else "").strip()
    if not fp:
        print("null")
        return
    briefing = load_cached_briefing(fp) or get_briefing_by_fingerprint(fp)
    if not briefing:
        print("null")
        return
    print(json.dumps(briefing, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
