"""Restore project files from Cursor local history snapshot wV35 (~14h before latest)."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HIST = Path(r"C:\Users\Administrator\AppData\Roaming\Cursor\User\History")

COPIES: list[tuple[Path, Path]] = [
    (HIST / "-904eee9" / "wV35.py", ROOT / "saju" / "ui" / "step_02.py"),
    (HIST / "61c07c4a" / "H6Ai.py", ROOT / "saju_app" / "ui" / "components.py"),
    (HIST / "-1afd4bf1" / "oJah.py", ROOT / "saju_app" / "ui" / "steps" / "router.py"),
    (HIST / "286df76a" / "wuLb.py", ROOT / "saju_app" / "ui" / "steps" / "step02.py"),
]


def main() -> None:
    for src, dst in COPIES:
        if not src.is_file():
            raise SystemExit(f"missing snapshot: {src}")
        text = src.read_text(encoding="utf-8")
        if dst.name == "step_02.py":
            text = text.replace(
                "    else:\n        st.session_state.p_name = pn\n",
                '    else:\n        pn = ""\n        st.session_state.p_name = pn\n',
            )
            dst.write_text(text, encoding="utf-8")
        else:
            shutil.copy2(src, dst)
        print(f"restored {dst} ({dst.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
