"""Restore saju/ui/step_02.py from Cursor local history MD08 (2026-05-22)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(
    r"C:\Users\Administrator\AppData\Roaming\Cursor\User\History\-904eee9\MD08.py"
)
DST = ROOT / "saju" / "ui" / "step_02.py"


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    text = text.replace(
        "from saju_app.ui import components as M\n",
        "from saju_app.ui import components as M\n\nSTEP2_UI_BUILD = \"2026-05-22-md08\"\n",
    )
    needle = "        unsafe_allow_html=True,\n    )\n\n    ret_after"
    repl = (
        "        unsafe_allow_html=True,\n    )\n"
        "    st.caption(f\"입력 화면 {STEP2_UI_BUILD} · 본인/상대 탭 · 접이식\")\n\n"
        "    ret_after"
    )
    if needle not in text:
        raise SystemExit("patch anchor not found in MD08 snapshot")
    text = text.replace(needle, repl, 1)
    DST.write_text(text, encoding="utf-8")
    print(f"restored {DST} ({len(text)} bytes)")


if __name__ == "__main__":
    main()
