#!/usr/bin/env python3
"""상담 아카이브 오래된 기록 정리 (cron / 작업 스케줄러).

예시 (PowerShell, 프로젝트 루트):
  .\\venv\\Scripts\\python.exe scripts\\archive_prune.py --days 180

Windows 작업 스케줄러:
  프로그램: C:\\...\\사주프로\\venv\\Scripts\\python.exe
  인수: scripts\\archive_prune.py --days 180
  시작 위치: C:\\...\\사주프로
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import saju_storage  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune old consultation archive records.")
    parser.add_argument(
        "--days",
        type=int,
        default=180,
        help="Keep records newer than this many days (default: 180).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=2000,
        help="Max rows deleted per SQLite/Redis batch (default: 2000).",
    )
    parser.add_argument(
        "--vacuum",
        action="store_true",
        help="Run SQLite VACUUM after delete (reclaims disk; may take time).",
    )
    args = parser.parse_args()
    result = saju_storage.archive_prune_old_records(
        args.days,
        batch_size=args.batch_size,
        vacuum_sqlite=bool(args.vacuum),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
