"""saju_storage.py 에서 3D 브리핑 인라인 블록 제거."""
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "saju_storage.py"
text = path.read_text(encoding="utf-8")
marker = "# ---END_SAJU_STORAGE---"
if marker not in text:
    raise SystemExit("marker not found")
head, _ = text.split(marker, 1)
path.write_text(head.rstrip() + "\n", encoding="utf-8")
print("trimmed", path, "to", len(head.splitlines()), "lines")
