"""Generate Teams app icons (color 192x192, outline 32x32 transparent)
and package the manifest into appPackage/build/streaming-teams-agent.zip.

Run with:  uv run python scripts/build_teams_package.py
"""
from __future__ import annotations

import json
import os
import struct
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_PKG = ROOT / "appPackage"
BUILD = APP_PKG / "build"


def _png(width: int, height: int, rgba: tuple[int, int, int, int]) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    row = bytes([0]) + bytes(rgba) * width
    raw = row * height
    idat = zlib.compress(raw, 9)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def main() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    color_path = APP_PKG / "color.png"
    outline_path = APP_PKG / "outline.png"

    if not color_path.exists():
        color_path.write_bytes(_png(192, 192, (75, 83, 188, 255)))
    if not outline_path.exists():
        outline_path.write_bytes(_png(32, 32, (255, 255, 255, 0)))

    manifest = (APP_PKG / "manifest.json").read_text(encoding="utf-8")
    for key in ("TEAMS_APP_ID", "BOT_APP_ID", "BOT_DOMAIN"):
        manifest = manifest.replace("${{" + key + "}}", os.environ.get(key, key))

    out_zip = BUILD / "streaming-teams-agent.zip"
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", manifest)
        zf.write(color_path, "color.png")
        zf.write(outline_path, "outline.png")

    json.loads(manifest)
    print(f"Wrote {out_zip}")


if __name__ == "__main__":
    main()
