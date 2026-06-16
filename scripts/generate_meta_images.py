#!/usr/bin/env python3
"""Genera JPG 1200×1200 para el catálogo de Meta (mínimo 500×500)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalogo"
OUT_DIR = CATALOG / "meta"
TARGET = 1200
BG = (255, 255, 255)


def export_for_meta(src: Path) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{src.stem}.jpg"
    with Image.open(src) as im:
        im = im.convert("RGBA")
        scale = min(TARGET / im.width, TARGET / im.height)
        w, h = int(im.width * scale), int(im.height * scale)
        resized = im.resize((w, h), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (TARGET, TARGET), BG)
        x = (TARGET - w) // 2
        y = (TARGET - h) // 2
        canvas.paste(resized, (x, y), resized)
        canvas.save(out, "JPEG", quality=88, optimize=True)
    return out


def main() -> None:
    sources = sorted(CATALOG.glob("*.webp"))
    if not sources:
        raise SystemExit("No hay imágenes .webp en catalogo/")
    for src in sources:
        out = export_for_meta(src)
        print(f"{src.name} → {out.relative_to(ROOT)} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
