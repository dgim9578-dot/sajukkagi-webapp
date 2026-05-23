#!/usr/bin/env python3
"""Solid-color PNG icons for PWA (stdlib only). Run from repo root: python scripts/gen_pwa_icons.py"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(tag + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)


def png_rgb(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    r, g, b = rgb
    row = bytes([0]) + bytes([r, g, b]) * width
    raw = row * height
    comp = zlib.compress(raw, 9)
    out = b"\x89PNG\r\n\x1a\n"
    out += _png_chunk(
        b"IHDR",
        struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0),
    )
    out += _png_chunk(b"IDAT", comp)
    out += _png_chunk(b"IEND", b"")
    return out


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    icons = root / "static" / "icons"
    icons.mkdir(parents=True, exist_ok=True)
    # .streamlit theme.dark backgroundColor (#0A0A14)
    color = (10, 10, 20)
    for w in (192, 512):
        (icons / f"icon-{w}.png").write_bytes(png_rgb(w, w, color))
    print("Wrote", icons / "icon-192.png", icons / "icon-512.png")


if __name__ == "__main__":
    main()
